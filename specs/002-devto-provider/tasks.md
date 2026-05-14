# Tasks: mdfetch — dev.to Extractor

**Input**: Design documents from `specs/002-devto-provider/`

**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅

**Organization**: Tasks are grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- Exact file paths in every description

---

## Phase 1: Setup

**Purpose**: Verify baseline is green before adding any new code

- [x] T001 Run `make test` and confirm all existing unit tests pass (green baseline)

---

## Phase 2: Foundational

**Purpose**: No new shared infrastructure is required — the existing `BaseExtractor`, router, and exception hierarchy are sufficient. This phase is a no-op; begin user story work immediately after Phase 1.

**Checkpoint**: Foundation ready — proceed directly to Phase 3.

---

## Phase 3: User Story 1 — Extract a dev.to Article to Markdown (Priority: P1) 🎯 MVP

**Goal**: Calling `extract("https://dev.to/...")` on a valid article URL returns clean Markdown containing the title, cover image, and article body.

**Independent Test**: `uv run python -c "from mdfetch import extract; md = extract('https://dev.to/stn1slv/integration-digest-for-december-2025-5dlp'); assert '# ' in md and '![' in md and '<' not in md; print('US1 PASS')"`

### Implementation for User Story 1

- [x] T002 [US1] Implement `DevToExtractor` in `src/mdfetch/providers/devto.py`:
  - Declare `DOMAINS = frozenset({"dev.to"})` and apply `@register`
  - `clean_html`: locate `div#article-body`; extract `<h1>` and cover `<img class="crayons-article__cover__image">` from `<header class="crayons-article__header">` and prepend to body; strip empty `<a name="...">` anchor links inside headings; replace `<iframe>` tags with `<a href="{src}">{src}</a>`; replace liquid-tag embeds (class matching `ltag`) with plain links; raise `UnsupportedContentTypeError` if `div#article-body` absent
  - `convert_to_markdown`: call `markdownify` with `heading_style="ATX"`, `strip=["script", "style"]`; strip result; collapse 3+ newlines to 2; raise `EmptyContentError` if blank

### Tests for User Story 1

- [x] T003 [US1] Write unit tests for happy path in `tests/unit/test_devto_extractor.py`:
  - Fixture with minimal article HTML: `<header class="crayons-article__header">` containing `<h1>` + `<img class="crayons-article__cover__image">` and `<div id="article-body">` containing heading, paragraph, code block, list, inline image
  - `test_preserves_title` — `# Title` present in Markdown
  - `test_preserves_cover_image` — `![Cover image...](https://...)` present
  - `test_preserves_heading` — ATX `##` heading present
  - `test_preserves_code_block` — triple-backtick block present
  - `test_preserves_list` — `- ` or `* ` present
  - `test_preserves_body_image` — `![alt](url)` from body img present
  - `test_no_raw_html_tags` — regex confirms no `<tag>` in output (excluding Markdown autolinks)
  - `test_strips_empty_anchor_links` — headings do not contain empty `[]()` fragments

- [x] T004 [US1] Add unit tests for embed→link conversion in `tests/unit/test_devto_extractor.py`:
  - Fixture article HTML with `<iframe src="https://gist.github.com/...">` inside `div#article-body`
  - `test_iframe_replaced_with_link` — assert output Markdown contains `https://gist.github.com/...` as a plain link and no `<iframe>`
  - Fixture article HTML with `<div class="ltag__github-readme" data-url="https://github.com/...">` inside `div#article-body`
  - `test_liquid_tag_replaced_with_link` — assert output Markdown contains `https://github.com/...` as a plain link and no `ltag` div content

**Checkpoint**: At this point, `extract("https://dev.to/...")` returns clean Markdown for any valid article — US1 fully functional.

---

## Phase 4: User Story 2 — Meaningful Errors for Non-Article Pages (Priority: P2)

**Goal**: Passing a dev.to profile URL or tag page URL raises `UnsupportedContentTypeError`; passing a non-dev.to URL raises `UnsupportedPlatformError`.

**Independent Test**: `uv run python -c "from mdfetch import extract; from mdfetch.exceptions import UnsupportedContentTypeError; [extract('https://dev.to/stn1slv')]` should raise `UnsupportedContentTypeError` (profile, no article-body).

### Tests for User Story 2

- [x] T005 [US2] Add error-path unit tests to `tests/unit/test_devto_extractor.py`:
  - Fixture `profile_html`: HTML with no `div#article-body` (simulates author profile page)
  - `test_raises_unsupported_content_type_for_profile` — `clean_html(profile_soup)` raises `UnsupportedContentTypeError`
  - Fixture `tag_listing_html`: HTML with no `div#article-body` (simulates `https://dev.to/t/kafka` tag listing page)
  - `test_raises_unsupported_content_type_for_tag_listing` — `clean_html(tag_listing_soup)` raises `UnsupportedContentTypeError`
  - Fixture `empty_article_html`: `<div id="article-body"></div>` with no text
  - `test_raises_empty_content_error_for_blank_body` — `convert_to_markdown(cleaned)` raises `EmptyContentError`

**Note**: `UnsupportedPlatformError` for non-dev.to domains is already covered by existing `tests/unit/test_router.py` — no new test needed.

**Checkpoint**: All error scenarios for dev.to verified — US2 fully functional alongside US1.

---

## Phase 5: User Story 3 — Integration Tests Pass Against Real dev.to URLs (Priority: P3)

**Goal**: `uv run pytest -m integration tests/integration/test_devto_integration.py -v` exits green for all three reference articles.

**Independent Test**: All three integration tests pass without failures or skips when run with a stable internet connection.

### Implementation for User Story 3

- [x] T006 [US3] Generate snapshots for the three reference articles by running extraction and saving output:
  ```
  uv run python -c "from mdfetch import extract; open('tests/integration/snapshots/devto-integration-digest-december-2025.md','w').write(extract('https://dev.to/stn1slv/integration-digest-for-december-2025-5dlp'))"
  uv run python -c "from mdfetch import extract; open('tests/integration/snapshots/devto-integration-digest-july-2025.md','w').write(extract('https://dev.to/stn1slv/integration-digest-for-july-2025-4lk9'))"
  uv run python -c "from mdfetch import extract; open('tests/integration/snapshots/devto-integration-digest-march-2026.md','w').write(extract('https://dev.to/stn1slv/integration-digest-for-march-2026-599p'))"
  ```
  Inspect each snapshot file — confirm non-empty, Markdown formatted, title present, no raw HTML.

- [x] T007 [US3] Write `tests/integration/test_devto_integration.py` mirroring the Medium integration test pattern:
  - `DEVTO_TEST_CASES` list of `(url, snapshot_filename)` tuples for all three reference articles
  - `@pytest.mark.integration @pytest.mark.parametrize` over `DEVTO_TEST_CASES`
  - `test_extract_contains_snapshot`: read snapshot, call `extract(url)`, assert `expected in result`
  - Include snapshot regeneration hint in assertion message

- [x] T008 [US3] Run `uv run pytest -m integration tests/integration/test_devto_integration.py -v` and confirm all 3 tests pass

**Checkpoint**: All three integration tests green — US3 fully functional, feature complete.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final quality gate across all new files before marking feature done.

- [x] T009 [P] Run `make lint` (`ruff check`) on new files and fix any reported issues in `src/mdfetch/providers/devto.py` and test files
- [x] T010 [P] Run `make format` (`ruff format`) on new files to ensure consistent style
- [x] T011 [P] Run `uv run mypy src/` and fix any type errors in `src/mdfetch/providers/devto.py` (zero errors required)
- [x] T012 Run `make test` and confirm all unit tests pass with no regressions

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies — start immediately
- **Phase 2 (Foundational)**: N/A — no blocking prerequisites for this feature
- **Phase 3 (US1)**: Depends on Phase 1 green baseline; T002 must complete before T003/T004
- **Phase 4 (US2)**: Depends on T002 (error-handling code is in devto.py written in T002)
- **Phase 5 (US3)**: Depends on T002 (provider must work to generate snapshots)
- **Phase 6 (Polish)**: Depends on all phases complete

### User Story Dependencies

- **US1 (P1)**: Can start after Phase 1 — no dependencies on other stories
- **US2 (P2)**: Depends on T002 (the `UnsupportedContentTypeError` guard is in devto.py) — tests can be written once T002 is done
- **US3 (P3)**: Depends on T002 (provider must work to generate snapshots and run integration tests)

### Within Each User Story

- T002 must complete before T003, T004, T005, T006, T007
- T006 (snapshot generation) must complete before T007 (writing integration tests)
- T007 must complete before T008 (running integration tests)

### Parallel Opportunities

- T003 and T004 write to the same file — run sequentially
- T005 writes to the same file as T003/T004 — run after T003/T004
- T009, T010, T011 (Phase 6) work on different concerns — run in parallel

---

## Parallel Example: User Story 1

```bash
# After T002 is complete, run T003 and T004 sequentially (same file):
# First: write happy-path tests in test_devto_extractor.py
# Then: add iframe test to test_devto_extractor.py
# Verify: uv run pytest tests/unit/test_devto_extractor.py -v
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. T001: Confirm green baseline
2. T002: Implement DevToExtractor
3. T003–T004: Unit tests (happy path + iframe)
4. **STOP and VALIDATE**: `make test` passes; manual extraction of a reference URL works
5. Proceed to US2 and US3

### Incremental Delivery

1. T001 → T002 → T003–T004 → US1 done ✓
2. T005 → US2 done ✓
3. T006 → T007 → T008 → US3 done ✓
4. T009–T012 → Polish done ✓

---

## Remediation: Gaps

*Discovered via `/speckit-reconcile-run check everything` on 2026-05-14.*

- [ ] T013 Add `"dev.to"` to the `keywords` list in `pyproject.toml` so the package is discoverable for dev.to-related searches on PyPI [Sync: Gap Report]

---

## Notes

- `[P]` tasks work on different concerns — safe to run in parallel
- `[USN]` label maps each task to the user story it serves for traceability
- US2 has no new implementation tasks — the guard code is part of US1's devto.py; only test tasks are new
- Snapshots (T006) must be generated before integration tests (T007) can reference them
- A snapshot is a subset of the full extraction output; `expected in result` checks are resilient to minor layout changes
