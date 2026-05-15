# Merged Features Log

---

### mdfetch — Remove Exponential Backoff — 2026-05-15

**Branch**: `004-remove-backoff`
**Spec**: specs/004-remove-backoff

**What was added**:
- Fixed-delay retry behaviour: `fetch_html` now sleeps exactly `retry_delay` seconds between attempts (previously exponential `retry_delay × 2ⁿ`, capped at 60 s). The change makes retry timing predictable for callers and aligns with the Freedium fallback that already absorbs 403/429 errors.
- Removed `MDFETCH_RETRIES` and `MDFETCH_RETRY_DELAY` env-var support from integration test fixtures (`conftest.py` deleted) and CI workflow (`integration.yml`). Integration tests now hardcode `retries=3, retry_delay=2.0`.
- Deleted two unit tests (`test_exponential_backoff_sleep_sequence`, `test_exponential_backoff_capped_at_max_delay`) that verified the removed exponential schedule. Added sleep-value assertion to `test_status_code_not_in_no_retry_set_still_retries` to close the FR-029 gap.

**New Components**:
- No new files. Pure removal: `tests/integration/conftest.py` deleted; `_MAX_RETRY_DELAY` constant removed from `src/mdfetch/base.py`.

**Tasks Completed**: 16/16

---

### mdfetch — Medium Freedium Fallback — 2026-05-15

**Branch**: `003-medium-freedium-fallback`
**Spec**: specs/003-medium-freedium-fallback

**What was added**:
- Transparent fallback to `https://freedium-mirror.cfd/` when medium.com returns HTTP 403 (paywall) or HTTP 429 (rate limit) — caller sees no difference in the `extract()` interface
- `_no_retry_status_codes: frozenset[int]` class attribute on `BaseExtractor`; codes in this set skip retry/backoff and raise immediately (defaults to `frozenset()` — safe for all existing providers)
- `_no_retry_codes: frozenset[int] | None = None` keyword-only parameter on `fetch_html()` for per-call override without instance mutation (thread-safe)
- `_parse_freedium(soup)` method on `MediumExtractor`: locates `div.main-content`, remaps h4→h3/h5→h4/h6→h5, converts to Markdown; heading remap ensures output is structurally identical to the direct medium.com path
- `extract()` override on `MediumExtractor`: on 403/429, fetches `freedium_url` with `_no_retry_codes=frozenset()`, routes to `_parse_freedium()`; always sets `exc.url` to the original Medium URL on failure
- 18 new unit tests across `test_medium_extractor.py` (TestParseFreedium, TestFreediumFallback, TestRateLimitFallback, TestNoFallbackOnSuccess) and `test_fetch_errors.py`
- Integration test suite now resilient to medium.com 403 responses — paywalled URL included in snapshot tests

**New Components**:
- Changes to `src/mdfetch/base.py` — `_no_retry_status_codes` attribute + `_no_retry_codes` param on `fetch_html()`
- Changes to `src/mdfetch/providers/medium.py` — `_parse_freedium()` + `extract()` override + Freedium constants

**Tasks Completed**: 12/12

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
