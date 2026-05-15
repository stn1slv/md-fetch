# mdfetch

Python library that extracts article content from web platforms and returns it as clean Markdown.

## Project structure

```
src/mdfetch/
├── __init__.py       # extract() public API + exception re-exports
├── exceptions.py     # MdfetchError hierarchy (7 exception classes)
├── base.py           # BaseExtractor ABC
├── router.py         # Domain-to-provider routing
└── providers/
    ├── __init__.py
    ├── medium.py     # MediumExtractor (medium.com + *.medium.com)
    ├── devto.py      # DevToExtractor (dev.to)
    └── substack.py   # SubstackExtractor (substack.com + *.substack.com)

tests/
├── unit/             # pytest unit tests (no network)
└── integration/      # real network tests (Medium + dev.to + Substack URLs + snapshots)

.github/workflows/
├── ci.yml            # lint + unit tests on push/PR (Python 3.12–3.14)
├── integration.yml   # scheduled integration tests every Friday 23:30 UTC
└── publish.yml       # PyPI publish on release

specs/                # Speckit feature specifications
pyproject.toml        # hatchling build, uv package manager
Makefile              # setup / test / lint / format / build / upgrade-deps / clean
```

## Key conventions

- **Package manager**: `uv` for all dev workflows — never use `pip`, `venv`, or `pip-tools` directly
- **Provider pattern**: new platforms = one new file under `src/mdfetch/providers/`, no changes to shared code
- **No logging**: all failures communicated via typed exceptions only (FR-013)
- **Type hints**: strict (`mypy src/` must pass with zero errors)
- **Linter/formatter**: `ruff` (`make lint` / `make format`)

## Common commands

```bash
make setup        # uv sync --all-extras
make test         # unit tests only
make lint         # ruff check
make format       # ruff format
make build        # uv build (wheel + sdist)
make upgrade-deps # uv sync --all-extras --upgrade
make integration  # integration tests (network required)
uv run mypy src/  # type check
```

<!-- SPECKIT START -->
## Known Issues & Gotchas

### ⚠️ test_router.py "unsupported domain" fixture must be updated per new provider
**Issue:** When a new provider registers a domain (e.g., `dev.to`, then `substack.com`), the existing `test_raises_for_unsupported_domain` and `test_unsupported_error_includes_domain` tests in `tests/unit/test_router.py` use that domain as their "unsupported" example and start routing successfully instead of raising `UnsupportedPlatformError`.
**Root Cause:** The domain used in the router tests was `substack.com` after the dev.to feature; adding SubstackExtractor made it valid too.
**Prevention Rule:** When adding a new provider, update the unsupported-domain fixture in `test_router.py` to use a domain not registered by any provider (currently `wordpress.com`).
<!-- SPECKIT END -->
