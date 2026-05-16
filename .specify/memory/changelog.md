### mdfetch — Homebrew Tap Formula — 2026-05-16

**Branch**: `009-homebrew-tap-formula`
**Spec**: specs/009-homebrew-tap-formula

**What was added**:
- `Formula/md-fetch.rb` in `stn1slv/homebrew-tap` using `Language::Python::Virtualenv` pattern with 13 resource blocks; `depends_on "python@3.12"`; `uses_from_macos "libxml2"` and `uses_from_macos "libxslt"` (required by lxml); test block verifying `md-fetch --version`
- `update-homebrew-tap` job in `.github/workflows/publish.yml`: polls PyPI JSON API (3×30s retry), patches formula url+sha256 via sed, commits and pushes to tap; `concurrency: group=homebrew-tap-update, cancel-in-progress: false` serializes concurrent release runs
- `README.md` updated with `brew install stn1slv/tap/md-fetch` as secondary install option beneath `pip install mdfetch`
- `homebrew-tap/README.md` updated with md-fetch row in Available Formulas table
- TAP_GITHUB_TOKEN documented as required fine-grained PAT (`Contents: read+write` on `stn1slv/homebrew-tap` only)

**New Components**:
- `Formula/md-fetch.rb` (in `stn1slv/homebrew-tap`) — Homebrew formula
- `update-homebrew-tap` CI job (in `.github/workflows/publish.yml`)

**Tasks Completed**: 13/15 (T002 manual PAT setup, T015 post-merge verification pending)

---

### mdfetch — Architecture Refactoring & CLI Improvements — 2026-05-16

**Branch**: `refactor/reduce-duplication-and-robustness`

**What was added**:
- Centralized duplicated markdown conversion and iframe stripping into `BaseExtractor`, utilizing a `_markdownify_kwargs()` hook.
- Added strict `Content-Type` header validation in `_do_fetch` to eagerly reject non-HTML responses (e.g., `application/json`, `application/pdf`).
- Implemented `httpx.Client` connection pooling across retry attempts.
- Exported new public API `mdfetch.supported_domains()` which returns a `frozenset[str]` of all registered domains.
- Expanded the CLI (`mdfetch.cli:main`) with configurable options: `--retries`, `--retry-delay` (with click `IntRange`/`FloatRange` validation), and `--version`.
- Removed control-flow assertions in favor of explicit `RuntimeError` guards.
- Consolidated test helpers (`make_stream_mock`) into `tests/conftest.py`.
- Bumped package version to `0.5.0`.

**New Components**:
- Updates across `base.py`, `router.py`, `cli.py`, and `__init__.py`.
- Refactored providers (`devto.py`, `substack.py`, `thenewstack.py`, `dzone.py`) to leverage `BaseExtractor` defaults.
- Additional unit and integration test coverage for CLI flags and content types.

**Tasks Completed**: Refactoring and PR Review updates

---

# Merged Features Log

---

### mdfetch — The New Stack Provider — 2026-05-16

**Branch**: `006-thenewstack-provider`
**Spec**: specs/006-thenewstack-provider

**What was added**:
- `TheNewStackExtractor` provider for `thenewstack.io` articles, auto-discovered via `@register` decorator
- Article body isolation from `div#tns-post-body-content`; title prepended from `h1.title` in `div#tns-post-headline`; optional deck/subtitle prepended as plain `<p>` tag from `div.post-excerpt`
- 4 sponsored-content selectors decomposed from body: `div.sponsored-post-disclosure`, `div.tns-sponsored-post-disclosure`, `div.sponsor-disclosure`, `div.tns-sponsor-note`
- iframes converted to plain anchor links (defensive; not observed in reference articles)
- `UnsupportedContentTypeError` raised when `div#tns-post-body-content` is absent; `EmptyContentError` raised when body yields no extractable text
- 14 unit tests in `tests/unit/test_thenewstack_extractor.py`; 6 integration tests (5 article snapshots + 1 homepage error) in `tests/integration/test_thenewstack_integration.py`
- VoxPop polls (`div.tns-voxpop-screen`) confirmed as page-level modals outside body — no stripping needed
- Snapshots use verbatim first-30-line prefix format (preserves blank lines for containment assertion)

**New Components**:
- `src/mdfetch/providers/thenewstack.py` — TheNewStackExtractor
- `tests/unit/test_thenewstack_extractor.py` — 14 unit tests
- `tests/integration/test_thenewstack_integration.py` — 6 integration tests
- `tests/integration/snapshots/thenewstack-developer-portal-api.md`
- `tests/integration/snapshots/thenewstack-async-apis.md`
- `tests/integration/snapshots/thenewstack-json-schema-ai.md`
- `tests/integration/snapshots/thenewstack-mcp-api-governance.md`
- `tests/integration/snapshots/thenewstack-api-mcp-agent.md`

**Tasks Completed**: 20/20

---

### mdfetch — Substack Provider — 2026-05-15

**Branch**: `005-substack-provider`
**Spec**: specs/005-substack-provider

**What was added**:
- `SubstackExtractor` provider for `substack.com` and all `*.substack.com` subdomain articles, auto-discovered via `@register` decorator
- Article body isolation from `div.body.markup`; title prepended from `h1.post-title` in `div.post-header` (unconditional — structurally outside body); optional subtitle from `h3.subtitle` prepended after title
- `div.subscription-widget-wrap` stripped (inline subscribe CTAs and paywall terminal widget — achieves silent free-preview truncation for paywalled posts without error or marker)
- `<iframe>` and unknown `div[data-component-name]` embed containers converted to plain anchor links (consistent with dev.to embed handling)
- HTTP 429 retried via base-class fixed-delay retry (no `_no_retry_status_codes` override — no Freedium-style mirror for Substack)
- `UnsupportedContentTypeError` raised when `div.body.markup` is absent; `EmptyContentError` raised when body yields no extractable text
- 18 unit tests in `tests/unit/test_substack_extractor.py`; 3 integration tests in `tests/integration/test_substack_integration.py` with 2 snapshot golden files
- `test_router.py` unsupported-domain fixture updated from `substack.com` to `wordpress.com`

**New Components**:
- `src/mdfetch/providers/substack.py` — SubstackExtractor
- `tests/unit/test_substack_extractor.py` — 18 unit tests
- `tests/integration/test_substack_integration.py` — 3 integration tests
- `tests/integration/snapshots/substack-kafka-topic-types.md`
- `tests/integration/snapshots/substack-api-trends-2025.md`

**Tasks Completed**: 21/21

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
