# Implementation Plan: List Supported Platforms

**Branch**: `012-list-platforms` | **Date**: 2026-06-02 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/012-list-platforms/spec.md`

## Summary

Add a `--list-platforms` flag to the existing `md-fetch` CLI command that prints
every supported platform domain (alphabetically, indicating subdomain support for
multi-tenant providers) to stdout and exits 0, without requiring a URL or making
any network request. The data is sourced from a new typed router accessor
`supported_platforms()` so the list stays in lock-step with the provider registry.
This is a CLI/presentation enhancement — **no new provider, no extraction logic,
no base-class changes.**

## Technical Context

**Language/Version**: Python 3.12+ (CI matrix 3.12–3.14)

**Primary Dependencies**: `click` (CLI — already a dependency), `pytest` + `pytest-mock` (testing). No new dependencies.

**Storage**: N/A

**Testing**: `pytest` via `uv run pytest` — unit tests only (`tests/unit/`), `CliRunner`. No integration test (operation is offline).

**Target Platform**: PyPI library + `md-fetch` console script (cross-platform)

**Project Type**: Library + CLI

**Performance Goals**: Completes in well under 1 s, no network (SC-001)

**Constraints**: Presentation-layer change in `cli.py` + one thin read-only accessor in `router.py`. No changes to providers, base class, or extraction pipeline. Backward-compatible: bare `md-fetch <URL>` unchanged (FR-001a).

**Scale/Scope**: ~7 registered domains today; grows as providers are added.

## Constitution Check

*GATE: Must pass before implementation. Re-check after design phase.*

- [x] **Provider Pattern Architecture** — No provider added or modified; the registry remains the single source of truth. New accessor reads it read-only; no duplication.
- [x] **Technology Stack** — Uses existing `click` + `pytest`; no new tech introduced.
- [x] **Coding Standards** — New function fully type-hinted (`list[tuple[str, bool]]`); PEP 8; clear naming (`supported_platforms`).
- [x] **Integration Testing** — Principle IV mandates real-link integration tests *for extractors*. This feature performs no fetch and exposes no extractor, so there is nothing to fetch; unit tests with `CliRunner` are the appropriate and sufficient coverage. **Justified deviation, not a violation.**
- [x] **Packaging and Distribution** — No structural change; `pyproject.toml` version bump only; all workflows via `uv run`.

**Result**: PASS. The Principle IV note is recorded in Complexity Tracking for traceability.

## Project Structure

### Documentation (this feature)

```text
specs/012-list-platforms/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   └── cli.md           # CLI command contract
└── tasks.md             # Phase 2 output (/speckit-tasks — NOT created here)
```

### Source Code

```text
src/mdfetch/
├── router.py            # MODIFIED: add supported_platforms() accessor
└── cli.py               # MODIFIED: add --list-platforms flag; url becomes optional

tests/unit/
├── test_cli.py          # MODIFIED: add --list-platforms cases + no-URL/no-flag usage error
└── test_router.py       # MODIFIED: add supported_platforms() test
```

**Non-runtime changes**: `pyproject.toml` (version bump 0.7.1 → 0.8.0, minor — user-facing feature); `README.md` (document the `--list-platforms` flag in usage); `CLAUDE.md` (no structural change required — CLI gains a flag, project tree unchanged).

## Implementation Outline

```
router.supported_platforms() -> list[tuple[str, bool]]:
  return sorted(
    (domain, cls.MATCH_SUBDOMAINS) for domain, cls in _REGISTRY.items()
  )                                  # sorted by domain (tuple natural order)

cli.main:
  add option: --list-platforms (is_flag=True, is_eager=True)
  make `url` argument required=False
  body:
    if list_platforms:
      for domain, subs in supported_platforms():
        line = f"{domain} (and *.{domain})" if subs else domain
        click.echo(f"  {line}")            # under a "Supported platforms:" header
      return                                # exit 0; no extraction, no network
    if url is None:
      raise click.UsageError("Missing argument 'URL'.")  # exit code 2
    ... existing fetch/extract path unchanged ...
```

## Error / Exit-Code Mapping

| Condition | Behavior |
|-----------|----------|
| `--list-platforms` supplied | Print list to stdout, exit 0 |
| No URL and no `--list-platforms` | Usage error to stderr, exit 2 |
| `md-fetch <URL>` (flag absent) | Unchanged existing behavior |

## Complexity Tracking

| Item | Why | Note |
|------|-----|------|
| No integration test (Constitution IV) | Operation is offline; exposes no extractor and performs no fetch | Unit tests via `CliRunner` provide full coverage; documented in research.md R4 |
| `url` argument made optional | Required to invoke the list operation without a URL (FR-001a) | Requiredness re-enforced manually so `md-fetch <URL>` error UX is preserved |
