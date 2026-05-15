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
    └── devto.py      # DevToExtractor (dev.to)

tests/
├── unit/             # pytest unit tests (no network)
└── integration/      # real network tests (Medium + dev.to URLs + snapshots)

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
## Active Feature

**005-substack-provider** — Add Substack platform extractor
Plan: [specs/005-substack-provider/plan.md](specs/005-substack-provider/plan.md)

Key implementation details:
- New file: `src/mdfetch/providers/substack.py` — `SubstackExtractor(BaseExtractor)`, `DOMAINS = frozenset({"substack.com"})`
- Extraction root: `div.body.markup` (inside `div.available-content`)
- Title: prepend `h1.post-title` from `div.post-header`; subtitle: prepend `h3.subtitle` if present
- Strip: `div.subscription-widget-wrap` (inline CTAs + paywall terminal widget)
- Embeds: replace `iframe` and unknown `div[data-component-name]` with plain anchor links
- HTTP 429: retried (no `_no_retry_status_codes` override)
- Tests: `tests/unit/test_substack.py` + `tests/integration/test_substack_integration.py`
<!-- SPECKIT END -->
