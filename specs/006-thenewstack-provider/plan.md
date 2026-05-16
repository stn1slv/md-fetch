# Implementation Plan: The New Stack Platform Provider

**Branch**: `006-thenewstack-provider` | **Date**: 2026-05-16 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/006-thenewstack-provider/spec.md`

## Summary

Add a `TheNewStackExtractor` that fetches public thenewstack.io articles and returns them as clean Markdown. The extractor targets `div#tns-post-body-content` as the article body, prepends `h1.title` and `div.post-excerpt` (deck) from `div#tns-post-headline`, strips sponsored-content disclosures and sponsor-note injections, and follows the identical provider pattern as `SubstackExtractor` and `DevToExtractor` — one new file, no shared-infrastructure changes.

## Technical Context

**Language/Version**: Python 3.12+ (matches CI matrix: 3.12–3.14)

**Primary Dependencies**: `httpx` (HTTP fetch), `BeautifulSoup` / `lxml` (HTML parsing), `markdownify` (Markdown conversion), `pytest` (testing)

**Storage**: N/A — stateless extraction library

**Testing**: `pytest` via `uv run pytest` — unit tests (no network) + integration tests (`-m integration`, real URLs + snapshots)

**Target Platform**: PyPI library (cross-platform)

**Project Type**: Library

**Performance Goals**: Inherits base class 30-second fetch timeout; no additional targets

**Constraints**: One new provider file (`src/mdfetch/providers/thenewstack.py`); no changes to shared infrastructure, router, base class, or exceptions.

**Scale/Scope**: Single-article extraction per call

## Constitution Check

*GATE: Must pass before implementation.*

- [x] Validates Provider Pattern Architecture — single new file inheriting `BaseExtractor`; zero duplication; Open/Closed Principle respected
- [x] Confirms Technology Stack — `httpx` (base), `BeautifulSoup` / `lxml`, `markdownify`, `pytest`; no new dependencies
- [x] Adheres to Coding Standards — PEP 8, strict type hints, clear English identifiers
- [x] Incorporates Integration Testing — real URL tests with snapshot assertions against all 5 reference articles
- [x] Respects Packaging and Distribution — `src/` layout; `uv` for all dev workflows; `pyproject.toml` unchanged

**No violations detected. No Complexity Tracking entry required.**

## Project Structure

### Documentation (this feature)

```text
specs/006-thenewstack-provider/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit-tasks)
```

### Source Code

```text
src/mdfetch/providers/
└── thenewstack.py                          # NEW: TheNewStackExtractor

tests/unit/
└── test_thenewstack_extractor.py           # NEW: unit tests (no network)

tests/integration/
├── snapshots/
│   ├── thenewstack-developer-portal-api.md   # NEW: snapshot (article 1)
│   ├── thenewstack-async-apis.md             # NEW: snapshot (article 2)
│   ├── thenewstack-json-schema-ai.md         # NEW: snapshot (article 3)
│   ├── thenewstack-mcp-api-governance.md     # NEW: snapshot (article 4)
│   └── thenewstack-api-mcp-agent.md          # NEW: snapshot (article 5)
└── test_thenewstack_integration.py           # NEW: integration tests (real URLs)
```

**Non-runtime changes**:
- `tests/unit/test_router.py` — add `test_routes_thenewstack_io` routing test (no fixture update needed; `wordpress.com` already the unsupported-domain fixture)

## Extraction Algorithm

```
extract(url):
  html ← fetch_html(url)                   # base class; retries on all transient errors
  soup ← BeautifulSoup(html, "lxml")
  body_tag ← clean_html(soup)              # → article body with chrome stripped
  return convert_to_markdown(body_tag)

clean_html(soup):
  1. body ← soup.find("div", id="tns-post-body-content")
     → raise UnsupportedContentTypeError if None (FR-006)
  2. Strip sponsored content disclosures (FR-003):
     - decompose div.sponsored-post-disclosure
     - decompose div.tns-sponsored-post-disclosure
     - decompose div.sponsor-disclosure
     - decompose div.tns-sponsor-note
  3. Convert iframes → anchor links (FR-009):
     - for each iframe: replace with <a href=src>src</a> or decompose
  4. headline ← soup.find("div", id="tns-post-headline")
  5. If headline found:
     a. deck ← headline.find("div", class_="post-excerpt")
        If deck: create <p> with deck text; insert at body[0]   (FR-004 clarification Q2)
     b. title ← headline.find("h1", class_="title")
        If title: copy.copy(title); insert at body[0]            (FR-004)
  6. Return body

  Note: VoxPop (div.tns-voxpop-screen) confirmed absent from tns-post-body-content
  across all 5 reference articles — no stripping needed.

convert_to_markdown(tag):
  md ← markdownify(str(tag), heading_style="ATX", code_language="",
                   strip=["script", "style"])
  md ← md.strip()
  md ← re.sub(r"\n{3,}", "\n\n", md)       # FR-008
  if not md → raise EmptyContentError       # FR-007
  return md
```

## Error Mapping

| Condition | Exception |
|-----------|-----------|
| `div#tns-post-body-content` not found | `UnsupportedContentTypeError` |
| Body found but no extractable text | `EmptyContentError` |
| HTTP error (any non-2xx after retries) | `HTTPStatusError` |
| Network / timeout failure | `FetchError` |

## Key Selectors Reference

| Purpose | Selector |
|---------|----------|
| Article body | `div#tns-post-body-content` |
| Article title | `h1.title` inside `div#tns-post-headline` |
| Article deck/subtitle | `div.post-excerpt` inside `div#tns-post-headline` |
| Sponsored disclosure (3 variants) | `div.sponsored-post-disclosure`, `div.tns-sponsored-post-disclosure`, `div.sponsor-disclosure` |
| Injected sponsor note | `div.tns-sponsor-note` |
| VoxPop (not in body — no action needed) | `div.tns-voxpop-screen` (page-level modal) |

### Revision: Implementation Sync 2026-05-16
- Reason: Post-implementation reconciliation. Implementation matches plan exactly. Snapshot approach confirmed as verbatim first-30-line prefix (not stripped blank lines); integration test error message corrected to reflect this. No plan changes required.
