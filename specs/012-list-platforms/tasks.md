---
description: "Task list for List Supported Platforms feature"
---

# Tasks: List Supported Platforms

**Input**: Design documents from `/specs/012-list-platforms/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/cli.md

**Organization**: Tasks are grouped by user story so each story can be implemented and tested independently.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: Which user story this task belongs to (US1, US2)

## Path Conventions

- **CLI source**: `src/mdfetch/cli.py`
- **Router source**: `src/mdfetch/router.py`
- **Unit tests**: `tests/unit/test_cli.py`, `tests/unit/test_router.py`
- **No integration tests**: the operation is offline (research.md R4)

---

## Phase 1: Setup

**Purpose**: Confirm a green baseline before changing anything.

- [ ] T001 Run `make test` and confirm all existing unit tests pass (green baseline per dev guidelines)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Provide the subdomain-aware data source both user stories read from.

**⚠️ CRITICAL**: User-story work depends on this accessor.

- [ ] T002 Add `supported_platforms() -> list[tuple[str, bool]]` to `src/mdfetch/router.py`: return `sorted((domain, cls.MATCH_SUBDOMAINS) for domain, cls in _REGISTRY.items())`. Fully type-hinted, read-only, no side effects. Leave existing `supported_domains()` unchanged.
- [ ] T003 [P] Add a unit test in `tests/unit/test_router.py` asserting `supported_platforms()` returns sorted `(domain, bool)` tuples, covers every domain in `supported_domains()` (this registry-derived equality is what guarantees SC-003: a newly registered provider appears automatically with no edit to the list code), and marks `medium.com`/`substack.com` as subdomain-matching while `dev.to` is exact-match.

**Checkpoint**: `make test` + `make typecheck` pass; accessor verified.

---

## Phase 3: User Story 1 - Discover supported platforms (Priority: P1) 🎯 MVP

**Goal**: `md-fetch --list-platforms` prints every supported domain and exits 0 without a URL or network call.

**Independent Test**: Invoke `md-fetch --list-platforms` (via `CliRunner`); assert exit 0, output lists every supported domain, and `extract` is never called. Bare-domain rendering is sufficient at this stage.

### Implementation for User Story 1

- [ ] T004 [US1] In `src/mdfetch/cli.py`: add a `--list-platforms` flag (`is_flag=True`, `is_eager=True`, help text "List all supported platforms and exit" per FR-007); change the `url` argument to `required=False`. When `list_platforms` is set, print a `Supported platforms:` header followed by one indented bare domain per entry from `supported_platforms()` and `return` (exit 0) before any extraction. When `url is None` and the flag is absent, raise `click.UsageError("Missing argument 'URL'.")` (exit 2). Import `supported_platforms` from `mdfetch.router`.
- [ ] T005 [US1] Add unit tests in `tests/unit/test_cli.py`: (a) `--list-platforms` exits 0 and output contains every domain from `supported_domains()`; (b) patch `mdfetch.cli.extract` and assert it is NOT called when `--list-platforms` is used (FR-004); (c) invoking with no URL and no flag exits 2 with a usage/missing-argument message; (d) confirm an existing `md-fetch <URL>` happy-path test still passes (no regression); (e) invoking `--list-platforms` **together with** a URL (e.g. `--list-platforms https://dev.to/x`) exits 0, prints the list, and still does NOT call `extract` — the list takes precedence (FR-008 precedence path).

**Checkpoint**: `make test` passes; US1 is independently demonstrable.

---

## Phase 4: User Story 2 - Subdomain support indication (Priority: P2)

**Goal**: Multi-tenant platforms are visibly distinguished from exact-match platforms in the list output.

**Independent Test**: Invoke `md-fetch --list-platforms`; assert subdomain-matching platforms render `<domain> (and *.<domain>)` and exact-match platforms render the bare domain.

### Implementation for User Story 2

- [ ] T006 [US2] In `src/mdfetch/cli.py`, enhance the list-rendering loop so each entry from `supported_platforms()` renders `f"{domain} (and *.{domain})"` when its `matches_subdomains` flag is `True`, and the bare `domain` otherwise (FR-006).
- [ ] T007 [US2] Add a unit test in `tests/unit/test_cli.py` asserting `--list-platforms` output contains `*.medium.com` (subdomain-annotated) and that an exact-match domain such as `dev.to` appears without a `*.` wildcard.

**Checkpoint**: `make test` passes; output distinguishes multi-tenant vs exact-match (SC-004).

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Version, docs, and full verification per project conventions.

- [ ] T008 Bump `version` in `pyproject.toml` from `0.7.1` to `0.8.0` (minor — user-facing feature; gates PyPI release + Homebrew auto-update).
- [ ] T009 [P] Update `README.md`: document the `--list-platforms` flag with a usage example (per CLAUDE.md README-sync rule).
- [ ] T010 Run `make lint`, `make typecheck`, and `make test`; confirm all pass with zero errors before completion.

---

## Dependencies & Execution Order

```
T001 (baseline)
  └─> T002 ─> T003            (Foundational accessor + test)
        └─> T004 ─> T005      (US1: flag + list, MVP)
              └─> T006 ─> T007 (US2: subdomain annotation, builds on US1 rendering)
                    └─> T008, T009, T010 (Polish)
```

- **US1 (P1)** is the MVP: completing T001–T005 delivers a working `--list-platforms`.
- **US2 (P2)** refines the same render loop (T004) — it depends on US1 and is not parallel with it.
- Cross-file parallelism is limited (one CLI file, one router file); `[P]` tasks (T003, T009) touch independent files.

## Parallel Execution Example

- After T002 lands, T003 (router test) can be written in parallel with starting T004 (CLI flag), since they touch different files.
- T009 (README) can proceed in parallel with T010's lint/typecheck once code is final.

## Implementation Strategy

1. **MVP**: T001 → T005. Ship the list operation with bare domains.
2. **Increment**: T006 → T007. Add subdomain annotations.
3. **Release-ready**: T008 → T010. Version bump, README, full green verification.

## Independent Test Criteria

- **US1**: `md-fetch --list-platforms` exits 0, lists all domains, makes no network call.
- **US2**: subdomain platforms annotated `(and *.x)`; exact-match platforms plain.
