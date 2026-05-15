---
description: "Task list for Substack platform provider implementation"
---

# Tasks: Substack Platform Provider

**Input**: Design documents from `specs/005-substack-provider/`

**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅

**Organization**: Tasks are grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)

---

## Phase 1: Setup

**Purpose**: Create new provider and test file stubs.

- [x] T001 Create `src/mdfetch/providers/substack.py` with module docstring, `from __future__ import annotations`, and all required imports (`re`, `BeautifulSoup`, `Tag`, `markdownify`, `BaseExtractor`, `EmptyContentError`, `UnsupportedContentTypeError`, `register`)
- [x] T002 [P] Create `tests/unit/test_substack_extractor.py` with module docstring, imports (`pytest`, `BeautifulSoup`, `SubstackExtractor`), and an empty `extractor` fixture
- [x] T003 [P] Create `tests/integration/test_substack_integration.py` with module docstring, imports (`pytest`, `Path`, `extract`), `SNAPSHOTS_DIR` constant, and empty `SUBSTACK_TEST_CASES` list

**Checkpoint**: Files exist; project structure matches plan.

---

## Phase 2: Foundational (Blocking Prerequisite)

**Purpose**: Register the extractor so the router resolves `*.substack.com` URLs. All user stories depend on this.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [x] T004 Add `SubstackExtractor(BaseExtractor)` class to `src/mdfetch/providers/substack.py` with `@register` decorator, `DOMAINS: frozenset[str] = frozenset({"substack.com"})`, and stub bodies for `clean_html` and `convert_to_markdown` (raise `NotImplementedError`)
- [x] T005 [P] Add routing unit tests in `tests/unit/test_substack_extractor.py`: verify `route("https://getkafkanated.substack.com/p/x")` returns a `SubstackExtractor` instance; verify `route("https://substack.com/")` also routes to `SubstackExtractor`; import `route` from `mdfetch.router`; assert `SubstackExtractor._no_retry_status_codes == frozenset()` to lock in FR-010 (HTTP 429 retried, not raised immediately)

**Checkpoint**: `make test` passes (stubs present); routing is verified.

---

## Phase 3: User Story 1 — Extract a Free Substack Article (Priority: P1) 🎯 MVP

**Goal**: `extract()` called with a free `*.substack.com/p/...` URL returns clean Markdown with title and body, no subscription CTAs or chrome.

**Independent Test**: `extract("https://getkafkanated.substack.com/p/kafka-deserves-topic-types")` returns a string starting with `# Kafka deserves topic types` containing article headings and body text but not the word "Subscribe".

### Implementation for User Story 1

- [x] T006 [US1] Implement `clean_html(self, soup: BeautifulSoup) -> Tag` in `src/mdfetch/providers/substack.py`:
  1. Find `div.body.markup`; raise `UnsupportedContentTypeError("URL is not an article page — no article body element found")` if absent
  2. Strip all `div.subscription-widget-wrap` elements inside the body
  3. Find `h1.post-title` in `div.post-header`; if present, insert as first child of body
  4. Find `h3.subtitle` in `div.post-header`; if present, insert after title (before body content)
  5. Return the body tag
- [x] T007 [US1] Implement embed conversion inside `clean_html` in `src/mdfetch/providers/substack.py`:
  1. For each `iframe` in body: replace with `<a href=src>src</a>` using `src` or `data-src` attribute; decompose if no src
  2. For each `div[data-component-name]` where `data-component-name` is not `"SubscribeWidget"` or `"Image2ToDOM"`: replace with `<a href>url</a>` using first available `href`, `data-url`, or `src` attribute; decompose if no URL found
- [x] T008 [US1] Implement `convert_to_markdown(self, tag: Tag) -> str` in `src/mdfetch/providers/substack.py`:
  1. Call `markdownify(str(tag), heading_style="ATX", code_language="", strip=["script", "style"])`
  2. Strip leading/trailing whitespace
  3. Collapse three or more consecutive blank lines to one blank line using `re.sub(r"\n{3,}", "\n\n", md)`
  4. Raise `EmptyContentError("Article body contained no extractable text content")` if result is empty
  5. Return the Markdown string

### Tests for User Story 1

- [x] T009 [P] [US1] Add unit tests for `clean_html` happy path in `tests/unit/test_substack_extractor.py`:
  - Fixture: minimal HTML with `div.post-header > h1.post-title` + `h3.subtitle`, `div.available-content > div.body.markup` containing a paragraph and `div.subscription-widget-wrap`
  - Assert returned tag is `div.body.markup`
  - Assert `div.subscription-widget-wrap` is absent from returned tag
  - Assert returned tag starts with `h1` containing title text
  - Assert `h3` subtitle is second element
- [x] T010 [P] [US1] Add unit tests for `convert_to_markdown` in `tests/unit/test_substack_extractor.py`:
  - Assert output starts with `# ` heading (title)
  - Assert no triple blank lines in output
  - Assert images rendered as `![alt](url)` Markdown syntax
- [x] T011 [US1] Add integration test for free article in `tests/integration/test_substack_integration.py`:
  - Add `("https://getkafkanated.substack.com/p/kafka-deserves-topic-types", "substack-kafka-topic-types.md")` to `SUBSTACK_TEST_CASES`
  - Add `@pytest.mark.integration @pytest.mark.parametrize` test function `test_extract_contains_snapshot` matching the pattern in `test_devto_integration.py`
  - Generate snapshot file `tests/integration/snapshots/substack-kafka-topic-types.md` by running: `uv run python -c "from mdfetch import extract; open('tests/integration/snapshots/substack-kafka-topic-types.md','w').write(extract('https://getkafkanated.substack.com/p/kafka-deserves-topic-types'))"`

**Checkpoint**: `make test` green; `make integration` passes for `test_substack_integration.py`; User Story 1 is independently functional.

---

## Phase 4: User Story 2 — Paywalled Post Handling (Priority: P2)

**Goal**: `extract()` on a paywalled Substack post returns the free preview as Markdown without raising an exception.

**Independent Test**: Pass a known paywalled URL to `extract()`; result is a non-empty string not containing the text `"Subscribe to read"`.

**Note**: No new implementation is required — paywalled post handling is achieved by the `div.subscription-widget-wrap` stripping implemented in T006. This phase adds tests to verify and lock in that behaviour.

### Tests for User Story 2

- [x] T012 [P] [US2] Add unit test for paywalled post in `tests/unit/test_substack_extractor.py`:
  - Fixture: HTML where `div.body.markup` contains two paragraphs of prose followed by a `div.subscription-widget-wrap` as the last element
  - Assert `extract()` (or `clean_html` + `convert_to_markdown`) returns non-empty Markdown
  - Assert the string `"Subscribe"` does not appear in the output
- [x] T013 [US2] Add integration test for CTA stripping (and paywalled behaviour) in `tests/integration/test_substack_integration.py`:
  - Add `("https://pragmaticapi.substack.com/p/api-trends-for-2025-the-evolution", "substack-api-trends-2025.md")` to `SUBSTACK_TEST_CASES` — this URL verifies that inline `div.subscription-widget-wrap` CTAs are stripped from a real article
  - Generate snapshot: `uv run python -c "from mdfetch import extract; open('tests/integration/snapshots/substack-api-trends-2025.md','w').write(extract('https://pragmaticapi.substack.com/p/api-trends-for-2025-the-evolution'))"`
  - **Note**: this article's content is publicly accessible (free article with inline CTAs). For a true paywalled-post integration test, source a Substack URL that returns a truncated body (where the subscription widget is the final element and less than ~300 words precede it); add it as an additional entry when found. The unit test in T012 covers the paywalled-truncation logic using an HTML fixture.

**Checkpoint**: Both unit and integration tests for paywalled posts pass.

---

## Phase 5: User Story 3 — Reject Non-Article Pages (Priority: P3)

**Goal**: `extract()` on a Substack homepage or page with no article body raises `UnsupportedContentTypeError`; on an article with empty body raises `EmptyContentError`.

**Independent Test**: `extract("https://getkafkanated.substack.com/")` raises `UnsupportedContentTypeError`.

**Note**: No new implementation required — `UnsupportedContentTypeError` is raised in T006 when `div.body.markup` is absent; `EmptyContentError` is raised in T008 when the body produces no text. This phase adds tests to verify.

### Tests for User Story 3

- [x] T014 [P] [US3] Add unit test for `UnsupportedContentTypeError` in `tests/unit/test_substack_extractor.py`:
  - Fixture: HTML with no `div.body.markup` element (e.g., a homepage-like structure)
  - Assert `clean_html(soup)` raises `UnsupportedContentTypeError`
- [x] T015 [P] [US3] Add unit test for `EmptyContentError` in `tests/unit/test_substack_extractor.py`:
  - Fixture: HTML with `div.body.markup` present but containing only whitespace
  - Assert calling `convert_to_markdown` on the cleaned tag raises `EmptyContentError`
- [x] T016 [US3] Add integration test for non-article URL in `tests/integration/test_substack_integration.py`:
  - Separate test function (not parametrized with snapshots) that calls `extract("https://getkafkanated.substack.com/")` and asserts `UnsupportedContentTypeError` is raised

**Checkpoint**: All three user stories independently functional; all unit and integration tests pass.

---

## Phase 6: Polish & Cross-Cutting Concerns

- [x] T017 [P] Run `uv run mypy src/mdfetch/providers/substack.py` and fix any type errors until output is clean with zero errors
- [x] T018 [P] Run `make lint` and fix any ruff violations in `src/mdfetch/providers/substack.py`, `tests/unit/test_substack_extractor.py`, and `tests/integration/test_substack_integration.py`
- [x] T019 Run `make test` and confirm all unit tests pass (green baseline)
- [x] T020 Run `make integration` and confirm all integration tests pass including the three new Substack tests
- [x] T021 [Sync: Gap Report] Update unsupported-domain test fixtures in `tests/unit/test_router.py` from `substack.com` to `wordpress.com` — registering `SubstackExtractor` caused the original fixtures to route successfully instead of raising `UnsupportedPlatformError`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies — start immediately; T002 and T003 can run in parallel with T001
- **Phase 2 (Foundational)**: Depends on Phase 1 — T004 requires T001; T005 requires T002 and T004
- **Phase 3 (US1)**: Depends on Phase 2 — T006, T007, T008 are sequential within the same method; T009 and T010 can run in parallel with T006–T008 once T004 exists; T011 requires T006–T008 complete
- **Phase 4 (US2)**: Can start after T006 (stripping is implemented); T012 and T013 are parallel
- **Phase 5 (US3)**: Can start after T006 and T008; T014 and T015 are parallel
- **Phase 6 (Polish)**: Depends on all prior phases complete

### User Story Dependencies

- **US1 (P1)**: Depends on Phase 2 only — primary implementation
- **US2 (P2)**: Depends on US1 T006 (CTA stripping) — test-only phase
- **US3 (P3)**: Depends on US1 T006 and T008 (error raises) — test-only phase

### Parallel Opportunities

- T002 and T003 (stub test files) parallel with T001
- T009 and T010 (unit tests) parallel with T006–T008 if using stubs
- T012 and T013 (US2 tests) parallel with each other
- T014 and T015 (US3 tests) parallel with each other
- T017 and T018 (mypy and lint) parallel with each other

---

## Parallel Example: User Story 1

```bash
# Once T004 is done, these can run in parallel:
Task T006: "Implement clean_html in src/mdfetch/providers/substack.py"
Task T009: "Write clean_html unit tests (using stubs) in tests/unit/test_substack_extractor.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001–T003)
2. Complete Phase 2: Foundational (T004–T005)
3. Complete Phase 3: User Story 1 (T006–T011)
4. **STOP and VALIDATE**: `make test && make integration` — US1 independently functional
5. Ship: Substack free articles work end-to-end

### Incremental Delivery

1. Phase 1 + Phase 2 → extractor registered, routing works
2. Phase 3 → free article extraction works (MVP)
3. Phase 4 → paywalled post handling verified
4. Phase 5 → error cases verified
5. Phase 6 → clean mypy + lint pass

---

## Notes

- `[P]` tasks operate on different files or are independent of in-progress tasks in the same file
- Integration test snapshots must be generated from real network calls before they can be used as assertions
- The `tests/integration/snapshots/` directory already exists from prior providers — add new `.md` files there
- Snapshot generation command pattern (matches existing providers): `uv run python -c "from mdfetch import extract; open('tests/integration/snapshots/<name>.md','w').write(extract('<url>'))"`
- Run `make format` after implementing to ensure consistent style before lint check
