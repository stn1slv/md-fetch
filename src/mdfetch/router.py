"""Domain-to-provider routing."""

from __future__ import annotations

import importlib
import pkgutil
from urllib.parse import urlparse

from mdfetch.base import BaseExtractor
from mdfetch.exceptions import InvalidURLError, UnsupportedPlatformError

_REGISTRY: dict[str, type[BaseExtractor]] = {}


def register(provider_cls: type[BaseExtractor]) -> type[BaseExtractor]:
    """Register *provider_cls* for each domain it declares."""
    for domain in provider_cls.DOMAINS:
        existing = _REGISTRY.get(domain)
        if existing is not None and existing is not provider_cls:
            raise ValueError(
                f"Domain {domain!r} is already registered to {existing.__name__!r}; "
                f"cannot re-register to {provider_cls.__name__!r}"
            )
        _REGISTRY[domain] = provider_cls
    return provider_cls


def route(url: str) -> BaseExtractor:
    """Return a provider instance for *url*, raising typed errors on failure."""
    parsed = urlparse(url)

    # Use parsed.hostname (lowercased, port-stripped) for routing and validation.
    # Checking hostname rather than netloc correctly rejects edge cases like
    # "https://:80/" where netloc is non-empty but hostname is None/empty.
    hostname = (parsed.hostname or "").lower()

    if parsed.scheme not in ("http", "https") or not hostname:
        raise InvalidURLError(f"Invalid URL: {url!r}", url=url)

    # Exact match first; fall back to a subdomain suffix check only for providers
    # that opt in via MATCH_SUBDOMAINS=True (multi-tenant sites like Medium and
    # Substack).  Sort candidates by length descending so the most-specific
    # suffix wins when multiple registered domains are suffixes of the same host.
    provider_cls = _REGISTRY.get(hostname)
    if provider_cls is None:
        for domain in sorted(_REGISTRY, key=len, reverse=True):
            candidate = _REGISTRY[domain]
            if candidate.MATCH_SUBDOMAINS and hostname.endswith(f".{domain}"):
                provider_cls = candidate
                break

    if provider_cls is None:
        raise UnsupportedPlatformError(f"No provider registered for domain {hostname!r}", url=url)

    return provider_cls()


def supported_domains() -> frozenset[str]:
    """Return the set of domains that have a registered provider."""
    return frozenset(_REGISTRY)


def _autodiscover_providers() -> None:
    """Import every module in mdfetch.providers; classes decorated with @register self-enrol."""
    import mdfetch.providers as _providers_pkg  # noqa: PLC0415

    for _, module_name, _ in pkgutil.iter_modules(_providers_pkg.__path__):
        importlib.import_module(f"mdfetch.providers.{module_name}")


_autodiscover_providers()
