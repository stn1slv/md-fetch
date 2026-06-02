# Tasks: Boomi Blog Provider

**Input**: Design documents from `/specs/010-boomi-blog-provider/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Organization**: Tasks are grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2)
- Include exact file paths in descriptions

## Path Conventions

- **Provider source**: `src/mdfetch/providers/boomi.py`
- **Unit tests**: `tests/unit/test_boomi_extractor.py`
- **Integration tests**: `tests/integration/test_boomi_integration.py`
- **Snapshots**: `tests/integration/snapshots/boomi-<slug>.md`

> **Pattern note**: `BoomiExtractor` overrides only `clean_html`. `fetch_html`, `convert_to_markdown`,
> `extract`, and default markdownify kwargs are **inherited unchanged** from `BaseExtractor`
> (matches `DZoneExtractor`). Do NOT re-implement or stub `convert_to_markdown`.

---

## Phase 1: Setup

**Purpose**: Verify baseline and create file stubs.

- [X] T001 Run `make test` and confirm all existing unit tests pass (green baseline)
- [X] T002 Create `src/mdfetch/providers/boomi.py` with module docstring `"""Boomi blog platform extractor."""`, `from __future__ import annotations`, and imports (`copy`, `BeautifulSoup`, `Tag`, `BaseExtractor`, `UnsupportedContentTypeError`, `register`)
- [X] T003 [P] Create `tests/unit/test_boomi_extractor.py` with module docstring, imports, and sample HTML fixtures (article with `div.post-content` > `section.wysiwyg-section` + `div.blog-nav`, plus an `<h1>` in a hero `section`)
- [X] T004 [P] Create `tests/integration/test_boomi_integration.py` with module docstring, imports, `SNAPSHOTS_DIR`, and the `BOOMI_TEST_CASES` list (3 reference URLs → snapshot filenames)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Register the extractor so the router resolves `boomi.com` URLs. All user stories depend on this.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [X] T005 Add `BoomiExtractor(BaseExtractor)` to `src/mdfetch/providers/boomi.py` with `@register` decorator, `DOMAINS = frozenset({"boomi.com"})`, `MATCH_SUBDOMAINS = False` (default), and a `clean_html` stub raising `NotImplementedError`
- [X] T006 Confirm the module self-registers: `mdfetch.router._autodiscover_providers()` `pkgutil`-imports every module in `mdfetch.providers` at import time, so creating `boomi.py` with `@register` is sufficient — NO manual import in `src/mdfetch/providers/__init__.py` is needed (that file is intentionally empty)
- [X] T007 [P] Add routing unit test: verify `route("https://boomi.com/blog/some-slug/")` returns a `BoomiExtractor` instance, in `tests/unit/test_boomi_extractor.py`

**Checkpoint**: `make test` passes (stub present); routing is verified.

---

## Phase 3: User Story 1 - Extract a Boomi blog article as clean Markdown (Priority: P1) 🎯 MVP

**Goal**: Given a public Boomi blog article URL, return Markdown that starts with `# <title>` followed by the body (headings, paragraphs, lists, blockquotes, in-body images), with all site chrome removed.

**Independent Test**: Call `extract()` with a reference URL; assert the result starts with the title heading and contains body section headings/paragraphs, and contains none of the chrome (top nav, "On this page", share buttons, prev/next links, footer).

### Implementation for User Story 1

- [X] T008 [US1] Implement `clean_html(self, soup: BeautifulSoup) -> Tag` in `src/mdfetch/providers/boomi.py`:
  1. `body = soup.find("div", class_="post-content")`; if not a `Tag` → raise `UnsupportedContentTypeError("URL is not an article page — no article body element found")`
  2. Decompose every `div.blog-nav` descendant of `body` (prev/next chrome)
  3. `title_el = soup.find("h1")`; if a `Tag`, `body.insert(0, copy.copy(title_el))`
  4. Return `body`

### Tests for User Story 1

- [X] T009 [P] [US1] Unit test in `tests/unit/test_boomi_extractor.py`: `clean_html` on the article fixture returns a `Tag` whose first child is the `<h1>` title and that no longer contains `div.blog-nav`
- [X] T010 [P] [US1] Unit test in `tests/unit/test_boomi_extractor.py`: end-to-end `extractor.convert_to_markdown(extractor.clean_html(soup))` (inherited convert) yields Markdown starting with `# <title>`, preserving a heading, list, blockquote, and an in-body image, with no 3+ blank-line runs
- [X] T011 [US1] Generate the 3 snapshots from real network calls (first 30 lines, blank lines preserved) into `tests/integration/snapshots/`:
  - `boomi-gartner-magic-quadrant-ipaas-2026.md`
  - `boomi-real-time-vs-batch-data-integration.md`
  - `boomi-data-consistency-saas-on-prem.md`
  - Command: `uv run python -c "from mdfetch import extract; c=extract('<url>'); open('tests/integration/snapshots/<name>.md','w',encoding='utf-8').write('\n'.join(c.split('\n')[:30]).rstrip())"`
- [X] T012 [US1] Add `@pytest.mark.integration` parametrized snapshot-containment test in `tests/integration/test_boomi_integration.py` (`assert expected in result`) over `BOOMI_TEST_CASES`, with a regenerate-snapshot hint in the assertion message

**Checkpoint**: `make test` green; `make integration` passes for the 3 articles; User Story 1 is independently functional (MVP).

---

## Phase 4: User Story 2 - Reject non-article Boomi URLs cleanly (Priority: P2)

**Goal**: Non-article Boomi URLs (blog index, non-blog pages) raise `UnsupportedContentTypeError`; an article body that yields no text raises `EmptyContentError`.

**Independent Test**: `extract("https://boomi.com/blog/")` raises `UnsupportedContentTypeError`; a `div.post-content` containing no text raises `EmptyContentError`.

### Tests for User Story 2

- [X] T013 [P] [US2] Unit test in `tests/unit/test_boomi_extractor.py`: HTML lacking `div.post-content` → `clean_html` raises `UnsupportedContentTypeError` (note: the `/blog/` index has a `wysiwyg-section` but no `post-content`, so include a fixture with `wysiwyg-section` only to lock in this discriminator)
- [X] T014 [P] [US2] Unit test in `tests/unit/test_boomi_extractor.py`: `div.post-content` present but empty → `extract` path raises `EmptyContentError` (via inherited `convert_to_markdown`)
- [X] T015 [US2] Add `@pytest.mark.integration` test in `tests/integration/test_boomi_integration.py`: `extract("https://boomi.com/blog/", retries=1, retry_delay=0.0)` raises `UnsupportedContentTypeError`

**Checkpoint**: User Stories 1 AND 2 both verified independently.

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Final quality gate across all new files.

- [X] T016 [P] Run `uv run mypy src/` and fix any type errors in `src/mdfetch/providers/boomi.py`
- [X] T017 [P] Run `make format` then `make lint`; fix any ruff violations in new files
- [X] T018 [P] Add a `Boomi | boomi.com` row to the Supported platforms table in `README.md` (and a usage example line if appropriate)
- [X] T019 Verify `tests/unit/test_router.py` unsupported-domain fixture still uses `wordpress.com` (NOT `boomi.com`); no change expected — confirm the router tests still pass
- [X] T020 Run `make test` and confirm all unit tests pass with no regressions
- [X] T021 Run `make integration` and confirm all Boomi integration tests pass

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Setup — BLOCKS all user stories
- **User Stories (Phase 3–4)**: Depend on Foundational completion; US1 before US2 (US2 reuses US1's `clean_html`)
- **Polish (Phase 5)**: Depends on US1 (and US2 if shipping both)

### User Story Dependencies

- **US1 (P1)**: Starts after Foundational — primary implementation (`clean_html`)
- **US2 (P2)**: Depends on US1's `clean_html` (its `UnsupportedContentTypeError` branch); largely test-only

### Within Each User Story

- Implementation (`clean_html`) before tests
- Unit tests before integration tests
- Snapshot generation (T011) before the containment test (T012)

### Parallel Opportunities

- T003 / T004 (Setup, different files) can run in parallel
- T009 / T010 (US1 unit tests, same file — write together, run together)
- T013 / T014 (US2 unit tests) can be written in parallel with US1 tests once `clean_html` exists
- T016 / T017 / T018 (Polish, independent) can run in parallel

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Phase 1: Setup
2. Phase 2: Foundational (register + routing)
3. Phase 3: User Story 1 (`clean_html` + snapshots + integration)
4. **STOP and VALIDATE**: `make test && make integration` — US1 independently functional
5. Ship if ready

### Incremental Delivery

1. Phase 1 + Phase 2 → extractor registered, routing works
2. Phase 3 → extraction works (MVP)
3. Phase 4 → non-article / empty-body handling verified
4. Phase 5 → mypy + lint clean, README updated, no regressions

---

## Notes

- `BoomiExtractor` overrides ONLY `clean_html`; everything else is inherited from `BaseExtractor`.
- `div.post-content` is the discriminator: present on articles, absent on the `/blog/` index → clean `UnsupportedContentTypeError`.
- Body images flow through inherited conversion (Option A); no image-specific code. Hero image is outside the body and excluded automatically.
- Snapshots must be generated from real network calls (first-30-line verbatim prefix, blank lines preserved) before the containment test can assert against them.
- Run `make format` after implementing, before `make lint`.
- Commit after each logical group; stop at any checkpoint to validate a story independently.
