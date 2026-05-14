# Implementation Plan: mdfetch — Medium Extractor (Initial Release)

**Branch**: `001-mdfetch-medium-extractor` | **Date**: 2026-05-14 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/001-mdfetch-medium-extractor/spec.md`

## Summary

Build the initial release of `mdfetch`, a Python library that extracts article content from Medium and returns it as clean Markdown. The library enforces a provider pattern (abstract base + one concrete provider per platform), routes requests by URL domain, raises typed exceptions for all failure modes, and is distributed via PyPI using a modern `src/` layout. This release supports `medium.com` only.

## Technical Context

**Language/Version**: Python 3.10+

**Primary Dependencies**:
- `httpx` — HTTP client for fetching article pages (sync interface)
- `beautifulsoup4` + `lxml` — HTML parsing and article-body targeting
- `markdownify` — HTML-to-Markdown conversion
- `pytest` — test runner (unit + integration)
- `ruff` — linter and formatter (dev tooling)

**Package Manager**: `uv` — all local development workflows (install, run, test, lint, format, build) MUST use `uv`. Direct use of `pip`, `venv`, or `pip-tools` is prohibited in development commands.

**Storage**: N/A — stateless library; no persistence layer

**Testing**: pytest; unit tests for routing and extraction logic; integration tests using real Medium article URLs

**Target Platform**: Cross-platform PyPI library (Linux, macOS, Windows); Python 3.10+

**Project Type**: library

**Performance Goals**: Extraction completes in under 10 seconds for a standard Medium article on a stable connection (SC-002)

**Constraints**:
- No JavaScript rendering; operates on static HTML only
- No response caching; each call performs a fresh HTTP request
- No rate-limit handling or authentication in v1
- Explicit browser-like User-Agent string; MUST NOT identify the library by name or version (FR-014)
- Network timeout: 30 seconds (fixed, not user-configurable in v1)

**Scale/Scope**: Single-caller, single-threaded library call; no concurrency model required

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- [x] Validates Provider Pattern Architecture — `BaseExtractor` ABC with abstract `fetch_html`, `clean_html`, `convert_to_markdown`; `MediumExtractor` inherits; shared HTTP and conversion logic in base class only
- [x] Confirms Technology Stack — `httpx`, `beautifulsoup4`/`lxml`, `markdownify`, `pytest`, `ruff` are the only permitted dependencies
- [x] Adheres to Coding Standards — PEP 8, strict type hints on all functions/methods, clear English identifiers and docstrings
- [x] Incorporates Integration Testing — FR-010 mandates integration tests with real Medium URLs asserting expected Markdown structure
- [x] Respects Packaging and Distribution — `pyproject.toml` + `src/mdfetch/` layout; distribution via PyPI; all dev workflow Makefile targets invoke tools via `uv run <tool>`; `uv` replaces `pip`/`venv`/`pip-tools`

**Gate result**: PASS — no violations. Proceed to Phase 0.

## Project Structure

### Documentation (this feature)

```text
specs/001-mdfetch-medium-extractor/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── api.md
└── tasks.md             # Phase 2 output (created by /speckit-tasks)
```

### Source Code (repository root)

```text
src/
└── mdfetch/
    ├── __init__.py          # Public surface: exposes extract()
    ├── exceptions.py        # Custom exception hierarchy
    ├── router.py            # Domain → provider routing
    ├── base.py              # BaseExtractor ABC
    └── providers/
        ├── __init__.py
        └── medium.py        # MediumExtractor

tests/
├── unit/
│   ├── test_router.py
│   ├── test_exceptions.py
│   └── test_medium_extractor.py
└── integration/
    └── test_medium_integration.py

pyproject.toml
Makefile
```

**Structure Decision**: Single-project layout (Option 1). The `src/` layout follows modern Python packaging best practices (PEP 517/518) and is mandated by the constitution. Providers live in a sub-package to isolate platform-specific logic. Exceptions are centralised in `exceptions.py` so all error types are importable from one location.

## Complexity Tracking

> No constitution violations — section not applicable.
