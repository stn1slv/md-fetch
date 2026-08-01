"""mdfetch — extract article content from web platforms as clean Markdown."""

from __future__ import annotations

import os

from mdfetch.exceptions import (
    EmptyContentError,
    FetchError,
    HTTPStatusError,
    InvalidURLError,
    MdfetchError,
    MissingAPIKeyError,
    UnsupportedContentTypeError,
    UnsupportedPlatformError,
)
from mdfetch.fallback import tavily_extract
from mdfetch.router import route, supported_domains

__all__ = [
    "extract",
    "supported_domains",
    "MdfetchError",
    "InvalidURLError",
    "UnsupportedPlatformError",
    "UnsupportedContentTypeError",
    "FetchError",
    "HTTPStatusError",
    "EmptyContentError",
    "MissingAPIKeyError",
]


def extract(
    url: str,
    *,
    retries: int = 3,
    retry_delay: float = 2.0,
    tavily_fallback: bool = False,
) -> str:
    """Extract article content from *url* and return it as Markdown.

    On transient network failures (timeouts, connection errors, non-2xx responses) the
    request is attempted up to *retries* times total (so ``retries=3`` means one initial
    attempt plus two retries) with a fixed delay of *retry_delay* seconds between attempts.
    Set ``retries=1`` to disable retries.
    """
    if tavily_fallback and not os.environ.get("TAVILY_API_KEY"):
        raise MissingAPIKeyError(
            "TAVILY_API_KEY environment variable is required when fallback is enabled."
        )

    try:
        return route(url).extract(url, retries=retries, retry_delay=retry_delay)
    except Exception as e:
        if not tavily_fallback:
            raise
        if isinstance(e, (MissingAPIKeyError, InvalidURLError)):
            raise

        return tavily_extract(url, timeout=30.0)
