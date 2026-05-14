# Public API Contract: mdfetch — dev.to Extractor

**Branch**: `002-devto-provider` | **Date**: 2026-05-14

## Overview

The dev.to extractor introduces no new public API surface. The existing `mdfetch.extract()` function is the sole entry point — callers use it identically for Medium and dev.to URLs.

## `mdfetch.extract(url, *, retries=3, retry_delay=2.0) -> str`

```python
from mdfetch import extract

markdown = extract("https://dev.to/stn1slv/integration-digest-for-december-2025-5dlp")
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `url` | `str` | required | Full URL of a dev.to article |
| `retries` | `int` | `3` | Number of fetch attempts before raising |
| `retry_delay` | `float` | `2.0` | Seconds between retry attempts |

### Return value

A `str` containing the article's content as Markdown. Structure:

```markdown
# Article Title

![Cover image for Article Title](https://...)

## Section Heading

Paragraph text with [links](https://...).

- List item
- List item

```python
code block
```

[https://gist.github.com/...](https://gist.github.com/...)
```

### Exceptions

All exceptions inherit from `mdfetch.MdfetchError` and carry `.url` and `.message` attributes.

| Exception | When raised |
|-----------|------------|
| `InvalidURLError` | `url` is syntactically invalid |
| `UnsupportedPlatformError` | Domain is not `dev.to` (or other registered domain) |
| `UnsupportedContentTypeError` | `dev.to` URL is not an article (profile, tag, etc.) |
| `FetchError` | Network error or timeout |
| `HTTPStatusError` | Non-2xx HTTP response (adds `.status_code`) |
| `EmptyContentError` | Article body found but contains no text |

### Routing

The router auto-discovers `DevToExtractor` at import time. No configuration required. Adding the provider file to `src/mdfetch/providers/devto.py` is sufficient for routing to work.

## `DevToExtractor` (internal)

Not part of the public API. Exposed only for testing via direct instantiation.

```python
from mdfetch.providers.devto import DevToExtractor

extractor = DevToExtractor()
html = extractor.fetch_html(url)
from bs4 import BeautifulSoup
soup = BeautifulSoup(html, "lxml")
cleaned = extractor.clean_html(soup)
markdown = extractor.convert_to_markdown(cleaned)
```
