# mdfetch — Main Specification

**Last Updated**: 2026-05-16
**Sources**: [specs/001-mdfetch-medium-extractor/spec.md], [specs/002-devto-provider/spec.md], [specs/003-medium-freedium-fallback/spec.md], [specs/004-remove-backoff/spec.md], [specs/005-substack-provider/spec.md], [specs/006-thenewstack-provider/spec.md]

---

## Overview

`mdfetch` is a Python library that extracts article content from web platforms and returns it as clean, well-structured Markdown. The library enforces a provider pattern — an abstract base defines the extraction contract, and each supported platform is implemented as a separate, independent provider. Supported platforms: `medium.com` (and subdomains), `dev.to`, `substack.com` (and `*.substack.com` subdomains), `thenewstack.io`.

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

### US-014 — Extract a Public thenewstack.io Article to Markdown (P1)
[Source: specs/006-thenewstack-provider]

A developer calls `extract()` with a thenewstack.io article URL. The function fetches the article and returns its content as clean Markdown, with no navigation menus, subscription banners, poll widgets, author bios, social share buttons, related articles sections, or any other page chrome.

**Acceptance Scenarios**:
1. Given a valid URL pointing to a public thenewstack.io article, when `extract()` is called, then it returns a non-empty Markdown string containing the article title as a top-level heading followed by the body content.
2. Given a thenewstack.io article with multiple headings, paragraphs, lists, and inline links, when `extract()` is called, then the returned Markdown preserves all headings, paragraphs, lists, code blocks, and hyperlinks while stripping navigation, subscription CTAs, poll widgets, and social share buttons.
3. Given a thenewstack.io article containing images, when `extract()` is called, then images appear in the output as Markdown image syntax (`![alt](url)`).

---

### US-015 — Reject Non-Article thenewstack.io Pages (P2)
[Source: specs/006-thenewstack-provider]

A developer passes a thenewstack.io URL that does not point to an article (e.g., the homepage, a category listing page, or a tag archive). The function raises a typed exception rather than returning empty or garbage Markdown.

**Acceptance Scenarios**:
1. Given the thenewstack.io homepage URL, when `extract()` is called, then `UnsupportedContentTypeError` is raised.
2. Given a thenewstack.io category/tag listing page URL, when `extract()` is called, then `UnsupportedContentTypeError` is raised.
3. Given an article page whose extractable body text is empty after stripping all chrome, when `extract()` is called, then `EmptyContentError` is raised.

---

### US-016 — Install md-fetch via Homebrew (P1)
[Source: specs/009-homebrew-tap-formula]

A macOS or Linux developer who does not want to manage a Python environment installs the `md-fetch` CLI using a single Homebrew command. After installation, the `md-fetch` binary is immediately available on the PATH without any additional configuration.

**Acceptance Scenarios**:
1. Given a macOS or Linux machine with Homebrew installed, when the user runs `brew install stn1slv/tap/md-fetch`, then the installation completes without errors and `md-fetch` is available on the PATH.
2. Given a successful installation, when the user runs `md-fetch --version`, then the command exits with code 0 and outputs the installed package version.
3. Given a successful installation, when the user runs `md-fetch <url>` with a supported URL, then the command returns Markdown output, confirming all dependencies are correctly bundled.
4. Given an existing installation, when the user runs `brew upgrade stn1slv/tap/md-fetch`, then the installation upgrades to the latest published version.

---

### US-017 — Formula Stays in Sync with PyPI Releases (P2)
[Source: specs/009-homebrew-tap-formula]

When a new version of `md-fetch` is published to PyPI, the Homebrew formula in `stn1slv/homebrew-tap` is updated automatically without any manual intervention from the maintainer. Users running `brew upgrade` receive the new version promptly.

**Acceptance Scenarios**:
1. Given a new version is successfully published to PyPI, when the release pipeline completes, then the formula in `stn1slv/homebrew-tap` reflects the new version number and correct integrity checksum.
2. Given a new version is successfully published to PyPI, when the release pipeline completes, then the tap update is committed and pushed without any manual step from the maintainer.
3. Given the automated tap update fails (e.g., token invalid, network error), when the pipeline completes, then the failure is reported as a visible CI job failure.
4. Given a published package, when a user on the previous formula version runs `brew upgrade`, then they receive the newly published version.

---

### US-018 — Discover Homebrew Installation via Documentation (P3)
[Source: specs/009-homebrew-tap-formula]

A new user reading the project README discovers that Homebrew is an installation option on macOS and can install `md-fetch` without reading further instructions.

**Acceptance Scenarios**:
1. Given the updated README, when a user visits the install section, then `brew install stn1slv/tap/md-fetch` is present as an installation option below the existing `pip install mdfetch` instruction.
2. Given the README install section, when a user follows the brew instruction verbatim, then the installation succeeds.

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

### The New Stack Platform
- **FR-041**: The library MUST route all `thenewstack.io` URLs to the TheNewStack provider using the existing domain-registration mechanism (`@register` decorator + `DOMAINS` frozenset). [Source: specs/006-thenewstack-provider]
- **FR-042**: The library MUST extract the main article body from a thenewstack.io page (`div#tns-post-body-content`) and return it as clean Markdown. [Source: specs/006-thenewstack-provider]
- **FR-043**: The library MUST strip all non-content elements from within the article body before Markdown conversion, including: sponsored content disclosures (`div.sponsored-post-disclosure`, `div.tns-sponsored-post-disclosure`, `div.sponsor-disclosure`) and injected sponsor notes (`div.tns-sponsor-note`). Navigation, VoxPop polls, social buttons, related posts, sidebar, and footer are outside the body container and require no explicit stripping. [Source: specs/006-thenewstack-provider]
- **FR-044**: The library MUST prepend the article title as a top-level Markdown heading (`# Title`) from `h1.title` in `div#tns-post-headline`, followed immediately by the article deck/subtitle as a plain paragraph (from `div.post-excerpt` in `div#tns-post-headline`) when one is present. [Source: specs/006-thenewstack-provider]
- **FR-045**: The library MUST preserve the thenewstack.io article's structural content: headings (all levels), paragraphs, ordered and unordered lists, inline code, fenced code blocks, blockquotes, hyperlinks, and images. [Source: specs/006-thenewstack-provider]
- **FR-046**: The library MUST raise `UnsupportedContentTypeError` when the fetched thenewstack.io page does not contain a recognisable article body element (`div#tns-post-body-content`). [Source: specs/006-thenewstack-provider]
- **FR-047**: The library MUST raise `EmptyContentError` when the thenewstack.io article body is present but yields no extractable text after stripping. [Source: specs/006-thenewstack-provider]
- **FR-048**: The library MUST collapse runs of three or more consecutive blank lines to a single blank line in the thenewstack.io output Markdown. [Source: specs/006-thenewstack-provider]
- **FR-049**: The library MUST convert embedded third-party content (e.g., YouTube video iframes) in thenewstack.io articles to plain anchor links using the embed's source URL, discarding the embed wrapper — matching the pattern used by existing providers. [Source: specs/006-thenewstack-provider]
- **FR-050**: The library MUST treat sponsored and native-advertising thenewstack.io article pages identically to editorial articles — extracting content as-is with no special detection, marking, or rejection. [Source: specs/006-thenewstack-provider]

### Homebrew Distribution
- **FR-051**: A Homebrew formula for the `md-fetch` package MUST be available in the `stn1slv/homebrew-tap` repository so that users can install the tool with standard Homebrew commands. [Source: specs/009-homebrew-tap-formula]
- **FR-052**: The formula MUST install a working `md-fetch` binary into Homebrew's `bin/` directory, making it immediately available on the user's PATH after installation. [Source: specs/009-homebrew-tap-formula]
- **FR-053**: The formula MUST bundle all runtime dependencies so that no external Python environment or manual dependency installation is required. [Source: specs/009-homebrew-tap-formula]
- **FR-054**: The formula MUST include a `brew test` block that verifies the installed binary runs successfully (`md-fetch --version` exits with code 0). [Source: specs/009-homebrew-tap-formula]
- **FR-055**: When a new version is published to PyPI, the release pipeline MUST automatically update the formula with the new version and correct integrity checksum. The checksum fetch MUST retry up to 3 times with 30-second intervals before failing. [Source: specs/009-homebrew-tap-formula]
- **FR-056**: The automated formula update MUST commit and push to `stn1slv/homebrew-tap` using a dedicated fine-grained PAT (`Contents: read+write` on that repository only). [Source: specs/009-homebrew-tap-formula]
- **FR-057**: If the automated formula update step fails for any reason, the failure MUST surface as a failed CI job, preventing silent divergence between PyPI and Homebrew. [Source: specs/009-homebrew-tap-formula]
- **FR-058**: The project README MUST include the `brew install stn1slv/tap/md-fetch` command as a secondary install option beneath `pip install mdfetch`. [Source: specs/009-homebrew-tap-formula]
- **FR-059**: The `TAP_GITHUB_TOKEN` secret (a fine-grained PAT with `Contents: read+write` on `stn1slv/homebrew-tap`) must be documented as a required repository secret for the automation to function. [Source: specs/009-homebrew-tap-formula]

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

**Invariants**: Each domain suffix registered to exactly one provider. Stateless — every call is independent. Registered providers: `MediumExtractor` (medium.com), `DevToExtractor` (dev.to), `SubstackExtractor` (substack.com and all `*.substack.com` subdomains), `TheNewStackExtractor` (thenewstack.io).

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

### TheNewStack Article
[Source: specs/006-thenewstack-provider]
| Attribute | Type | Description |
|-----------|------|-------------|
| `title` | `str` | Article title from `h1.title` in `div#tns-post-headline`; prepended as `# Title` |
| `deck` | `str \| None` | Optional subtitle from `div.post-excerpt` in `div#tns-post-headline`; rendered as plain paragraph after title |
| `body` | `Tag` | Prose content inside `div#tns-post-body-content` |

**Validation**: Page must contain `div#tns-post-body-content`; absent → `UnsupportedContentTypeError`. Body must yield non-empty text after stripping → else `EmptyContentError`. No paywall — all thenewstack.io articles are publicly accessible.

### Homebrew Formula
[Source: specs/009-homebrew-tap-formula]
| Attribute | Type | Description |
|-----------|------|-------------|
| `url` | `str` | PyPI sdist tarball URL, changes on every release |
| `sha256` | `str` | Hex SHA-256 of the sdist tarball, changes on every release |
| `depends_on` | `str` | `"python@3.12"` (static) |
| `uses_from_macos` | `list[str]` | `["libxml2", "libxslt"]` — required by `lxml` resource |
| `resource` blocks | 13 entries | All runtime dependencies pinned to versions in `uv.lock` at formula creation time |

**Mutable fields per release**: `url` and `sha256` only. All `resource` blocks are static until a separate manual dependency-bump PR.

### TAP_GITHUB_TOKEN
[Source: specs/009-homebrew-tap-formula]

A GitHub fine-grained Personal Access Token with `Contents: read+write` on `stn1slv/homebrew-tap` only. Stored as a repository secret in `stn1slv/md-fetch` and consumed exclusively by the `update-homebrew-tap` CI job.

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
- **thenewstack.io non-article pages**: Homepage, category/tag listing, and author archive pages do not render `div#tns-post-body-content` → `UnsupportedContentTypeError` is raised immediately. [Source: specs/006-thenewstack-provider]
- **thenewstack.io VoxPop polls**: `div.tns-voxpop-screen` and `div.tns-voxpop-modal` are page-level overlay modals injected outside `div#tns-post-body-content` — confirmed via live DOM inspection. No explicit stripping is required; scoping extraction to the body container naturally excludes them. [Source: specs/006-thenewstack-provider]
- **thenewstack.io sponsored content**: `div.tns-sponsor-note` (mid-article sponsor injection) and three disclosure div variants are inside `div#tns-post-body-content` and must be decomposed before conversion. Sponsored article pages are extracted identically to editorial articles (FR-050). [Source: specs/006-thenewstack-provider]
- **thenewstack.io deck element**: `div.post-excerpt` is a `<div>`, not a semantic subtitle element; the extractor creates a new `<p>` tag with the deck text rather than copying the div directly, to ensure proper paragraph rendering. [Source: specs/006-thenewstack-provider]
- **thenewstack.io HTML structure changes**: If the site redesign moves content outside `div#tns-post-body-content`, the extractor will require an update.
- **Homebrew tap temporarily unavailable**: If `stn1slv/homebrew-tap` is unreachable when the pipeline tries to push, `git push` fails and the CI job surfaces a failure — the maintainer must retry manually. [Source: specs/009-homebrew-tap-formula]
- **TAP_GITHUB_TOKEN expired or revoked**: `git clone` or `git push` exits non-zero → CI job fails → maintainer is alerted to rotate the token. [Source: specs/009-homebrew-tap-formula]
- **PyPI release yanked after formula update**: The formula is not automatically rolled back; the maintainer handles yanked-release scenarios manually. [Source: specs/009-homebrew-tap-formula]
- **Concurrent releases**: Addressed by `concurrency: group=homebrew-tap-update, cancel-in-progress=false` — runs are serialized so the second release waits for the first tap-update to complete. [Source: specs/009-homebrew-tap-formula]
- **brew test fails after install**: `brew test md-fetch` exits non-zero when a transitive dependency is missing or `md-fetch --version` fails — installation validation fails. [Source: specs/009-homebrew-tap-formula]
- **Formula structure changed (sed no-op)**: If the formula is manually edited and the url/sha256 line format changes, `sed` produces no diff and `git commit` finds nothing staged → exits non-zero → CI job fails. [Source: specs/009-homebrew-tap-formula]

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

- **SC-026**: A public thenewstack.io article returns Markdown that contains the full article title and body text with zero non-content element fragments (navigation link text, subscription prompts, poll questions, author bio text). [Source: specs/006-thenewstack-provider]
- **SC-027**: Extraction of a thenewstack.io article completes within the base class 30-second fetch timeout on stable internet. [Source: specs/006-thenewstack-provider]
- **SC-028**: A thenewstack.io homepage URL raises `UnsupportedContentTypeError` within the normal fetch timeout. [Source: specs/006-thenewstack-provider]
- **SC-029**: The extracted Markdown for any thenewstack.io article contains no consecutive blank-line runs of three or more lines. [Source: specs/006-thenewstack-provider]
- **SC-030**: The TheNewStack provider is exercised by integration tests using real network requests against all five reference article URLs, matching the pattern established by existing providers. [Source: specs/006-thenewstack-provider]

- **SC-031**: A user with Homebrew installed can complete the full `md-fetch` installation using a single command, with no Python environment setup required, in under 3 minutes on a standard broadband connection. [Source: specs/009-homebrew-tap-formula]
- **SC-032**: The Homebrew formula's built-in test (`brew test md-fetch`) passes on macOS and Linux after every installation. [Source: specs/009-homebrew-tap-formula]
- **SC-033**: The formula in `stn1slv/homebrew-tap` is updated within 10 minutes of PyPI publish confirmation — no manual maintainer action is required. [Source: specs/009-homebrew-tap-formula]
- **SC-034**: Formula update failures produce a visible CI job failure on every failed attempt, with zero silent failures. [Source: specs/009-homebrew-tap-formula]
- **SC-035**: The README install section includes the Homebrew installation command, enabling users to discover and use it without prior knowledge of the project's Python packaging. [Source: specs/009-homebrew-tap-formula]

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
- Homebrew is already installed on the user's machine; the feature does not cover installing Homebrew itself. [Source: specs/009-homebrew-tap-formula]
- The formula targets the standard Homebrew installation on both macOS and Linux; Windows (WSL) is out of scope. [Source: specs/009-homebrew-tap-formula]
- Only the source distribution (sdist) is used as the formula's source artifact; binary wheels are not referenced by the formula. [Source: specs/009-homebrew-tap-formula]
- A `TAP_GITHUB_TOKEN` PAT will be created and added to repository secrets by the maintainer before first use — this is a one-time manual prerequisite. [Source: specs/009-homebrew-tap-formula]
- If a PyPI release is yanked after the formula has been updated, the formula is not automatically rolled back. [Source: specs/009-homebrew-tap-formula]

---

*Last Updated: 2026-05-16 | Sources appended: [specs/004-remove-backoff/spec.md], [specs/005-substack-provider/spec.md], [specs/006-thenewstack-provider/spec.md], [specs/009-homebrew-tap-formula/spec.md]*
