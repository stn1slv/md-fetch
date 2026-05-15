# Feature Specification: Remove Exponential Backoff and Env-Var Retry Config

**Feature Branch**: `004-remove-backoff`

**Created**: 2026-05-15

**Status**: Draft

**Input**: User description: "let's deprecate and remove the exponential backoff and env.variables which was implemented in https://github.com/stn1slv/md-fetch/pull/6"

## Background

PR #6 introduced two related changes to mdfetch:

1. **Exponential backoff** — the wait before retry attempt *n* was changed from a fixed `retry_delay` seconds to `min(60, retry_delay × 2ⁿ)`. A `_MAX_RETRY_DELAY = 60.0` module-level constant was added to cap the delay.
2. **Configurable retries via environment variables** — `tests/integration/conftest.py` reads `MDFETCH_RETRIES` and `MDFETCH_RETRY_DELAY` env vars and exposes them as pytest fixtures. CI sets `MDFETCH_RETRIES=6` in `integration.yml`.

Both changes are to be removed, restoring the simpler fixed-delay retry behaviour.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Fixed-Delay Retry Behaviour Restored (Priority: P1)

A developer calling `extract()` encounters a transient network error. The library retries using a simple, predictable fixed delay — exactly `retry_delay` seconds between every attempt — rather than an exponentially growing delay.

**Why this priority**: This is the core change. Simple, deterministic retry behaviour is easier to reason about and test. The exponential schedule was added to work around aggressive CI rate-limiting; that problem is now solved at the infrastructure level (Freedium fallback for 403/429) rather than in the retry loop.

**Independent Test**: Can be fully tested by calling `fetch_html` with a failing URL and verifying that `time.sleep` is called with the exact `retry_delay` value for every inter-attempt gap (not an exponentially growing value).

**Acceptance Scenarios**:

1. **Given** `fetch_html` is called with `retries=3` and `retry_delay=2.0`, **When** the first two attempts raise a transient error, **Then** the library sleeps exactly `2.0` seconds before each retry (not `2.0` then `4.0`).
2. **Given** `fetch_html` is called with `retries=1`, **When** the attempt fails, **Then** no sleep occurs and the exception is raised immediately.
3. **Given** a status code that is in `_no_retry_status_codes`, **When** that error is raised, **Then** no sleep or retry occurs.

---

### User Story 2 - Integration Tests Use Hardcoded Retry Defaults (Priority: P2)

A developer runs `make integration` locally or in CI without setting any `MDFETCH_*` environment variables. The integration tests use fixed defaults (3 retries, 2.0 s delay) and do not consult environment variables.

**Why this priority**: Env vars coupling test behaviour to CI configuration makes tests harder to reason about and reproduce locally. With the Freedium fallback absorbing 403/429 errors, 3 retries at a fixed 2 s delay is sufficient.

**Independent Test**: Can be fully tested by running `make integration` without setting `MDFETCH_RETRIES` or `MDFETCH_RETRY_DELAY` and verifying all 6 tests pass.

**Acceptance Scenarios**:

1. **Given** neither `MDFETCH_RETRIES` nor `MDFETCH_RETRY_DELAY` is set, **When** `make integration` runs, **Then** all integration tests pass using 3 retries and 2.0 s delay.
2. **Given** the `MDFETCH_RETRIES=6` env var is set in `integration.yml`, **When** this feature is shipped, **Then** that env var is removed from the CI workflow.

---

### Edge Cases

- What happens if tests currently rely on the `http_retries` / `http_retry_delay` fixtures by name? They must be updated to use hardcoded defaults or inline constants.
- What happens to the two unit tests that assert exponential sleep sequences? They must be removed entirely.
- What happens to the `_MAX_RETRY_DELAY` module-level constant? It is unused after the change and must be removed to avoid dead code.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The `fetch_html` method MUST use a fixed delay of exactly `retry_delay` seconds between retry attempts — no exponential multiplication.
- **FR-002**: The `_MAX_RETRY_DELAY` module-level constant in `base.py` MUST be removed.
- **FR-003**: The `import time` statement in `base.py` MUST be retained (still needed for `time.sleep`).
- **FR-004**: The `MDFETCH_RETRIES` and `MDFETCH_RETRY_DELAY` environment variable reads in `tests/integration/conftest.py` MUST be removed.
- **FR-005**: The `http_retries` and `http_retry_delay` pytest fixtures MUST be simplified to return hardcoded defaults (`3` and `2.0` respectively) or be inlined into the test functions.
- **FR-006**: The `MDFETCH_RETRIES` and `MDFETCH_RETRY_DELAY` env var entries in `.github/workflows/integration.yml` MUST be removed.
- **FR-007**: The two unit tests `test_exponential_backoff_sleep_sequence` and `test_exponential_backoff_capped_at_max_delay` in `tests/unit/test_fetch_errors.py` MUST be removed.
- **FR-008**: The `fetch_html` docstring in `base.py` MUST be updated to describe fixed-delay retry behaviour (remove references to exponential schedule and `min(60, …)` formula).
- **FR-009**: The `extract()` docstring in `src/mdfetch/__init__.py` MUST be updated if it references exponential backoff.
- **FR-010**: All remaining unit and integration tests MUST continue to pass after the changes.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: `make test` passes with zero failures after the changes (all unit tests green).
- **SC-002**: `make integration` passes with zero failures when run without any `MDFETCH_*` environment variables.
- **SC-003**: The two exponential-backoff unit tests no longer exist in the test suite.
- **SC-004**: No reference to `MDFETCH_RETRIES`, `MDFETCH_RETRY_DELAY`, or `_MAX_RETRY_DELAY` remains anywhere in the codebase.
- **SC-005**: The CI `integration.yml` workflow no longer sets `MDFETCH_RETRIES` or `MDFETCH_RETRY_DELAY`.

## Assumptions

- The Freedium fallback (introduced in PR #7) adequately handles the Medium 403/429 rate-limiting that originally motivated exponential backoff. Fixed delay at 3 retries is therefore sufficient for CI reliability.
- The `http_retries` and `http_retry_delay` fixtures in `conftest.py` are used only in `test_medium_integration.py` and `test_devto_integration.py`; no other test files depend on them.
- The `timeout-minutes: 30` setting in `integration.yml` can remain as-is — it provides adequate headroom even with fixed delay retries.
