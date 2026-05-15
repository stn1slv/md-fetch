# Implementation Plan: Substack Platform Provider

**Branch**: `005-substack-provider` | **Date**: 2026-05-15 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/005-substack-provider/spec.md`

## Summary

Add a `SubstackExtractor` provider that extracts article content from `substack.com` and all `*.substack.com` URLs and returns it as clean Markdown. The extractor targets `div.body.markup` as the article prose root, prepends the title from `div.post-header h1.post-title`, strips inline subscription CTAs (`div.subscription-widget-wrap`) and converts rich embeds to plain anchor links. Paywalled posts are handled silently — `div.body.markup` already contains only the free preview; stripping the terminal subscribe widget achieves truncation without error. No changes to shared infrastructure are required.

## Technical Context

**Language/Version**: Python 3.12–3.14 (matches existing CI matrix)

**Primary Dependencies**: `httpx`, `BeautifulSoup` (lxml parser), `markdownify`, `pytest`

**Storage**: N/A

**Testing**: `pytest` via `uv run pytest`

**Target Platform**: PyPI library (any OS)

**Project Type**: Library

**Performance Goals**: Inherits base class 30-second fetch timeout; no additional targets

**Constraints**: Single `src/mdfetch/providers/substack.py` file; no changes outside the new provider and its tests

**Scale/Scope**: Single article per call

## Constitution Check

*GATE: Must pass before implementation. Re-check after design phase.*

- [x] Validates Provider Pattern Architecture — new `SubstackExtractor(BaseExtractor)` subclass; no shared-code changes
- [x] Confirms Technology Stack — `httpx`, `BeautifulSoup`, `markdownify`, `pytest`; no new dependencies
- [x] Adheres to Coding Standards — strict type hints, PEP 8, clear vocabulary
- [x] Incorporates Integration Testing — at least one real-network integration test required (SC-005)
- [x] Respects Packaging and Distribution — `src/` layout, `pyproject.toml` unchanged, `uv run` for all dev commands

**Result**: All gates pass. No violations to justify.

## Project Structure

### Documentation (this feature)

```text
specs/005-substack-provider/
├── plan.md              # This file
├── research.md          # Phase 0 output (complete)
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit-tasks)
```

### Source Code

```text
src/mdfetch/providers/
└── substack.py          # NEW: SubstackExtractor

tests/
├── unit/
│   └── test_substack_extractor.py # NEW: unit tests (no network)
└── integration/
    └── test_substack_integration.py  # NEW: real-network integration tests
```

No other files are modified.

## Phase 1: Design & Contracts

See [data-model.md](data-model.md), [contracts/](contracts/), and [quickstart.md](quickstart.md) for Phase 1 outputs.

### Extraction Algorithm (derived from research)

```
extract(url):
  html ← fetch_html(url)                   # base class; retries on all transient errors
  soup ← BeautifulSoup(html, "lxml")
  body_tag ← clean_html(soup)              # → div.body.markup with chrome stripped
  return convert_to_markdown(body_tag)

clean_html(soup):
  1. Find h1.post-title in div.post-header  → store as title_el (structurally outside div.body.markup; unconditional prepend per FR-004)
  2. Find h3.subtitle in div.post-header    → store as subtitle_el (optional)
  3. Find div.body.markup                   → raise UnsupportedContentTypeError if absent
  4. Strip div.subscription-widget-wrap inside body (inline CTAs + paywall terminal widget)
  5. Convert iframe elements → <a href=src>src</a>  (embeds)
  6. Convert embed divs (data-component-name ≠ SubscribeWidget|Image2ToDOM) → <a href>
  7. Prepend subtitle_el (if present) at body top
  8. Prepend title_el at body top
  9. Return body tag

convert_to_markdown(tag):
  md ← markdownify(str(tag), heading_style="ATX", code_language="", strip=["script","style"])
  md ← strip leading/trailing whitespace
  md ← collapse 3+ blank lines → single blank line
  if md empty → raise EmptyContentError
  return md
```

### Error Mapping

| Condition | Exception |
|-----------|-----------|
| `div.body.markup` not found | `UnsupportedContentTypeError` |
| Body found but no extractable text | `EmptyContentError` |
| HTTP error (any non-2xx, including 429 after retries) | `HTTPStatusError` |
| Network / timeout failure | `FetchError` |

### Heading Output Structure

For a typical Substack post the output begins:

```markdown
# Post Title

### Subtitle text (if present)

First paragraph…

# Section Heading

…
```

Section headings inside `div.body.markup` use `<h1 class="header-anchor-post">` and render as `#` headings — consistent with existing provider behaviour (headings not remapped).

## Complexity Tracking

No constitution violations. Table omitted.

### Revision: Implementation Sync 2026-05-15
- Reason: Feature fully implemented and all tests green. Supplementary change: `tests/unit/test_router.py` unsupported-domain fixtures updated from `substack.com` to `wordpress.com` (registering SubstackExtractor made the original fixtures route successfully rather than raise `UnsupportedPlatformError`). All 5 constitution gates confirmed passing post-implementation.
