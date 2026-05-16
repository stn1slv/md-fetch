---
description: "Task list for mdfetch-cli implementation"
---

# Tasks: mdfetch-cli

**Input**: Design documents from `/specs/008-mdfetch-cli/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/cli.md

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Phase 1: Setup

**Purpose**: Verify baseline and create file stubs.

- [ ] T001 Run `make test` and confirm all existing unit tests pass (green baseline)
- [ ] T002 Update `pyproject.toml` to add `click` (version >= 8.1) to dependencies and define `[project.scripts]` for `md-fetch = "mdfetch.cli:main"`
- [ ] T003 Run `make setup` to sync new dependencies
- [ ] T004 Create `src/mdfetch/cli.py` with module docstring, `from __future__ import annotations`, and required imports (`click`, `extract` from `mdfetch`, and `MdfetchError`)
- [ ] T005 [P] Create `tests/integration/test_cli_integration.py` with module docstring and required imports (`subprocess`, `pytest`)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Set up the CLI entry point wrapper. All user stories depend on this.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [ ] T006 Implement the basic `@click.command()` shell in `src/mdfetch/cli.py` named `main`, accepting a `url` argument.

**Checkpoint**: `uv run md-fetch --help` executes without error and displays basic help text.

---

## Phase 3: User Story 1 - Fetch to Standard Output (Priority: P1) 🎯 MVP

**Goal**: Run `md-fetch <URL>` and see extracted Markdown content directly in the terminal.

**Independent Test**: Running `uv run md-fetch https://dev.to/stn1slv/from-a-developer-to-an-ai-agent-what-to-expect-in-a-new-environment-3if5` outputs Markdown content to stdout and exits with code 0.

### Implementation for User Story 1

- [ ] T007 [US1] Implement standard output fetching in `src/mdfetch/cli.py`:
  1. Call `extract(url)` inside the `main` function.
  2. Print the result using `click.echo()`.

### Tests for User Story 1

- [ ] T008 [US1] Add integration test for stdout printing in `tests/integration/test_cli_integration.py` using `subprocess.run(["uv", "run", "md-fetch", "<URL>"])`.

**Checkpoint**: User Story 1 is independently functional. `uv run md-fetch <URL>` works.

---

## Phase 4: User Story 2 - Fetch and Save to File (Priority: P2)

**Goal**: Specify an output file using an `--output` or `-o` flag to save the extracted Markdown without shell redirection.

**Independent Test**: Running `uv run md-fetch <URL> -o output.md` creates the file with content, leaves stdout empty, and exits with code 0.

### Implementation for User Story 2

- [ ] T009 [US2] Update `main` in `src/mdfetch/cli.py` to accept an `-o` / `--output` option using `@click.option()`.
- [ ] T010 [US2] Update `main` logic to write content to the specified file path if provided, rather than printing to stdout.

### Tests for User Story 2

- [ ] T011 [US2] Add integration test for file writing in `tests/integration/test_cli_integration.py` using a temporary directory fixture.

**Checkpoint**: User Stories 1 AND 2 both work independently.

---

## Phase 5: User Story 3 - Graceful Error Handling (Priority: P1)

**Goal**: See clear, human-readable error messages for unsupported URLs or timeouts instead of Python tracebacks.

**Independent Test**: Running `uv run md-fetch https://unsupported.com` prints an error message to stderr (no traceback) and exits with code 1.

### Implementation for User Story 3

- [ ] T012 [US3] Update `main` in `src/mdfetch/cli.py` to wrap the `extract()` call in a `try...except MdfetchError` block.
- [ ] T013 [US3] In the `except` block, print the error string to `stderr` in red using `click.secho()` and exit gracefully with `sys.exit(1)` or `raise click.Abort()`.

### Tests for User Story 3

- [ ] T014 [US3] Add integration test for unsupported URL in `tests/integration/test_cli_integration.py`, asserting stderr output and exit code 1.
- [ ] T014b [US3] Add mock test for network timeout (`FetchError`) in `tests/integration/test_cli_integration.py`, asserting stderr output and exit code 1.

**Checkpoint**: All user stories independently functional; graceful error handling verified.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final quality gate across all new files.

- [ ] T015 [P] Run `uv run mypy src/mdfetch/cli.py` and fix any type errors
- [ ] T016 [P] Run `make lint` and fix any ruff violations in `src/mdfetch/cli.py` and `tests/integration/test_cli_integration.py`
- [ ] T017 Run `make format` to ensure consistent code styling
- [ ] T018 Run `make test` and confirm all existing unit tests still pass
- [ ] T018b Run `make integration` and confirm the new CLI integration tests pass alongside the others
- [ ] T019 Update `README.md` to document the new `md-fetch` CLI command usage (stdout and file output).

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User Story 1 (P1) must be completed first to establish base functionality.
  - User Story 2 (P2) and User Story 3 (P1) can proceed in any order after US1.
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### Parallel Opportunities

- File stubs in Setup (Phase 1) can run in parallel.
- MyPy and Lint checks in Polish (Final Phase) can run in parallel.

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: User Story 1 (stdout fetching)
4. **STOP and VALIDATE**: Test basic CLI execution.

### Incremental Delivery

1. Phase 1 + Phase 2 → CLI command registered and responds to `--help`.
2. Phase 3 → Base fetching works (MVP).
3. Phase 4 → File output feature verified.
4. Phase 5 → Error cases are handled gracefully.
5. Phase 6 → Code is clean, typed, and documented.
