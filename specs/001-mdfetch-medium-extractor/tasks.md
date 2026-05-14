# Tasks: mdfetch — Medium Extractor (Initial Release)

**Input**: Design documents from `/specs/001-mdfetch-medium-extractor/`

**Prerequisites**: plan.md ✅ | spec.md ✅ | research.md ✅ | data-model.md ✅ | contracts/api.md ✅

**Tests**: Integration tests are REQUIRED by the project constitution (FR-010) and are included in all user story phases.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: Can run in parallel (different files, no dependencies on concurrent tasks)
- **[Story]**: User story this task belongs to ([US1], [US2], [US3])

---

## Phase 1: Setup

**Purpose**: Project scaffolding — directory layout, packaging configuration, development tooling.

- [x] T001 Create project directory structure: `src/mdfetch/`, `src/mdfetch/providers/`, `tests/unit/`, `tests/integration/`
- [x] T002 Create `pyproject.toml` with hatchling build backend, Python ≥3.12 constraint, and runtime dependencies (`httpx≥0.27`, `beautifulsoup4≥4.12`, `lxml≥5.0`, `markdownify≥0.13`) plus dev extras (`pytest≥8.0`, `ruff`); add `[tool.ruff]` section for lint/format configuration
- [x] T003 [P] Create `Makefile` with targets: `setup` (`uv sync`), `test` (`uv run pytest tests/unit/`), `lint` (`uv run ruff check src/ tests/`), `format` (`uv run ruff format src/ tests/`), `build` (`uv build`), `clean` (remove `dist/`, `__pycache__`); all targets that invoke Python tools MUST call them via `uv run <tool>`
- [x] T004 [P] Add pytest configuration to `pyproject.toml`: set `testpaths = ["tests"]`, register custom `integration` marker to separate unit from network-dependent tests; create `tests/conftest.py` with marker declaration

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core abstractions shared by all user stories. No user story work can begin until this phase is complete.

**⚠️ CRITICAL**: Exceptions, the base class, and the router skeleton must exist before any provider can be implemented.

- [x] T005 Implement `MdfetchError` exception hierarchy in `src/mdfetch/exceptions.py`: define `MdfetchError` (base, with `message: str` and `url: str | None`), `InvalidURLError`, `UnsupportedPlatformError`, `UnsupportedContentTypeError`, `FetchError`, `HTTPStatusError` (with `status_code: int`), `EmptyContentError` — all with strict type hints
- [x] T006 Implement `BaseExtractor` ABC in `src/mdfetch/base.py`: class-level `DOMAINS: frozenset[str]`; concrete `fetch_html(self, url: str) -> str` using `httpx.Client(timeout=30.0)` with default User-Agent, raising `FetchError` / `HTTPStatusError` on failure; abstract `clean_html` and `convert_to_markdown` with type-hinted signatures; concrete `extract(self, url: str) -> str` orchestrating all three steps
- [x] T007 [P] Implement router skeleton in `src/mdfetch/router.py`: `_REGISTRY: dict[str, type[BaseExtractor]] = {}`; `register(provider_cls)` function; `route(url: str) -> BaseExtractor` function that validates URL syntax (raising `InvalidURLError`), extracts `netloc`, looks up provider (raising `UnsupportedPlatformError` if missing), and returns a provider instance
- [x] T008 [P] Create `src/mdfetch/providers/__init__.py` (empty package marker)

**Checkpoint**: Foundation ready — all three user story phases can now begin.

---

## Phase 3: User Story 1 — Extract a Medium Article to Markdown (Priority: P1) 🎯 MVP

**Goal**: A developer calls `extract(url)` with a valid Medium article URL and receives a clean Markdown string.

**Independent Test**: Call `extract("https://medium.com/...")` with a known public article; assert output is non-empty, contains no HTML tags, and includes at least one Markdown heading.

### Tests for User Story 1

> Write these tests FIRST and confirm they fail (red) before implementing.

- [x] T009 [P] [US1] Write unit tests for `MediumExtractor` happy path in `tests/unit/test_medium_extractor.py`: use an HTML fixture with `<article>` body containing headings, lists, and a code block; assert `clean_html` returns soup with noise removed; assert `convert_to_markdown` output contains `#`, ` ``` `, and `-` markers; assert no raw HTML tags remain
- [x] T010 [P] [US1] Write integration test skeleton in `tests/integration/test_medium_integration.py`: define `MEDIUM_TEST_URLS` list (3 real public Medium article URLs); write `test_extract_returns_markdown` asserting: non-empty string, no `<tag>` patterns (regex), at least one `# ` heading, length > 200 characters; mark with `@pytest.mark.integration`

### Implementation for User Story 1

- [x] T011 [US1] Implement `MediumExtractor.clean_html()` in `src/mdfetch/providers/medium.py`: `soup.find("article")` to locate body (raise `UnsupportedContentTypeError` if `None`); remove `<nav>`, `<button>` elements with `aria-label` containing `"clap"` or `"applaud"`, `<div data-testid="post-sidebar">`, social share `<div>`/`<button>` elements (selector: `data-testid` containing `"share"`), author biography `<section>` after article body, response/comment prompts (`data-testid` matching `"post-footer"`); return cleaned soup
- [x] T012 [US1] Implement `MediumExtractor.convert_to_markdown()` in `src/mdfetch/providers/medium.py`: call `markdownify(str(soup), heading_style="ATX", strip=["script", "style"])`; strip leading/trailing whitespace and collapse runs of 3+ blank lines to 2; raise `EmptyContentError` if result is empty after stripping; return final string
- [x] T013 [US1] Register `MediumExtractor` in `src/mdfetch/router.py`: add `"medium.com"` and `"www.medium.com"` to `_REGISTRY`; ensure `username.medium.com` subdomains match by checking `netloc.endswith(".medium.com") or netloc == "medium.com"`
- [x] T014 [US1] Implement `extract()` public function and re-export all exception classes in `src/mdfetch/__init__.py`: `extract(url: str) -> str` delegates to `route(url).extract(url)`; `__all__` includes `extract`, `MdfetchError`, `InvalidURLError`, `UnsupportedPlatformError`, `UnsupportedContentTypeError`, `FetchError`, `HTTPStatusError`, `EmptyContentError`
- [x] T015 [US1] Run `pytest -m integration` against the 3 curated Medium article URLs defined in T010 and confirm all assertions pass (green)

**Checkpoint**: User Story 1 fully functional — `extract()` works end-to-end on real Medium articles.

---

## Phase 4: User Story 2 — Receive Meaningful Errors for Unsupported or Invalid URLs (Priority: P2)

**Goal**: A developer passing a bad URL, unsupported domain, or non-article Medium URL receives a typed, descriptive exception — not a crash or silent failure.

**Independent Test**: Call `extract()` with each error scenario (invalid URL, non-Medium domain, Medium profile URL, HTTP 404 URL) and assert the correct exception type is raised with a non-empty `message`.

### Tests for User Story 2

> Write these tests FIRST and confirm they fail (red) before implementing the missing pieces.

- [x] T016 [P] [US2] Write unit tests for URL validation errors in `tests/unit/test_router.py`: assert `route("not-a-url")` raises `InvalidURLError`; assert `route("ftp://medium.com/article")` raises `InvalidURLError` (bad scheme); assert `route("https://dev.to/post")` raises `UnsupportedPlatformError`
- [x] T017 [P] [US2] Write unit tests for `UnsupportedContentTypeError` in `tests/unit/test_medium_extractor.py`: provide HTML fixture with no `<article>` element (e.g., a tag page); assert `MediumExtractor().clean_html(soup)` raises `UnsupportedContentTypeError`
- [x] T018 [P] [US2] Write unit tests for HTTP error propagation in `tests/unit/test_medium_extractor.py`: mock `httpx.Client.get` to return HTTP 404 and assert `FetchError` (or `HTTPStatusError` with `status_code=404`) is raised; mock a connection timeout and assert `FetchError` is raised

### Implementation for User Story 2

- [x] T019 [US2] Harden URL validation in `src/mdfetch/router.py`: use `urllib.parse.urlparse` to validate scheme is `http` or `https` and `netloc` is non-empty; raise `InvalidURLError` with message including the offending URL for all invalid cases
- [x] T020 [US2] Verify `UnsupportedContentTypeError` path in `src/mdfetch/providers/medium.py`: confirm the `soup.find("article") is None` guard (from T011) raises `UnsupportedContentTypeError` with message `"URL is not an article page"`; verify `EmptyContentError` path in `convert_to_markdown` (from T012) includes the URL in its message
- [x] T021 [US2] Run `pytest tests/unit/` and confirm all error scenario tests pass (green)

**Checkpoint**: All typed exceptions work correctly — callers can distinguish every failure mode.

---

## Phase 5: User Story 3 — Install and Use via Standard Package Manager (Priority: P3)

**Goal**: `pip install mdfetch` works from PyPI; after installation, `from mdfetch import extract` succeeds and produces correct results.

**Independent Test**: Build the distribution wheel, install it in a fresh `venv`, import `extract`, run it against a real Medium URL, and confirm the result is valid Markdown.

### Implementation for User Story 3

- [x] T022 [US3] Finalize `pyproject.toml` metadata: add `description`, `readme = "README.md"`, `license`, `authors`, `keywords`, `classifiers` (Python version, license, topic), `[project.urls]` (Homepage, Source, Issues)
- [x] T023 [US3] Create `README.md` with install instructions (`pip install mdfetch`), a minimal usage example, and a link to the quickstart guide
- [x] T024 [P] [US3] Run `uv build` (or `make build`) and verify the wheel and sdist are produced without errors in `dist/`
- [x] T025 [P] [US3] Create a temporary environment with `uv venv`, install the built wheel via `uv pip install dist/mdfetch-*.whl`, and verify `from mdfetch import extract` succeeds and `extract("https://medium.com/...")` returns a non-empty Markdown string
- [x] T026 [US3] Walk through `quickstart.md` step-by-step in the clean `venv` and confirm all code examples execute without error

**Checkpoint**: Library installable and usable from PyPI distribution artifact.

---

## Polish & Cross-Cutting Concerns

**Purpose**: Final quality pass across all stories.

- [x] T027 [P] Write unit test in `tests/unit/test_silent.py` asserting FR-013: call `extract()` on a mock HTTP response and assert `sys.stdout` and `sys.stderr` are empty (use `capsys` pytest fixture); assert no Python `logging` handlers emit output during a successful extraction
- [x] T028 [P] Add one-line docstrings to all public classes and functions (`BaseExtractor`, `MediumExtractor`, `extract`, each exception class) in their respective files
- [x] T029 [P] Run `make lint` (`uv run ruff check src/ tests/`) and fix all reported issues
- [x] T030 [P] Run `make format` (`uv run ruff format src/ tests/`) and ensure consistent style
- [x] T031 Run full test suite: `make test` (unit) then `uv run pytest -m integration` — confirm zero failures
- [x] T032 [P] Verify `uv run mypy src/` reports no errors on the `src/mdfetch/` package

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies — start immediately
- **Phase 2 (Foundational)**: Depends on Phase 1 — blocks all user stories
- **Phase 3 (US1)**: Depends on Phase 2 — first user story, MVP scope
- **Phase 4 (US2)**: Depends on Phase 2 — can start in parallel with Phase 3 after T005–T008
- **Phase 5 (US3)**: Depends on Phases 3 and 4 being complete
- **Polish**: Depends on all user story phases being complete

### User Story Dependencies

- **US1 (P1)**: Depends on Foundational (Phase 2) only — no dependency on US2 or US3
- **US2 (P2)**: Depends on Foundational (Phase 2) — many error paths already implemented in US1; Phase 4 hardens and tests them
- **US3 (P3)**: Depends on US1 and US2 — validates the full distribution lifecycle

### Within Each Phase

- Unit tests → written first, confirmed red → implementation → confirmed green
- `clean_html` (T011) before `convert_to_markdown` (T012) within `MediumExtractor`
- Router registration (T013) before public API export (T014)
- Build (T024) before install verification (T025)

### Parallel Opportunities

- T003 ‖ T004 (Makefile and pytest config touch different files)
- T007 ‖ T008 (router skeleton and providers package are independent)
- T009 ‖ T010 (unit test fixtures and integration test skeleton are independent)
- T016 ‖ T017 ‖ T018 (three different unit test files)
- T024 ‖ T025 after T023 (build and install-verify are sequential but each parallelisable internally)
- T027 ‖ T028 ‖ T029 ‖ T031 (polish tasks touch different concerns)

---

## Parallel Execution Example: Phase 3 (US1)

```bash
# Step 1: Write tests in parallel (both can start after T008)
Task T009: tests/unit/test_medium_extractor.py — unit test fixtures
Task T010: tests/integration/test_medium_integration.py — real URL test skeleton

# Step 2: Implement provider (sequential within one file)
Task T011: MediumExtractor.clean_html()
Task T012: MediumExtractor.convert_to_markdown()

# Step 3: Wire up (sequential)
Task T013: Register provider in router.py
Task T014: Export from __init__.py

# Step 4: Validate
Task T015: pytest -m integration (green)
```

---

## Implementation Strategy

### MVP (User Story 1 Only — Phases 1–3)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Run `pytest -m integration` → all 3 real URL tests pass
5. Library is functional for core use case

### Full Release (All Stories)

1. MVP above
2. Phase 4 (US2): Harden and test all error paths
3. Phase 5 (US3): Build and verify PyPI distribution
4. Polish phase: lint, format, type check, full suite green

---

## Notes

- `[P]` tasks operate on different files and have no mutual dependency — safe to execute simultaneously
- Integration tests (`@pytest.mark.integration`) require network access — excluded from `make test` default run
- Commit after each checkpoint to preserve independent story milestones
- Do not skip the red→green cycle for test tasks — constitution mandates integration test coverage (FR-010)
