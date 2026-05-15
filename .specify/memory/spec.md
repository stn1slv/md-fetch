# mdfetch — Main Specification

**Last Updated**: 2026-05-15
**Sources**: [specs/001-mdfetch-medium-extractor/spec.md], [specs/002-devto-provider/spec.md], [specs/003-medium-freedium-fallback/spec.md], [specs/004-remove-backoff/spec.md], [specs/005-substack-provider/spec.md]

---

## Overview

`mdfetch` is a Python library that extracts article content from web platforms and returns it as clean, well-structured Markdown. The library enforces a provider pattern — an abstract base defines the extraction contract, and each supported platform is implemented as a separate, independent provider. Supported platforms: `medium.com` (and subdomains), `dev.to`, `substack.com` (and `*.substack.com` subdomains).

---

## User Stories

### US-001 — Extract a Medium Article to Markdown (P1)
[Source: specs/001-mdfetch-medium-extractor]

A developer retrieves the readable content of a Medium article as clean Markdown by calling a single library function with the article URL. The library handles fetching, isolating the article body, stripping non-content elements, and returning formatted Markdown — with no configuration required.

**Acceptance Scenarios**:
1. Given a valid, publicly accessible Medium article URL, when `extract(url)` is called, then it returns a non-empty Markdown string containing the article's title and at least one paragraph, with no raw HTML tags.
2. Given a valid Medium article URL, the returned Markdown contains no navigation menus, "clap" interaction elements, social sharing buttons, or author biography sections.
3. Given a Medium article with headings, code blocks, and lists, the returned Markdown preserves those structural elements as proper Markdown equivalents (`#`, ` ``` `, `-`).

---

### US-002 — Receive Meaningful Errors for Unsupported or Invalid URLs (P2)
[Source: specs/001-mdfetch-medium-extractor]

A developer passing an unsupported domain, malformed URL, or unreachable page receives a clear, descriptive typed exception.

**Acceptance Scenarios**:
1. Given a URL from a domain other than Medium, `extract()` raises `UnsupportedPlatformError`.
2. Given a syntactically invalid URL string, `extract()` raises `InvalidURLError`.
3. Given a well-formed URL that returns an HTTP error (e.g., 404, 503), `extract()` raises `HTTPStatusError` including the status code.

---

### US-003 — Install and Use via Standard Package Manager (P3)
[Source: specs/001-mdfetch-medium-extractor]

A developer installs `mdfetch` from PyPI with `pip install mdfetch`, imports `extract`, and immediately converts Medium URLs to Markdown with zero configuration.

**Acceptance Scenarios**:
1. `pip install mdfetch` completes without errors and resolves all dependencies automatically.
2. `from mdfetch import extract` succeeds and the function is callable.

---

### US-004 — Extract a dev.to Article to Markdown (P1)
[Source: specs/002-devto-provider]

A developer retrieves the readable content of a dev.to article as clean Markdown by calling the same single library function used for Medium — passing only the article URL, with no additional configuration. The library routes the request to the dev.to provider, fetches the page, isolates the article body, strips all non-content elements, and returns formatted Markdown.

**Acceptance Scenarios**:
1. Given a valid, publicly accessible dev.to article URL, when `extract(url)` is called, then it returns a non-empty Markdown string containing the article's title and at least one paragraph, with no raw HTML tags.
2. Given a valid dev.to article URL, the returned Markdown contains no navigation menus, reaction buttons, comment sections, or author sidebar widgets.
3. Given a dev.to article with headings, code blocks, and lists, the returned Markdown preserves those structural elements as proper Markdown equivalents (`#`, ` ``` `, `-`).

---

### US-005 — Receive Meaningful Errors for Non-Article dev.to Pages (P2)
[Source: specs/002-devto-provider]

A developer passing a dev.to URL that points to a profile page, a tag listing, or a podcast page receives a clear, typed error indicating the dev.to domain is recognised but the page type is not extractable.

**Acceptance Scenarios**:
1. Given a dev.to URL pointing to an author profile page, `extract()` raises `UnsupportedContentTypeError` (domain recognised, content type not extractable).
2. Given a dev.to URL pointing to a tag listing page (e.g., `dev.to/t/kafka`), `extract()` raises `UnsupportedContentTypeError`.
3. Given a URL from a domain other than dev.to, `extract()` raises `UnsupportedPlatformError` (unchanged from existing behaviour).

---

### US-007 — Transparent Fallback on Blocked Medium Article (P1)
[Source: specs/003-medium-freedium-fallback]

A developer calls the library's extract function with a Medium URL. The article is behind a paywall or the user is geo-blocked, causing Medium to return a 403 error. Without any code changes, the library automatically retrieves the same article via the Freedium mirror and returns clean Markdown content.

**Acceptance Scenarios**:
1. Given a valid Medium article URL that returns 403 from medium.com, when `extract()` is called, then the library returns clean Markdown content retrieved via the Freedium mirror.
2. Given a valid Medium article URL that returns 403 from medium.com, when the Freedium mirror also fails, then the library raises an appropriate extraction error with `exc.url` set to the original Medium URL.
3. Given a valid Medium article URL that returns 403 from medium.com, when the library falls back to Freedium, then the caller receives the result without any knowledge of which source was used.

---

### US-008 — Automatic Fallback on Rate Limiting (P2)
[Source: specs/003-medium-freedium-fallback]

A developer calls the library's extract function for a Medium URL. Medium responds with 429 Too Many Requests. The library automatically uses the Freedium mirror as a fallback and returns clean Markdown without requiring the caller to retry.

**Acceptance Scenarios**:
1. Given a valid Medium article URL that returns 429 from medium.com, when `extract()` is called, then the library returns clean Markdown content retrieved via the Freedium mirror.
2. Given a valid Medium article URL that returns 429 from medium.com, when the Freedium mirror also fails, then the library raises an appropriate extraction error.

---

### US-009 — No Fallback When Primary Succeeds (P3)
[Source: specs/003-medium-freedium-fallback]

A developer calls the library's extract function for a publicly accessible Medium article. Medium responds successfully. The library returns the content directly without involving the Freedium mirror, preserving the existing happy-path behavior.

**Acceptance Scenarios**:
1. Given a valid Medium article URL that returns a successful response, when `extract()` is called, then the library returns clean Markdown content without making any request to the Freedium mirror.

---

### US-010 — Predictable Fixed-Delay Retry Behaviour (P1)
[Source: specs/004-remove-backoff]

A developer calling `extract()` encounters a transient network error. The library retries using a simple, predictable fixed delay — exactly `retry_delay` seconds between every attempt — rather than an exponentially growing delay. The retry timing is constant and easy to reason about regardless of which attempt number is being made.

**Acceptance Scenarios**:
1. Given `fetch_html` is called with `retries=3` and `retry_delay=2.0`, when the first two attempts raise a transient error, then the library sleeps exactly `2.0` seconds before each retry (not `2.0` then `4.0`).
2. Given `fetch_html` is called with `retries=1`, when the attempt fails, then no sleep occurs and the exception is raised immediately.
3. Given a status code in `_no_retry_status_codes`, when that error is raised, then no sleep or retry occurs.

---

### US-011 — Extract a Free Substack Article to Markdown (P1)
[Source: specs/005-substack-provider]

A developer calls `extract()` with a free public `*.substack.com/p/...` URL. The function fetches the article and returns its content as clean Markdown — with no subscription banners, navigation menus, author bios, share buttons, or page chrome.

**Acceptance Scenarios**:
1. Given a valid URL pointing to a free public Substack post, when `extract()` is called, then it returns a non-empty Markdown string containing the article title as a top-level heading followed by the body content.
2. Given a Substack post with multiple headings, paragraphs, lists, and inline links, when `extract()` is called, then the returned Markdown preserves all headings, paragraphs, lists, and hyperlinks while stripping subscription CTAs and navigation elements.
3. Given a Substack post containing images, when `extract()` is called, then images appear in the output as Markdown image syntax (`![alt](url)`).

---

### US-012 — Handle a Paywalled Substack Post Gracefully (P2)
[Source: specs/005-substack-provider]

A developer calls `extract()` with a URL for a subscriber-only Substack post. The function returns the visible free-preview content as Markdown without raising an error.

**Acceptance Scenarios**:
1. Given a Substack post that is subscriber-only, when `extract()` is called, then it returns the freely available preview section as Markdown without raising an exception.
2. Given a paywalled post whose free preview contains at least one paragraph, when `extract()` is called, then the output does not contain the paywall call-to-action text (e.g., "Subscribe to read the full post").

---

### US-013 — Reject Non-Article Substack Pages (P3)
[Source: specs/005-substack-provider]

A developer accidentally passes a Substack URL that does not point to an article (e.g., a publication homepage). The function raises a typed exception rather than returning empty or garbage Markdown.

**Acceptance Scenarios**:
1. Given a Substack publication homepage URL, when `extract()` is called, then `UnsupportedContentTypeError` is raised.
2. Given a Substack post whose extractable text is empty after stripping all chrome, when `extract()` is called, then `EmptyContentError` is raised.

---

### US-006 — Integration Tests Pass Against Real dev.to Article URLs (P3)
[Source: specs/002-devto-provider]

A developer runs the integration test suite and all dev.to integration tests pass against three reference articles. The tests confirm title, structural elements, and absence of HTML tags on live content.

**Acceptance Scenarios**:
1. When integration tests for the three reference dev.to URLs execute with a stable internet connection, all three pass without errors or assertion failures.
2. For each reference dev.to article, the extraction function returns non-empty Markdown free of HTML tags and containing recognisable content from the article.

---

## Functional Requirements

### Extraction
- **FR-001**: The library MUST expose a single primary function `extract(url: str) -> str` that accepts a URL string and returns the extracted article content as a Markdown string.
- **FR-002**: The library MUST enforce a provider pattern: a shared abstract base defines the extraction contract, and each supported platform is implemented as a separate, independent provider.
- **FR-003**: The library MUST include a Medium provider that fetches the article page, isolates the main article body, removes all non-content elements (navigation, social sharing widgets, reader interaction components, author biographies), and returns the body as Markdown.
- **FR-008**: The library MUST produce Markdown that preserves the structural hierarchy of the source article, including headings, code blocks, inline code, lists, and blockquotes.
- **FR-011**: The library MUST raise a descriptive error when the article body is located but yields no extractable text content.
- **FR-012**: The library MUST raise a distinct error — separate from the "unsupported platform" error — when a `medium.com` URL is provided but the page is not an article (e.g., an author profile or tag page).
- **FR-013**: The library MUST NOT emit any logging, print output, or diagnostic messages. All failure information is communicated exclusively through raised exceptions.

### Routing
- **FR-004**: The library MUST route extraction requests to the correct provider based on the URL's domain without requiring the caller to specify the provider explicitly. For v1, routing recognises only `medium.com` and its subdomains (e.g., `username.medium.com`).
- **FR-005**: The library MUST raise a descriptive error when given a URL whose domain has no registered provider.
- **FR-007**: The library MUST raise a descriptive error when given a URL that is syntactically invalid.

### Network
- **FR-006**: The library MUST raise a descriptive error when a network request fails (connection error, timeout, non-2xx HTTP status).
- **FR-014**: HTTP requests MUST use a standard browser-like User-Agent string so that web servers return readable HTML. The User-Agent MUST NOT identify the library by name or version. The library does not check or respect `robots.txt` in v1.
- **FR-029**: The `fetch_html` method MUST use a fixed delay of exactly `retry_delay` seconds between retry attempts — no exponential multiplication. The retry delay is constant and does not grow with each attempt number. [Source: specs/004-remove-backoff]

### Packaging & Testing
- **FR-009**: The library MUST be packaged and distributed via PyPI using modern Python packaging best practices, enabling installation through the standard package manager without additional steps.
- **FR-010**: The test suite MUST include integration tests that supply real article URLs (Medium and dev.to) to the extraction function and assert that the output matches expected Markdown structure and content.

### Freedium Fallback (Medium)
- **FR-020**: When a Medium article extraction results in HTTP 403, the system MUST immediately attempt extraction via the Freedium mirror (`https://freedium-mirror.cfd/{url}`) — no retries against medium.com are made first. [Source: specs/003-medium-freedium-fallback]
- **FR-021**: When a Medium article extraction results in HTTP 429, the system MUST immediately attempt extraction via the Freedium mirror — no retries against medium.com are made first. [Source: specs/003-medium-freedium-fallback]
- **FR-022**: When the Freedium mirror is used as a fallback, the system MUST return content in the same clean Markdown format as direct extraction; Freedium's `<h4>` headings are remapped to `<h3>` so both paths produce identical heading-level output. [Source: specs/003-medium-freedium-fallback]
- **FR-023**: When the primary Medium request succeeds (HTTP 200), the system MUST NOT make any request to the Freedium mirror. [Source: specs/003-medium-freedium-fallback]
- **FR-024**: When both the primary Medium request and the Freedium fallback fail, the system MUST raise an error consistent with the existing exception hierarchy; `exc.url` MUST be set to the original Medium URL (never the Freedium URL). [Source: specs/003-medium-freedium-fallback]
- **FR-025**: The Freedium fallback mechanism MUST require no changes to the caller's code — the public `extract()` interface remains unchanged. [Source: specs/003-medium-freedium-fallback]
- **FR-026**: The Freedium fallback MUST only apply to Medium provider URLs; other providers are unaffected. [Source: specs/003-medium-freedium-fallback]
- **FR-027**: The Freedium fallback MUST be unconditionally active for all Medium URL extractions — no caller configuration, opt-in flag, or extractor parameter is required or supported. [Source: specs/003-medium-freedium-fallback]
- **FR-028**: The Freedium fallback MUST be fully transparent to the caller — no warning, signal, metadata, or result field shall indicate which source (medium.com or Freedium) provided the content. [Source: specs/003-medium-freedium-fallback]

### Substack Platform
- **FR-030**: The library MUST route all `substack.com` and `*.substack.com` URLs to the Substack provider using the existing domain-registration mechanism. [Source: specs/005-substack-provider]
- **FR-031**: The library MUST extract the main article body from a Substack post page (`div.body.markup`) and return it as clean Markdown. [Source: specs/005-substack-provider]
- **FR-032**: The library MUST strip all non-content elements from a Substack article page before conversion, including: navigation headers, subscription call-to-action blocks, paywall nag prompts, social share buttons, author bio sections, comment sections, and page footers. [Source: specs/005-substack-provider]
- **FR-033**: The library MUST prepend the article title as a top-level Markdown heading (`# Title`) from `h1.post-title` in `div.post-header`. Because Substack's HTML structure always places the post title outside `div.body.markup`, unconditional prepend achieves exactly-once inclusion. [Source: specs/005-substack-provider]
- **FR-034**: The library MUST preserve the article's structural content: headings (all levels), paragraphs, ordered and unordered lists, inline code, fenced code blocks, blockquotes, hyperlinks, images, and article subtitle (when present as `h3.subtitle` in the post header). [Source: specs/005-substack-provider]
- **FR-035**: The library MUST raise `UnsupportedContentTypeError` when the fetched Substack page does not contain a recognisable article body element (`div.body.markup`). [Source: specs/005-substack-provider]
- **FR-036**: The library MUST raise `EmptyContentError` when the Substack article body is present but yields no extractable text after stripping. [Source: specs/005-substack-provider]
- **FR-037**: For paywalled Substack posts, the library MUST silently extract only the publicly visible free-preview section without raising an exception and without appending any truncation marker, provided the preview contains at least some text. [Source: specs/005-substack-provider]
- **FR-038**: The library MUST collapse runs of three or more consecutive blank lines to a single blank line in the Substack output Markdown. [Source: specs/005-substack-provider]
- **FR-039**: The library MUST NOT treat HTTP 429 responses from Substack as a non-retryable condition; 429 MUST be retried up to the configured retry count with the standard fixed delay. [Source: specs/005-substack-provider]
- **FR-040**: The library MUST convert embedded third-party content in Substack posts (e.g., tweet embeds, YouTube video iframes, and similar rich-media widgets) to plain anchor links using the embed's source URL, matching the pattern used by the dev.to provider. [Source: specs/005-substack-provider]

### dev.to Platform
- **FR-015**: The library MUST add `dev.to` to the provider router so that any URL with the `dev.to` domain is dispatched to the dev.to provider without any change to the caller's code. [Source: specs/002-devto-provider]
- **FR-016**: The library MUST include a dev.to provider that fetches the article page, isolates the main article body from `<div id="article-body">`, removes all non-content elements (navigation, social reaction widgets, comments, author sidebar, tag links), and returns the body as Markdown. [Source: specs/002-devto-provider]
- **FR-017**: The dev.to provider MUST produce Markdown that preserves both the cover image (from the article header) and all inline body images as Markdown image syntax (`![alt](url)`). [Source: specs/002-devto-provider]
- **FR-018**: The dev.to provider MUST raise `UnsupportedContentTypeError` when a `dev.to` URL is provided but the page is not an article (e.g., an author profile, a tag listing, or an organisation page). [Source: specs/002-devto-provider]
- **FR-019**: The dev.to provider MUST replace embedded third-party content (GitHub Gists, CodePen demos, YouTube videos, liquid-tag embeds) with a plain Markdown link to the embedded resource URL. Embeds must not be silently dropped. [Source: specs/002-devto-provider]

---

## Key Entities

### URL (Input)
| Attribute | Type | Description |
|-----------|------|-------------|
| `raw` | `str` | The original string as supplied by the caller |
| `scheme` | `str` | Must be `http` or `https`; any other value triggers `InvalidURLError` |
| `hostname` | `str` | Lowercased hostname used for provider routing (e.g., `medium.com`) |
| `path` | `str` | Used to distinguish article pages from profile/tag pages |

**Validation**: syntactically parseable; scheme must be http/https; hostname must match a registered provider.

### Provider (Internal)
| Attribute | Type | Description |
|-----------|------|-------------|
| `DOMAINS` | `frozenset[str]` | Domain suffixes this provider handles (e.g., `{"medium.com"}`, `{"dev.to"}`) |

**Invariants**: Each domain suffix registered to exactly one provider. Stateless — every call is independent. Registered providers: `MediumExtractor` (medium.com), `DevToExtractor` (dev.to), `SubstackExtractor` (substack.com and all `*.substack.com` subdomains).

### Substack Post
[Source: specs/005-substack-provider]
| Attribute | Type | Description |
|-----------|------|-------------|
| `url` | `str` | A `*.substack.com/p/<slug>` URL (or equivalent custom-domain path) |
| `title` | `str` | Article title from `h1.post-title` in `div.post-header` |
| `subtitle` | `str \| None` | Optional subtitle/deck from `h3.subtitle` in `div.post-header` |
| `body` | `Tag` | Prose content inside `div.body.markup` |

**Validation**: Page must contain `div.body.markup`; absent → `UnsupportedContentTypeError`. Body must yield non-empty text after stripping → else `EmptyContentError`.

### Free Preview
[Source: specs/005-substack-provider]
| Attribute | Type | Description |
|-----------|------|-------------|
| `content` | `str` | Portion of a paywalled post publicly readable without a subscription |

**Boundary**: In the DOM, bounded by the last `div.subscription-widget-wrap` at the truncation point. Stripping that element silently achieves truncation.

### ExtractionResult (Output)
| Attribute | Type | Description |
|-----------|------|-------------|
| `content` | `str` | The extracted article body as Markdown text |

**Validation**: Non-empty string; contains no raw HTML tags; preserves at least one heading or paragraph.

### Exception Hierarchy
```
MdfetchError (base)
├── InvalidURLError             — syntactically invalid URL
├── UnsupportedPlatformError    — domain not recognised by any provider
├── UnsupportedContentTypeError — recognised domain, but page is not an article
├── FetchError                  — network/HTTP failure
│   └── HTTPStatusError         — non-2xx response; carries .status_code (int)
└── EmptyContentError           — article body found but no extractable text
```

All exceptions carry `message: str` and `url: str | None`. `HTTPStatusError` additionally carries `status_code: int`.

---

## Call Lifecycle / State Transitions

```
caller provides URL string
        │
        ▼
[VALIDATE URL] ──── invalid syntax ────► InvalidURLError
        │
        ▼
[ROUTE by domain] ── no provider ──────► UnsupportedPlatformError
        │
        ▼
[FETCH HTML] ─────── network failure ──► FetchError / HTTPStatusError
        │
        ▼
[LOCATE ARTICLE] ─── not an article ───► UnsupportedContentTypeError
        │
        ▼
[CLEAN & CONVERT] ── empty result ─────► EmptyContentError
        │
        ▼
   return str (Markdown)
```

---

## Edge Cases and Error Handling

- **Paywalled content (HTTP 403)**: When Medium returns HTTP 403 (paywall or geo-block), the library automatically retries via the Freedium mirror (`https://freedium-mirror.cfd/`). If Freedium also fails, the error raised carries `exc.url` set to the original Medium URL. [Source: specs/003-medium-freedium-fallback]
- **Freedium mirror unreachable**: If the Freedium mirror returns a network error, timeout, or non-2xx status, the fallback fails and the exception is propagated with `exc.url` set to the original Medium URL — Freedium's URL never appears in `exc.url`.
- **Freedium HTML structure**: Freedium uses `<div class="main-content">` (no `<article>`); if this element is absent, `UnsupportedContentTypeError` is raised with a source-agnostic message ("Fallback page missing main-content element").
- **Freedium heading levels**: Freedium renders section headings as `<h4>` vs. medium.com's `<h2>`/`<h3>`; `_parse_freedium()` remaps h4→h3, h5→h4, h6→h5 before conversion so snapshot tests pass regardless of which source served the content.
- **HTML structure changes**: If Medium changes its HTML structure and `<article>` is absent, `UnsupportedContentTypeError` is raised.
- **Empty article body**: If `<article>` is found but contains no extractable text, `EmptyContentError` is raised.
- **Network timeouts**: Covered by `FetchError` (30-second fixed timeout).
- **Oversized responses**: Responses exceeding 10 MB are rejected with `FetchError` to prevent OOM.
- **Profile/tag pages**: When a `medium.com` URL points to a non-article page, `UnsupportedContentTypeError` is raised (distinct from `UnsupportedPlatformError`).
- **HTTP 403 / transient failures**: Integration tests use 3 retries with a 2-second fixed delay (hardcoded; not env-var configurable) to handle transient rate limits. [Source: specs/004-remove-backoff]
- **dev.to profile pages**: When a `dev.to` URL points to an author profile (no `div#article-body`), `UnsupportedContentTypeError` is raised.
- **dev.to tag listing pages**: When a `dev.to` URL points to a tag page (e.g., `dev.to/t/kafka`), `UnsupportedContentTypeError` is raised.
- **dev.to liquid-tag embeds**: Embedded third-party widgets (GitHub Gists, CodePen, YouTube) serialised as `<div class="ltag__*" data-url="...">` are replaced with plain Markdown links; they are never silently dropped.
- **dev.to cover image**: The cover image lives in `<header class="crayons-article__header">`, not in `div#article-body` — the provider explicitly extracts and prepends it.
- **dev.to HTML structure changes**: If `div#article-body` is absent, `UnsupportedContentTypeError` is raised.
- **Substack paywalled posts**: `div.body.markup` already contains only the free-preview content; stripping `div.subscription-widget-wrap` achieves silent truncation (no error, no marker). [Source: specs/005-substack-provider]
- **Substack homepage URLs**: `div.body.markup` is absent → `UnsupportedContentTypeError` is raised immediately. [Source: specs/005-substack-provider]
- **Substack rich embeds**: `<iframe>` elements and `div[data-component-name]` containers (excluding `SubscribeWidget` and `Image2ToDOM`) are converted to plain anchor links using the embed's source URL. [Source: specs/005-substack-provider]
- **Substack HTTP 429**: Treated as a retryable transient error (no `_no_retry_status_codes` override) — contrasts with `MediumExtractor` which uses `frozenset({403, 429})` to trigger Freedium fallback. [Source: specs/005-substack-provider]
- **Substack HTML structure changes**: If Substack redesigns and removes `div.body.markup`, the extractor will require an update.

---

## Success Criteria

- **SC-001**: A developer can go from installing the library to extracting a real Medium article in fewer than 5 minutes with zero configuration.
- **SC-002**: The extraction function returns a result for a standard Medium article in under 10 seconds on a stable internet connection.
- **SC-003**: The returned Markdown for a standard Medium article contains no raw HTML tags.
- **SC-004**: The returned Markdown for an article with headings, lists, and code blocks preserves all three structural element types in correct Markdown syntax.
- **SC-005**: 100% of integration tests pass against a curated set of real Medium article URLs at the time of initial release.
- **SC-006**: Adding support for a second platform requires creating exactly one new file (one new provider class decorated with `@register`). The router auto-discovers all provider modules at import time; no changes to shared library code are required.
- **SC-007**: A developer already using the library for Medium can extract a dev.to article without any code change — only the URL changes. [Source: specs/002-devto-provider]
- **SC-008**: The extraction function returns a result for a standard dev.to article in under 10 seconds on a stable internet connection. [Source: specs/002-devto-provider]
- **SC-009**: The returned Markdown for any of the three reference dev.to articles contains no raw HTML tags (verified by automated assertion). [Source: specs/002-devto-provider]
- **SC-010**: The returned Markdown for a dev.to article with headings, lists, and code blocks preserves all three structural element types in correct Markdown syntax. [Source: specs/002-devto-provider]
- **SC-011**: 100% of integration tests pass against the three provided reference dev.to article URLs at the time of release. [Source: specs/002-devto-provider]
- **SC-012**: The dev.to provider is delivered as exactly one new file; no existing source files are modified (except `test_router.py` for expected domain-example maintenance when the provider registers `dev.to`). [Source: specs/002-devto-provider]

- **SC-021**: A free public Substack article returns Markdown that contains the full article title and body text with zero subscription prompt phrases (e.g., "Subscribe", "This post is for paid subscribers"). [Source: specs/005-substack-provider]
- **SC-022**: A paywalled Substack post returns a non-empty Markdown string (the free preview) without raising an exception, provided the free preview contains at least one paragraph. [Source: specs/005-substack-provider]
- **SC-023**: A Substack homepage URL raises `UnsupportedContentTypeError` within the normal fetch timeout. [Source: specs/005-substack-provider]
- **SC-024**: The extracted Markdown for any Substack article contains no consecutive blank-line runs of three or more lines. [Source: specs/005-substack-provider]
- **SC-025**: The Substack provider is exercised by at least one integration test using a real network request, matching the pattern established by existing providers. [Source: specs/005-substack-provider]

---

## Assumptions

- The library targets developers as its primary users; no graphical interface or configuration file is required.
- Medium articles used in integration testing are publicly accessible (not behind a paywall).
- No response caching; each call performs a fresh network request.
- Rate limiting or authentication with Medium's servers is out of scope for v1.
- The library supports Python 3.12 and later.
- The library operates on publicly accessible HTML; it does not execute JavaScript or render dynamic content.
- Network timeouts use a fixed default of 30 seconds (not user-configurable in v1).
- **SC-018**: `make test` passes with zero failures (all unit tests green) when run without any `MDFETCH_*` environment variables. [Source: specs/004-remove-backoff]
- **SC-019**: `make integration` passes with zero failures when run without any `MDFETCH_RETRIES` or `MDFETCH_RETRY_DELAY` environment variables — integration tests use hardcoded defaults (3 retries, 2.0 s delay). [Source: specs/004-remove-backoff]
- **SC-020**: No reference to `MDFETCH_RETRIES`, `MDFETCH_RETRY_DELAY`, or `_MAX_RETRY_DELAY` appears in `src/`, `tests/`, or `.github/` (specification and documentation files excluded). [Source: specs/004-remove-backoff]
- **SC-013**: Articles that previously failed with a 403 paywall error are successfully extracted in at least 90% of cases where the Freedium mirror has the content available. [Source: specs/003-medium-freedium-fallback]
- **SC-014**: Articles that previously failed with a 429 rate-limit error are successfully extracted via fallback without requiring the caller to retry. [Source: specs/003-medium-freedium-fallback]
- **SC-015**: Zero changes are required in existing caller code to benefit from the Freedium fallback — existing integrations continue to work as-is. [Source: specs/003-medium-freedium-fallback]
- **SC-016**: When the primary Medium request succeeds, there is no additional latency attributable to the fallback mechanism. [Source: specs/003-medium-freedium-fallback]
- **SC-017**: All existing unit and integration tests for the Medium extractor continue to pass without modification after the fallback is introduced. [Source: specs/003-medium-freedium-fallback]

---

*Last Updated: 2026-05-15 | Sources appended: [specs/004-remove-backoff/spec.md], [specs/005-substack-provider/spec.md]*
