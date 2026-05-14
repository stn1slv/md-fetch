# Research: mdfetch — Medium Extractor

**Phase**: 0 | **Date**: 2026-05-14 | **Plan**: [plan.md](plan.md)

## R-001: HTTP Client Selection

**Decision**: Use `httpx` (sync interface) as the HTTP client.

**Rationale**: The constitution permits `httpx` or `requests`. `httpx` is the more modern choice: it supports both sync and async out of the box, has a cleaner API for setting headers and timeouts, and requires no additional packages to enable HTTP/2. For v1 (sync-only), the interface difference from `requests` is minimal, but `httpx` leaves the door open for an async-enabled v2 without swapping the dependency.

**Alternatives considered**:
- `requests` — mature and ubiquitous, but sync-only; would require `httpx` later if async is added
- `aiohttp` — async-only; not appropriate for a sync-first library

**Usage pattern**:
```python
import httpx

with httpx.Client(timeout=30.0) as client:
    response = client.get(url)
    response.raise_for_status()
    return response.text
```

---

## R-002: Medium HTML Structure and Article Targeting

**Decision**: Target the `<article>` element as the primary article body container. Fall back to `<div>` elements with Medium-specific section roles if `<article>` is absent.

**Rationale**: Medium renders article content inside a single `<article>` tag in its server-side HTML. This is the most stable selector: it is a semantic HTML5 element, unlikely to be repurposed, and has been consistent across Medium's HTML output for several years.

**Targeting strategy**:
1. Parse full page HTML with BeautifulSoup (`lxml` parser for speed and tolerance)
2. Call `soup.find("article")` to locate the article container
3. If `None`, raise `UnsupportedContentTypeError` (page is not an article — profile, tag page, etc.)

**Elements to remove before conversion** (applied to the located `<article>` element):
| Element type | Selector / description |
|---|---|
| Navigation menus | `<nav>` tags anywhere in the article tree |
| Social sharing buttons | `<div>` / `<button>` elements with `data-testid` containing `"share"` or class containing `"share"` |
| Clap / reaction components | `<button>` elements with `aria-label` containing `"clap"` or `"applaud"`; `<div>` with `data-testid="post-sidebar"` |
| Author biography | `<div>` elements after the article body that contain author metadata; typically `<section>` with class pattern matching `"author"` |
| Response / comment prompts | `<div>` elements with `data-testid` matching `"response-sidenav"` or `"post-footer"` |
| Membership / paywall banners | `<div>` elements with `data-testid="overflow-menu"` or class patterns matching `"paywall"` |

**Alternatives considered**:
- Targeting by CSS class — Medium obfuscates class names; these change with each deploy and are not stable selectors
- Targeting by `data-testid` for the body — Medium uses `data-testid="post-content"` but this is less semantically stable than `<article>`

---

## R-003: Markdownify Configuration

**Decision**: Use `markdownify.markdownify()` with ATX-style headings and code fencing enabled.

**Rationale**: `markdownify` converts BeautifulSoup-parsed or raw HTML strings to Markdown. ATX headings (`#`, `##`) are the most widely supported Markdown style. Code fencing (` ``` `) is required by FR-008 to preserve code block structure.

**Configuration**:
```python
from markdownify import markdownify as md

markdown_output = md(
    str(cleaned_html_element),
    heading_style="ATX",       # # Heading style
    code_language="",          # no auto language detection; leave fences bare
    strip=["script", "style"], # belt-and-suspenders strip of any remaining noise
)
```

**Post-processing**: Strip leading/trailing blank lines; collapse runs of 3+ blank lines to 2.

**Alternatives considered**:
- `html2text` — older library; less configurable; produces inconsistent output for nested lists
- Manual regex replacement — fragile and unmaintainable

---

## R-004: Python Packaging (pyproject.toml + src/ layout)

**Decision**: Use `hatchling` as the build backend with `pyproject.toml`; package source under `src/mdfetch/`.

**Rationale**: `hatchling` is the default build backend for modern Python projects, requires zero additional config for a `src/` layout, and is recommended by the Python Packaging Authority. The `src/` layout prevents accidental imports of the local development tree during testing.

**Minimum pyproject.toml structure**:
```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "mdfetch"
version = "0.1.0"
description = "Extract Medium articles as clean Markdown"
requires-python = ">=3.10"
dependencies = [
    "httpx>=0.27",
    "beautifulsoup4>=4.12",
    "lxml>=5.0",
    "markdownify>=0.13",
]

[project.optional-dependencies]
dev = ["pytest>=8.0", "pytest-httpx>=0.30"]

[tool.hatch.build.targets.wheel]
packages = ["src/mdfetch"]

[tool.pytest.ini_options]
testpaths = ["tests"]
```

**Alternatives considered**:
- `setuptools` with `setup.cfg` — still widely used but more verbose; `hatchling` is simpler for this scope
- `flit` — minimal but lacks flexibility for future optional dependencies

---

## R-005: Exception Hierarchy Design

**Decision**: Define a hierarchy of custom exceptions all inheriting from a single base `MdfetchError`.

**Rationale**: A common base exception lets callers catch all library errors with a single `except MdfetchError` while still allowing fine-grained handling of specific cases. Each exception type maps directly to an FR.

**Hierarchy**:
```
MdfetchError                    # Base for all library errors
├── InvalidURLError             # FR-007: URL is syntactically invalid
├── UnsupportedPlatformError    # FR-005: domain not recognised by any provider
├── UnsupportedContentTypeError # FR-012: recognised domain, but page is not an article
├── FetchError                  # FR-006: network/HTTP failure (wraps httpx exceptions)
│   └── HTTPStatusError         # non-2xx HTTP response (subclass with .status_code)
└── EmptyContentError           # FR-011: article body found but no extractable text
```

**Alternatives considered**:
- Reusing built-in exceptions (`ValueError`, `RuntimeError`) — loses type-safety and discoverability for callers building on the library

---

## R-006: Integration Test Strategy

**Decision**: Maintain a small curated list (3–5) of stable, publicly accessible Medium article URLs as integration test fixtures. Tests assert structural Markdown properties, not exact string equality.

**Rationale**: Exact string matching would make tests fragile against Medium's minor HTML updates. Asserting structural properties (presence of `#` headings, absence of HTML tags, non-empty output) gives meaningful coverage without brittleness.

**Assert patterns**:
- Output is a non-empty string
- Output contains no raw HTML tags (regex: `<[a-zA-Z][^>]*>`)
- Output contains at least one ATX heading (`# ` prefix)
- Output length > 200 characters (guards against near-empty extractions)

**Test fixture format**:
```python
MEDIUM_TEST_URLS = [
    "https://medium.com/...",   # article with headings + code blocks
    "https://medium.com/...",   # article with lists
]
```

**Network isolation**: Integration tests are marked with a custom `@pytest.mark.integration` marker and excluded from the default `pytest` run (run explicitly with `-m integration`). This keeps the unit test suite fast and offline-capable.
