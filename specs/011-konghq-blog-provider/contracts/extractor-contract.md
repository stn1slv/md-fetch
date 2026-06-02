# Provider Contract: KongExtractor

This is a library; its external contracts are (1) the public `extract()` API and
(2) the `BaseExtractor` subclass contract the new provider must satisfy.

## 1. Public API (unchanged)

```python
from mdfetch import extract

markdown: str = extract("https://konghq.com/blog/<category>/<slug>", retries=3, retry_delay=2.0)
```

- **Input**: a `konghq.com` blog article URL (`str`).
- **Output**: clean Markdown (`str`), title-first, with the publication date under the title.
- **Raises**: `UnsupportedPlatformError` (domain not registered — N/A once Kong is registered),
  `UnsupportedContentTypeError`, `EmptyContentError`, `HTTPStatusError`, `FetchError`
  (all from `mdfetch.exceptions`). No new exception types.

## 2. Subclass contract

```python
@register
class KongExtractor(BaseExtractor):
    DOMAINS: frozenset[str] = frozenset({"konghq.com"})
    # MATCH_SUBDOMAINS stays False (default)

    def clean_html(self, soup: BeautifulSoup) -> Tag: ...
```

### `clean_html(soup)` obligations

| # | Obligation |
|---|------------|
| C1 | Return a `Tag` containing: a copy of the page `<h1>`, then the publication date (when present), then the cleaned article body, in that order. |
| C2 | Raise `UnsupportedContentTypeError` when `main.type-article` is absent (index, category listing, non-article). |
| C3 | Select the body as the `main` `<section>` with the most `.rich-text-block` descendants; raise `UnsupportedContentTypeError` if none. |
| C4 | Decompose in-body chrome: `.component.video`, `.component.more-on-this`, `[class*="TableOfContents"]`, `.order-top`, and trailing `.section-header-block` not carrying `intro`. |
| C5 | Keep the publication date (hero `<div>` matching a month-name date pattern); MUST NOT include author bylines or read time. |
| C6 | Depend only on stable companion classes (no hashed `__xxxxx` CSS-module suffixes). |
| C7 | MUST NOT modify the base class or shared utilities; MUST NOT add image-specific logic (body images flow through default conversion). |

`extract()` and `convert_to_markdown()` are inherited unchanged; the latter enforces the
ATX-heading, blank-line-collapsing, and `EmptyContentError` behavior.

## 3. Acceptance contract (maps to spec SC-00x)

| Check | Maps to |
|-------|---------|
| Each reference article → Markdown begins with `# <title>` and contains body section headings + paragraph text; no chrome | SC-001, FR-002/003/004/005 |
| Publication date appears under the title; no author byline / read-time text | SC-006, FR-004 |
| `extract("https://konghq.com/blog")` (index) raises `UnsupportedContentTypeError` | SC-003, FR-006, FR-009 |
| Output has no 3+ consecutive blank lines | SC-004, FR-008 |
| ≥1 integration test hits a real reference URL with snapshot containment | SC-005 |

## 4. Routing contract

- After `@register`, `route("https://konghq.com/blog/...")` resolves to `KongExtractor`.
- `test_router.py` unsupported-domain fixture (`wordpress.com`) remains valid — no change needed.
