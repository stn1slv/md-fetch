# mdfetch — Main Implementation Plan

**Last Updated**: 2026-05-14
**Sources**: [specs/001-mdfetch-medium-extractor/plan.md]

---

## Technical Context

**Language/Version**: Python 3.10+

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

**Target Platform**: Cross-platform PyPI library (Linux, macOS, Windows); Python 3.10+

**Project Type**: library

---

## Architecture

### Provider Pattern

```
BaseExtractor (ABC)               — src/mdfetch/base.py
├── fetch_html(url) → str         — concrete: streaming HTTP with 30s timeout, 10 MB cap
├── clean_html(soup) → Tag        — abstract: platform-specific HTML isolation
├── convert_to_markdown(tag) → str— abstract: platform-specific Markdown conversion
└── extract(url) → str            — concrete template method (orchestrates the above)

MediumExtractor(BaseExtractor)    — src/mdfetch/providers/medium.py
├── DOMAINS = frozenset({"medium.com"})
├── clean_html() → removes nav, clap buttons, sidebars, share elements, post-footer, author bio
└── convert_to_markdown() → markdownify with ATX headings, fenced code blocks
```

### Router / Auto-Discovery

```
router.py
├── _REGISTRY: dict[str, type[BaseExtractor]]
├── @register decorator          — self-enrolls provider at class definition time
├── _autodiscover_providers()    — pkgutil.iter_modules scans mdfetch/providers/ at import
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
    ├── base.py              # BaseExtractor ABC + fetch_html() + extract() template
    └── providers/
        ├── __init__.py      # Empty — auto-discovery handles registration
        └── medium.py        # MediumExtractor

tests/
├── unit/
│   ├── test_router.py
│   ├── test_medium_extractor.py
│   ├── test_fetch_errors.py
│   └── test_silent.py
└── integration/
    ├── snapshots/           # Golden Markdown files (article body snapshots)
    │   ├── from-drift-to-parity.md
    │   ├── architecting-the-asynchronous-agent.md
    │   └── integration-digest-december-2025.md
    └── test_medium_integration.py

specs/                       # Speckit feature specifications
pyproject.toml               # hatchling build backend, uv package manager
Makefile                     # setup / test / integration / lint / typecheck / format / build / clean / upgrade-deps
```

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

**Unit tests** (30 tests, offline):
- Router: domain routing, subdomain suffix matching, duplicate registration, invalid URLs, unsupported platforms
- MediumExtractor: clean_html, convert_to_markdown, empty content, non-article pages
- Fetch errors: HTTP 404, 503, timeout, connection error, size limit exceeded
- Silent: no stdout/stderr output, no logging during extraction

**Integration tests** (3 tests, network required):
- Parametrized over 3 real stn1slv.medium.com articles
- Snapshot-based containment check: `expected_body in extracted_result`
- 3 retries with 2-second delay on `FetchError` (covers transient 403s/timeouts)
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
| Article targeting | `<article>` element | Stable semantic HTML5; consistent across Medium versions |
| Markdown converter | `markdownify` with ATX + `code_language=""` | Fenced code blocks, standard headings |
| Routing | `pkgutil.iter_modules` auto-discovery + `@register` | SC-006: one new file = one new platform |
| Integration tests | Snapshot containment + retry | Durable against minor HTML changes; resilient to transient 403s |

---

## Constitution Compliance

- [x] Provider Pattern Architecture — `BaseExtractor` ABC with concrete `fetch_html` and abstract `clean_html`, `convert_to_markdown`; `MediumExtractor` inherits
- [x] Technology Stack — `httpx`, `beautifulsoup4`/`lxml`, `markdownify`, `pytest`, `ruff`; `uv` for all dev workflows
- [x] Coding Standards — PEP 8, strict type hints, `mypy --strict` passes
- [x] Integration Testing — real Medium URLs, snapshot-based containment assertions
- [x] Packaging and Distribution — `pyproject.toml` + `src/` layout + `hatchling`; all Makefile targets use `uv run`
