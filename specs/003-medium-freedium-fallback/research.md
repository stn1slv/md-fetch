# Research: Medium Freedium Fallback

**Branch**: `003-medium-freedium-fallback` | **Date**: 2026-05-14

## Decision 1: Retry Loop and HTTPStatusError Inheritance

**Decision**: Introduce a `_no_retry_status_codes: frozenset[int]` class attribute on `BaseExtractor`; `MediumExtractor` overrides it with `frozenset({403, 429})`.

**Rationale**: `HTTPStatusError` is a subclass of `FetchError`. The current `fetch_html()` retry loop catches all `FetchError` instances — including `HTTPStatusError` — which means 403 and 429 are already retried three times before raising. The spec (FR-001/FR-002) requires immediate fallback on first 403/429 with no retries against `medium.com`. A `_no_retry_status_codes` class attribute lets each provider declare which status codes are terminal (no retry warranted), resolved inside the existing loop with a single `isinstance` check. This is the only path that avoids duplicating the retry logic.

**Alternatives considered**:
- Override `fetch_html()` fully in `MediumExtractor` — rejected because it duplicates the entire retry/backoff logic, violating Constitution I (no code duplication).
- Catch the error after all retries exhaust in `extract()` — rejected because this adds unnecessary backoff latency for 403 (permanent) and 429 (rate-limited) before falling back.
- Add a `no_retry_status_codes` parameter to `fetch_html()` — rejected because it changes the method signature for all callers; a class attribute is cleaner for provider-specific behaviour.

## Decision 2: Fallback Implementation Location

**Decision**: Override `extract()` in `MediumExtractor` to catch `HTTPStatusError` with status in `_no_retry_status_codes`, construct the Freedium URL, and call `fetch_html()` + `clean_html()` + `convert_to_markdown()` on it.

**Rationale**: The fallback is Medium-specific logic. Keeping it in `MediumExtractor.extract()` follows the Open/Closed Principle: `BaseExtractor` is untouched beyond the `_no_retry_status_codes` hook. The full extraction pipeline (fetch → clean → convert) must run on the Freedium HTML, so overriding `extract()` is the right level.

**Alternatives considered**:
- Override `_do_fetch()` to transparently rewrite the URL — rejected because `_do_fetch()` has no knowledge of fallback logic; the override would need to duplicate error-detection logic from `extract()`.
- Return the Freedium URL from a helper called inside the retry loop — rejected because it conflates URL routing with HTTP error handling.

## Decision 3: Freedium URL Construction

**Decision**: `freedium_url = f"https://freedium-mirror.cfd/{original_url}"`

**Rationale**: The Freedium mirror service appends the full original URL as a path segment, including the scheme. This is the standard pattern for Freedium mirrors (e.g., `https://freedium-mirror.cfd/https://medium.com/...`). The original URL is passed as-is without percent-encoding since Freedium expects a human-readable URL.

**Alternatives considered**: Stripping the scheme and prepending `https://` — rejected because the mirror expects the full original URL.

## Decision 4: HTML Structure Compatibility *(updated after live verification)*

**Decision**: Freedium HTML is **structurally incompatible** with `MediumExtractor.clean_html()`. A dedicated `_parse_freedium(soup)` method is required in `MediumExtractor`.

**Finding** (verified by fetching `https://freedium-mirror.cfd/https://stn1slv.medium.com/...`):

| Aspect | medium.com | freedium-mirror.cfd |
|---|---|---|
| Content root | `<article>` | `<div class="main-content">` |
| Section headings | `<h2>` / `<h3>` | `<h4>` |
| Medium-specific attributes | `data-testid`, clap buttons, nav | **None** — content is already clean |
| Stripping needed | Yes (nav, buttons, sidebar, footer) | No — `main-content` contains only article body |

**Impact**: Calling `clean_html()` on Freedium HTML always raises `UnsupportedContentTypeError` because `soup.find("article")` returns `None`. The previous assumption that the HTML structure was compatible was **incorrect**.

**Revised approach**: Add `_parse_freedium(soup: BeautifulSoup) -> str` to `MediumExtractor`:
- Find `soup.find("div", class_="main-content")`
- Raise `UnsupportedContentTypeError` if missing
- Pass directly to `convert_to_markdown()` — no stripping needed
- Note: headings will render as `####` (Freedium uses `<h4>`) rather than `##`/`###` (medium.com uses `<h2>`/`<h3>`). This is an accepted structural difference; content is fully preserved.

**Alternatives considered**:
- Reuse `clean_html()` with a fallback tag search — rejected because `clean_html()` strips elements by Medium-specific `data-testid` attributes that don't exist on Freedium; adding a fallback tag lookup conflates two distinct HTML schemas in one method.
- A unified `clean_html()` that auto-detects the source — rejected because it couples Medium and Freedium parsing logic, making both harder to reason about and test.

## Decision 5: Error Surfaced When Both Sources Fail

**Decision**: When Freedium also fails, raise the exception from the Freedium attempt (`HTTPStatusError`, `FetchError`, or `UnsupportedContentTypeError`). Set `exc.url` to the original Medium URL (not the Freedium URL).

**Rationale**: Setting `exc.url` to the original Medium URL avoids leaking the Freedium mirror as an internal implementation detail, consistent with FR-009 (fully transparent fallback). The exception type from the Freedium attempt is the most actionable signal for the caller.

**Alternatives considered**: Re-raising the original `medium.com` error — rejected because it misrepresents what was last attempted.

## Decision 6: Integration Test Strategy

**Decision**: Add a new `@pytest.mark.integration` test in `test_medium_integration.py` using a known paywalled Medium URL. Verify that `extract()` returns non-empty Markdown containing at least one expected keyword from the article title.

**Rationale**: Full snapshot comparison is inappropriate for Freedium content because heading levels differ from medium.com output (`####` vs `##`). A keyword-presence assertion is stricter than a non-empty check while remaining resilient to structural differences.

**Alternatives considered**: Full snapshot comparison — rejected because Freedium heading levels (`<h4>`) differ from Medium (`<h2>`/`<h3>`), making snapshots immediately stale.
