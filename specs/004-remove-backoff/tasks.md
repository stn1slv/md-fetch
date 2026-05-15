# Tasks: Remove Exponential Backoff and Env-Var Retry Config

**Input**: Design documents from `specs/004-remove-backoff/`

**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅

**Organization**: Tasks are grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: Which user story this task belongs to (US1, US2)

---

## Phase 1: Setup

**Purpose**: Establish green baseline before making any changes

- [ ] T001 Verify baseline by running `make test` — confirm 65 unit tests pass before changes

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: No shared infrastructure changes needed for this feature — this phase is satisfied by T001.

**⚠️ NOTE**: US1 and US2 are fully independent; either can be implemented first or in parallel.

---

## Phase 3: User Story 1 — Fixed-Delay Retry Behaviour Restored (Priority: P1) 🎯 MVP

**Goal**: Replace the exponential backoff formula with a flat `retry_delay` seconds sleep; remove the `_MAX_RETRY_DELAY` cap constant; update docstrings; delete the two unit tests that verified the exponential schedule.

**Independent Test**: Run `make test` — the remaining retry tests (`TestNoRetryStatusCodes`, `TestFetchErrors`) must pass; the two deleted tests must no longer exist.

### Implementation for User Story 1

- [ ] T002 [US1] Remove `_MAX_RETRY_DELAY = 60.0` constant and change `time.sleep(min(_MAX_RETRY_DELAY, retry_delay * (2**attempt)))` to `time.sleep(retry_delay)` in `src/mdfetch/base.py`
- [ ] T003 [US1] Update `fetch_html` docstring in `src/mdfetch/base.py` to say "fixed delay of *retry_delay* seconds" (remove mention of exponential schedule and `min(60, …)` formula)
- [ ] T004 [P] [US1] Update `extract()` docstring in `src/mdfetch/__init__.py` — replace "exponential backoff starting at *retry_delay* seconds" with "fixed delay of *retry_delay* seconds between attempts"
- [ ] T005 [P] [US1] Delete `test_exponential_backoff_sleep_sequence` and `test_exponential_backoff_capped_at_max_delay` test methods from `tests/unit/test_fetch_errors.py`

**Checkpoint**: Run `make test` — all remaining unit tests pass; no reference to exponential backoff remains in `src/`.

---

## Phase 4: User Story 2 — Integration Tests Use Hardcoded Retry Defaults (Priority: P2)

**Goal**: Remove the `MDFETCH_RETRIES` / `MDFETCH_RETRY_DELAY` env-var fixtures from the integration test suite and CI; inline the defaults directly in test call sites; delete `conftest.py`.

**Independent Test**: Run `make integration` without any `MDFETCH_*` env vars set — all 6 integration tests pass.

### Implementation for User Story 2

- [ ] T006 [P] [US2] Remove `http_retries` and `http_retry_delay` fixture parameters from the test function signature and inline `retries=3, retry_delay=2.0` in the `extract()` call in `tests/integration/test_medium_integration.py`; remove the env-var docstring line from the test docstring
- [ ] T007 [P] [US2] Same changes as T006 in `tests/integration/test_devto_integration.py`
- [ ] T008 [US2] Delete `tests/integration/conftest.py` (file is empty after T006 + T007 remove all fixture consumers; no other test files reference these fixtures)
- [ ] T009 [US2] Remove the `MDFETCH_RETRIES: "6"` and `MDFETCH_RETRY_DELAY: "2.0"` lines from the `env:` block of the `Run integration tests` step in `.github/workflows/integration.yml`

**Checkpoint**: Run `make integration` — all 6 tests pass; no `MDFETCH_*` variables appear anywhere in the codebase.

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Final validation — confirm all quality gates pass together

- [ ] T010 Run `make test` to confirm all unit tests pass (expected: 63 tests — 65 minus the 2 deleted backoff tests)
- [ ] T011 Run `uv run mypy src/` to confirm zero type errors after docstring and code changes
- [ ] T012 Run `make lint` to confirm ruff check passes with no violations
- [ ] T013 Verify no remaining references to `_MAX_RETRY_DELAY`, `MDFETCH_RETRIES`, or `MDFETCH_RETRY_DELAY` anywhere in the codebase by running `grep -r "MAX_RETRY_DELAY\|MDFETCH_RETRIES\|MDFETCH_RETRY_DELAY" src/ tests/ .github/`
- [ ] T014 Run `make integration` without any `MDFETCH_*` env vars set and confirm all 6 integration tests pass (verifies SC-002)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **US1 (Phase 3)**: Depends on T001 (baseline green) — can start after setup
- **US2 (Phase 4)**: Depends on T001 (baseline green) — **independent from US1; can run in parallel**
- **Polish (Phase 5)**: Depends on US1 and US2 both complete

### Within Each User Story

- **US1**: T002 → T003 (same file, sequential); T004 and T005 are [P] (different files, independent of T002/T003)
- **US2**: T006 and T007 are [P] (different files); T008 depends on T006 + T007 (delete conftest only after test files no longer reference fixtures); T009 is [P] with T006/T007/T008 (different file)

### Parallel Opportunities

```text
After T001 (baseline green):

Stream A (US1):
  T002 → T003   # base.py: formula + docstring (same file, sequential)
  T004          # __init__.py docstring [P with T005]
  T005          # delete backoff unit tests [P with T004]

Stream B (US2):
  T006 [P]      # test_medium_integration.py (parallel with T007)
  T007 [P]      # test_devto_integration.py (parallel with T006)
  T008          # delete conftest.py (after T006 + T007)
  T009          # integration.yml env vars [P, independent]

After both streams: T010 → T011 → T012 → T013 → T014
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. T001 — establish baseline
2. T002 → T003 — fix retry formula and docstring in `base.py`
3. T004 + T005 — update `__init__.py` docstring; delete backoff tests
4. T010 + T011 + T012 — validate
5. **STOP and VALIDATE**: `make test` passes with 63 tests

### Full Delivery (US1 + US2)

Continue after MVP:
6. T006 + T007 — update integration test signatures
7. T008 — delete conftest.py
8. T009 — remove CI env vars
9. T013 — confirm no residual references

---

## Notes

- [P] tasks operate on different files with no shared dependencies — safe to run concurrently
- T008 (delete conftest.py) MUST come after T006 + T007 — deleting conftest.py while test functions still declare `http_retries`/`http_retry_delay` parameters will cause pytest fixture-not-found errors
- T009 (.github/workflows) is independent of all other tasks; can be done at any point after T001
- Expected final unit test count: 63 (65 baseline − 2 deleted backoff tests)
