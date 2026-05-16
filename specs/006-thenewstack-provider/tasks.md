---

description: "Task list for The New Stack Platform Provider"
---

# Tasks: The New Stack Platform Provider

**Input**: Design documents from `specs/006-thenewstack-provider/`

**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅, quickstart.md ✅

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2)

## Path Conventions

- **Provider source**: `src/mdfetch/providers/thenewstack.py`
- **Unit tests**: `tests/unit/test_thenewstack_extractor.py`
- **Integration tests**: `tests/integration/test_thenewstack_integration.py`
- **Snapshots**: `tests/integration/snapshots/thenewstack-*.md`

---

## Phase 1: Setup

**Purpose**: Verify baseline and create file stubs.

- [X] T001 Run `make test` and confirm all existing unit tests pass (green baseline before any changes)
- [X] T002 Create `src/mdfetch/providers/thenewstack.py` with module docstring `"""The New Stack platform extractor."""`, `from __future__ import annotations`, and required imports (`copy`, `re`, `BeautifulSoup`, `Tag`, `markdownify`, `BaseExtractor`, `EmptyContentError`, `UnsupportedContentTypeError`, `register`)
- [X] T003 [P] Create `tests/unit/test_thenewstack_extractor.py` with module docstring, imports (`pytest`, `BeautifulSoup`, `TheNewStackExtractor`, `EmptyContentError`, `UnsupportedContentTypeError`, `route`), and empty `extractor` fixture returning `TheNewStackExtractor()`
- [X] T004 [P] Create `tests/integration/test_thenewstack_integration.py` with module docstring, imports (`Path`, `pytest`, `extract`, `UnsupportedContentTypeError`), `SNAPSHOTS_DIR` constant, and empty `THENEWSTACK_TEST_CASES` list

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Register the extractor so the router resolves `thenewstack.io` URLs. All user stories depend on this.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [X] T005 Add `TheNewStackExtractor(BaseExtractor)` class in `src/mdfetch/providers/thenewstack.py` with `@register` decorator, `DOMAINS: frozenset[str] = frozenset({"thenewstack.io"})`, and stub bodies for `clean_html` and `convert_to_markdown` (raise `NotImplementedError`)
- [X] T006 [P] Add routing test `test_routes_thenewstack_io` to `tests/unit/test_router.py`: assert `route("https://thenewstack.io/some-article/")` returns a `TheNewStackExtractor` instance

**Checkpoint**: `make test` passes (stubs present, routing verified). Note: `wordpress.com` unsupported-domain fixture requires no change (already correct per research.md).

---

## Phase 3: User Story 1 - Extract a Public Article (Priority: P1) 🎯 MVP

**Goal**: A thenewstack.io article URL returns clean Markdown with title, optional deck, and full body — with sponsored content stripped and iframes converted to anchor links.

**Independent Test**: Pass `https://thenewstack.io/using-a-developer-portal-for-api-management/` to `extract()` and verify the result starts with `# Using a Developer Portal for API Management`, contains a deck paragraph, has body prose, and contains no `div.tns-sponsor-note` text.

### HTML Fixtures

- [X] T007 [P] [US1] Add inline HTML fixtures to `tests/unit/test_thenewstack_extractor.py`:
  - `ARTICLE_HTML` — includes `div#tns-post-headline` with `h1.title` + `div.post-excerpt`, and `div#tns-post-body-content` with paragraphs, a link, an image, and a `div.tns-sponsor-note` block
  - `ARTICLE_NO_DECK_HTML` — same as above but without `div.post-excerpt` (no deck)
  - `SPONSOR_DISCLOSURE_HTML` — body contains `div.sponsored-post-disclosure`, `div.tns-sponsored-post-disclosure`, `div.sponsor-disclosure` variants
  - `IFRAME_EMBED_HTML` — body contains an `<iframe src="https://www.youtube.com/embed/abc">` between paragraphs
  - `EMPTY_BODY_HTML` — `div#tns-post-body-content` present but whitespace-only
  - `NO_ARTICLE_HTML` — page without `div#tns-post-body-content` (homepage-like)

### Implementation for User Story 1

- [X] T008 [US1] Implement `clean_html(self, soup: BeautifulSoup) -> Tag` in `src/mdfetch/providers/thenewstack.py`:
  1. `body = soup.find("div", id="tns-post-body-content")` → raise `UnsupportedContentTypeError("URL is not an article page — no article body element found")` if not a `Tag` (FR-006)
  2. Decompose sponsored disclosures from body (FR-003): `div.sponsored-post-disclosure`, `div.tns-sponsored-post-disclosure`, `div.sponsor-disclosure`, `div.tns-sponsor-note`
  3. Convert iframes to anchor links (FR-009): for each `iframe`, replace with `<a href=src>src</a>` or decompose if no `src`
  4. `headline = soup.find("div", id="tns-post-headline")`; if present:
     - Find `div.post-excerpt`; if present, create `<p>` with deck text and insert at `body` position 0 (FR-004 deck clarification)
     - Find `h1.title`; if present, `copy.copy()` and insert at `body` position 0 (FR-004 title)
  5. Return `body`
- [X] T009 [US1] Implement `convert_to_markdown(self, tag: Tag) -> str` in `src/mdfetch/providers/thenewstack.py`:
  1. `md = markdownify(str(tag), heading_style="ATX", code_language="", strip=["script", "style"])`
  2. `md = md.strip()`
  3. `md = re.sub(r"\n{3,}", "\n\n", md)` (FR-008)
  4. Raise `EmptyContentError("Article body contained no extractable text content")` if `not md` (FR-007)
  5. Return `md`

### Tests for User Story 1

- [X] T010 [P] [US1] Add `clean_html` happy-path unit tests in `tests/unit/test_thenewstack_extractor.py`:
  - `test_clean_html_returns_body_content_div` — result is a `Tag` with `id="tns-post-body-content"`
  - `test_clean_html_prepends_title` — first element child is `h1` with title text
  - `test_clean_html_prepends_deck_as_paragraph` — second element child is `p` with deck text
  - `test_clean_html_no_deck_when_absent` — using `ARTICLE_NO_DECK_HTML`, first element child is `h1` (no extra `p` before body)
  - `test_clean_html_strips_sponsor_note` — `result.find("div", class_="tns-sponsor-note")` is `None`
  - `test_clean_html_strips_all_disclosure_variants` — using `SPONSOR_DISCLOSURE_HTML`, all three disclosure div variants absent from result
  - `test_clean_html_converts_iframe_to_anchor` — using `IFRAME_EMBED_HTML`, `result.find("iframe")` is `None`; anchor `href="https://www.youtube.com/embed/abc"` present
- [X] T011 [P] [US1] Add `convert_to_markdown` unit tests in `tests/unit/test_thenewstack_extractor.py`:
  - `test_convert_to_markdown_starts_with_title` — result starts with `# ` followed by title text
  - `test_convert_to_markdown_deck_paragraph_after_title` — deck text appears in output after title heading
  - `test_convert_to_markdown_no_triple_blank_lines` — `"\n\n\n"` not in result
  - `test_convert_to_markdown_renders_images` — `![alt](url)` syntax present
  - `test_convert_to_markdown_preserves_links` — `[link text](url)` syntax present

### Integration for User Story 1

- [X] T012 [US1] Generate snapshot files for all 5 reference articles using real network calls (run from repo root):
  ```
  uv run python -c "
  from mdfetch import extract
  articles = [
    ('https://thenewstack.io/using-a-developer-portal-for-api-management/', 'thenewstack-developer-portal-api.md'),
    ('https://thenewstack.io/api-management-for-asynchronous-apis/', 'thenewstack-async-apis.md'),
    ('https://thenewstack.io/json-schema-ai-reliability/', 'thenewstack-json-schema-ai.md'),
    ('https://thenewstack.io/mcp-api-governance-readiness/', 'thenewstack-mcp-api-governance.md'),
    ('https://thenewstack.io/api-mcp-agent-integration/', 'thenewstack-api-mcp-agent.md'),
  ]
  for url, name in articles:
      content = extract(url)
      lines = [l for l in content.split('\n') if l.strip()]
      open(f'tests/integration/snapshots/{name}', 'w').write('\n'.join(lines[:25]))
  "
  ```
- [X] T013 [US1] Add integration tests in `tests/integration/test_thenewstack_integration.py`:
  - Populate `THENEWSTACK_TEST_CASES` with all 5 (url, snapshot_filename) pairs
  - Add `@pytest.mark.integration @pytest.mark.parametrize` test `test_extract_contains_snapshot` with snapshot containment assertion (matching pattern from `test_substack_integration.py`)
  - Run `make integration` and confirm all 5 pass

**Checkpoint**: `make test` green; `make integration` passes for all 5 articles; US1 independently functional.

---

## Phase 4: User Story 2 - Reject Non-Article Pages (Priority: P2)

**Goal**: Non-article thenewstack.io URLs (homepage, category pages) raise typed exceptions rather than returning empty/garbage Markdown.

**Independent Test**: Pass `https://thenewstack.io/` to `extract()` and verify `UnsupportedContentTypeError` is raised. Pass `EMPTY_BODY_HTML` fixture to `convert_to_markdown()` and verify `EmptyContentError` is raised.

### Tests for User Story 2

- [X] T014 [P] [US2] Add unit test `test_clean_html_raises_on_no_article_body` in `tests/unit/test_thenewstack_extractor.py`: parse `NO_ARTICLE_HTML`, assert `clean_html(soup)` raises `UnsupportedContentTypeError`
- [X] T015 [P] [US2] Add unit test `test_convert_to_markdown_raises_on_empty_body` in `tests/unit/test_thenewstack_extractor.py`: parse `EMPTY_BODY_HTML`, call `clean_html(soup)` to get the body tag, assert `convert_to_markdown(tag)` raises `EmptyContentError`
- [X] T016 [US2] Add integration test `test_homepage_raises_unsupported_content_type_error` in `tests/integration/test_thenewstack_integration.py`: assert `extract("https://thenewstack.io/", retries=1, retry_delay=0.0)` raises `UnsupportedContentTypeError`

**Checkpoint**: All US1 and US2 tests pass. All error scenarios verified.

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Final quality gate across all new and modified files.

- [X] T017 [P] Run `uv run mypy src/mdfetch/providers/thenewstack.py` and fix any type errors (ensure return types, `isinstance` guards, and `copy.copy` import are all correct)
- [X] T018 [P] Run `make format` then `make lint` and fix any ruff violations in `src/mdfetch/providers/thenewstack.py`, `tests/unit/test_thenewstack_extractor.py`, `tests/integration/test_thenewstack_integration.py`
- [X] T019 Run `make test` and confirm all unit tests pass with no regressions in existing providers
- [X] T020 Run `make integration` and confirm all integration tests pass (5 thenewstack articles + homepage error case)

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
- **US1 (Phase 3)**: Depends on Phase 2 — primary implementation; T007 (fixtures) can start in parallel with T008–T009 (implementation)
- **US2 (Phase 4)**: Depends on Phase 2; T014–T015 (unit tests) can run in parallel with Phase 3 once fixtures exist
- **Polish (Phase 5)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Phase 2 — full implementation + integration
- **User Story 2 (P2)**: Depends on US1 implementation (error paths tested after core extraction exists); T014–T015 use fixtures created in T007

### Within Phase 3

- T007 (fixtures) → T008 (clean_html) → T009 (convert_to_markdown): sequential
- T010 (clean_html unit tests) and T011 (convert_to_markdown unit tests): parallel, both depend on T008–T009
- T012 (snapshot generation) → T013 (integration tests): sequential, both depend on T009

### Parallel Opportunities

- T003 and T004 in Phase 1 are parallel (different files)
- T006 in Phase 2 is parallel with T005 (different files)
- T007 in Phase 3 is parallel with T008 once started (fixtures in test file, implementation in provider file)
- T010 and T011 in Phase 3 are parallel
- T014 and T015 in Phase 4 are parallel

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: User Story 1 (T007–T013)
4. **STOP and VALIDATE**: `make test && make integration` — US1 independently functional
5. Ship if ready

### Incremental Delivery

1. Phase 1 + Phase 2 → extractor registered, routing works (`make test` green)
2. Phase 3 → extraction works, all 5 articles extractable (MVP)
3. Phase 4 → error cases verified (`UnsupportedContentTypeError`, `EmptyContentError`)
4. Phase 5 → clean mypy + lint pass

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks
- [Story] label maps task to specific user story for traceability
- Snapshots are subset-match assertions (first 25 non-empty lines) — not exact full-content match
- Snapshot generation (T012) requires a live network connection
- VoxPop polls (`div.tns-voxpop-screen`) are page-level modals — confirmed NOT inside `div#tns-post-body-content` across all 5 reference articles; no stripping needed
- `wordpress.com` unsupported-domain fixture in `test_router.py` requires no update (already correct)
- Run `make format` before `make lint` to avoid formatting-only lint failures
