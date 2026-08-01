# Tasks: tavily-fallback

**Input**: Design documents from `/specs/013-tavily-fallback/`

**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Phase 1: Setup

**Purpose**: Verify baseline and create file stubs.

- [ ] T001 Run `make test` and confirm all existing unit tests pass (green baseline)
- [ ] T002 Add `tavily-python` dependency via `uv add tavily-python` in `pyproject.toml`
- [ ] T003 Create `src/mdfetch/fallback.py` with module docstring
- [ ] T004 [P] Create `tests/unit/test_fallback.py` with module docstring
- [ ] T005 [P] Create `tests/integration/test_fallback_integration.py` with module docstring

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Implement basic API and CLI wiring for the new fallback flag.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [ ] T006 Add `MissingAPIKeyError` class to `src/mdfetch/exceptions.py`
- [ ] T007 Add `--tavily-fallback` boolean option to CLI in `src/mdfetch/cli.py`
- [ ] T008 Add `tavily_fallback: bool = False` argument to `extract()` in `src/mdfetch/__init__.py` and raise `MissingAPIKeyError` if True and `TAVILY_API_KEY` is missing

**Checkpoint**: `make test` passes; CLI recognizes `--tavily-fallback`.

---

## Phase 3: User Story 1 - Tavily for Non-Supported Platforms (Priority: P1) 🎯 MVP

**Goal**: Extract content from URLs that don't belong to any supported platform so that I can still get Markdown for arbitrary blogs.

**Independent Test**: Can be fully tested by calling the main extraction function with an unsupported URL while `TAVILY_API_KEY` is set, verifying it returns valid Markdown.

### Implementation for User Story 1

- [ ] T009 [US1] Implement `tavily_extract(url: str) -> str` in `src/mdfetch/fallback.py`:
  1. Initialize `TavilyClient()`
  2. Attempt `client.extract(urls=[url], extract_depth="basic")`
  3. If exception or empty `raw_content`, attempt `client.extract(urls=[url], extract_depth="advanced")`
  4. Return `raw_content` or raise wrapped `FetchError`/`EmptyContentError`
- [ ] T010 [US1] Update `extract()` in `src/mdfetch/__init__.py` to catch `UnsupportedPlatformError` from `route(url)` and call `tavily_extract(url)` if `tavily_fallback` is True.

### Tests for User Story 1

- [ ] T011 [P] [US1] Add unit tests for `tavily_extract` basic/advanced depth switching using mocked `TavilyClient` in `tests/unit/test_fallback.py`
- [ ] T012 [P] [US1] Add unit tests for `extract()` routing `UnsupportedPlatformError` to fallback in `tests/unit/test_fallback.py`
- [ ] T013 [US1] Add integration test for fallback on an unsupported blog URL in `tests/integration/test_fallback_integration.py` (requires `TAVILY_API_KEY`)

**Checkpoint**: `make test` green; `make integration` passes; User Story 1 is independently functional.

---

## Phase 4: User Story 2 - Tavily as Fallback for Supported Platforms (Priority: P2)

**Goal**: The system falls back to Tavily if the dedicated provider for a supported platform fails to extract content so that I have a higher success rate.

**Independent Test**: Can be tested by mocking a supported provider to raise an exception, and verifying the main extraction workflow catches it and successfully uses Tavily (given `TAVILY_API_KEY` is set).

### Implementation for User Story 2

- [ ] T014 [US2] Update `extract()` in `src/mdfetch/__init__.py` to catch all exceptions (except `MissingAPIKeyError`, `InvalidURLError`) and call `tavily_extract(url)` if `tavily_fallback` is True. If fallback also fails, chain the exception.

### Tests for User Story 2

- [ ] T015 [P] [US2] Add unit tests verifying `extract()` intercepts provider exceptions (e.g. `FetchError`) and falls back in `tests/unit/test_fallback.py`
- [ ] T016 [US2] Add integration test for a supported platform (e.g., Medium) but mock the initial extraction to fail, ensuring it succeeds via Tavily in `tests/integration/test_fallback_integration.py`

**Checkpoint**: User Stories 1 AND 2 both work independently.

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Final quality gate across all new files.

- [ ] T017 [P] Run `uv run mypy src/mdfetch/fallback.py src/mdfetch/cli.py src/mdfetch/__init__.py` and fix any type errors
- [ ] T018 [P] Run `make lint` and fix any ruff violations in new files
- [ ] T019 Run `make test` and confirm all unit tests pass with no regressions
- [ ] T020 Run `make integration` and confirm all integration tests pass

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - Primary implementation
- **User Story 2 (P2)**: Depends on US1 implementation of `tavily_extract()`

### Within Each User Story

- Implementation before tests (tests verify implemented behaviour)
- Unit tests before integration tests
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Unit tests for a story marked [P] can run in parallel (different test classes/methods)

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: `make test && make integration` — US1 independently functional
5. Ship if ready

### Incremental Delivery

1. Phase 1 + Phase 2 → API configuration and CLI working
2. Phase 3 → extraction works for unsupported sites (MVP)
3. Phase 4 → extraction works for failing supported providers
4. Phase N → clean mypy + lint pass

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
