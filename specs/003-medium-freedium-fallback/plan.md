# Implementation Plan: Medium Freedium Fallback

**Branch**: `003-medium-freedium-fallback` | **Date**: 2026-05-14 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/003-medium-freedium-fallback/spec.md`

## Summary

Add transparent fallback to the Freedium mirror (`https://freedium-mirror.cfd/`) within `MediumExtractor` when `medium.com` returns HTTP 403 or 429. On these status codes the fallback is immediate (no retries against `medium.com` first). The public `extract()` interface is unchanged. The implementation requires a minimal extension to `BaseExtractor` (a `_no_retry_status_codes` class attribute) and an override of `extract()` in `MediumExtractor`.

## Technical Context

**Language/Version**: Python 3.12–3.14

**Primary Dependencies**: httpx ≥0.27, beautifulsoup4 ≥4.12, lxml ≥5.0, markdownify ≥0.13 — all existing; no new runtime dependencies

**Storage**: N/A

**Testing**: pytest with `@pytest.mark.integration` marker for network tests

**Target Platform**: Any (Python library distributed via PyPI)

**Project Type**: library

**Performance Goals**: Zero added latency on successful primary fetch; fallback adds exactly one additional HTTP roundtrip

**Constraints**: Public `extract(url, *, retries, retry_delay)` signature unchanged; no new runtime dependencies; all existing tests must pass unmodified

**Scale/Scope**: Per-call behaviour change within `MediumExtractor`; no state, no storage. Thread-safe by design: `_no_retry_codes` override is passed as a parameter to `fetch_html()` rather than mutating instance state.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- [x] Validates Provider Pattern Architecture — changes confined to `MediumExtractor` plus one minimal hook in `BaseExtractor`; no code duplication
- [x] Confirms Technology Stack — httpx (existing), BeautifulSoup (existing); no new deps
- [x] Adheres to Coding Standards — PEP 8, strict type hints, clear naming required throughout
- [x] Incorporates Integration Testing — new `@pytest.mark.integration` test for paywalled URL via Freedium
- [x] Respects Packaging and Distribution standards — `pyproject.toml` + `src/` layout unchanged; all Makefile targets delegate to `uv run`

**Post-design re-check**: All gates remain green. No violations requiring justification.

## Project Structure

### Documentation (this feature)

```text
specs/003-medium-freedium-fallback/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── contracts/
│   └── extract-api.md   # Phase 1 output — public extract() contract
└── tasks.md             # Phase 2 output (/speckit-tasks command)
```

### Source Code (repository root)

No new files. Changes to existing files only:

```text
src/mdfetch/
├── base.py                    # Add _no_retry_status_codes + loop guard
└── providers/
    └── medium.py              # Add _parse_freedium(); override _no_retry_status_codes + extract()

tests/
├── unit/
│   ├── test_fetch_errors.py   # Add tests: 403/429 not retried for MediumExtractor
│   └── test_medium_extractor.py  # Add tests: _parse_freedium(), fallback URL + 403/429 paths
└── integration/
    └── test_medium_integration.py  # Add test: paywalled URL succeeds via Freedium (keyword assertion)
```

**Structure Decision**: Single project layout unchanged; all changes are surgical modifications to existing files.

## Phase 0: Research

See [research.md](research.md) for full rationale. Key decisions:

| Topic | Decision |
|---|---|
| Preventing retries on 403/429 | Add `_no_retry_status_codes: frozenset[int] = frozenset()` to `BaseExtractor`; override with `frozenset({403, 429})` in `MediumExtractor` |
| Fallback implementation location | Override `extract()` in `MediumExtractor` |
| Freedium URL construction | `f"https://freedium-mirror.cfd/{original_url}"` |
| HTML parsing | Freedium uses `<div class="main-content">` — **incompatible** with `clean_html()` which requires `<article>`; add dedicated `_parse_freedium(soup)` method to `MediumExtractor` |
| Error when both fail | Raise `HTTPStatusError`/`FetchError` from Freedium attempt; set `exc.url` to original Medium URL |
| Integration test | Snapshot containment assertion (`expected in result`) — paywalled URL covered by existing snapshot test suite; dedicated keyword-only test removed as redundant |

## Phase 1: Design & Contracts

### BaseExtractor changes (`src/mdfetch/base.py`)

Add class attribute:
```python
_no_retry_status_codes: frozenset[int] = frozenset()
```

Also add a `_no_retry_codes` keyword-only parameter to `fetch_html()` so callers can pass a per-call override without mutating instance state (used for the Freedium fetch):

```python
def fetch_html(
    self,
    url: str,
    *,
    retries: int = 3,
    retry_delay: float = 2.0,
    _no_retry_codes: frozenset[int] | None = None,
) -> str: ...
```

In the retry loop, resolve the effective set before the loop:
```python
no_retry = self._no_retry_status_codes if _no_retry_codes is None else _no_retry_codes
# ...
except FetchError as exc:
    if isinstance(exc, HTTPStatusError) and exc.status_code in no_retry:
        raise
    last_exc = exc
    if attempt < retries - 1:
        time.sleep(...)
```

These are the only changes to `base.py`. The attribute is empty by default, so all existing providers and tests are unaffected.

### MediumExtractor changes (`src/mdfetch/providers/medium.py`)

**Verified finding**: Freedium HTML uses `<div class="main-content">` as the content root — no `<article>` element exists. The existing `clean_html()` always raises `UnsupportedContentTypeError` on Freedium HTML. A dedicated parser method is required.

Add two class-level constants, a new `_parse_freedium()` method, and override `extract()`:

```python
_FREEDIUM_BASE = "https://freedium-mirror.cfd/"
_no_retry_status_codes: frozenset[int] = frozenset({403, 429})

def _parse_freedium(self, soup: BeautifulSoup) -> str:
    """Parse Freedium mirror HTML, which uses div.main-content instead of <article>."""
    content = soup.find("div", class_="main-content")
    if not isinstance(content, Tag):
        raise UnsupportedContentTypeError(
            "Fallback page missing main-content element",
        )
    # Remap h4→h3, h5→h4, h6→h5 so output matches medium.com's heading levels
    for level in (4, 5, 6):
        for tag in list(content.find_all(f"h{level}")):
            tag.name = f"h{level - 1}"
    return self.convert_to_markdown(content)

def extract(self, url: str, *, retries: int = 3, retry_delay: float = 2.0) -> str:
    """Extract article, falling back to Freedium mirror on HTTP 403 or 429."""
    try:
        return super().extract(url, retries=retries, retry_delay=retry_delay)
    except HTTPStatusError as exc:
        if exc.status_code not in self._no_retry_status_codes:
            raise
    freedium_url = f"{self._FREEDIUM_BASE}{url}"
    # Pass _no_retry_codes=frozenset() so a 429 from Freedium is retried
    # with backoff rather than raised immediately (thread-safe: no mutation).
    try:
        html = self.fetch_html(
            freedium_url, retries=retries, retry_delay=retry_delay, _no_retry_codes=frozenset()
        )
        soup = BeautifulSoup(html, "lxml")
        return self._parse_freedium(soup)
    except MdfetchError as inner_exc:
        inner_exc.url = url
        raise
```

Notes:
- `HTTPStatusError` and `MdfetchError` imported in `medium.py`
- `_parse_freedium()` skips all Medium-specific stripping — Freedium's `main-content` div contains only article body
- Error message in `UnsupportedContentTypeError` is source-agnostic ("Fallback page…") to preserve transparent-fallback contract (FR-009)
- `exc.url` is set unconditionally to the original URL (not guarded by `is None`) — ensures the Freedium URL never escapes to callers regardless of which exception type is raised
- `_no_retry_codes=frozenset()` on the Freedium fetch prevents class-level 429 no-retry behavior from suppressing retries against the mirror (thread-safe: no instance mutation)

### Data Model

No new entities. This feature is a pure behaviour change with no persistent state.

### Contracts

See [contracts/extract-api.md](contracts/extract-api.md). The public `extract()` signature is unchanged. The Freedium URL is a fully internal implementation detail — never exposed through any public interface or exception message visible to callers.

### Revision: Implementation Sync 2026-05-15
- Code snippets updated to reflect shipped implementation: `_no_retry_codes` parameter on `fetch_html()`, heading remap in `_parse_freedium()`, unconditional `exc.url` assignment, source-agnostic error message ("Fallback page…"), thread-safe Freedium fetch via parameter override.
- Integration test strategy updated: keyword-only paywalled test removed; paywalled URL is covered by snapshot containment test.
- Scale/Scope updated: concurrency safety now explicitly documented.
