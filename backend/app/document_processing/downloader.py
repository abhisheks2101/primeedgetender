"""Safe tender document downloader."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass

import httpx

from app.core.enums import TenderDocumentErrorCode
from app.document_processing.url_validation import URLValidationError, validate_document_url

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class DownloadResult:
    success: bool
    content: bytes | None = None
    content_type: str | None = None
    status_code: int | None = None
    error_code: TenderDocumentErrorCode | None = None
    error_message: str | None = None
    access_restricted: bool = False


class DocumentDownloader:
    def __init__(
        self,
        *,
        timeout_seconds: int,
        max_size_bytes: int,
        retries: int,
        delay_seconds: float,
        allowed_domains: list[str],
    ) -> None:
        self.timeout_seconds = timeout_seconds
        self.max_size_bytes = max_size_bytes
        self.retries = retries
        self.delay_seconds = delay_seconds
        self.allowed_domains = allowed_domains

    async def download(self, url: str) -> DownloadResult:
        try:
            validate_document_url(url, allowed_domains=self.allowed_domains)
        except URLValidationError as exc:
            return DownloadResult(False, error_code=TenderDocumentErrorCode.INVALID_FILE, error_message=str(exc))

        last_error: DownloadResult | None = None
        for attempt in range(1, self.retries + 1):
            if attempt > 1 and self.delay_seconds:
                await asyncio.sleep(self.delay_seconds)
            result = await self._download_once(url)
            if result.success:
                return result
            last_error = result
            if result.access_restricted or result.error_code in {
                TenderDocumentErrorCode.INVALID_FILE,
                TenderDocumentErrorCode.FILE_TOO_LARGE,
                TenderDocumentErrorCode.ACCESS_RESTRICTED,
            }:
                break
        return last_error or DownloadResult(False, error_code=TenderDocumentErrorCode.UNKNOWN_ERROR, error_message="Download failed.")

    async def _download_once(self, url: str) -> DownloadResult:
        try:
            async with httpx.AsyncClient(follow_redirects=True, timeout=self.timeout_seconds) as client:
                async with client.stream("GET", url) as response:
                    if response.status_code in {401, 403}:
                        return DownloadResult(
                            False,
                            status_code=response.status_code,
                            error_code=TenderDocumentErrorCode.ACCESS_RESTRICTED,
                            error_message="Document access is restricted.",
                            access_restricted=True,
                        )
                    if response.status_code >= 400:
                        return DownloadResult(
                            False,
                            status_code=response.status_code,
                            error_code=TenderDocumentErrorCode.HTTP_ERROR,
                            error_message=f"HTTP {response.status_code} while downloading document.",
                        )

                    chunks: list[bytes] = []
                    total = 0
                    async for chunk in response.aiter_bytes():
                        total += len(chunk)
                        if total > self.max_size_bytes:
                            return DownloadResult(
                                False,
                                error_code=TenderDocumentErrorCode.FILE_TOO_LARGE,
                                error_message="Document exceeds configured maximum size.",
                            )
                        chunks.append(chunk)

                    content = b"".join(chunks)
                    lowered = content[:512].lower()
                    if b"captcha" in lowered or b"login" in lowered and b"password" in lowered:
                        return DownloadResult(
                            False,
                            status_code=response.status_code,
                            error_code=TenderDocumentErrorCode.ACCESS_RESTRICTED,
                            error_message="Document appears to require authentication or CAPTCHA.",
                            access_restricted=True,
                        )
                    return DownloadResult(
                        True,
                        content=content,
                        content_type=response.headers.get("content-type"),
                        status_code=response.status_code,
                    )
        except httpx.TimeoutException:
            return DownloadResult(False, error_code=TenderDocumentErrorCode.TIMEOUT, error_message="Document download timed out.")
        except httpx.RequestError as exc:
            logger.warning("Document download network error: %s", exc)
            return DownloadResult(False, error_code=TenderDocumentErrorCode.NETWORK_ERROR, error_message=str(exc))
