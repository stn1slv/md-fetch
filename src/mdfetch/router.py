"""Domain-to-provider routing."""

from __future__ import annotations

from urllib.parse import urlparse

from mdfetch.base import BaseExtractor
from mdfetch.exceptions import InvalidURLError, UnsupportedPlatformError

_REGISTRY: dict[str, type[BaseExtractor]] = {}

_MEDIUM_DOMAINS = ("medium.com", "www.medium.com")


def register(provider_cls: type[BaseExtractor]) -> type[BaseExtractor]:
    """Register *provider_cls* for each domain it declares."""
    for domain in provider_cls.DOMAINS:
        _REGISTRY[domain] = provider_cls
    return provider_cls


def route(url: str) -> BaseExtractor:
    """Return a provider instance for *url*, raising typed errors on failure."""
    parsed = urlparse(url)

    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise InvalidURLError(f"Invalid URL: {url!r}", url=url)

    netloc = parsed.netloc

    # Resolve medium.com subdomains (e.g. username.medium.com) to the base registration
    resolved = netloc
    if netloc.endswith(".medium.com") or netloc in _MEDIUM_DOMAINS:
        resolved = "medium.com"

    provider_cls = _REGISTRY.get(resolved)
    if provider_cls is None:
        raise UnsupportedPlatformError(f"No provider registered for domain {netloc!r}", url=url)

    return provider_cls()


def _register_builtin_providers() -> None:
    from mdfetch.providers.medium import MediumExtractor  # noqa: PLC0415

    register(MediumExtractor)


_register_builtin_providers()
