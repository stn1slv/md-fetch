# Public API Contract: thenewstack.io Provider

**Branch**: `006-thenewstack-provider` | **Date**: 2026-05-16

## Library Interface (unchanged)

The thenewstack.io provider is exposed through the existing `mdfetch.extract()` public API. No new public symbols are added.

```python
from mdfetch import extract

markdown: str = extract(
    url="https://thenewstack.io/using-a-developer-portal-for-api-management/",
    retries=3,        # optional, default 3
    retry_delay=2.0,  # optional, default 2.0
)
```

### Inputs

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `url` | `str` | Yes | Must be an `http(s)://thenewstack.io/<slug>/` URL |
| `retries` | `int` | No | Number of retry attempts on transient failures |
| `retry_delay` | `float` | No | Seconds between retries |

### Outputs

| Condition | Return / Exception |
|-----------|-------------------|
| Success | `str` — clean Markdown, title as `# H1`, optional deck as paragraph, body content |
| Not an article page | `UnsupportedContentTypeError` |
| Article has no extractable text | `EmptyContentError` |
| HTTP error after retries | `HTTPStatusError` |
| Network / timeout | `FetchError` |
| Non-http(s) or malformed URL | `InvalidURLError` |
| Domain not supported | `UnsupportedPlatformError` |

### Output Format Guarantees

- First line: `# <article title>`
- Second block (when deck present): `<deck text as plain paragraph>`
- Body: full article prose with headings, lists, links, images preserved
- No consecutive blank-line runs of 3 or more lines
- No sponsored-content disclosure text
- No navigation, byline, poll, or footer text

## Routing Contract

`thenewstack.io` is registered via the `@register` decorator on `TheNewStackExtractor`. The router matches on exact domain (no subdomain wildcard needed).

```python
DOMAINS: frozenset[str] = frozenset({"thenewstack.io"})
```
