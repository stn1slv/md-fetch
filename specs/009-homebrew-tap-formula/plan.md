# Implementation Plan: Homebrew Tap Formula

**Branch**: `009-homebrew-tap-formula` | **Date**: 2026-05-16 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/009-homebrew-tap-formula/spec.md`

## Summary

Add a Homebrew formula for the `md-fetch` CLI to `stn1slv/homebrew-tap` using the `Language::Python::Virtualenv` pattern, with all 13 runtime dependencies declared as pinned `resource` blocks. Extend the existing `publish.yml` workflow with a sequential `update-homebrew-tap` job that polls the PyPI JSON API (up to 3×30s retries) for the new release's sdist SHA-256, patches the formula in-place with `sed`, commits, and pushes. Update both READMEs (md-fetch and homebrew-tap).

## Technical Context

**Language/Version**: Python 3.12+ (unchanged); formula is Ruby (Homebrew DSL)

**Primary Dependencies**: Same runtime stack as the library (`httpx`, `beautifulsoup4/lxml`, `markdownify`, `click` + transitive deps); all 13 are pinned in `research.md`

**Storage**: N/A — no data storage

**Testing**: `brew test md-fetch` (runs `assert_match version.to_s, shell_output("md-fetch --version")`) — separate from the project's pytest suite

**Target Platform**: macOS (primary) + Linux (Homebrew on Linux)

**Project Type**: Packaging / distribution infrastructure; no changes to the Python library itself

**Performance Goals**: Formula installation ≤ 3 minutes (SC-001); tap update ≤ 10 minutes post-publish (SC-003)

**Constraints**:
- No changes to `src/mdfetch/` or `tests/` — this feature is purely packaging and CI
- The `HOMEBREW_TAP_TOKEN` PAT must be created and stored as a repository secret by the maintainer before first use (one-time manual step)
- Formula resource blocks pin dependency versions to those in `uv.lock` at time of formula creation; dependency bumps are a separate manual operation

**Scale/Scope**: Single formula file; single CI job addition; two README updates

## Constitution Check

*GATE: Must pass before implementation. Re-check after design phase.*

- [x] **Provider Pattern Architecture** — No changes to the provider pattern; this feature adds packaging infrastructure only. N/A check passes.
- [x] **Technology Stack** — Python library runtime stack unchanged. CI job uses Python 3 (available on ubuntu-latest) for JSON parsing without adding new project dependencies. N/A for Ruby formula file (Homebrew DSL, not project source).
- [x] **Coding Standards** — No Python source files are modified. README updates follow existing style.
- [x] **Integration Testing** — No changes to the Python extraction library; existing integration tests are unaffected. `brew test` validates the installed binary end-to-end.
- [x] **Packaging and Distribution** — This feature directly advances the packaging goal. Formula follows Homebrew Python virtualenv best practices. `pyproject.toml` and `src/` layout are unchanged.

**Constitution violations**: None. No complexity tracking entry required.

## Project Structure

### Documentation (this feature)

```text
specs/009-homebrew-tap-formula/
├── plan.md              ← this file
├── research.md          ← Phase 0: dependency hashes, patterns, decisions
├── data-model.md        ← Phase 1: entities and field definitions
├── contracts/
│   ├── formula.md       ← complete formula skeleton with all resource blocks
│   └── tap-update-job.md ← CI job skeleton and failure mode table
└── tasks.md             ← Phase 2 output (/speckit-tasks — not yet created)
```

### Files Created / Modified

**Repository: `stn1slv/homebrew-tap`**

```text
Formula/
└── md-fetch.rb          NEW: Homebrew formula (Language::Python::Virtualenv)
README.md                MODIFIED: add md-fetch row to Available Formulas table
```

**Repository: `stn1slv/md-fetch`**

```text
.github/workflows/
└── publish.yml          MODIFIED: add update-homebrew-tap job after publish
README.md                MODIFIED: add brew install as secondary install option
```

**No changes to**:
- `src/mdfetch/` (library unchanged)
- `tests/` (test suite unchanged)
- `pyproject.toml` / `uv.lock` (dependencies unchanged)

## Formula Architecture

The formula uses `Language::Python::Virtualenv` (Homebrew's standard Python CLI pattern):

```
brew install stn1slv/tap/md-fetch
  ↓
Homebrew fetches mdfetch sdist + all 13 resource tarballs
  ↓
virtualenv_install_with_resources:
  1. Creates Python 3.12 venv in Cellar/md-fetch/{version}/libexec/
  2. Installs each resource into the venv via pip (no network)
  3. Installs mdfetch into the venv
  4. Symlinks libexec/bin/md-fetch → bin/md-fetch
  ↓
md-fetch binary available on PATH
```

**Resources declared** (alphabetical, as required by Homebrew style):
anyio, beautifulsoup4, certifi, click, h11, httpcore, httpx, idna, lxml, markdownify, six, soupsieve, typing-extensions

Full skeleton with all URLs and hashes: [`contracts/formula.md`](contracts/formula.md)

## CI Job Design

```
GitHub Release published (tag vX.Y.Z on main)
  ↓
build job (existing) → publish job (existing)
  ↓
update-homebrew-tap job (NEW, needs: publish)
  1. Strip 'v' prefix from GITHUB_REF_NAME → VERSION
  2. Poll https://pypi.org/pypi/mdfetch/{VERSION}/json
     - Retry up to 3× with 30s sleep on failure/empty
     - Extract: SDIST_URL, SHA256
     - Exit 1 if not available after 3 retries
  3. Clone stn1slv/homebrew-tap via HOMEBREW_TAP_TOKEN
  4. sed patch Formula/md-fetch.rb:
     - Replace url line (package)
     - Replace first sha256 line (package only, not resource blocks)
  5. git commit "chore: bump md-fetch to v{VERSION}"
  6. git pull --rebase (concurrent release safety)
  7. git push
```

Full YAML skeleton: [`contracts/tap-update-job.md`](contracts/tap-update-job.md)

## Failure Modes

| Condition | Behaviour |
|-----------|-----------|
| PyPI doesn't return new version after 3×30s | Job exits 1 → CI failure (SC-004) |
| `HOMEBREW_TAP_TOKEN` missing or revoked | `git clone` fails → CI failure (SC-004) |
| Formula file structure changed (sed no-op) | `git commit` finds nothing staged → exits 1 → CI failure |
| Push conflict (concurrent release) | `git pull --rebase` succeeds for sequential; true concurrent fails loudly |
| `brew test` fails after install | `brew test md-fetch` exits non-zero → installation validation fails |
