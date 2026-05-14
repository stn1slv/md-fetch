# mdfetch — Main Specification

**Last Updated**: 2026-05-14
**Sources**: [specs/001-mdfetch-medium-extractor/spec.md]

---

## Overview

`mdfetch` is a Python library that extracts article content from web platforms and returns it as clean, well-structured Markdown. The library enforces a provider pattern — an abstract base defines the extraction contract, and each supported platform is implemented as a separate, independent provider. The initial release supports `medium.com` and its subdomains only.

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

### Packaging & Testing
- **FR-009**: The library MUST be packaged and distributed via PyPI using modern Python packaging best practices, enabling installation through the standard package manager without additional steps.
- **FR-010**: The test suite MUST include integration tests that supply real Medium article URLs to the extraction function and assert that the output matches expected Markdown structure and content.

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
| `DOMAINS` | `frozenset[str]` | Domain suffixes this provider handles (e.g., `{"medium.com"}`) |

**Invariants**: Each domain suffix registered to exactly one provider. Stateless — every call is independent.

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

- **Paywalled content**: If Medium gates content behind a paywall and the body is not in the public HTML, the library may return an `EmptyContentError` or a reduced extraction. Full paywall bypass is out of scope for v1.
- **HTML structure changes**: If Medium changes its HTML structure and `<article>` is absent, `UnsupportedContentTypeError` is raised.
- **Empty article body**: If `<article>` is found but contains no extractable text, `EmptyContentError` is raised.
- **Network timeouts**: Covered by `FetchError` (30-second fixed timeout).
- **Oversized responses**: Responses exceeding 10 MB are rejected with `FetchError` to prevent OOM.
- **Profile/tag pages**: When a `medium.com` URL points to a non-article page, `UnsupportedContentTypeError` is raised (distinct from `UnsupportedPlatformError`).
- **HTTP 403 / transient failures**: Integration tests use a 3-retry helper with 2-second delay to handle transient rate limits.

---

## Success Criteria

- **SC-001**: A developer can go from installing the library to extracting a real Medium article in fewer than 5 minutes with zero configuration.
- **SC-002**: The extraction function returns a result for a standard Medium article in under 10 seconds on a stable internet connection.
- **SC-003**: The returned Markdown for a standard Medium article contains no raw HTML tags.
- **SC-004**: The returned Markdown for an article with headings, lists, and code blocks preserves all three structural element types in correct Markdown syntax.
- **SC-005**: 100% of integration tests pass against a curated set of real Medium article URLs at the time of initial release.
- **SC-006**: Adding support for a second platform requires creating exactly one new file (one new provider class decorated with `@register`). The router auto-discovers all provider modules at import time; no changes to shared library code are required.

---

## Assumptions

- The library targets developers as its primary users; no graphical interface or configuration file is required.
- Medium articles used in integration testing are publicly accessible (not behind a paywall).
- No response caching; each call performs a fresh network request.
- Rate limiting or authentication with Medium's servers is out of scope for v1.
- The library supports Python 3.12 and later.
- The library operates on publicly accessible HTML; it does not execute JavaScript or render dynamic content.
- Network timeouts use a fixed default of 30 seconds (not user-configurable in v1).
