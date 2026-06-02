# Implementation Plan: Boomi Blog Provider

**Branch**: `010-boomi-blog-provider` | **Date**: 2026-06-02 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/010-boomi-blog-provider/spec.md`

## Summary

Add a new provider that extracts public Boomi blog articles (`boomi.com/blog/<slug>/`) and returns them as clean Markdown. The site runs WordPress; all three reference articles share an identical, stable structure: the article body is `div.post-content`, which contains the real content (`section.wysiwyg-section`) plus a previous/next post navigation block (`div.blog-nav`) to strip. The article title is an `<h1>` rendered in the page hero (`section.post-detail-hero`), outside the body. The blog index, non-article pages, and other `boomi.com` pages do **not** contain `div.post-content`, so its absence cleanly signals "not an article" → `UnsupportedContentTypeError`. The implementation is a single new provider file subclassing `BaseExtractor`, reusing all shared fetch/convert logic.

## Technical Context

**Language/Version**: Python 3.12+ (matches CI matrix: 3.12–3.14)

**Primary Dependencies**: `httpx` (HTTP fetch), `BeautifulSoup` / `lxml` (HTML parsing), `markdownify` (Markdown conversion), `pytest` (testing)

**Storage**: N/A — stateless extraction library

**Testing**: `pytest` via `uv run pytest` — unit tests (no network) + integration tests (`-m integration`, real URLs + snapshots)

**Target Platform**: PyPI library (cross-platform)

**Project Type**: Library

**Performance Goals**: Inherits base class 30-second fetch timeout; no additional targets

**Constraints**: One new provider file; no changes to shared infrastructure

**Scale/Scope**: Single-article extraction per call

## Constitution Check

*GATE: Must pass before implementation. Re-check after design phase.*

- [x] Validates Provider Pattern Architecture (new `BoomiExtractor(BaseExtractor)`; no base-class changes; no code duplication — reuses `fetch_html`/`convert_to_markdown`)
- [x] Confirms Technology Stack (`httpx`, `BeautifulSoup`, `Markdownify`, `pytest` — all inherited)
- [x] Adheres to Coding Standards (PEP 8, strict type hints, clear vocabulary)
- [x] Incorporates Integration Testing (real reference URLs + snapshot containment, matching existing providers)
- [x] Respects Packaging and Distribution standards (`pyproject.toml`, `src/` layout, `uv` for all dev commands)

**Result**: PASS — no violations. Complexity Tracking not required.

## Project Structure

### Documentation (this feature)

```text
specs/010-boomi-blog-provider/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   └── extractor-contract.md   # Phase 1 output (provider contract)
└── tasks.md             # Phase 2 output (/speckit-tasks — NOT created here)
```

### Source Code

```text
src/mdfetch/providers/
└── boomi.py                          # NEW: BoomiExtractor

tests/unit/
└── test_boomi_extractor.py           # NEW: unit tests (no network)

tests/integration/
├── snapshots/
│   ├── boomi-gartner-magic-quadrant-ipaas-2026.md          # NEW
│   ├── boomi-real-time-vs-batch-data-integration.md        # NEW
│   └── boomi-data-consistency-saas-on-prem.md              # NEW
└── test_boomi_integration.py         # NEW: integration tests (real URLs)
```

**Non-runtime changes**: `README.md` (add Boomi row to Supported platforms table + usage example); `pyproject.toml` (version bump `0.5.2` → `0.6.0`, new provider = minor per dev.to/Substack precedent); `CLAUDE.md` (provider tree + integration-test description + Boomi discriminator gotcha). No `test_router.py` fixture change required — the unsupported-domain fixture uses `wordpress.com`, which Boomi does not register.

### Revision: Implementation Sync 2026-06-02
- Reason: Reconciled release/docs drift found after implementation — version was not bumped and `CLAUDE.md` (project structure, integration-test description, gotchas) did not reflect the new Boomi provider. No behavioral drift; extraction output verified clean against all 3 reference articles.

## Extraction Algorithm

```
extract(url):                                  # inherited from BaseExtractor
  html ← fetch_html(url)                        # 30s timeout, 3 retries on transient errors
  soup ← BeautifulSoup(html, "lxml")
  body_tag ← clean_html(soup)
  return convert_to_markdown(body_tag)          # ATX headings, collapse 3+ blank lines, EmptyContentError if blank

clean_html(soup):                              # BoomiExtractor implementation
  1. body ← soup.find("div", class_="post-content")
        → if not a Tag: raise UnsupportedContentTypeError   # index / non-article / non-blog page
  2. for nav in body.find_all("div", class_="blog-nav"): nav.decompose()   # strip prev/next chrome
  3. title ← soup.find("h1")                    # hero title, outside body
        → if Tag: body.insert(0, copy.copy(title))          # prepend as top-level heading
  4. return body
```

**Design notes**:
- `div.post-content` is the *discriminating* selector: present on every article, absent on the blog index and non-article pages (verified live across 3 articles + the `/blog/` index). This is why no URL-path filtering is needed (FR-009 satisfied via body-container presence, consistent with the existing route-by-domain pattern).
- Body images live inside `post-content` and are preserved by default markdownify (Option A clarification). The hero/banner image sits in `section.post-detail-hero` — outside the body — and is therefore excluded automatically. No image-specific code is needed.
- Blockquotes (e.g., the Gartner pull-quote) are inside `wysiwyg-section` and convert natively. No embed/iframe handling observed in references; if present, base `_replace_iframes_with_links` is available but not wired in unless a future article requires it.
- `MATCH_SUBDOMAINS` stays `False` (default): only `boomi.com` is in scope.

## Error Mapping

| Condition | Exception |
|-----------|-----------|
| `div.post-content` not found (index / non-article / non-blog page) | `UnsupportedContentTypeError` |
| Body found but no extractable text after conversion | `EmptyContentError` |
| HTTP error (any non-2xx after retries) | `HTTPStatusError` |
| Network / timeout failure | `FetchError` |

## Complexity Tracking

> No Constitution Check violations — section intentionally empty.
