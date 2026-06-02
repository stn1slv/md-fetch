# Quickstart: List Supported Platforms

## Try it

```bash
md-fetch --list-platforms
```

Expected output (exit 0):

```
Supported platforms:
  boomi.com
  dev.to
  dzone.com
  konghq.com
  medium.com (and *.medium.com)
  substack.com (and *.substack.com)
  thenewstack.io
```

Fetching still works exactly as before:

```bash
md-fetch https://dev.to/some/article        # unchanged
md-fetch                                     # error: missing URL (exit 2)
```

## Verify (developer)

```bash
make setup        # uv sync --all-extras
make lint         # ruff check
make typecheck    # mypy src/
make test         # unit tests (no network)
```

All of the above must pass. The feature adds no network dependency, so
`make integration` is unaffected by this change.

## What changed

- `src/mdfetch/router.py` — new `supported_platforms()` accessor.
- `src/mdfetch/cli.py` — new `--list-platforms` flag; `URL` now optional.
- `tests/unit/test_cli.py`, `tests/unit/test_router.py` — new coverage.
- `pyproject.toml` — version bump `0.7.1` → `0.8.0` (minor).
- `README.md` — documents the new flag.
