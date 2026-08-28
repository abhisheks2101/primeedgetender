"""HTTP client for the Madhya Pradesh NIC GeP tender portal."""

from __future__ import annotations

import asyncio
import logging

import httpx

from app.collectors.errors import HttpCollectionError, NetworkCollectionError, TimeoutCollectionError
from app.schemas.tender_source import SourceConfiguration

logger = logging.getLogger(__name__)

DEFAULT_BASE_URL = "https://mptenders.gov.in/nicgep/app"
PORTAL_ORIGIN = "https://mptenders.gov.in"


class MPPortalClient:
    """Conservative, session-aware client for permitted public MP portal pages."""

    def __init__(
        self,
        configuration: SourceConfiguration,
        *,
        app_version: str = "0.1.0",
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.configuration = configuration
        self.base_url = str(configuration.source_url or f"{DEFAULT_BASE_URL}?page=Home&service=page")
        self.read_timeout = max(float(configuration.request_timeout_seconds), 60.0)
        self.request_delay = configuration.request_delay_seconds
        self.user_agent = (
            f"TenderIntelligencePlatform/{app_version} "
            "(+https://github.com/abhisheks2101/primeedgetender; MP-tender-collector)"
        )
        self._transport = transport
        self._client: httpx.AsyncClient | None = None
        self._session_ready = False

    def _build_timeout(self) -> httpx.Timeout:
        return httpx.Timeout(
            connect=min(30.0, self.read_timeout),
            read=self.read_timeout,
            write=30.0,
            pool=30.0,
        )

    async def __aenter__(self) -> "MPPortalClient":
        self._client = httpx.AsyncClient(
            timeout=self._build_timeout(),
            headers={
                "User-Agent": self.user_agent,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-IN,en;q=0.9",
            },
            follow_redirects=True,
            transport=self._transport,
            http2=False,
        )
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None
        self._session_ready = False

    async def _sleep_between_requests(self) -> None:
        if self.request_delay > 0:
            await asyncio.sleep(self.request_delay)

    async def _ensure_session(self) -> None:
        if self._session_ready:
            return
        await self.fetch_home_listing()
        self._session_ready = True

    async def _get_text(self, url: str, *, operation: str, referer: str | None = None) -> str:
        if self._client is None:
            raise RuntimeError("MPPortalClient must be used as an async context manager.")

        await self._sleep_between_requests()
        headers = {"Referer": referer or self.base_url} if referer or operation == "tender_detail" else None
        try:
            response = await self._client.get(url, headers=headers)
        except httpx.TimeoutException as exc:
            raise TimeoutCollectionError(
                f"{operation} timed out after {self.read_timeout:.0f}s for {url}. "
                "The MP portal can be slow; try increasing request_timeout_seconds on the source."
            ) from exc
        except httpx.RequestError as exc:
            raise NetworkCollectionError(f"{operation} network error for {url}: {exc}") from exc

        if response.status_code >= 400:
            retryable = response.status_code in {408, 429, 500, 502, 503, 504}
            raise HttpCollectionError(
                f"{operation} failed with HTTP {response.status_code} for {url}.",
                retryable=retryable,
            )

        logger.info(
            "Fetched MP portal page",
            extra={"operation": operation, "url": url, "bytes": len(response.text)},
        )
        return response.text

    async def fetch_home_listing(self) -> str:
        html = await self._get_text(self.base_url, operation="home_listing")
        self._session_ready = True
        return html

    async def fetch_detail_page(self, detail_url: str) -> str:
        if not self._session_ready:
            await self._ensure_session()
        return await self._get_text(
            detail_url,
            operation="tender_detail",
            referer=self.base_url,
        )

    def listing_page_url(self) -> str:
        return self.base_url
