# Feature Specification: mdfetch — dev.to Extractor

**Feature Branch**: `002-devto-provider`

**Created**: 2026-05-14

**Status**: Draft

**Input**: User description: "Let's implement support of dev.to platform in addition to medium."

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Extract a dev.to Article to Markdown (Priority: P1)

A developer wants to retrieve the readable content of a dev.to article as clean, well-structured Markdown text by calling the same single library function used for Medium — passing only the article URL, with no additional configuration. The library routes the request to the dev.to provider, fetches the page, isolates the article body, strips all non-content elements, and returns formatted Markdown.

**Why this priority**: This is the core deliverable. The entire feature has no value until at least one real dev.to URL can be converted to clean Markdown through the existing public API.

**Independent Test**: Can be fully tested by calling the library's extraction function with a known dev.to article URL (e.g., `https://dev.to/stn1slv/integration-digest-for-december-2025-5dlp`) and verifying the returned string is valid Markdown with article content and no HTML tags.

**Acceptance Scenarios**:

1. **Given** a valid, publicly accessible dev.to article URL, **When** the developer calls the extraction function, **Then** the function returns a non-empty Markdown string containing the article's title and at least one paragraph of body text, with no raw HTML tags present.
2. **Given** a valid dev.to article URL, **When** the function is called, **Then** the returned Markdown does not contain navigation menus, reaction buttons ("❤️ Like", "🦄 Unicorn"), comment sections, or author sidebar widgets.
3. **Given** a dev.to article URL whose content includes headings, code blocks, and lists, **When** the function returns, **Then** those structural elements appear as proper Markdown equivalents (`#`, ` ``` `, `-`).

---

### User Story 2 — Receive Meaningful Errors for Unsupported dev.to Page Types (Priority: P2)

A developer passes a dev.to URL that points to a profile page, a tag listing, or a podcast page rather than an article. Instead of returning garbled content or crashing, the library raises a clear error indicating the dev.to domain is recognised but the page type is not extractable.

**Why this priority**: Consistent, typed error signalling prevents silent data corruption and lets downstream systems make informed decisions about retry or fallback.

**Independent Test**: Can be tested by calling the extraction function with a dev.to profile URL (e.g., `https://dev.to/stn1slv`) and asserting that the library raises the correct error type with an informative message.

**Acceptance Scenarios**:

1. **Given** a dev.to URL pointing to an author profile page, **When** the extraction function is called, **Then** the library raises a distinct error indicating the domain is supported but the content type is not an extractable article.
2. **Given** a dev.to URL pointing to a tag listing page, **When** the extraction function is called, **Then** the library raises the same distinct "unsupported content type" error.
3. **Given** a URL from a domain other than dev.to, **When** the extraction function is called with a dev.to-style path on that domain, **Then** the library raises an "unsupported platform" error (unchanged from existing behaviour).

---

### User Story 3 — Integration Tests Pass Against Real dev.to Article URLs (Priority: P3)

A developer runs the integration test suite and all dev.to integration tests pass against the three reference articles provided during feature specification. The tests confirm that title, structural elements, and absence of HTML are all verified on live content.

**Why this priority**: Integration tests are the definitive evidence that the provider works correctly against the real platform. Without them, production correctness cannot be verified.

**Independent Test**: Can be fully tested by running `uv run pytest -m integration` and asserting all dev.to integration tests pass with a green result and no skips.

**Acceptance Scenarios**:

1. **Given** the integration test suite is run with a stable internet connection, **When** tests for the three reference URLs execute, **Then** all three pass without errors or assertion failures.
2. **Given** an integration test for a reference dev.to article, **When** the extraction function returns, **Then** the test asserts the output is non-empty Markdown free of HTML tags and containing recognisable content from the article.

---

### Edge Cases

- What happens when a dev.to article is behind a paywall or requires login to view?
- What happens when dev.to's HTML structure changes and the article body selector no longer matches?
- What happens when the article body is found but contains no extractable text (e.g., only embedded images or videos)?
- What happens when the network request to dev.to times out?
- What happens when a dev.to URL uses the organisation page path (e.g., `https://dev.to/t/...`) rather than an article path?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The library MUST add `dev.to` to the provider router so that any URL with the `dev.to` domain is dispatched to the dev.to provider without any change to the caller's code.
- **FR-002**: The library MUST include a dev.to provider that fetches the article page, isolates the main article body, removes all non-content elements (navigation, social reaction widgets, comments, author sidebar, tag links), and returns the body as Markdown.
- **FR-003**: The dev.to provider MUST produce Markdown that preserves the structural hierarchy of the source article, including headings, code blocks, inline code, lists, blockquotes, and images. Both the cover image and inline body images MUST be rendered as Markdown image syntax (`![alt](url)`).
- **FR-004**: The dev.to provider MUST raise a distinct error — separate from the "unsupported platform" error — when a `dev.to` URL is provided but the page is not an article (e.g., an author profile, a tag listing, or an organisation page). The error must indicate the domain is recognised but the content type cannot be extracted.
- **FR-005**: The dev.to provider MUST raise a descriptive error when the article body is located but yields no extractable text content.
- **FR-008**: The dev.to provider MUST replace embedded third-party content (GitHub Gists, CodePen demos, YouTube videos, and similar iframes) with a plain Markdown link to the embedded resource URL. The embed must not be silently dropped.
- **FR-006**: The test suite MUST include integration tests that supply real dev.to article URLs to the extraction function and assert that the output matches expected Markdown structure and content. The three reference articles from the feature description MUST be included as test cases.
- **FR-007**: Adding the dev.to provider MUST require creating exactly one new file under the providers directory. No changes to shared library code (base class, router, public API, exception hierarchy) are required.

### Key Entities

- **URL**: A string input identifying the article to be extracted. Carries the domain used for provider routing and the path used to retrieve the page.
- **Provider**: A unit of platform-specific extraction logic. Each provider knows how to retrieve, clean, and convert content from one supported domain.
- **Extracted Article**: The output of extraction — a Markdown-formatted string representing the readable body of the source article, free of navigational or interactive chrome.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A developer already using the library for Medium can extract a dev.to article without any code change — only the URL changes.
- **SC-002**: The extraction function returns a result for a standard dev.to article in under 10 seconds on a stable internet connection.
- **SC-003**: The returned Markdown for any of the three reference dev.to articles contains no raw HTML tags (verified by automated assertion).
- **SC-004**: The returned Markdown for a dev.to article with headings, lists, and code blocks preserves all three structural element types in correct Markdown syntax.
- **SC-005**: 100% of integration tests pass against the three provided reference dev.to article URLs at the time of release.
- **SC-006**: The dev.to provider is delivered as exactly one new file; no existing source files are modified.

## Clarifications

### Session 2026-05-14

- Q: Should images (cover image and inline body images) be preserved in the Markdown output? → A: Yes — both the cover image and inline body images are preserved as Markdown image syntax (`![alt](url)`).
- Q: When an article contains embedded iframes (Gists, CodePens, YouTube), what should the provider output? → A: Replace each embed with a plain Markdown link to the embedded resource URL; embeds must not be silently dropped.
- Q: Should the article's tag list (e.g., `#integration`, `#api`) at the bottom of the page be preserved or stripped? → A: Strip tags — they are navigational metadata, not article content (confirmed by FR-002).

## Assumptions

- dev.to articles used in integration testing are publicly accessible without login; paywalled or login-gated content is out of scope.
- Only the `dev.to` domain is supported; custom domain dev.to publications (if any exist) are out of scope for this release.
- The library's existing exception hierarchy covers all required error cases; no new exception classes are needed.
- The provider auto-discovery mechanism (decorator-based registration) works for the dev.to provider in the same way as for Medium, requiring no changes to the router.
- The library's existing HTTP client configuration (User-Agent, timeout) is reused by the dev.to provider without modification.
- dev.to renders its article content in static HTML accessible without JavaScript execution; the provider does not need a headless browser.
- The three reference URLs (`/integration-digest-for-december-2025-5dlp`, `/integration-digest-for-july-2025-4lk9`, `/integration-digest-for-march-2026-599p`) remain publicly accessible during development and testing.

### Revision: Implementation Sync 2026-05-14
- Reason: All acceptance criteria verified as correctly implemented. Minor documentation drift reconciled: FR-007 wording clarified in plan.md ("no existing library source files") to account for the necessary `test_router.py` update; version bump (0.1.0 → 0.2.0) documented; `pyproject.toml` keywords gap added as T013.
