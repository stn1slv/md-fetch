"""mdfetch — extract article content from web platforms as clean Markdown."""

from __future__ import annotations

from mdfetch.exceptions import (
    EmptyContentError,
    FetchError,
    HTTPStatusError,
    InvalidURLError,
    MdfetchError,
    UnsupportedContentTypeError,
    UnsupportedPlatformError,
)
from mdfetch.router import route

__all__ = [
    "extract",
    "MdfetchError",
    "InvalidURLError",
    "UnsupportedPlatformError",
    "UnsupportedContentTypeError",
    "FetchError",
    "HTTPStatusError",
    "EmptyContentError",
]


def extract(url: str, *, retries: int = 3, retry_delay: float = 2.0) -> str:
    """Extract article content from *url* and return it as Markdown.

    On transient network failures (timeouts, connection errors, non-2xx responses) the
    request is attempted up to *retries* times total (so ``retries=3`` means one initial
    attempt plus two retries) with a fixed delay of *retry_delay* seconds between attempts.
    Set ``retries=1`` to disable retries.
    """
    return route(url).extract(url, retries=retries, retry_delay=retry_delay)
