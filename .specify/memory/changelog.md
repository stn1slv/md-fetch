# Merged Features Log

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
