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
        _REGISTRY[domain] = provider_cls
    return provider_cls


def route(url: str) -> BaseExtractor:
    """Return a provider instance for *url*, raising typed errors on failure."""
    parsed = urlparse(url)

    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise InvalidURLError(f"Invalid URL: {url!r}", url=url)

    # Use parsed.hostname (lowercased, port-stripped) for lookup; keep netloc for error messages
    hostname = (parsed.hostname or "").lower()

    # Resolve *.medium.com subdomains to the canonical "medium.com" registration
    lookup = "medium.com" if hostname.endswith(".medium.com") else hostname

    provider_cls = _REGISTRY.get(lookup)
    if provider_cls is None:
        raise UnsupportedPlatformError(
            f"No provider registered for domain {parsed.netloc!r}", url=url
        )

    return provider_cls()


def _autodiscover_providers() -> None:
    """Import every module in mdfetch.providers; classes decorated with @register self-enrol."""
    import mdfetch.providers as _providers_pkg  # noqa: PLC0415

    for _, module_name, _ in pkgutil.iter_modules(_providers_pkg.__path__):
        importlib.import_module(f"mdfetch.providers.{module_name}")


_autodiscover_providers()
