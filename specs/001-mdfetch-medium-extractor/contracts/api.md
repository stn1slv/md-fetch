# Public API Contract: mdfetch

**Phase**: 1 | **Date**: 2026-05-14 | **Plan**: [../plan.md](../plan.md)

This document defines the complete public surface of the `mdfetch` library for v0.1.0. Everything listed here is importable by callers. Nothing else is part of the public contract.

---

## Public Function: `extract`

```python
from mdfetch import extract

def extract(url: str) -> str: ...
```

**Description**: Fetches the article at `url`, extracts its readable body, and returns it as a clean Markdown string.

**Parameters**:

| Parameter | Type | Required | Description |
|---|---|---|---|
| `url` | `str` | Yes | Fully-qualified URL of the article (must include scheme: `http://` or `https://`) |

**Returns**: `str` — the article body as Markdown. Non-empty on success.

**Raises**:

| Exception | Condition |
|---|---|
| `mdfetch.InvalidURLError` | `url` is syntactically invalid or missing scheme |
| `mdfetch.UnsupportedPlatformError` | `url` domain has no registered provider |
| `mdfetch.UnsupportedContentTypeError` | domain is recognised but the page is not an article (e.g., profile, tag page) |
| `mdfetch.FetchError` | network error or connection timeout |
| `mdfetch.HTTPStatusError` | server returned a non-2xx HTTP status; exposes `.status_code: int` |
| `mdfetch.EmptyContentError` | article body was found but contained no extractable text |

**Behaviour guarantees**:
- Deterministic: given the same live page, returns the same Markdown structure
- No side effects: no files written, no global state modified
- Thread safety: safe to call from multiple threads (no shared mutable state)

---

## Public Exceptions

All exceptions are importable directly from `mdfetch`:

```python
from mdfetch import (
    MdfetchError,
    InvalidURLError,
    UnsupportedPlatformError,
    UnsupportedContentTypeError,
    FetchError,
    HTTPStatusError,
    EmptyContentError,
)
```

### `MdfetchError`

Base class for all library exceptions. Catch this to handle any `mdfetch` failure with a single `except` clause.

```python
class MdfetchError(Exception):
    message: str
    url: str | None
```

### `InvalidURLError(MdfetchError)`

Raised when the input string cannot be parsed as a valid URL or is missing a scheme.

### `UnsupportedPlatformError(MdfetchError)`

Raised when the URL's domain does not match any registered provider.

### `UnsupportedContentTypeError(MdfetchError)`

Raised when the URL's domain is recognised (e.g., `medium.com`) but the page is not an extractable article (e.g., a tag page or author profile).

### `FetchError(MdfetchError)`

Raised when the HTTP request fails due to a network error or timeout.

### `HTTPStatusError(FetchError)`

Raised when the server responds with a non-2xx status code.

```python
class HTTPStatusError(FetchError):
    status_code: int  # e.g., 404, 503
```

### `EmptyContentError(MdfetchError)`

Raised when the article body element is located but yields no extractable text content.

---

## Provider Extension Contract (internal, not public API)

For developers extending the library with new providers (not part of the v1 public surface, documented here for completeness):

```python
from abc import ABC, abstractmethod
from bs4 import BeautifulSoup
from bs4.element import Tag

class BaseExtractor(ABC):
    DOMAINS: frozenset[str]  # domains this provider handles

    def extract(self, url: str) -> str:
        """Orchestrates fetch → clean → convert. Implemented in base class."""

    def fetch_html(self, url: str) -> str:
        """HTTP GET; raises FetchError / HTTPStatusError. Implemented in base class."""

    @abstractmethod
    def clean_html(self, soup: BeautifulSoup) -> Tag:
        """Platform-specific: locate article body, strip noise, return the root Tag."""

    @abstractmethod
    def convert_to_markdown(self, tag: Tag) -> str:
        """Platform-specific: convert cleaned Tag to Markdown string."""
```

**Adding a new provider**:
1. Create `src/mdfetch/providers/<platform>.py`
2. Define a class inheriting `BaseExtractor`, set `DOMAINS`, implement `clean_html` and `convert_to_markdown`
3. Decorate the class with `@register` (imported from `mdfetch.router`)
4. No other files need to change — the router auto-discovers all provider modules at import time (SC-006)

---

## Usage Examples

```python
from mdfetch import extract, MdfetchError, UnsupportedPlatformError

# Happy path
markdown = extract("https://medium.com/@author/some-article-slug")
print(markdown)

# Error handling
try:
    markdown = extract("https://dev.to/some-post")
except UnsupportedPlatformError as e:
    print(f"Platform not supported: {e.message}")
except MdfetchError as e:
    print(f"Extraction failed: {e.message}")
```
