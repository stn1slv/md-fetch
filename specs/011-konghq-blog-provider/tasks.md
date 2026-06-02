# Tasks: Kong Blog Provider

**Input**: Design documents from `/specs/011-konghq-blog-provider/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Organization**: Tasks are grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2)
- Include exact file paths in descriptions

## Path Conventions

- **Provider source**: `src/mdfetch/providers/kong.py`
- **Unit tests**: `tests/unit/test_kong_extractor.py`
- **Integration tests**: `tests/integration/test_kong_integration.py`
- **Snapshots**: `tests/integration/snapshots/kong-<slug>.md`

> **Pattern note**: `KongExtractor` overrides only `clean_html`. `fetch_html`, `convert_to_markdown`,
> `extract`, and default markdownify kwargs are **inherited unchanged** from `BaseExtractor`
> (matches `DZoneExtractor`/`BoomiExtractor`). Do NOT re-implement or stub `convert_to_markdown`.
>
> **Fragility note (Next.js CSS modules)**: Kong's per-component class names are build hashes
> (e.g. `Section_section__Grz_Y`). Every selector MUST use a stable companion class only
> (`type-article`, `rich-text-block`, `component`, `video`, `more-on-this`, `section-header-block`,
> `intro`, `order-top`, `toc-wrap`, `agent`) or the date regex. NEVER pin to a hashed `__xxxxx`
> suffix. IMPLEMENTATION NOTE: the TOC sidebar is `.toc-wrap` — do NOT use `[class*=TableOfContents]`,
> because the `TableOfContents` component WRAPS the entire body. Also strip all `.agent` spans
> ("agent mode" affordances that inject literal Markdown `**`/`- `/`# ` duplicating styled content).

---

## Phase 1: Setup

**Purpose**: Verify baseline and create file stubs.

- [X] T001 Run `make test` and confirm all existing unit tests pass (green baseline)
- [X] T002 Create `src/mdfetch/providers/kong.py` with module docstring `"""Kong blog platform extractor."""`, `from __future__ import annotations`, and imports (`copy`, `re`, `BeautifulSoup`, `Tag`, `BaseExtractor`, `UnsupportedContentTypeError`, `register`)
- [X] T003 [P] Create `tests/unit/test_kong_extractor.py` with module docstring, imports, and sample HTML fixtures: an article fixture mirroring the real DOM — `<main class="... type-article">` containing a hero `<section>` (category link, a date `<div>` "May 26, 2026", a "5 min read" `<div>`, an `<h1>`, author `<div>`s) and a content `<section>` with several `.rich-text-block` blocks plus chrome blocks (`.component.video`, `.component.more-on-this`, a `[class*=TableOfContents]` block, a `.order-top` block, a trailing non-`intro` `.section-header-block`, and a kept `.section-header-block.intro` TL;DR)
- [X] T004 [P] Create `tests/integration/test_kong_integration.py` with module docstring, imports, `SNAPSHOTS_DIR`, and the `KONG_TEST_CASES` list (3 reference URLs → snapshot filenames)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Register the extractor so the router resolves `konghq.com` URLs. All user stories depend on this.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [X] T005 Add `KongExtractor(BaseExtractor)` to `src/mdfetch/providers/kong.py` with `@register` decorator, `DOMAINS = frozenset({"konghq.com"})`, `MATCH_SUBDOMAINS = False` (default), and a `clean_html` stub raising `NotImplementedError`
- [X] T006 Confirm the module self-registers: `mdfetch.router._autodiscover_providers()` `pkgutil`-imports every module in `mdfetch.providers` at import time, so creating `kong.py` with `@register` is sufficient — NO manual import in `src/mdfetch/providers/__init__.py` is needed (that file is intentionally empty)
- [X] T007 [P] Add routing unit test: verify `route("https://konghq.com/blog/product-releases/some-slug")` returns a `KongExtractor` instance, in `tests/unit/test_kong_extractor.py`

**Checkpoint**: `make test` passes (stub present); routing is verified.

---

## Phase 3: User Story 1 - Extract a Kong blog article as clean Markdown (Priority: P1) 🎯 MVP

**Goal**: Given a public Kong blog article URL, return Markdown that starts with `# <title>`, then the publication date, then the body (TL;DR lead, headings, paragraphs, lists, code, blockquotes, in-body images), with all site chrome removed and no author byline / read time.

**Independent Test**: Call `extract()` with a reference URL; assert the result starts with the title heading, has the publication date directly under it, contains body section headings/paragraphs and code, and contains none of the chrome (breadcrumbs, TOC, topics/authors, read time, "More on this topic", recommended-posts carousel, "See Kong in action" CTA, footer).

### Implementation for User Story 1

- [X] T008 [US1] Add a module-level date pattern to `src/mdfetch/providers/kong.py`: `_DATE_RE = re.compile(r"^[A-Z][a-z]+ \d{1,2}, \d{4}$")` (matches "May 26, 2026"); add a short comment that it is used to pick the hero publication-date `<div>` while skipping the "… min read" and category/author elements
- [X] T009 [US1] Implement `clean_html(self, soup: BeautifulSoup) -> Tag` in `src/mdfetch/providers/kong.py`:
  1. `main = soup.find("main")`; if not a `Tag` or `"type-article"` not in its class list → raise `UnsupportedContentTypeError("URL is not an article page — no article body element found")`
  2. `sections = main.find_all("section", recursive=False)`; choose `content` = the section with the most `.rich-text-block` descendants; if there is none or it has zero `.rich-text-block` → raise `UnsupportedContentTypeError`
  3. Decompose in-body chrome inside `content`: every `.component.video`, `.component.more-on-this`, `.toc-wrap` (NOT `[class*=TableOfContents]` — that wraps the whole body), `.order-top`, and every `.section-header-block` whose class list does NOT contain `intro`
  4. `hero = sections[0]`; `title_el = hero.find("h1")`; `date_el = next((d for d in hero.find_all("div") if _DATE_RE.match(d.get_text(strip=True))), None)`
  5. Build a new wrapper `div` (via `soup.new_tag("div")`): append `copy.copy(title_el)` if present; if `date_el` present, append a new `<p>` whose text is the date string; append `content`
  6. Decompose every `.agent` span in the wrapper ("agent mode" affordances that inject literal Markdown duplicating the styled content)
  7. Return the wrapper `Tag`

### Tests for User Story 1

- [X] T010 [P] [US1] Unit test in `tests/unit/test_kong_extractor.py`: `clean_html` on the article fixture returns a `Tag` whose first child is the `<h1>` title, whose second child is a `<p>` containing the publication date, and which no longer contains any `.component.video`, `.component.more-on-this`, `[class*=TableOfContents]`, `.order-top`, or trailing non-`intro` `.section-header-block`
- [X] T011 [P] [US1] Unit test in `tests/unit/test_kong_extractor.py`: the `.section-header-block.intro` (TL;DR) and `.rich-text-block` / `.component.image` / `.component.pull-quote` content blocks are PRESERVED in the returned `Tag`
- [X] T012 [P] [US1] Unit test in `tests/unit/test_kong_extractor.py`: end-to-end `extractor.convert_to_markdown(extractor.clean_html(soup))` (inherited convert) yields Markdown starting with `# <title>` followed by the date line, preserving a heading, list, and inline code, with no 3+ blank-line runs, and containing no author-name or "min read" text
- [X] T013 [US1] Generate the 3 snapshots from real network calls (first 30 lines, blank lines preserved) into `tests/integration/snapshots/`:
  - `kong-insomnia-12-6.md`
  - `kong-ai-gateway-vs-litellm.md`
  - `kong-gateway-3-14.md`
  - Command: `uv run python -c "from mdfetch import extract; c=extract('<url>'); open('tests/integration/snapshots/<name>.md','w',encoding='utf-8').write('\n'.join(c.split('\n')[:30]).rstrip())"`
- [X] T014 [US1] Add `@pytest.mark.integration` parametrized snapshot-containment test in `tests/integration/test_kong_integration.py` (`assert expected in result`) over `KONG_TEST_CASES`, with a regenerate-snapshot hint in the assertion message

**Checkpoint**: `make test` green; `make integration` passes for the 3 articles; User Story 1 is independently functional (MVP).

---

## Phase 4: User Story 2 - Reject non-article Kong URLs cleanly (Priority: P2)

**Goal**: Non-article Kong URLs (blog index, category listings, non-blog pages) raise `UnsupportedContentTypeError`; an article whose content section yields no text raises `EmptyContentError`.

**Independent Test**: `extract("https://konghq.com/blog")` and `extract("https://konghq.com/blog/product-releases")` both raise `UnsupportedContentTypeError`; a `main.type-article` whose content section has no extractable text raises `EmptyContentError`.

### Tests for User Story 2

- [X] T015 [P] [US2] Unit test in `tests/unit/test_kong_extractor.py`: HTML whose `<main>` lacks the `type-article` class (e.g. `<main class="Layout_main__x product-releases">` with no content) → `clean_html` raises `UnsupportedContentTypeError` (locks in the discriminator; mirrors the index and category-listing pages)
- [X] T016 [P] [US2] Unit test in `tests/unit/test_kong_extractor.py`: `main.type-article` present but with no `<section>` containing `.rich-text-block` → `clean_html` raises `UnsupportedContentTypeError`
- [X] T017 [P] [US2] Unit test in `tests/unit/test_kong_extractor.py`: `main.type-article` + a content section with a `.rich-text-block` that is empty/whitespace → `extract` path raises `EmptyContentError` (via inherited `convert_to_markdown`)
- [X] T018 [US2] Add `@pytest.mark.integration` test in `tests/integration/test_kong_integration.py`: `extract("https://konghq.com/blog", retries=1, retry_delay=0.0)` and `extract("https://konghq.com/blog/product-releases", retries=1, retry_delay=0.0)` each raise `UnsupportedContentTypeError`

**Checkpoint**: User Stories 1 AND 2 both verified independently.

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Final quality gate across all new files.

- [X] T019 [P] Run `uv run mypy src/` and fix any type errors in `src/mdfetch/providers/kong.py`
- [X] T020 [P] Run `make format` then `make lint`; fix any ruff violations in new files
- [X] T021 [P] Add a `Kong | konghq.com` row to the Supported platforms table in `README.md` (and a usage example line if appropriate)
- [X] T022 Bump `version` from `0.6.0` to `0.7.0` in `pyproject.toml` (new provider = minor bump, matching dev.to/Substack/Boomi precedent)
- [X] T023 Sync `CLAUDE.md` (inside the `<!-- SPECKIT -->` block): add `kong.py` to the project-structure tree, add Kong to the integration-test description, and add a gotcha documenting (a) `main.type-article` as the article discriminator and (b) the Next.js CSS-module hash fragility / stable-class-only rule
- [X] T024 Verify `tests/unit/test_router.py` unsupported-domain fixture still uses `wordpress.com` (NOT `konghq.com`); no change expected — confirm the router tests still pass
- [X] T025 Run `make test` and confirm all unit tests pass with no regressions
- [X] T026 Run `make integration` and confirm all Kong integration tests pass

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Setup — BLOCKS all user stories
- **User Stories (Phase 3–4)**: Depend on Foundational completion; US1 before US2 (US2 reuses US1's `clean_html`)
- **Polish (Phase 5)**: Depends on US1 (and US2 if shipping both)

### User Story Dependencies

- **US1 (P1)**: Starts after Foundational — primary implementation (`clean_html` + date handling)
- **US2 (P2)**: Depends on US1's `clean_html` (its `UnsupportedContentTypeError` branches); largely test-only

### Within Each User Story

- Implementation (`_DATE_RE` then `clean_html`) before tests
- Unit tests before integration tests
- Snapshot generation (T013) before the containment test (T014)

### Parallel Opportunities

- T003 / T004 (Setup, different files) can run in parallel
- T010 / T011 / T012 (US1 unit tests, same file — write together, run together)
- T015 / T016 / T017 (US2 unit tests) can be written in parallel with US1 tests once `clean_html` exists
- T019 / T020 / T021 (Polish, independent) can run in parallel

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Phase 1: Setup
2. Phase 2: Foundational (register + routing)
3. Phase 3: User Story 1 (`clean_html` + date + snapshots + integration)
4. **STOP and VALIDATE**: `make test && make integration` — US1 independently functional
5. Ship if ready

### Incremental Delivery

1. Phase 1 + Phase 2 → extractor registered, routing works
2. Phase 3 → extraction works (MVP)
3. Phase 4 → non-article / empty-body handling verified
4. Phase 5 → mypy + lint clean, README + version + CLAUDE.md updated, no regressions

---

## Notes

- `KongExtractor` overrides ONLY `clean_html`; everything else is inherited from `BaseExtractor`.
- `main.type-article` is the discriminator: present on articles, absent on the blog index and category listings (both also have 0 `.rich-text-block`) → clean `UnsupportedContentTypeError`.
- Selectors pin to stable companion classes only — NEVER hashed `__xxxxx` CSS-module suffixes.
- Publication date is kept under the title (clarification, Option B); author bylines and read time are dropped.
- Body images/pull-quotes flow through inherited conversion; no media-specific code. The `.component.video` placeholder has no usable URL and is decomposed, not linked.
- Snapshots must be generated from real network calls (first-30-line verbatim prefix, blank lines preserved) before the containment test can assert against them.
- Run `make format` after implementing, before `make lint`.
- Commit after each logical group; stop at any checkpoint to validate a story independently.
