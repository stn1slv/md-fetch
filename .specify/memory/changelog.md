# Merged Features Log

---

### mdfetch — dev.to Extractor — 2026-05-14

**Branch**: `002-devto-provider`
**Spec**: specs/002-devto-provider

**What was added**:
- `DevToExtractor` provider for `dev.to` articles, auto-discovered via `@register` decorator
- Article body isolation from `<div id="article-body">` with cover image extracted from `<header class="crayons-article__header">` and prepended to output
- `<iframe>` and liquid-tag embed (`ltag__*`) replacement with plain Markdown links (FR-019)
- `UnsupportedContentTypeError` raised for non-article dev.to pages (profiles, tag listings)
- 17 new unit tests in `tests/unit/test_devto_extractor.py`
- 3 dev.to integration tests in `tests/integration/test_devto_integration.py` with snapshot golden files
- Library version bumped from `0.1.0` to `0.2.0`
- `"dev.to"` added to `pyproject.toml` keywords (T013)

**New Components**:
- `src/mdfetch/providers/devto.py` — DevToExtractor
- `tests/unit/test_devto_extractor.py` — 17 unit tests
- `tests/integration/test_devto_integration.py` — 3 integration tests
- `tests/integration/snapshots/devto-integration-digest-december-2025.md`
- `tests/integration/snapshots/devto-integration-digest-july-2025.md`
- `tests/integration/snapshots/devto-integration-digest-march-2026.md`

**Tasks Completed**: 13/13

---

### mdfetch — Medium Extractor (Initial Release) — 2026-05-14

**Branch**: `feature/first-draft`
**Spec**: specs/001-mdfetch-medium-extractor

**What was added**:
- `extract(url: str) -> str` public API for converting Medium articles to Markdown
- Provider pattern with `BaseExtractor` ABC and `MediumExtractor` implementation
- Auto-discovery routing via `pkgutil.iter_modules` + `@register` decorator (SC-006 compliant)
- Full typed exception hierarchy: `MdfetchError` → `InvalidURLError`, `UnsupportedPlatformError`, `UnsupportedContentTypeError`, `FetchError` → `HTTPStatusError`, `EmptyContentError`
- Streaming HTTP fetch with 10 MB response size cap
- Browser-like User-Agent (FR-014 compliant, no library branding)
- Snapshot-based integration tests with retry logic (3 retries, 2-second delay)
- PyPI-ready package: `pyproject.toml` + `src/` layout + `hatchling` build backend
- `Makefile` with full dev workflow (setup, test, integration, lint, typecheck, format, build, upgrade-deps, clean)

**New Components**:
- `src/mdfetch/__init__.py` — public surface
- `src/mdfetch/exceptions.py` — typed exception hierarchy
- `src/mdfetch/base.py` — BaseExtractor ABC + fetch_html + extract template method
- `src/mdfetch/router.py` — @register, auto-discovery, route()
- `src/mdfetch/providers/medium.py` — MediumExtractor
- `tests/unit/` — 30 unit tests (offline)
- `tests/integration/` — 3 integration tests with 3 snapshot golden files

**Tasks Completed**: 32/32
