"""Custom exception hierarchy for mdfetch."""

from __future__ import annotations


class MdfetchError(Exception):
    """Base exception for all mdfetch errors."""

    def __init__(self, message: str, url: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.url = url


class InvalidURLError(MdfetchError):
    """Raised when the supplied URL is syntactically invalid."""


class UnsupportedPlatformError(MdfetchError):
    """Raised when the URL domain has no registered provider."""


class UnsupportedContentTypeError(MdfetchError):
    """Raised when the domain is recognised but the page is not an extractable article."""


class FetchError(MdfetchError):
    """Raised when a network request fails (connection error, timeout)."""


class HTTPStatusError(FetchError):
    """Raised when the server returns a non-2xx HTTP status code."""

    def __init__(self, message: str, status_code: int, url: str | None = None) -> None:
        super().__init__(message, url)
        self.status_code = status_code


class EmptyContentError(MdfetchError):
    """Raised when the article body yields no extractable text content."""
