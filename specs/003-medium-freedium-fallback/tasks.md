# Tasks: Medium Freedium Fallback

**Input**: Design documents from `specs/003-medium-freedium-fallback/`

**Prerequisites**: plan.md ✅ | spec.md ✅ | research.md ✅ | contracts/extract-api.md ✅

**Organization**: Tasks grouped by user story — each story is independently testable.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: US1 = 403 Fallback, US2 = 429 Fallback, US3 = No Fallback on Success

---

## Phase 1: Setup

No new setup required — all project infrastructure exists. Proceeding directly to foundational changes.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Extend `BaseExtractor` with the `_no_retry_status_codes` hook that both US1 and US2 depend on. No user story work can begin until this phase is complete.

**⚠️ CRITICAL**: Both US1 and US2 implementation tasks depend on T001.

- [ ] T001 Add `_no_retry_status_codes: frozenset[int] = frozenset()` class attribute to `BaseExtractor` and insert early-exit guard `if isinstance(exc, HTTPStatusError) and exc.status_code in self._no_retry_status_codes: raise` in the `fetch_html()` retry loop in `src/mdfetch/base.py`
- [ ] T002 [P] Add unit tests in `tests/unit/test_fetch_errors.py` verifying that status codes in `_no_retry_status_codes` are raised immediately without sleep/retry (use `MediumExtractor` with a subclass that sets the attribute, mock `httpx.Client`) and that codes NOT in the set still trigger the existing backoff

**Checkpoint**: `BaseExtractor` extended — user story implementation can now begin

---

## Phase 3: User Story 1 — Transparent Fallback on Blocked Article (Priority: P1) 🎯 MVP

**Goal**: When `medium.com` returns HTTP 403, the library automatically retries via `https://freedium-mirror.cfd/{url}` and returns clean Markdown. Caller sees no difference.

**Independent Test**: Call `extract()` with a mock that returns 403 on the first request and valid HTML on the second. Verify Markdown is returned and the second call used the Freedium URL.

- [ ] T003 [P] [US1] Add unit tests in `tests/unit/test_medium_extractor.py` for 403 fallback: mock `httpx.Client` to return 403 on the medium.com request and valid article HTML on the Freedium request; verify returned Markdown is non-empty and the Freedium URL (`https://freedium-mirror.cfd/https://medium.com/...`) was fetched
- [ ] T004 [P] [US1] Add `@pytest.mark.integration` test in `tests/integration/test_medium_integration.py` for a known paywalled Medium URL; assert `extract()` returns a non-empty string (no snapshot comparison — Freedium content may differ)
- [ ] T005 [US1] Implement fallback in `src/mdfetch/providers/medium.py`: add `_FREEDIUM_BASE = "https://freedium-mirror.cfd/"` and `_no_retry_status_codes: frozenset[int] = frozenset({403, 429})` class attributes; override `extract()` to catch `HTTPStatusError` for status codes in `_no_retry_status_codes`, construct `freedium_url = f"{self._FREEDIUM_BASE}{url}"`, fetch and parse via existing `fetch_html()` + `clean_html()` + `convert_to_markdown()`; set `exc.url = url` (original URL) on any `MdfetchError` raised from the Freedium path (depends on T001)

**Checkpoint**: US1 fully functional — 403 on medium.com transparently resolved via Freedium

---

## Phase 4: User Story 2 — Automatic Retry on Rate Limiting (Priority: P2)

**Goal**: When `medium.com` returns HTTP 429, the same fallback mechanism activates immediately. No retries against `medium.com` are attempted first.

**Independent Test**: Mock `httpx.Client` to return 429 on the medium.com call, valid HTML on the Freedium call. Verify no `time.sleep` is called before the Freedium request.

- [ ] T006 [P] [US2] Add unit tests in `tests/unit/test_medium_extractor.py` for 429 fallback: mock `httpx.Client` to return 429 on the medium.com request; verify `time.sleep` is NOT called before the Freedium request (use `patch("mdfetch.base.time.sleep")`), and valid Markdown is returned from the Freedium path (depends on T005)

**Checkpoint**: US2 fully functional — 429 handled identically to 403 with no medium.com retries

---

## Phase 5: User Story 3 — No Fallback When Primary Succeeds (Priority: P3)

**Goal**: When `medium.com` returns HTTP 200, no request is made to the Freedium mirror. Existing behaviour is fully preserved.

**Independent Test**: Mock `httpx.Client` to return 200 with valid HTML. Assert `extract()` returns Markdown and no second HTTP request is made.

- [ ] T007 [P] [US3] Add unit test in `tests/unit/test_medium_extractor.py` verifying that `httpx.Client.stream` is called exactly once (only the medium.com request) when the primary fetch succeeds with HTTP 200 (depends on T005)

**Checkpoint**: All three user stories independently verified

---

## Phase 6: Polish & Cross-Cutting Concerns

- [ ] T008 [P] Run `uv run ruff check src/ tests/` and `uv run mypy src/` and fix any lint or type errors introduced by T001 and T005
- [ ] T009 Run `make test` (full unit suite) and confirm all tests pass including T002, T003, T006, T007

---

## Dependencies & Execution Order

### Phase Dependencies

- **Foundational (Phase 2)**: No dependencies — start immediately
- **US1 (Phase 3)**: T003 and T004 can start immediately (tests only); T005 depends on T001
- **US2 (Phase 4)**: T006 depends on T005 (tests the implemented fallback)
- **US3 (Phase 5)**: T007 depends on T005
- **Polish (Phase 6)**: Depends on all phases complete

### User Story Dependencies

- **US1 (P1)**: Depends on T001 (foundational) — no other story dependency
- **US2 (P2)**: Depends on T005 (US1 implementation — shared `extract()` override covers both)
- **US3 (P3)**: Depends on T005 (verifies the override preserves happy-path behaviour)

### Within Each Story

- Test tasks [P] can begin writing before implementation (T003, T004 before T005)
- T005 is the only implementation task — it covers US1 and US2 simultaneously
- All test tasks for a story can be written in parallel

### Parallel Opportunities

- T002 and T003/T004 can run in parallel (different files, no shared dependencies)
- T006 and T007 can run in parallel after T005 completes (different assertions)
- T008 and T009 can run in parallel (different tools)

---

## Parallel Example: Foundational + US1 Test Writing

```bash
# Can run in parallel immediately:
Task T001: "Extend BaseExtractor with _no_retry_status_codes in src/mdfetch/base.py"
Task T002: "Unit tests for _no_retry_status_codes in tests/unit/test_fetch_errors.py"
Task T003: "Unit tests for 403 fallback in tests/unit/test_medium_extractor.py"
Task T004: "Integration test for paywalled URL in tests/integration/test_medium_integration.py"

# After T001 completes:
Task T005: "Implement MediumExtractor.extract() fallback in src/mdfetch/providers/medium.py"

# After T005 completes, in parallel:
Task T006: "Unit tests for 429 no-retry in tests/unit/test_medium_extractor.py"
Task T007: "Unit test for no-fallback on 200 in tests/unit/test_medium_extractor.py"
```

---

## Implementation Strategy

### MVP (User Story 1 Only)

1. Complete T001 (base class extension)
2. Complete T005 (MediumExtractor override — covers US1 and US2 simultaneously)
3. Run T003 unit tests to verify 403 fallback
4. **STOP and VALIDATE**: `make test` passes; integration test T004 passes
5. US1 and US2 are both delivered at this point

### Full Delivery

1. T001 → T005 → run all test tasks → T008 → T009
2. Total: 9 tasks across 6 phases
3. Estimated changed files: 3 source files (`base.py`, `medium.py`) + 2–3 test files

---

## Notes

- [P] tasks = different files, no shared dependencies — safe to parallelize
- T005 implements both US1 (403) and US2 (429) — they share the same `extract()` override
- US3 requires no implementation — only a verification test (T007)
- Integration test T004 requires network access: run with `make integration` not `make test`
- `exc.url` on fallback failures must be the original Medium URL (never the Freedium URL) — see contracts/extract-api.md
