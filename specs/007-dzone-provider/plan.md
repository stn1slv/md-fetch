# Implementation Plan: DZone Provider

**Branch**: `007-dzone-provider` | **Date**: 2026-05-16 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/007-dzone-provider/spec.md`

## Summary

Add `dzone.com` as a supported extraction platform. The provider isolates the article body from `div.content-html`, handles DZone's CodeMirror code-block widget (extracting language labels and stripping UI chrome before Markdown conversion), and prepends the article title from `h1.article-title`. All other non-content elements (sidebar, ads, sign-in prompts, tag pills) are outside the body container and naturally excluded. Implementation follows the established one-file provider pattern with no changes to shared infrastructure.

## Technical Context

**Language/Version**: Python 3.12+ (matches CI matrix: 3.12–3.14)

**Primary Dependencies**: `httpx` (HTTP fetch), `BeautifulSoup` / `lxml` (HTML parsing), `markdownify` (Markdown conversion), `pytest` (testing)

**Storage**: N/A — stateless extraction library

**Testing**: `pytest` via `uv run pytest` — unit tests (no network) + integration tests (`-m integration`, real URLs + snapshots)

**Target Platform**: PyPI library (cross-platform)

**Project Type**: Library

**Performance Goals**: Inherits base class 30-second fetch timeout; no additional targets

**Constraints**: One new provider file (`src/mdfetch/providers/dzone.py`); no changes to shared infrastructure; router test `test_router.py` requires `dzone.com` routing assertion (no unsupported-domain fixture update needed — `wordpress.com` remains unregistered)

**Scale/Scope**: Single-article extraction per call

## Constitution Check

*GATE: Must pass before implementation. Re-check after design phase.*

- [x] Validates Provider Pattern Architecture — one new file inheriting `BaseExtractor`; no code duplication; `@register` + `DOMAINS` follows Open/Closed Principle
- [x] Confirms Technology Stack — `httpx` (base class), `BeautifulSoup` (HTML parsing), `markdownify` (conversion), `pytest` (testing)
- [x] Adheres to Coding Standards — PEP 8, strict type hints, clear English identifiers
- [x] Incorporates Integration Testing — 3 real DZone article URLs with snapshot-based containment assertions
- [x] Respects Packaging and Distribution standards — `src/` layout, `pyproject.toml`, all dev commands via `uv run`

## Project Structure

### Documentation (this feature)

```text
specs/007-dzone-provider/
├── plan.md              # This file
├── research.md          # Phase 0: HTML structure analysis
├── data-model.md        # Phase 1: Entity and element taxonomy
├── quickstart.md        # Phase 1: Step-by-step implementation guide
├── contracts/
│   └── public-api.md    # Phase 1: Public API contract
└── tasks.md             # Phase 2 output (/speckit-tasks)
```

### Source Code

```text
src/mdfetch/providers/
└── dzone.py             # NEW: DZoneExtractor

tests/unit/
└── test_dzone_extractor.py    # NEW: unit tests (no network)

tests/integration/
├── snapshots/
│   ├── dzone-integration-patterns-fail-production.md   # NEW
│   ├── dzone-kiro-feature-to-requirements-design-tasks.md  # NEW
│   └── dzone-image-classification-pipeline-camel-djl.md   # NEW
└── test_dzone_integration.py  # NEW: integration tests (real URLs)
```

**Non-runtime changes**: `tests/unit/test_router.py` — add `test_routes_dzone_com` routing assertion (no fixture update needed; `wordpress.com` remains the unsupported domain).

## Extraction Algorithm

```
extract(url):
  html ← fetch_html(url)                   # base class; Chrome UA; 3 retries, 30s timeout
  soup ← BeautifulSoup(html, "lxml")
  body_tag ← clean_html(soup)              # → article body with chrome stripped
  return convert_to_markdown(body_tag)

clean_html(soup):
  1. Find div.content-html                  → raise UnsupportedContentTypeError if absent
  2. For each div.codeMirror-wrapper in body:
     a. Read language from div.nameLanguage (strip whitespace, lowercase)
        - "plain text" → "" (no fence info string)
        - absent / empty → ""
     b. Find code element inside wrapper
        - If language non-empty: set code["class"] = ["language-<lang>"]
     c. Decompose div.codeHeader (language label + cancel icon UI chrome)
  3. Find h1.article-title in soup          → prepend copy as first child of body
  4. Return body tag (div.content-html)

convert_to_markdown(tag):
  md ← markdownify(str(tag), heading_style="ATX", code_language="", strip=["script","style"])
  md ← strip leading/trailing whitespace
  md ← collapse 3+ blank lines → single blank line (re.sub(r"\n{3,}", "\n\n", md))
  if md empty → raise EmptyContentError
  return md
```

## Error Mapping

| Condition | Exception |
|-----------|-----------|
| `div.content-html` not found | `UnsupportedContentTypeError` |
| Body found but no extractable text | `EmptyContentError` |
| HTTP error (any non-2xx after retries) | `HTTPStatusError` |
| Network / timeout failure | `FetchError` |

## Complexity Tracking

No Constitution Check violations. No complexity justification required.
