# Provider Contract: BoomiExtractor

This is a library; its external contracts are (1) the public `extract()` API and
(2) the `BaseExtractor` subclass contract the new provider must satisfy.

## 1. Public API (unchanged)

```python
from mdfetch import extract

markdown: str = extract("https://boomi.com/blog/<slug>/", retries=3, retry_delay=2.0)
```

- **Input**: a `boomi.com` blog article URL (`str`).
- **Output**: clean Markdown (`str`), title-first.
- **Raises**: `UnsupportedPlatformError` (domain not registered — N/A once Boomi is registered),
  `UnsupportedContentTypeError`, `EmptyContentError`, `HTTPStatusError`, `FetchError`
  (all from `mdfetch.exceptions`). No new exception types.

## 2. Subclass contract

```python
@register
class BoomiExtractor(BaseExtractor):
    DOMAINS: frozenset[str] = frozenset({"boomi.com"})
    # MATCH_SUBDOMAINS stays False (default)

    def clean_html(self, soup: BeautifulSoup) -> Tag: ...
```

### `clean_html(soup)` obligations

| # | Obligation |
|---|------------|
| C1 | Return the `div.post-content` `Tag` with chrome stripped and the title prepended. |
| C2 | Raise `UnsupportedContentTypeError` when `div.post-content` is absent. |
| C3 | Decompose every `div.blog-nav` descendant before returning. |
| C4 | Prepend a copy of the page `<h1>` as the first child of the returned body. |
| C5 | MUST NOT modify the base class or shared utilities. |
| C6 | MUST NOT add image-specific logic (body images flow through default conversion). |

`extract()` and `convert_to_markdown()` are inherited unchanged; the latter enforces the
ATX-heading, blank-line-collapsing, and `EmptyContentError` behavior.

## 3. Acceptance contract (maps to spec SC-00x)

| Check | Maps to |
|-------|---------|
| Each reference article → Markdown begins with `# <title>` and contains body section headings + paragraph text; no chrome | SC-001, FR-002/003/004/005 |
| `extract("https://boomi.com/blog/")` (index) raises `UnsupportedContentTypeError` | SC-003, FR-006, FR-009 |
| Output has no 3+ consecutive blank lines | SC-004, FR-008 |
| ≥1 integration test hits a real reference URL with snapshot containment | SC-005 |

## 4. Routing contract

- After `@register`, `route("https://boomi.com/blog/...")` resolves to `BoomiExtractor`.
- `test_router.py` unsupported-domain fixture (`wordpress.com`) remains valid — no change needed.
