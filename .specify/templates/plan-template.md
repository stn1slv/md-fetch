# Implementation Plan: [FEATURE]

**Branch**: `[###-feature-name]` | **Date**: [DATE] | **Spec**: [link]

**Input**: Feature specification from `/specs/[###-feature-name]/spec.md`

**Note**: This template is filled in by the `/speckit-plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

[Extract from feature spec: primary requirement + technical approach from research]

## Technical Context

<!--
  The values below reflect mdfetch's established stack.
  Override only if this feature deviates from the norm.
-->

**Language/Version**: Python 3.12+ (matches CI matrix: 3.12–3.14)

**Primary Dependencies**: `httpx` (HTTP fetch), `BeautifulSoup` / `lxml` (HTML parsing), `markdownify` (Markdown conversion), `pytest` (testing)

**Storage**: N/A — stateless extraction library

**Testing**: `pytest` via `uv run pytest` — unit tests (no network) + integration tests (`-m integration`, real URLs + snapshots)

**Target Platform**: PyPI library (cross-platform)

**Project Type**: Library

**Performance Goals**: Inherits base class 30-second fetch timeout; no additional targets unless spec overrides

**Constraints**: [e.g., "One new provider file; no changes to shared infrastructure" or NEEDS CLARIFICATION]

**Scale/Scope**: Single-article extraction per call

## Constitution Check

*GATE: Must pass before implementation. Re-check after design phase.*

- [ ] Validates Provider Pattern Architecture (No code duplication, adheres to Open/Closed Principle)
- [ ] Confirms Technology Stack (`httpx`, `BeautifulSoup`, `Markdownify`, `pytest`)
- [ ] Adheres to Coding Standards (PEP 8, Type Hinting, Clear Vocabulary)
- [ ] Incorporates Integration Testing (Real links matching expected Markdown)
- [ ] Respects Packaging and Distribution standards (`pyproject.toml`, `src/` layout, `uv` for all dev workflow commands)

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md        # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
├── contracts/           # Phase 1 output (/speckit-plan command)
└── tasks.md             # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code
<!--
  ACTION REQUIRED: Replace the placeholder tree below with the concrete file
  list for this feature. The layout always follows the established provider pattern.
-->

```text
src/mdfetch/providers/
└── [platform].py          # NEW: [Platform]Extractor

tests/unit/
└── test_[platform]_extractor.py   # NEW: unit tests (no network)

tests/integration/
├── snapshots/
│   └── [platform]-[article-slug].md  # NEW: snapshot(s)
└── test_[platform]_integration.py    # NEW: integration tests (real URLs)
```

**Non-runtime changes** (if any): [e.g., "README.md (supported platforms table), tests/unit/test_router.py (unsupported-domain fixture update)"]

## Extraction Algorithm

<!--
  ACTION REQUIRED: Replace the pseudocode below with the actual extraction
  pipeline for this platform, derived from research.md analysis.
-->

```
extract(url):
  html ← fetch_html(url)                   # base class; retries on all transient errors
  soup ← BeautifulSoup(html, "lxml")
  body_tag ← clean_html(soup)              # → article body with chrome stripped
  return convert_to_markdown(body_tag)

clean_html(soup):
  1. Find [article body container]          → raise UnsupportedContentTypeError if absent
  2. Strip [non-content elements]
  3. Convert [embedded content] → anchor links
  4. Find [title element]                   → prepend to body
  5. Find [subtitle element] (optional)     → prepend after title
  6. Return body tag

convert_to_markdown(tag):
  md ← markdownify(str(tag), heading_style="ATX", code_language="", strip=["script","style"])
  md ← strip leading/trailing whitespace
  md ← collapse 3+ blank lines → single blank line
  if md empty → raise EmptyContentError
  return md
```

## Error Mapping

| Condition | Exception |
|-----------|-----------|
| Article body container not found | `UnsupportedContentTypeError` |
| Body found but no extractable text | `EmptyContentError` |
| HTTP error (any non-2xx after retries) | `HTTPStatusError` |
| Network / timeout failure | `FetchError` |

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| [e.g., modifies base class] | [current need] | [why provider-only approach insufficient] |
