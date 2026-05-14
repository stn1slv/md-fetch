"""Abstract base class for all platform extractors."""

from __future__ import annotations

from abc import ABC, abstractmethod

import httpx
from bs4 import BeautifulSoup
from bs4.element import Tag

from mdfetch.exceptions import FetchError, HTTPStatusError


class BaseExtractor(ABC):
    """Contract all platform-specific extractors must fulfil."""

    DOMAINS: frozenset[str] = frozenset()

    # Standard browser UA — required for sites that block non-browser clients (see FR-014)
    _USER_AGENT = (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )

    def fetch_html(self, url: str) -> str:
        """Fetch raw HTML from *url* using a 30-second timeout."""
        headers = {"User-Agent": self._USER_AGENT}
        try:
            with httpx.Client(timeout=30.0, follow_redirects=True) as client:
                response = client.get(url, headers=headers)
        except httpx.TimeoutException as exc:
            raise FetchError(f"Request timed out: {url}", url=url) from exc
        except httpx.RequestError as exc:
            raise FetchError(f"Network error fetching {url}: {exc}", url=url) from exc

        if not response.is_success:
            raise HTTPStatusError(
                f"HTTP {response.status_code} fetching {url}",
                status_code=response.status_code,
                url=url,
            )

        return response.text

    @abstractmethod
    def clean_html(self, soup: BeautifulSoup) -> Tag:
        """Isolate the article body, strip non-content elements, and return the root Tag."""

    @abstractmethod
    def convert_to_markdown(self, tag: Tag) -> str:
        """Convert the cleaned Tag to a Markdown string."""

    def extract(self, url: str) -> str:
        """Orchestrate fetch → clean → convert and return Markdown."""
        html = self.fetch_html(url)
        soup = BeautifulSoup(html, "lxml")
        cleaned = self.clean_html(soup)
        return self.convert_to_markdown(cleaned)
