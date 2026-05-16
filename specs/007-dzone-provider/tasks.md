---

description: "Task list for DZone Platform Provider"
---

# Tasks: DZone Platform Provider

**Input**: Design documents from `specs/007-dzone-provider/`

**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅, quickstart.md ✅

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)

## Path Conventions

- **Provider source**: `src/mdfetch/providers/dzone.py`
- **Unit tests**: `tests/unit/test_dzone_extractor.py`
- **Integration tests**: `tests/integration/test_dzone_integration.py`
- **Snapshots**: `tests/integration/snapshots/dzone-*.md`

---

## Phase 1: Setup

**Purpose**: Verify baseline and create file stubs.

- [ ] T001 Run `make test` and confirm all existing unit tests pass (green baseline before any changes)
- [ ] T002 Create `src/mdfetch/providers/dzone.py` with module docstring `"""DZone platform extractor."""`, `from __future__ import annotations`, and required imports (`copy`, `re`, `BeautifulSoup`, `Tag`, `markdownify`, `BaseExtractor`, `EmptyContentError`, `UnsupportedContentTypeError`, `register`)
- [ ] T003 [P] Create `tests/unit/test_dzone_extractor.py` with module docstring, imports (`pytest`, `BeautifulSoup`, `Tag`, `DZoneExtractor`, `EmptyContentError`, `UnsupportedContentTypeError`), and empty `extractor` fixture returning `DZoneExtractor()`
- [ ] T004 [P] Create `tests/integration/test_dzone_integration.py` with module docstring, imports (`Path`, `pytest`, `extract`, `UnsupportedContentTypeError`), `SNAPSHOTS_DIR` constant, and empty `DZONE_TEST_CASES` list

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Register the extractor so the router resolves `dzone.com` URLs. All user stories depend on this.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [ ] T005 Add `DZoneExtractor(BaseExtractor)` class in `src/mdfetch/providers/dzone.py` with `@register` decorator, `DOMAINS: frozenset[str] = frozenset({"dzone.com"})`, and stub bodies for `clean_html` and `convert_to_markdown` (raise `NotImplementedError`)
- [ ] T006 [P] Add routing test `test_routes_dzone_com` to `tests/unit/test_router.py`: assert `route("https://dzone.com/articles/some-article")` returns a `DZoneExtractor` instance

**Checkpoint**: `make test` passes (stubs present, routing verified). Note: `wordpress.com` unsupported-domain fixture requires no change (confirmed in research.md — `dzone.com` does not conflict).

---

## Phase 3: User Story 1 — Extract a Standard Article (Priority: P1) 🎯 MVP

**Goal**: A `dzone.com/articles/<slug>` URL returns clean Markdown with the article title as an H1 heading and the full article body (headings, lists, links, images) — with no ads, sidebar, sign-in prompts, or UI chrome.

**Independent Test**: Pass `https://dzone.com/articles/integration-patterns-fail-production` to `extract()` and verify the result starts with `# 6 Integration Patterns`, contains H2 body headings, and does not contain navigation or ad text.

### HTML Fixtures

- [ ] T007 [P] [US1] Add inline HTML fixtures to `tests/unit/test_dzone_extractor.py`:
  - `ARTICLE_HTML` — minimal page with `h1.article-title` inside `div.title > div.header-title`, and `div.content-html` containing a `<p>`, an `<h2>`, a `<ul>`, a `<a>`, and an `<img>`
  - `NO_ARTICLE_HTML` — page without `div.content-html` (refcard-like, no article body)
  - `EMPTY_BODY_HTML` — page with `h1.article-title` and `div.content-html` present but whitespace-only

### Implementation for User Story 1

- [ ] T008 [US1] Implement `clean_html(self, soup: BeautifulSoup) -> Tag` in `src/mdfetch/providers/dzone.py` (base extraction only, CodeMirror handling added in T015):
  1. `body = soup.find("div", class_="content-html")` → raise `UnsupportedContentTypeError("URL is not an article page — no article body element found")` if not a `Tag` (FR-004)
  2. `title_el = soup.find("h1", class_="article-title")` → if `isinstance(title_el, Tag)`, insert `copy.copy(title_el)` at position 0 of body (FR-003)
  3. Return `body`
- [ ] T009 [US1] Implement `convert_to_markdown(self, tag: Tag) -> str` in `src/mdfetch/providers/dzone.py`:
  1. `md = markdownify(str(tag), heading_style="ATX", code_language="", strip=["script", "style"])`
  2. `md = md.strip()`
  3. `md = re.sub(r"\n{3,}", "\n\n", md)` (FR-008)
  4. Raise `EmptyContentError("Article body contained no extractable text content")` if `not md` (FR-005)
  5. Return `md`

### Tests for User Story 1

- [ ] T010 [P] [US1] Add `clean_html` happy-path unit tests in `tests/unit/test_dzone_extractor.py`:
  - `test_clean_html_returns_content_html_div` — result is a `Tag` with class `content-html`
  - `test_clean_html_prepends_title` — first element child of result is `h1` with `article-title` class and correct text
  - `test_clean_html_raises_on_no_article_body` — parse `NO_ARTICLE_HTML`, assert `clean_html(soup)` raises `UnsupportedContentTypeError`
- [ ] T011 [P] [US1] Add `convert_to_markdown` unit tests in `tests/unit/test_dzone_extractor.py`:
  - `test_convert_to_markdown_starts_with_title` — result starts with `# ` followed by title text
  - `test_convert_to_markdown_no_triple_blank_lines` — `"\n\n\n"` not in result
  - `test_convert_to_markdown_preserves_links` — `[text](url)` syntax present
  - `test_convert_to_markdown_raises_on_empty_body` — parse `EMPTY_BODY_HTML`, call `clean_html`, assert `convert_to_markdown` raises `EmptyContentError`

### Integration for User Story 1

- [ ] T012 [US1] Generate snapshot for article 1 (no code blocks) using a real network call:
  ```
  uv run python -c "
  from mdfetch import extract
  content = extract('https://dzone.com/articles/integration-patterns-fail-production')
  snapshot = '\n'.join(content.split('\n')[:30]).rstrip()
  open('tests/integration/snapshots/dzone-integration-patterns-fail-production.md', 'w', encoding='utf-8').write(snapshot)
  "
  ```
- [ ] T013 [US1] Add integration test in `tests/integration/test_dzone_integration.py`:
  - Populate `DZONE_TEST_CASES` with the first `(url, snapshot_filename)` pair
  - Add `@pytest.mark.integration @pytest.mark.parametrize` test `test_extract_contains_snapshot` with snapshot containment assertion (`expected in result`), matching pattern from `test_thenewstack_integration.py`
  - Run `make integration` and confirm article 1 passes

**Checkpoint**: `make test` green; `make integration` passes for article 1; US1 independently functional.

---

## Phase 4: User Story 2 — Extract an Article With Code Blocks (Priority: P2)

**Goal**: DZone articles with CodeMirror code blocks produce fenced Markdown code blocks with the correct language info string. The `div.codeHeader` UI chrome (language label element and cancel icon) is stripped; `pre > code` content is preserved.

**Independent Test**: Pass `https://dzone.com/articles/image-classification-pipeline-camel-djl` to `extract()` and verify the result contains ` ```java ` fenced code blocks and no `cm-remove` cancel icon text.

### HTML Fixtures

- [ ] T014 [P] [US2] Add code-block HTML fixtures to `tests/unit/test_dzone_extractor.py`:
  - `ARTICLE_WITH_CODE_HTML` — `div.content-html` containing a `div.codeMirror-wrapper` with:
    - `div.codeHeader > div.nameLanguage` text "Java" and `i.cm-remove` icon
    - `div.codeMirror-code--wrapper > pre > code` with a short Java snippet
  - `ARTICLE_WITH_PLAIN_TEXT_CODE_HTML` — same structure but `div.nameLanguage` text "Plain Text"

### Implementation for User Story 2

- [ ] T015 [US2] Extend `clean_html` in `src/mdfetch/providers/dzone.py` to handle CodeMirror blocks (insert BEFORE the title-prepend step, so the title is always the first element):
  1. For each `wrapper` in `body.find_all("div", class_="codeMirror-wrapper")`:
     - `name_lang_el = wrapper.find("div", class_="nameLanguage")`; `lang = name_lang_el.get_text(strip=True).lower() if isinstance(name_lang_el, Tag) else ""`
     - If `lang == "plain text"`: `lang = ""`
     - `code_el = wrapper.find("code")`; if `isinstance(code_el, Tag)` and `lang`: `code_el["class"] = [f"language-{lang}"]`
     - `code_header = wrapper.find("div", class_="codeHeader")`; if `isinstance(code_header, Tag)`: `code_header.decompose()` (FR-006, FR-007)
  Note: `class_="codeMirror-wrapper"` matches both `codeMirror-wrapper` and `codeMirror-wrapper newest` (BS4 class subset match).

### Tests for User Story 2

- [ ] T016 [P] [US2] Add code-block unit tests in `tests/unit/test_dzone_extractor.py`:
  - `test_clean_html_code_block_java_language` — using `ARTICLE_WITH_CODE_HTML`, result `code` element has class `language-java`
  - `test_clean_html_code_block_plain_text_no_language` — using `ARTICLE_WITH_PLAIN_TEXT_CODE_HTML`, result `code` element has no `language-*` class
  - `test_clean_html_strips_code_header` — `result.find("div", class_="codeHeader")` is `None`
  - `test_convert_to_markdown_fenced_code_block_with_language` — full round-trip: output contains ` ```java\n`

### Integration for User Story 2

- [ ] T017 [US2] Generate snapshots for articles 2 and 3 (with code blocks):
  ```
  uv run python -c "
  from mdfetch import extract
  articles = [
    ('https://dzone.com/articles/kiro-feature-to-requirements-design-tasks', 'dzone-kiro-feature-to-requirements-design-tasks.md'),
    ('https://dzone.com/articles/image-classification-pipeline-camel-djl', 'dzone-image-classification-pipeline-camel-djl.md'),
  ]
  for url, name in articles:
      content = extract(url)
      snapshot = '\n'.join(content.split('\n')[:30]).rstrip()
      open(f'tests/integration/snapshots/{name}', 'w', encoding='utf-8').write(snapshot)
  "
  ```
- [ ] T018 [US2] Add articles 2 and 3 to `DZONE_TEST_CASES` in `tests/integration/test_dzone_integration.py` and run `make integration` to confirm all 3 snapshots pass

**Checkpoint**: All US1 and US2 tests pass. Code block extraction verified end-to-end for all 3 reference articles.

---

## Phase 5: User Story 3 — Unsupported or Non-Article URL (Priority: P3)

**Goal**: DZone URLs that are not article pages (refcards, topic listings, user profiles) raise `UnsupportedContentTypeError` rather than returning empty or garbled Markdown. Articles with empty body raise `EmptyContentError`.

**Independent Test**: Assert `UnsupportedContentTypeError` using `NO_ARTICLE_HTML` fixture (already created in T007) and via a real refcard URL. Assert `EmptyContentError` using `EMPTY_BODY_HTML` fixture (already created in T007).

### Tests for User Story 3

- [ ] T019 [P] [US3] Verify `test_clean_html_raises_on_no_article_body` in `tests/unit/test_dzone_extractor.py` covers the `UnsupportedContentTypeError` path (test created in T010 — confirm it uses `NO_ARTICLE_HTML` and asserts the correct exception type)
- [ ] T020 [P] [US3] Verify `test_convert_to_markdown_raises_on_empty_body` in `tests/unit/test_dzone_extractor.py` covers the `EmptyContentError` path (test created in T011 — confirm it uses `EMPTY_BODY_HTML` and asserts the correct exception type)
- [ ] T021 [US3] Add integration test `test_non_article_url_raises_unsupported_content_type_error` in `tests/integration/test_dzone_integration.py`: assert `extract("https://dzone.com/refcardz/corecss-part1", retries=1, retry_delay=0.0)` raises `UnsupportedContentTypeError`

**Checkpoint**: All US1, US2, and US3 tests pass. All error scenarios verified.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final quality gate across all new and modified files.

- [ ] T022 [P] Run `uv run mypy src/mdfetch/providers/dzone.py` and fix any type errors (ensure return types, `isinstance` guards, and `copy.copy` import are correct)
- [ ] T023 [P] Run `make format` then `make lint` and fix any ruff violations in `src/mdfetch/providers/dzone.py`, `tests/unit/test_dzone_extractor.py`, `tests/integration/test_dzone_integration.py`
- [ ] T024 Run `make test` and confirm all unit tests pass with no regressions in existing providers
- [ ] T025 Run `make integration` and confirm all integration tests pass (3 dzone articles + refcard error case)

---

## Remediation: Gaps

<!--
  Discovered via /speckit-reconcile-run or post-implementation review.
  Add tasks here for fixes that weren't part of the original plan.
-->

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 — BLOCKS all user stories
- **US1 (Phase 3)**: Depends on Phase 2; T007 (fixtures) can start in parallel with T008–T009 (implementation)
- **US2 (Phase 4)**: Depends on Phase 3 completion; T014 (fixtures) can start in parallel with T015 (implementation)
- **US3 (Phase 5)**: Depends on Phase 2; uses fixtures from T007 (created in Phase 3); tests are verification-only
- **Polish (Phase 6)**: Depends on all user stories complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Phase 2 — full implementation + integration for article 1
- **User Story 2 (P2)**: Depends on US1 clean_html existing (T008); extends it in T015
- **User Story 3 (P3)**: Depends on US1 clean_html and convert_to_markdown (T008, T009); test-only phase

### Within Phase 3

- T007 (fixtures) in parallel with T008 (clean_html implementation)
- T009 (convert_to_markdown): after T008
- T010 (clean_html unit tests) and T011 (convert_to_markdown unit tests): both depend on T008–T009; can run in parallel with each other
- T012 (snapshot generation) → T013 (integration test): sequential; both depend on T009

### Within Phase 4

- T014 (code-block fixtures) can start immediately (parallel with rest of Phase 4)
- T015 (CodeMirror implementation): after T014 fixtures are ready
- T016 (unit tests): after T014 and T015
- T017 (snapshot generation) → T018 (integration test): sequential; T017 depends on T015

### Parallel Opportunities

- T003 and T004 in Phase 1 are parallel (different files)
- T006 in Phase 2 is parallel with T005 (different files)
- T007 in Phase 3 is parallel with T008 (test file vs. provider file)
- T010 and T011 in Phase 3 are parallel (different test functions)
- T014 in Phase 4 is parallel with T015 (test file vs. provider file)
- T019 and T020 in Phase 5 are parallel
- T022 and T023 in Phase 6 are parallel

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: User Story 1 (T007–T013)
4. **STOP and VALIDATE**: `make test && make integration` — US1 independently functional (article 1 snapshot passes)
5. Ship if ready

### Incremental Delivery

1. Phase 1 + Phase 2 → extractor registered, routing works (`make test` green)
2. Phase 3 → basic extraction works, article 1 extractable (MVP)
3. Phase 4 → code block handling added, all 3 reference articles extractable
4. Phase 5 → error cases verified (`UnsupportedContentTypeError`, `EmptyContentError`)
5. Phase 6 → clean mypy + lint pass

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks
- [Story] label maps task to specific user story for traceability
- Snapshots are first-30-line verbatim prefixes — subset-match assertions (`expected in result`)
- Snapshot generation (T012, T017) requires a live network connection
- `class_="codeMirror-wrapper"` in BS4 matches elements with that class among multiple classes (e.g., `codeMirror-wrapper newest`) — no special handling needed
- Language normalisation: "plain text" → `""` (bare backticks); all other labels lowercased and used as fence info string
- `wordpress.com` unsupported-domain fixture in `test_router.py` requires no update
- Run `make format` before `make lint` to avoid formatting-only lint failures
