"""HTTP client for the Uttar Pradesh NIC GeP tender portal."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import httpx

from app.collectors.errors import HttpCollectionError, NetworkCollectionError, TimeoutCollectionError
from app.schemas.tender_source import SourceConfiguration

logger = logging.getLogger(__name__)

DEFAULT_BASE_URL = "https://etender.up.nic.in/nicgep/app"


class UPPortalClient:
    """Conservative, session-aware client for permitted public UP portal pages."""

    def __init__(
        self,
        configuration: SourceConfiguration,
        *,
        app_version: str = "0.1.0",
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.configuration = configuration
        self.base_url = str(configuration.source_url or f"{DEFAULT_BASE_URL}?page=Home&service=page")
        self.timeout = configuration.request_timeout_seconds
        self.request_delay = configuration.request_delay_seconds
        self.user_agent = (
            f"TenderIntelligencePlatform/{app_version} "
            "(+https://github.com/abhisheks2101/primeedgetender; UP-tender-collector)"
        )
        self._transport = transport
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> "UPPortalClient":
        self._client = httpx.AsyncClient(
            timeout=self.timeout,
            headers={"User-Agent": self.user_agent, "Accept": "text/html,application/xhtml+xml"},
            follow_redirects=True,
            transport=self._transport,
        )
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def _sleep_between_requests(self) -> None:
        if self.request_delay > 0:
            await asyncio.sleep(self.request_delay)

    async def _get_text(self, url: str, *, operation: str) -> str:
        if self._client is None:
            raise RuntimeError("UPPortalClient must be used as an async context manager.")

        await self._sleep_between_requests()
        try:
            response = await self._client.get(url)
        except httpx.TimeoutException as exc:
            raise TimeoutCollectionError(f"{operation} timed out for {url}.") from exc
        except httpx.RequestError as exc:
            raise NetworkCollectionError(f"{operation} network error for {url}: {exc}") from exc

        if response.status_code >= 400:
            retryable = response.status_code in {408, 429, 500, 502, 503, 504}
            raise HttpCollectionError(
                f"{operation} failed with HTTP {response.status_code} for {url}.",
                retryable=retryable,
            )

        logger.info("Fetched UP portal page", extra={"operation": operation, "url": url, "bytes": len(response.text)})
        return response.text

    async def fetch_home_listing(self) -> str:
        """Fetch the public home page containing the latest active tenders table."""
        return await self._get_text(self.base_url, operation="home_listing")

    async def fetch_detail_page(self, detail_url: str) -> str:
        """Fetch one tender detail page using the listing-provided URL."""
        return await self._get_text(detail_url, operation="tender_detail")

    def listing_page_url(self) -> str:
        return self.base_url
