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


def extract(url: str) -> str:
    """Extract article content from *url* and return it as Markdown."""
    return route(url).extract(url)
