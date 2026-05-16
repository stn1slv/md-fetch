"""Abstract base class for all platform extractors."""

from __future__ import annotations

import re
import time
from abc import ABC, abstractmethod
from typing import Any

import httpx
from bs4 import BeautifulSoup
from bs4.element import Tag
from markdownify import markdownify

from mdfetch.exceptions import (
    EmptyContentError,
    FetchError,
    HTTPStatusError,
    MdfetchError,
    UnsupportedContentTypeError,
)

_MAX_RESPONSE_BYTES = 10 * 1024 * 1024  # 10 MB — guard against runaway responses
_ACCEPTED_CONTENT_TYPES = frozenset({"text/html", "application/xhtml+xml"})


class BaseExtractor(ABC):
    """Contract all platform-specific extractors must fulfil."""

    DOMAINS: frozenset[str] = frozenset()
    _no_retry_status_codes: frozenset[int] = frozenset()

    # FR-014: use a browser-like UA (no mdfetch-specific branding) so servers serve readable HTML
    _USER_AGENT = (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )

    def fetch_html(
        self,
        url: str,
        *,
        retries: int = 3,
        retry_delay: float = 2.0,
        _no_retry_codes: frozenset[int] | None = None,
    ) -> str:
        """Fetch raw HTML from *url* using a 30-second timeout and a 10 MB size cap.

        Makes up to *retries* total attempts on transient :class:`FetchError` (network
        errors, timeouts, non-2xx responses) with a fixed delay of *retry_delay* seconds
        between attempts.  Status codes listed in :attr:`_no_retry_status_codes` are
        raised immediately without any retry or sleep.  Pass ``_no_retry_codes`` to
        override the class-level set for this call only (used internally for per-call
        overrides).
        """
        no_retry = self._no_retry_status_codes if _no_retry_codes is None else _no_retry_codes
        last_exc: FetchError | None = None
        with httpx.Client(timeout=30.0, follow_redirects=True) as client:
            for attempt in range(max(1, retries)):
                try:
                    return self._do_fetch(url, client)
                except FetchError as exc:
                    if isinstance(exc, HTTPStatusError) and exc.status_code in no_retry:
                        raise
                    last_exc = exc
                    if attempt < retries - 1:
                        time.sleep(retry_delay)
        if last_exc is None:
            raise RuntimeError("unreachable: retry loop completed without exception")
        raise last_exc

    def _do_fetch(self, url: str, client: httpx.Client) -> str:
        """Single HTTP fetch attempt (no retry logic)."""
        headers = {"User-Agent": self._USER_AGENT}
        try:
            with client.stream("GET", url, headers=headers) as response:
                if not response.is_success:
                    raise HTTPStatusError(
                        f"HTTP {response.status_code} fetching {url}",
                        status_code=response.status_code,
                        url=url,
                    )
                raw_ct = response.headers.get("content-type") or ""
                content_type = raw_ct.split(";")[0].strip().lower()
                if content_type and content_type not in _ACCEPTED_CONTENT_TYPES:
                    raise UnsupportedContentTypeError(
                        f"Expected HTML but got {content_type!r} from {url}",
                        url=url,
                    )
                chunks: list[bytes] = []
                total = 0
                for chunk in response.iter_bytes():
                    total += len(chunk)
                    if total > _MAX_RESPONSE_BYTES:
                        raise FetchError(
                            f"Response from {url} exceeded "
                            f"{_MAX_RESPONSE_BYTES // (1024 * 1024)} MB limit",
                            url=url,
                        )
                    chunks.append(chunk)
                return b"".join(chunks).decode(response.encoding or "utf-8", errors="replace")
        except httpx.TimeoutException as exc:
            raise FetchError(f"Request timed out: {url}", url=url) from exc
        except httpx.RequestError as exc:
            raise FetchError(f"Network error fetching {url}: {exc}", url=url) from exc

    @abstractmethod
    def clean_html(self, soup: BeautifulSoup) -> Tag:
        """Isolate the article body, strip non-content elements, and return the root Tag."""

    def _markdownify_kwargs(self) -> dict[str, Any]:
        """Return markdownify keyword arguments for this provider.

        The returned dict is merged with (and may override) the base defaults
        ``heading_style="ATX"``, ``code_language=""``, ``strip=["script","style"]``.
        Override in subclasses to customise or extend the conversion options.
        """
        return {}

    def convert_to_markdown(self, tag: Tag) -> str:
        """Convert the cleaned Tag to a Markdown string."""
        md = markdownify(
            str(tag),
            **{
                "heading_style": "ATX",
                "code_language": "",
                "strip": ["script", "style"],
                **self._markdownify_kwargs(),
            },
        )
        md = md.strip()
        md = re.sub(r"\n{3,}", "\n\n", md)

        if not md:
            raise EmptyContentError(
                "Article body contained no extractable text content",
            )

        return md

    @staticmethod
    def _replace_iframes_with_links(container: Tag, soup: BeautifulSoup) -> None:
        """Replace ``<iframe>`` elements inside *container* with plain anchor links."""
        for iframe in container.find_all("iframe"):
            src = str(iframe.get("src") or iframe.get("data-src") or "")
            if src:
                link = soup.new_tag("a", href=src)
                link.string = src
                iframe.replace_with(link)
            else:
                iframe.decompose()

    def extract(self, url: str, *, retries: int = 3, retry_delay: float = 2.0) -> str:
        """Orchestrate fetch → clean → convert and return Markdown."""
        html = self.fetch_html(url, retries=retries, retry_delay=retry_delay)
        soup = BeautifulSoup(html, "lxml")
        try:
            cleaned = self.clean_html(soup)
            return self.convert_to_markdown(cleaned)
        except MdfetchError as exc:
            if exc.url is None:
                exc.url = url
            raise
