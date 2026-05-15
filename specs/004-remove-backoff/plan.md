# Implementation Plan: Remove Exponential Backoff and Env-Var Retry Config

**Branch**: `004-remove-backoff` | **Date**: 2026-05-15 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/004-remove-backoff/spec.md`

## Summary

Replace the exponential backoff formula introduced in PR #6 (`min(60, retry_delay × 2ⁿ)`) with a simple fixed delay (`retry_delay` seconds, unchanged between attempts). Remove the `_MAX_RETRY_DELAY` module constant, remove `MDFETCH_RETRIES`/`MDFETCH_RETRY_DELAY` env-var reads from the integration test fixtures and CI workflow, and delete the two unit tests that verified the exponential schedule. The `extract()` public API signature and exception contract are entirely unchanged.

## Technical Context

**Language/Version**: Python 3.12+

**Primary Dependencies**:

| Package | Role |
|---------|------|
| `httpx` | HTTP client |
| `beautifulsoup4` / `lxml` | HTML parsing |
| `markdownify` | Markdown conversion |
| `pytest` | Test runner |
| `ruff` / `mypy` | Lint, format, type-check |

**Storage**: N/A

**Testing**: pytest; unit tests for retry logic; integration tests against real URLs

**Target Platform**: Cross-platform PyPI library (Linux, macOS, Windows); Python 3.12+

**Project Type**: library

**Performance Goals**: N/A — this change only affects retry sleep duration

**Constraints**: All 65 existing unit tests and 6 integration tests must pass; `mypy --strict` must pass

**Scale/Scope**: Small, targeted removal — 7 files touched, 2 tests deleted, no new files

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- [X] Validates Provider Pattern Architecture — no changes to `BaseExtractor` ABC or provider pattern
- [X] Confirms Technology Stack — no dependency additions or removals
- [X] Adheres to Coding Standards — PEP 8, strict type hints; removing code only improves compliance
- [X] Incorporates Integration Testing — integration tests remain; fixtures simplified not removed
- [X] Respects Packaging and Distribution standards — `pyproject.toml`, `src/` layout, `uv` unchanged

**No violations.** Complexity Tracking table not required.

## Project Structure

### Documentation (this feature)

```text
specs/004-remove-backoff/
├── plan.md       ← this file
├── research.md   ← Phase 0 output
└── tasks.md      ← Phase 2 output (/speckit-tasks)
```

### Source Code (files changed by this feature)

```text
src/mdfetch/
├── base.py                        # remove _MAX_RETRY_DELAY; fix sleep formula; update docstring
└── __init__.py                    # update docstring (remove exponential reference)

tests/
├── unit/test_fetch_errors.py      # remove 2 backoff tests
└── integration/
    ├── conftest.py                # remove os import + env var reads; simplify/remove fixtures
    ├── test_medium_integration.py # remove fixture params; inline retries=3, retry_delay=2.0
    └── test_devto_integration.py  # remove fixture params; inline retries=3, retry_delay=2.0

.github/workflows/integration.yml # remove MDFETCH_RETRIES and MDFETCH_RETRY_DELAY env vars
```

## Phase 0: Research

No NEEDS CLARIFICATION items and no new external dependencies. All design decisions are determined by the existing codebase.

See [research.md](research.md) for the decision log.

## Phase 1: Design

### Data Model

No entities. This feature removes code; no new data structures are introduced.

### Contracts

The public `extract()` signature and exception contract are **unchanged**:

```python
def extract(url: str, *, retries: int = 3, retry_delay: float = 2.0) -> str
```

- Same parameters, same defaults, same return type, same exception hierarchy.
- The only observable behaviour change: the sleep between retries is now a flat `retry_delay` seconds rather than `retry_delay × 2ⁿ`. This is not part of the public API contract.

No `contracts/` directory needed.

### Integration Test Strategy

**Before** (PR #6 pattern):

```python
# conftest.py reads env vars
@pytest.fixture
def http_retries() -> int:
    return int(os.environ.get("MDFETCH_RETRIES", "3"))

# test uses fixture params
def test_extract_contains_snapshot(
    url: str, snapshot: str, http_retries: int, http_retry_delay: float
) -> None:
    result = extract(url, retries=http_retries, retry_delay=http_retry_delay)
```

**After** (this feature):

```python
# conftest.py deleted or left empty
# test uses hardcoded constants
def test_extract_contains_snapshot(url: str, snapshot: str) -> None:
    result = extract(url, retries=3, retry_delay=2.0)
```

Rationale: the fixtures existed solely to expose env-var configurability. Without that purpose they are dead abstraction. Inlining `3` and `2.0` is simpler and leaves no misleading indirection.

### Key Changes by File

| File | Change |
|------|--------|
| `src/mdfetch/base.py` | Remove `_MAX_RETRY_DELAY = 60.0`; change `time.sleep(min(_MAX_RETRY_DELAY, retry_delay * (2**attempt)))` → `time.sleep(retry_delay)`; update docstring |
| `src/mdfetch/__init__.py` | Update docstring: replace "exponential backoff starting at *retry_delay* seconds" |
| `tests/unit/test_fetch_errors.py` | Delete `test_exponential_backoff_sleep_sequence` and `test_exponential_backoff_capped_at_max_delay` |
| `tests/integration/conftest.py` | Remove `import os`, remove both fixtures (or delete file if empty) |
| `tests/integration/test_medium_integration.py` | Remove `http_retries`/`http_retry_delay` fixture params; inline `retries=3, retry_delay=2.0` |
| `tests/integration/test_devto_integration.py` | Same as above |
| `.github/workflows/integration.yml` | Remove `MDFETCH_RETRIES: "6"` and `MDFETCH_RETRY_DELAY: "2.0"` from `env:` block |
