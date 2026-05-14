# Data Model: mdfetch — dev.to Extractor

**Branch**: `002-devto-provider` | **Date**: 2026-05-14

## Entities

This feature adds no new data structures. All entities are shared with the existing library model.

### URL
- **Representation**: Plain Python `str`
- **Routing key**: `hostname` extracted via `urllib.parse.urlparse`; dev.to provider registers `"dev.to"` — the router's existing subdomain suffix matching handles `www.dev.to` automatically
- **Validation**: Existing `InvalidURLError` raised by the router before the provider is invoked
- **Accepted forms**:
  - `https://dev.to/<username>/<article-slug>`  → article
  - `https://dev.to/<username>` → profile → `UnsupportedContentTypeError`
  - `https://dev.to/t/<tag>` → tag listing → `UnsupportedContentTypeError`

### Provider
- **New provider**: `DevToExtractor` implementing `BaseExtractor`
- **DOMAINS**: `frozenset({"dev.to"})`
- **Registered via**: `@register` decorator (auto-discovered by `_autodiscover_providers()`)
- **File**: `src/mdfetch/providers/devto.py` (one new file; no existing files modified)

### Extracted Article
- **Output**: `str` — clean Markdown with ATX-style headings
- **Content included**:
  - Title (`# Title` from article `<h1>`)
  - Cover image as `![alt](url)` (if present)
  - Article body: paragraphs, headings, code blocks, inline code, lists, blockquotes
  - Body images as `![alt](url)`
  - Embedded resources (Gists, CodePens, YouTube) as plain Markdown links `[url](url)`
- **Content excluded**:
  - Author name, avatar, publication date
  - Series navigation panels
  - Article tags (`#kafka`, `#api`, etc.)
  - Comments section
  - Reaction buttons
  - Advertisements

## State Transitions

None — extraction is a stateless, single-call operation with no persistent state.

## Error Cases

| Condition | Exception |
|-----------|-----------|
| URL has no `dev.to` domain | `UnsupportedPlatformError` (raised by router) |
| URL is syntactically invalid | `InvalidURLError` (raised by router) |
| HTTP request fails | `FetchError` |
| Non-2xx HTTP response | `HTTPStatusError` |
| `div#article-body` not found | `UnsupportedContentTypeError` |
| Article body has no extractable text | `EmptyContentError` |

All exception classes are defined in `mdfetch.exceptions` — no new classes needed.
