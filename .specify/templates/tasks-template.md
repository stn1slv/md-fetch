---

description: "Task list template for feature implementation"
---

# Tasks: [FEATURE NAME]

**Input**: Design documents from `/specs/[###-feature-name]/`

**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Provider source**: `src/mdfetch/providers/[platform].py`
- **Unit tests**: `tests/unit/test_[platform]_extractor.py`
- **Integration tests**: `tests/integration/test_[platform]_integration.py`
- **Snapshots**: `tests/integration/snapshots/[platform]-[slug].md`

<!--
  ============================================================================
  IMPORTANT: The tasks below are SAMPLE TASKS for illustration purposes only.

  The /speckit-tasks command MUST replace these with actual tasks based on:
  - User stories from spec.md (with their priorities P1, P2, P3...)
  - Feature requirements from plan.md
  - Extraction algorithm from plan.md
  - Entities from data-model.md
  - Endpoints from contracts/

  Tasks MUST be organized by user story so each story can be:
  - Implemented independently
  - Tested independently
  - Delivered as an MVP increment

  DO NOT keep these sample tasks in the generated tasks.md file.
  ============================================================================
-->

## Phase 1: Setup

**Purpose**: Verify baseline and create file stubs.

- [ ] T001 Run `make test` and confirm all existing unit tests pass (green baseline)
- [ ] T002 Create `src/mdfetch/providers/[platform].py` with module docstring, `from __future__ import annotations`, and required imports
- [ ] T003 [P] Create `tests/unit/test_[platform]_extractor.py` with module docstring, imports, and empty `extractor` fixture
- [ ] T004 [P] Create `tests/integration/test_[platform]_integration.py` with module docstring, imports, and empty test cases list

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Register the extractor so the router resolves platform URLs. All user stories depend on this.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [ ] T005 Add `[Platform]Extractor(BaseExtractor)` class with `@register` decorator, `DOMAINS` frozenset, and stub bodies for `clean_html` and `convert_to_markdown` (raise `NotImplementedError`)
- [ ] T006 [P] Add routing unit tests: verify `route("[platform URL]")` returns `[Platform]Extractor` instance

**Checkpoint**: `make test` passes (stubs present); routing is verified.

---

## Phase 3: User Story 1 - [Title] (Priority: P1) 🎯 MVP

**Goal**: [Brief description of what this story delivers]

**Independent Test**: [How to verify this story works on its own]

### Implementation for User Story 1

- [ ] T007 [US1] Implement `clean_html(self, soup: BeautifulSoup) -> Tag` in `src/mdfetch/providers/[platform].py`:
  1. Find article body container; raise `UnsupportedContentTypeError` if absent
  2. Strip non-content elements (CTAs, navigation, etc.)
  3. Convert embedded content (iframes, embeds) to anchor links
  4. Extract and prepend title (and subtitle if present)
  5. Return body tag
- [ ] T008 [US1] Implement `convert_to_markdown(self, tag: Tag) -> str` in `src/mdfetch/providers/[platform].py`:
  1. Call `markdownify` with `heading_style="ATX"`, `strip=["script", "style"]`
  2. Strip whitespace, collapse 3+ blank lines
  3. Raise `EmptyContentError` if result is empty
  4. Return Markdown string

### Tests for User Story 1

- [ ] T009 [P] [US1] Add unit tests for `clean_html` happy path in `tests/unit/test_[platform]_extractor.py`
- [ ] T010 [P] [US1] Add unit tests for `convert_to_markdown` in `tests/unit/test_[platform]_extractor.py`
- [ ] T011 [US1] Add integration test for free article in `tests/integration/test_[platform]_integration.py` with snapshot

**Checkpoint**: `make test` green; `make integration` passes; User Story 1 is independently functional.

---

## Phase 4: User Story 2 - [Title] (Priority: P2)

**Goal**: [Brief description of what this story delivers]

**Independent Test**: [How to verify this story works on its own]

### Tests for User Story 2

- [ ] T012 [P] [US2] Add unit test for [scenario] in `tests/unit/test_[platform]_extractor.py`
- [ ] T013 [US2] Add integration test for [scenario] in `tests/integration/test_[platform]_integration.py`

**Checkpoint**: User Stories 1 AND 2 both work independently.

---

## Phase 5: User Story 3 - [Title] (Priority: P3)

**Goal**: [Brief description of what this story delivers]

**Independent Test**: [How to verify this story works on its own]

### Tests for User Story 3

- [ ] T014 [P] [US3] Add unit test for `UnsupportedContentTypeError` in `tests/unit/test_[platform]_extractor.py`
- [ ] T015 [P] [US3] Add unit test for `EmptyContentError` in `tests/unit/test_[platform]_extractor.py`
- [ ] T016 [US3] Add integration test for non-article URL in `tests/integration/test_[platform]_integration.py`

**Checkpoint**: All user stories independently functional; all unit and integration tests pass.

---

[Add more user story phases as needed, following the same pattern]

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Final quality gate across all new files.

- [ ] TXXX [P] Run `uv run mypy src/mdfetch/providers/[platform].py` and fix any type errors
- [ ] TXXX [P] Run `make lint` and fix any ruff violations in new files
- [ ] TXXX Run `make test` and confirm all unit tests pass with no regressions
- [ ] TXXX Run `make integration` and confirm all integration tests pass
- [ ] TXXX Update unsupported-domain fixture in `tests/unit/test_router.py` if the new provider registers a previously-used "unsupported" domain

---

## Remediation: Gaps

<!--
  Discovered via /speckit-reconcile-run or post-implementation review.
  Add tasks here for fixes that weren't part of the original plan.
-->

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - Primary implementation
- **User Story 2 (P2)**: Depends on US1 implementation (often test-only phase if behaviour is inherent)
- **User Story 3 (P3)**: Depends on US1 error-handling code (often test-only phase)

### Within Each User Story

- Implementation before tests (tests verify implemented behaviour)
- `clean_html` before `convert_to_markdown`
- Unit tests before integration tests
- Snapshot generation before integration test assertions
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel
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

1. Phase 1 + Phase 2 → extractor registered, routing works
2. Phase 3 → extraction works (MVP)
3. Phase 4 → edge case handling verified
4. Phase 5 → error cases verified
5. Phase N → clean mypy + lint pass

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Integration test snapshots must be generated from real network calls before they can be used
- Snapshot generation command: `uv run python -c "from mdfetch import extract; open('tests/integration/snapshots/<name>.md','w').write(extract('<url>'))"`
- Run `make format` after implementing to ensure consistent style before lint check
