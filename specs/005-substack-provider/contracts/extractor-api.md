# Contract: SubstackExtractor Public API

This document defines the public contract for `SubstackExtractor`, which follows the same interface as all mdfetch providers.

## Registration

```python
from mdfetch.providers.substack import SubstackExtractor

SubstackExtractor.DOMAINS  # frozenset({"substack.com"})
```

The `@register` decorator auto-registers the extractor for `substack.com` and all `*.substack.com` subdomains when the module is imported. The router's autodiscovery imports it automatically.

## Method: `extract`

```python
def extract(self, url: str, *, retries: int = 3, retry_delay: float = 2.0) -> str
```

**Parameters**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `url` | `str` | — | A fully qualified `http(s)://` URL on `substack.com` or `*.substack.com` |
| `retries` | `int` | `3` | Total fetch attempts (including first) on transient errors |
| `retry_delay` | `float` | `2.0` | Fixed delay in seconds between retries |

**Returns**: `str` — the article content as ATX-style Markdown. Begins with `# Article Title`. Subtitle (if present) follows as `### Subtitle`. Body prose, headings, lists, code blocks, images, and hyperlinks follow.

**Raises**

| Exception | Condition |
|-----------|-----------|
| `UnsupportedContentTypeError` | Fetched page lacks `div.body.markup` (not an article) |
| `EmptyContentError` | Article body is present but yields no extractable text |
| `HTTPStatusError` | Non-2xx HTTP response after all retries exhausted |
| `FetchError` | Network error or timeout after all retries exhausted |
| `InvalidURLError` | URL scheme is not `http`/`https` or hostname is empty (raised by router before extractor is invoked) |

**HTTP 429 behaviour**: treated as a transient error and retried up to `retries` times with `retry_delay` seconds between attempts (no immediate-raise override).

## Top-level `extract()` function

The public entry point in `mdfetch.__init__` routes Substack URLs to this extractor automatically:

```python
from mdfetch import extract

markdown = extract("https://getkafkanated.substack.com/p/kafka-deserves-topic-types")
```

## Output Guarantees

- No consecutive blank-line runs of three or more lines.
- No subscription CTAs, navigation, author bio, or engagement buttons.
- For paywalled posts: returns only the freely visible preview; no exception; no truncation marker.
- Images rendered as `![alt text](https://…)`.
- Embeds (iframes, Substack embed containers) rendered as plain hyperlinks `[url](url)`.
