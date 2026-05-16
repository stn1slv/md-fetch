# Public API Contract: dzone.com Provider

**Branch**: `007-dzone-provider` | **Date**: 2026-05-16

## Library Interface (unchanged)

The dzone.com provider is exposed through the existing `mdfetch.extract()` public API. No new public symbols are added.

```python
from mdfetch import extract

markdown: str = extract(
    url="https://dzone.com/articles/integration-patterns-fail-production",
    retries=3,        # optional, default 3
    retry_delay=2.0,  # optional, default 2.0
)
```

### Inputs

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `url` | `str` | Yes | Must be an `https://dzone.com/articles/<slug>` URL |
| `retries` | `int` | No | Number of retry attempts on transient failures |
| `retry_delay` | `float` | No | Seconds between retries |

### Outputs

| Condition | Return / Exception |
|-----------|-------------------|
| Success | `str` — clean Markdown; title as `# H1`, body content with headings, lists, links, code blocks |
| Not an article page (no `div.content-html`) | `UnsupportedContentTypeError` |
| Article has no extractable text | `EmptyContentError` |
| HTTP error after retries | `HTTPStatusError` |
| Network / timeout | `FetchError` |
| Non-http(s) or malformed URL | `InvalidURLError` |
| Domain not supported | `UnsupportedPlatformError` |

### Output Format Guarantees

- First line: `# <article title>`
- Body: full article prose with headings, lists, links, images, and code blocks preserved
- Code blocks: fenced triple-backtick with lowercased language info string (e.g., ` ```java `); bare backticks when language is "Plain Text" or absent
- No consecutive blank-line runs of 3 or more lines
- No navigation, ads, sidebar, sign-in prompts, tag pills, author metadata, or UI chrome

## Routing Contract

`dzone.com` is registered via the `@register` decorator on `DZoneExtractor`. The router matches on exact domain (no subdomain wildcard needed).

```python
DOMAINS: frozenset[str] = frozenset({"dzone.com"})
```
