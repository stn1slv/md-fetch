# mdfetch — Main Implementation Plan

**Last Updated**: 2026-05-16
**Sources**: [specs/001-mdfetch-medium-extractor/plan.md], [specs/002-devto-provider/plan.md], [specs/003-medium-freedium-fallback/plan.md], [specs/004-remove-backoff/plan.md], [specs/005-substack-provider/plan.md], [specs/006-thenewstack-provider/plan.md]

---

## Technical Context

**Language/Version**: Python 3.12+

**Primary Dependencies**:
| Package | Version Constraint | Role |
|---------|-------------------|------|
| `httpx` | `>=0.27` | HTTP client (sync interface, streaming) |
| `beautifulsoup4` | `>=4.12` | HTML parsing and article-body targeting |
| `lxml` | `>=5.0` | Fast, tolerant HTML parser backend for BeautifulSoup |
| `markdownify` | `>=0.13` | HTML-to-Markdown conversion |
| `pytest` | `>=8.0` (dev) | Test runner (unit + integration) |
| `ruff` | (dev) | Linter and formatter |
| `mypy` | (dev) | Static type checker (strict mode) |

**Package Manager**: `uv` — all local development workflows. Direct use of `pip`, `venv`, or `pip-tools` is prohibited.

**Build Backend**: `hatchling` via `pyproject.toml`

**Testing**: pytest; unit tests for routing and extraction logic; integration tests using real Medium article URLs with snapshot-based containment checks and retry logic.

**Target Platform**: Cross-platform PyPI library (Linux, macOS, Windows); Python 3.12+

**Project Type**: library

---

## Architecture

### Provider Pattern

```
BaseExtractor (ABC)               — src/mdfetch/base.py
├── _no_retry_status_codes: frozenset[int] = frozenset()  — codes that skip retry; overridden by providers
├── fetch_html(url, *, retries, retry_delay, _no_retry_codes=None) → str
│                                 — streaming HTTP, 30s timeout, 10 MB cap;
│                                   fixed delay of retry_delay seconds between attempts (not exponential);
│                                   codes in _no_retry_codes (or class attribute) raise immediately
├── clean_html(soup) → Tag        — abstract: platform-specific HTML isolation
├── _markdownify_kwargs() → dict  — hook: platform-specific markdownify options (defaults to ATX + empty language)
├── _replace_iframes_with_links(container, soup) — helper: converts <iframe> embeds to plain anchors
├── convert_to_markdown(tag) → str— concrete: base implementation using markdownify and 3+ newlines collapse
└── extract(url) → str            — concrete template method (orchestrates the above)

MediumExtractor(BaseExtractor)    — src/mdfetch/providers/medium.py
├── DOMAINS = frozenset({"medium.com"})
├── _FREEDIUM_BASE = "https://freedium-mirror.cfd/"
├── _no_retry_status_codes = frozenset({403, 429})  — immediate fallback, no medium.com retry
├── clean_html() → removes nav, clap buttons, sidebars, share elements, post-footer, author bio
├── convert_to_markdown() → markdownify with ATX headings, fenced code blocks
├── _parse_freedium(soup) → remaps h4→h3/h5→h4/h6→h5; finds div.main-content; convert_to_markdown
└── extract() → override: on 403/429 calls fetch_html(freedium_url, _no_retry_codes=frozenset());
                           exc.url always set to original Medium URL on any Freedium failure

DevToExtractor(BaseExtractor)     — src/mdfetch/providers/devto.py
├── DOMAINS = frozenset({"dev.to"})
└── clean_html() → locates div#article-body; raises UnsupportedContentTypeError if absent;
                   replaces iframes and ltag embeds with anchor links (via helper); strips empty anchor-name
                   elements; prepends h1 + cover image from crayons-article__header

SubstackExtractor(BaseExtractor)  — src/mdfetch/providers/substack.py  [005-substack-provider]
├── DOMAINS = frozenset({"substack.com"})  — also matches *.substack.com via suffix routing
├── _no_retry_status_codes = frozenset()  — HTTP 429 retried (no Freedium-style fallback)
└── clean_html() → locates div.body.markup; raises UnsupportedContentTypeError if absent;
                   strips div.subscription-widget-wrap (inline CTAs + paywall terminal);
                   replaces iframes with anchor links (via helper);
                   replaces div[data-component-name] (except SubscribeWidget, Image2ToDOM) with anchor links;
                   prepends h3.subtitle from div.post-header (if present);
                   prepends h1.post-title from div.post-header (unconditional — structurally outside body)

TheNewStackExtractor(BaseExtractor) — src/mdfetch/providers/thenewstack.py  [006-thenewstack-provider]
├── DOMAINS = frozenset({"thenewstack.io"})  — no subdomain routing needed (single-site WordPress)
├── _no_retry_status_codes = frozenset()  — inherits base class default (no overrides needed)
└── clean_html() → locates div#tns-post-body-content; raises UnsupportedContentTypeError if absent;
                   decomposes 4 sponsored-content selectors: div.sponsored-post-disclosure,
                     div.tns-sponsored-post-disclosure, div.sponsor-disclosure, div.tns-sponsor-note;
                   replaces iframes with anchor links (via helper);
                   prepends div.post-excerpt text as new <p> tag (deck) from div#tns-post-headline (if present);
                   prepends copy.copy(h1.title) from div#tns-post-headline (if present)
                   Note: VoxPop polls (div.tns-voxpop-screen) are page-level modals outside body — no stripping needed

DZoneExtractor(BaseExtractor) — src/mdfetch/providers/dzone.py
├── DOMAINS = frozenset({"dzone.com"})
├── _markdownify_kwargs() → overrides to add code_language_callback
└── clean_html() → locates div.content-html; raises UnsupportedContentTypeError if absent;

KongExtractor(BaseExtractor) — src/mdfetch/providers/kong.py  [011-konghq-blog-provider]
├── DOMAINS = frozenset({"konghq.com"})
└── clean_html() → requires <main class="type-article"> (else UnsupportedContentTypeError);
                   body = the <main> <section> richest in .rich-text-block;
                   strips in-body chrome (.toc-wrap, .component.video, .component.more-on-this,
                     .order-top, trailing non-intro .section-header-block) and all .agent spans;
                   prepends copy(h1) + publication date (class-less hero <div>, month-name regex);
                   Note: Next.js CSS-module hashes — pin to stable classes only; TOC is .toc-wrap,
                     NOT [class*=TableOfContents] (that wraps the whole body)
```

### Router / Auto-Discovery

```
router.py
├── _REGISTRY: dict[str, type[BaseExtractor]]
├── @register decorator          — self-enrolls provider at class definition time
├── _autodiscover_providers()    — pkgutil.iter_modules scans mdfetch/providers/ at import
├── supported_domains() → frozenset[str] — returns all registered domain strings
├── route(url) → BaseExtractor   — exact hostname match, then longest-suffix fallback
└── Duplicate domain registration raises ValueError
```

**Routing rules**:
- Exact match on lowercased `parsed.hostname` first
- Suffix fallback sorted by domain length (descending) so most-specific wins
- URL validation: scheme must be `http` or `https`; credentials (`user:pass@host`) stripped from error messages (uses `hostname`, not `netloc`)

### Response Safety
- Streaming fetch via `client.stream()` — chunks accumulated, hard cap at 10 MB
- Responses exceeding the cap raise `FetchError` immediately

---

## Project Structure

```
src/
└── mdfetch/
    ├── __init__.py          # Public surface: exposes extract(), exception re-exports
    ├── exceptions.py        # MdfetchError hierarchy (6 exception classes)
    ├── router.py            # @register, _autodiscover_providers(), route()
    ├── base.py              # BaseExtractor ABC + fetch_html() + convert_to_markdown() + extract() template
    ├── cli.py               # click-based command line interface
    └── providers/
        ├── __init__.py      # Empty — auto-discovery handles registration
        ├── medium.py        # MediumExtractor
        ├── devto.py         # DevToExtractor [002-devto-provider]
        ├── substack.py      # SubstackExtractor [005-substack-provider]
        ├── thenewstack.py   # TheNewStackExtractor [006-thenewstack-provider]
        ├── dzone.py         # DZoneExtractor
        └── kong.py          # KongExtractor [011-konghq-blog-provider]

tests/
├── unit/
│   ├── test_router.py
│   ├── test_medium_extractor.py
│   ├── test_fetch_errors.py
│   ├── test_silent.py
│   ├── test_devto_extractor.py      # [002-devto-provider]
│   ├── test_substack_extractor.py   # [005-substack-provider]
│   └── test_thenewstack_extractor.py  # [006-thenewstack-provider]
└── integration/
    ├── snapshots/           # Golden Markdown files (article body snapshots)
    │   ├── from-drift-to-parity.md
    │   ├── architecting-the-asynchronous-agent.md
    │   ├── integration-digest-december-2025.md
    │   ├── devto-integration-digest-december-2025.md        # [002-devto-provider]
    │   ├── devto-integration-digest-july-2025.md            # [002-devto-provider]
    │   ├── devto-integration-digest-march-2026.md           # [002-devto-provider]
    │   ├── substack-kafka-topic-types.md                    # [005-substack-provider]
    │   ├── substack-api-trends-2025.md                      # [005-substack-provider]
    │   ├── thenewstack-developer-portal-api.md              # [006-thenewstack-provider]
    │   ├── thenewstack-async-apis.md                        # [006-thenewstack-provider]
    │   ├── thenewstack-json-schema-ai.md                    # [006-thenewstack-provider]
    │   ├── thenewstack-mcp-api-governance.md                # [006-thenewstack-provider]
    │   └── thenewstack-api-mcp-agent.md                     # [006-thenewstack-provider]
    ├── test_medium_integration.py
    ├── test_devto_integration.py          # [002-devto-provider]
    ├── test_substack_integration.py       # [005-substack-provider]
    └── test_thenewstack_integration.py    # [006-thenewstack-provider]

specs/                       # Speckit feature specifications
pyproject.toml               # hatchling build backend, uv package manager
Makefile                     # setup / test / integration / lint / typecheck / format / build / clean / upgrade-deps
.github/workflows/
├── ci.yml                   # lint + unit tests on push/PR (Python 3.12–3.14)
├── integration.yml          # scheduled integration tests
└── publish.yml              # PyPI publish + Homebrew tap update on release tag
```

**External repository: `stn1slv/homebrew-tap`** [009-homebrew-tap-formula]
```
Formula/
└── md-fetch.rb              # Language::Python::Virtualenv formula; 13 resource blocks;
                             # depends_on "python@3.12"; uses_from_macos "libxml2" + "libxslt"
README.md                    # Available Formulas table updated with md-fetch row
```

---

## Homebrew Distribution Architecture [009-homebrew-tap-formula]

```
GitHub Release tag vX.Y.Z
  ↓
build job → publish job (PyPI)
  ↓
update-homebrew-tap job (NEW, needs: publish)
  [concurrency: group=homebrew-tap-update, cancel-in-progress=false]
  1. Poll https://pypi.org/pypi/mdfetch/{VERSION}/json (retry 3× / 30s)
  2. Extract SDIST_URL and SHA256
  3. Clone stn1slv/homebrew-tap via TAP_GITHUB_TOKEN (fine-grained PAT)
  4. sed patch Formula/md-fetch.rb (url + first sha256 only)
  5. git commit + pull --rebase + push
```

**Formula pattern**: `Language::Python::Virtualenv` — creates isolated venv in Cellar, installs 13 resource blocks, symlinks `libexec/bin/md-fetch` → `bin/md-fetch`.

**System library dependencies** (required by `lxml` resource):
- `uses_from_macos "libxml2"`
- `uses_from_macos "libxslt"`

**TAP_GITHUB_TOKEN**: Fine-grained PAT with `Contents: read+write` on `stn1slv/homebrew-tap` only. Stored as repository secret in `stn1slv/md-fetch`. Must NOT be a classic `repo`-scoped PAT.

---

## Constraints

- No JavaScript rendering; operates on static HTML only
- No response caching; each call performs a fresh HTTP request
- No rate-limit handling or authentication in v1
- Explicit browser-like User-Agent string; MUST NOT identify the library by name or version (FR-014)
- Network timeout: 30 seconds (fixed, not user-configurable in v1)
- Response size cap: 10 MB (raises `FetchError` if exceeded)
- No logging; all failures communicated via typed exceptions (FR-013)

---

## Testing Strategy

**Unit tests** (101 tests, offline):
- Router: domain routing, subdomain suffix matching, duplicate registration, invalid URLs, unsupported platforms
- MediumExtractor: clean_html, convert_to_markdown, empty content, non-article pages, _parse_freedium (heading remap, missing main-content), fallback on 403/429 (URL construction, exc.url contract, no-sleep on 429), no-fallback on 200, UnsupportedContentTypeError.url on Freedium path [003-medium-freedium-fallback]
- DevToExtractor: clean_html (title/cover/heading/image preservation, iframe/ltag embed→link, anchor stripping, non-article error), convert_to_markdown (headings/code/lists/images, no raw HTML, empty content error) [002-devto-provider]
- SubstackExtractor: routing (subdomain + root domain + _no_retry_status_codes assertion), clean_html (body.markup tag return, subscription-widget strip, title prepend, subtitle prepend, prose preservation, iframe→anchor), convert_to_markdown (title heading, no triple blank lines, image syntax, link preservation), paywalled post (non-empty, Subscribe text absent, free preview present), error cases (UnsupportedContentTypeError on no body, EmptyContentError on whitespace body) [005-substack-provider]
- TheNewStackExtractor: routing (thenewstack.io domain), clean_html (body div return, title prepend, deck-as-paragraph prepend, sponsor note strip, all 3 disclosure variant strips, iframe→anchor, no deck when absent), convert_to_markdown (title heading, deck after title, no triple blank lines, image syntax, link preservation), error cases (UnsupportedContentTypeError on no body, EmptyContentError on whitespace body) [006-thenewstack-provider]
- KongExtractor: routing (konghq.com domain), clean_html (title+date prepend order, chrome strip — .toc-wrap/.component.video/.component.more-on-this/.order-top/non-intro .section-header-block, .agent affordance strip, body-block preservation, raises without type-article, raises without .rich-text-block), convert_to_markdown (title then date, structure + inline code preserved, chrome/authors excluded, no triple blank lines, EmptyContentError on whitespace body) [011-konghq-blog-provider]
- Fetch errors: HTTP 404, 503, timeout, connection error, size limit exceeded; `_no_retry_status_codes` immediate-raise + `_no_retry_codes` override [003-medium-freedium-fallback]
- Silent: no stdout/stderr output, no logging during extraction

**Integration tests** (15 tests, network required):
- Parametrized over 3 real stn1slv.medium.com articles (including a known paywalled URL that exercises the Freedium fallback when medium.com returns 403) [003-medium-freedium-fallback]
- Parametrized over 3 real dev.to/stn1slv articles [002-devto-provider]
- Parametrized over 2 real Substack articles + 1 homepage error test (`UnsupportedContentTypeError`) [005-substack-provider]
- Parametrized over 5 real thenewstack.io articles + 1 homepage error test (`UnsupportedContentTypeError`); snapshots are verbatim first-30-line prefixes of the full extraction output [006-thenewstack-provider]
- Snapshot-based containment check: `expected_body in extracted_result` — tests pass regardless of which source served the content
- 3 retries with 2-second **fixed** delay on `FetchError` (hardcoded; not env-var configurable) [004-remove-backoff]
- Run with: `make integration` or `uv run pytest tests/integration/ --override-ini=addopts=`
- Excluded from default `pytest` run via `addopts = "-m 'not integration'"` in pyproject.toml

---

## Makefile Targets

| Target | Command |
|--------|---------|
| `make setup` | `uv sync --all-extras` |
| `make test` | `uv run pytest tests/unit/` |
| `make integration` | `uv run pytest tests/integration/ --override-ini=addopts=` |
| `make lint` | `uv run ruff check src/ tests/` |
| `make typecheck` | `uv run mypy src/` |
| `make format` | `uv run ruff format src/ tests/` |
| `make build` | `uv build` |
| `make upgrade-deps` | `uv sync --all-extras --upgrade` |
| `make clean` | Remove dist/, caches |

---

## Key Technical Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| HTTP client | `httpx` (sync) | Supports async in v2 without swapping dependency |
| HTML parser | `lxml` | Fast, tolerant; BeautifulSoup backend |
| Article targeting (Medium) | `<article>` element | Stable semantic HTML5; consistent across Medium versions |
| Article targeting (dev.to) | `div#article-body` | dev.to does not use `<article>`; the id-scoped div already excludes all chrome | [002-devto-provider]
| dev.to cover image | Extracted from `header.crayons-article__header`, prepended to body | Cover image is outside the article body div — must be fetched separately | [002-devto-provider]
| dev.to embed handling | Replace `<iframe>` and `ltag__*` divs with anchor links | Embeds must not be silently dropped (FR-019); plain links are durable | [002-devto-provider]
| Markdown converter | `markdownify` with ATX + `code_language=""` | Fenced code blocks, standard headings |
| Routing | `pkgutil.iter_modules` auto-discovery + `@register` | SC-006: one new file = one new platform |
| Integration tests | Snapshot containment + retry | Durable against minor HTML changes; resilient to transient 403s |
| test_router.py domain example | Changed from `dev.to` to `substack.com` for "unsupported domain" test | Once DevToExtractor registers `dev.to`, those tests would no longer raise UnsupportedPlatformError | [002-devto-provider]
| test_router.py domain example | Changed from `substack.com` to `wordpress.com` for "unsupported domain" test | Once SubstackExtractor registers `substack.com`, those tests would no longer raise UnsupportedPlatformError | [005-substack-provider]
| Substack article targeting | `div.body.markup` as extraction root | Contains article prose only; `div.available-content` is a transparent wrapper; `div.post-footer` and `div.visibility-check` are sibling elements never encountered when using body as root | [005-substack-provider]
| Substack title prepend | Unconditional prepend of `h1.post-title` from `div.post-header` | Structurally guaranteed outside `div.body.markup`; section headings use distinct class `header-anchor-post` — no deduplication needed | [005-substack-provider]
| Substack subtitle | Prepend `h3.subtitle` after title (inserted at index 0 first, then title at index 0 displaces it to index 1) | Author intent preserved; subtitle rendered as `###` heading | [005-substack-provider]
| Substack HTTP 429 | No `_no_retry_status_codes` override — base class `frozenset()` applies | Unlike Medium, Substack has no Freedium-style mirror; retry is the correct fallback | [005-substack-provider]
| thenewstack.io article body | `div#tns-post-body-content` | Innermost element containing only prose (29 direct `<p>` children in reference articles); parent chain includes several wrapper divs that add no content | [006-thenewstack-provider]
| thenewstack.io deck element | Create new `<p>` tag with deck text rather than copying `div.post-excerpt` directly | `div.post-excerpt` is a `<div>`, not a semantic subtitle; wrapping text in `<p>` ensures proper paragraph rendering in Markdown | [006-thenewstack-provider]
| thenewstack.io VoxPop polls | No explicit stripping required | `div.tns-voxpop-screen` confirmed absent from `div#tns-post-body-content` across all 5 reference articles — page-level overlay modal, not inline content | [006-thenewstack-provider]
| thenewstack.io router test | No update to `test_router.py` unsupported-domain fixture | `wordpress.com` was already the fixture after the Substack provider; `thenewstack.io` registration requires no change | [006-thenewstack-provider]
| thenewstack.io snapshot format | Verbatim first-30-line prefix (not stripped/compacted) | Blank lines must be preserved for `snapshot in result` containment assertion to pass | [006-thenewstack-provider]
| Medium 403/429 fallback | Override `extract()` in `MediumExtractor`; `_no_retry_status_codes=frozenset({403,429})` on class | Immediate fallback with no medium.com retries; `BaseExtractor` extended with `_no_retry_codes` param for thread safety | [003-medium-freedium-fallback]
| Freedium HTML parsing | Dedicated `_parse_freedium()` method; `div.main-content`; h4→h3 remap | Freedium HTML is structurally incompatible with `clean_html()` (no `<article>`); heading remap ensures snapshot tests pass for both paths | [003-medium-freedium-fallback]
| Freedium exc.url contract | `inner_exc.url = url` unconditionally; error message is source-agnostic ("Fallback page…") | Preserves transparent-fallback contract (FR-028); `exc.url` is the authoritative field; message content is internal | [003-medium-freedium-fallback]
| Retry strategy | Fixed delay (`retry_delay` seconds per attempt, unchanged between attempts) | Exponential backoff removed (PR #8); Freedium fallback absorbs 403/429 at a higher level making exponential growth unnecessary; integration tests use hardcoded defaults (`retries=3, retry_delay=2.0`) with no env-var override | [004-remove-backoff]

---

## Constitution Compliance

- [x] Provider Pattern Architecture — `BaseExtractor` ABC with concrete `fetch_html` and abstract `clean_html`, `convert_to_markdown`; `MediumExtractor` inherits
- [x] Technology Stack — `httpx`, `beautifulsoup4`/`lxml`, `markdownify`, `pytest`, `ruff`; `uv` for all dev workflows
- [x] Coding Standards — PEP 8, strict type hints, `mypy --strict` passes
- [x] Integration Testing — real Medium, dev.to, and Substack URLs, snapshot-based containment assertions
- [x] Packaging and Distribution — `pyproject.toml` + `src/` layout + `hatchling`; all Makefile targets use `uv run`

---

### Revision: Archival 2026-06-02
- Archived **011-konghq-blog-provider**: added the `KongExtractor` architecture block, `kong.py` to the project-structure tree, and its unit/integration test coverage. No new runtime dependencies. [Source: specs/011-konghq-blog-provider]
- Note: features **007-dzone-provider** (partially present) and **010-boomi-blog-provider** (absent) are not fully archived in this memory plan (gap pre-dating this run).

*Last Updated: 2026-06-02 | Sources appended: [specs/004-remove-backoff/plan.md], [specs/005-substack-provider/plan.md], [specs/006-thenewstack-provider/plan.md], [specs/009-homebrew-tap-formula/plan.md], [specs/011-konghq-blog-provider/plan.md]*
