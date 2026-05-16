---

description: "Task list for Homebrew Tap Formula feature"
---

# Tasks: Homebrew Tap Formula

**Input**: Design documents from `specs/009-homebrew-tap-formula/`

**Prerequisites**: plan.md ✅ | spec.md ✅ | research.md ✅ | data-model.md ✅ | contracts/ ✅ | quickstart.md ✅

**Organization**: Tasks are grouped by user story. This feature spans two repositories:
- **homebrew-tap** repo: `/Users/Stanislav_Deviatov/src/github/homebrew-tap/`
- **md-fetch** repo: `/Users/Stanislav_Deviatov/src/github/md-fetch/`

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)

## Path Conventions

- **Formula**: `homebrew-tap/Formula/md-fetch.rb`
- **Tap README**: `homebrew-tap/README.md`
- **CI workflow**: `md-fetch/.github/workflows/publish.yml`
- **md-fetch README**: `md-fetch/README.md`
- **Formula skeleton**: `md-fetch/specs/009-homebrew-tap-formula/contracts/formula.md`
- **CI job skeleton**: `md-fetch/specs/009-homebrew-tap-formula/contracts/tap-update-job.md`

---

## Phase 1: Setup

**Purpose**: Confirm baseline and fulfil the one manual prerequisite.

- [x] T001 Run `make test` in `/Users/Stanislav_Deviatov/src/github/md-fetch` and confirm all existing unit tests pass (green baseline before any changes)
- [ ] T002 Create a GitHub PAT with `contents:write` scope on `stn1slv/homebrew-tap`, then add it as secret `TAP_GITHUB_TOKEN` in `stn1slv/md-fetch` → Settings → Secrets and variables → Actions *(manual step — required before Phase 4 CI testing)*

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Resolve the only runtime unknown — the mdfetch 0.5.0 sdist URL and SHA-256 from PyPI. Everything else in the formula and CI job is already defined in `contracts/formula.md`.

**⚠️ CRITICAL**: Phase 3 (formula creation) cannot be completed until this phase provides the sdist URL and SHA-256.

- [x] T003 Fetch the mdfetch 0.5.0 sdist URL and SHA-256 from the PyPI JSON API by running the command in `specs/009-homebrew-tap-formula/quickstart.md` Step 1 and recording the two values for use in T004

**Checkpoint**: `SDIST_URL` and `SHA256` values are known.

---

## Phase 3: User Story 1 - Install md-fetch via Homebrew (Priority: P1) 🎯 MVP

**Goal**: A working Homebrew formula that installs the `md-fetch` binary from PyPI with all dependencies bundled. Passes `brew test`.

**Independent Test**: `brew install --build-from-source homebrew-tap/Formula/md-fetch.rb && brew test md-fetch` succeeds; `md-fetch --version` exits 0.

### Implementation for User Story 1

- [x] T004 [US1] Create `homebrew-tap/Formula/md-fetch.rb` from the complete skeleton in `specs/009-homebrew-tap-formula/contracts/formula.md`: replace the two `<placeholder>` values (`url` path and `sha256`) with the values obtained in T003; all 13 resource blocks are already complete in the skeleton
- [x] T005 [P] [US1] Run `brew install --build-from-source /Users/Stanislav_Deviatov/src/github/homebrew-tap/Formula/md-fetch.rb` to build and install the formula from the local file; fix any dependency or build errors before proceeding
- [x] T006 [P] [US1] Run `brew test md-fetch` after T005 succeeds and confirm the `assert_match version.to_s` assertion passes
- [x] T007 [P] [US1] Run `brew audit --strict --new /Users/Stanislav_Deviatov/src/github/homebrew-tap/Formula/md-fetch.rb` and fix any style violations reported (common: trailing whitespace, missing `desc`, resource ordering)

**Checkpoint**: Formula installs cleanly; `md-fetch --version` exits 0; `brew test` passes; `brew audit` clean.

---

## Phase 4: User Story 2 - Formula Stays in Sync with PyPI Releases (Priority: P2)

**Goal**: The `update-homebrew-tap` job in `publish.yml` fetches the new sdist SHA-256 from PyPI (with retry), patches the formula, commits, and pushes — entirely without manual intervention.

**Independent Test**: Simulate the PyPI fetch script locally with `VERSION=0.5.0`; verify it outputs the correct `SDIST_URL` and `SHA256`. After merging, trigger a release and confirm the tap-update job completes green in GitHub Actions.

### Implementation for User Story 2

- [x] T008 [US2] Add the `update-homebrew-tap` job to `md-fetch/.github/workflows/publish.yml` by inserting the job skeleton from `specs/009-homebrew-tap-formula/contracts/tap-update-job.md` after the existing `publish` job; ensure `needs: publish` and `permissions: contents: read` are set
- [x] T009 [P] [US2] Simulate the PyPI fetch portion of the tap-update script locally: set `VERSION=0.5.0` and run the curl + Python snippet from `specs/009-homebrew-tap-formula/quickstart.md` Step 4; confirm `SDIST_URL` and `SHA256` match the values from T003

**Checkpoint**: `publish.yml` is syntactically valid (`actionlint` or manual inspection); simulation produces correct values.

---

## Phase 5: User Story 3 - Discover Homebrew Installation via Documentation (Priority: P3)

**Goal**: Both READMEs updated so users find the Homebrew install option without searching.

**Independent Test**: `grep "brew install stn1slv/tap/md-fetch" md-fetch/README.md` returns a match; the Available Formulas table in `homebrew-tap/README.md` includes a `md-fetch` row.

### Implementation for User Story 3

- [x] T010 [P] [US3] Update `md-fetch/README.md`: in the `## Install` section, add a Homebrew subsection after the existing `pip install mdfetch` block with the command `brew install stn1slv/tap/md-fetch` and a note that it requires no Python environment setup
- [x] T011 [P] [US3] Update `homebrew-tap/README.md`: add `| [md-fetch](https://github.com/stn1slv/md-fetch) | Extract article content from web platforms as clean Markdown |` to the Available Formulas table (alphabetical order between `http-proxy-logger` and `md-paste`)

**Checkpoint**: Both README files contain the Homebrew install instruction; links are correct.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Validate the full end-to-end flow and confirm no regressions.

- [x] T012 [P] Run `make test` in `md-fetch` and confirm all unit tests still pass after `publish.yml` changes
- [x] T013 [P] Commit and push all changes in `homebrew-tap` (`Formula/md-fetch.rb` + `README.md`) to `stn1slv/homebrew-tap` main branch
- [x] T014 [P] Commit and push all changes in `md-fetch` (`publish.yml` + `README.md`) to the `009-homebrew-tap-formula` branch, open a PR targeting `main`, and confirm CI passes
- [ ] T015 After T013 and T014 are merged, verify the live tap works: run `brew install stn1slv/tap/md-fetch` on a clean machine (or `brew reinstall stn1slv/tap/md-fetch`) and confirm `md-fetch --version` exits 0

---

## Remediation: Gaps

<!--
  Discovered via /speckit-reconcile-run or post-implementation review.
  Add tasks here for fixes that weren't part of the original plan.
-->

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on nothing; must complete before Phase 3
- **User Story 1 (Phase 3)**: Depends on Phase 2 (needs sdist URL+hash)
- **User Story 2 (Phase 4)**: Writing (T008) can start any time; testing (T009) can start any time; full CI test requires US1 formula to exist in the tap
- **User Story 3 (Phase 5)**: Fully independent — can run in parallel with Phases 3 and 4
- **Polish (Phase 6)**: Depends on Phases 3, 4, and 5 all complete

### User Story Dependencies

- **US1 (P1)**: Can start after Phase 2 — delivers the installable formula
- **US2 (P2)**: T008 (write CI job) independent; T009 (simulate) independent; full CI verification requires US1 merged to homebrew-tap
- **US3 (P3)**: Fully independent of US1 and US2

### Parallel Opportunities

- T005, T006, T007 (brew verification tasks) can run in parallel after T004
- T010 and T011 (README tasks) can run in parallel with each other and with all of Phase 3
- T008 (write CI job) can run in parallel with Phase 3
- T012, T013, T014 (commit/push tasks) can run in parallel — different repos

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001–T002)
2. Complete Phase 2: Foundational (T003)
3. Complete Phase 3: User Story 1 (T004–T007)
4. **STOP and VALIDATE**: `brew install` + `brew test` — formula works independently
5. Push formula to homebrew-tap and ship

### Incremental Delivery

1. Phases 1–2 → sdist info resolved, prereqs confirmed
2. Phase 3 → working Homebrew formula (MVP — users can install)
3. Phase 4 → automated tap updates on release
4. Phase 5 → documentation complete
5. Phase 6 → validated end-to-end, all tests green

---

## Notes

- **T002 is a manual prerequisite** (PAT creation and secret configuration) — it cannot be automated; complete before CI testing in Phase 4
- **T005/T006/T007** require Homebrew installed locally; if unavailable, skip to CI testing after pushing the formula
- **brew audit** in T007 may report warnings about Python dependency pinning; this is expected for older Homebrew-core Python formulas and can be suppressed if needed
- Commit after each phase checkpoint to maintain a clean history
- Resource block dependency versions are pinned to `uv.lock` at time of formula creation; dependency bumps are a separate future task not in scope here
