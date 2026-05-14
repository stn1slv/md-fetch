# Feature Specification: mdfetch — Medium Extractor (Initial Release)

**Feature Branch**: `001-mdfetch-medium-extractor`

**Created**: 2026-05-14

**Status**: Draft

**Input**: User description: "Draft the complete technical specification for the initial implementation of the `mdfetch` library, focusing strictly on the Medium platform as the first source."

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Extract a Medium Article to Markdown (Priority: P1)

A developer wants to retrieve the readable content of a Medium article as clean, well-structured Markdown text by calling a single library function with just the article URL. The library handles fetching the page, isolating the article body, stripping non-content elements, and returning formatted Markdown — all without requiring any configuration.

**Why this priority**: This is the core value proposition of the library. Without the ability to convert at least one real URL to clean Markdown, nothing else is deliverable.

**Independent Test**: Can be fully tested by calling the library's main extraction function with a known Medium article URL and verifying the returned string is valid Markdown with article content and no HTML tags.

**Acceptance Scenarios**:

1. **Given** a valid, publicly accessible Medium article URL, **When** the developer calls the extraction function with that URL, **Then** the function returns a non-empty string of clean Markdown containing the article's title and at least one paragraph of body text, with no raw HTML tags present.
2. **Given** a valid Medium article URL, **When** the function is called, **Then** the returned Markdown does not contain navigation menus, "clap" interaction elements, social sharing buttons, or author biography sections.
3. **Given** a valid Medium article URL with headings, code blocks, and lists in the article, **When** the function returns, **Then** those structural elements are present in the output as proper Markdown equivalents (e.g., `#`, ` ``` `, `-`).

---

### User Story 2 — Receive Meaningful Errors for Unsupported or Invalid URLs (Priority: P2)

A developer passes a URL that is not from Medium, or a URL that is malformed or unreachable. Instead of a silent failure or a crash, they receive a clear, descriptive error that explains why extraction could not be completed.

**Why this priority**: Correct error communication prevents silent data loss and enables developers to build reliable systems on top of the library.

**Independent Test**: Can be tested by calling the extraction function with an unsupported domain URL or a broken URL and asserting the appropriate error type and message is raised.

**Acceptance Scenarios**:

1. **Given** a URL from a domain other than Medium, **When** the developer calls the extraction function, **Then** the function raises an error indicating the platform is not supported.
2. **Given** a syntactically invalid URL string, **When** the developer calls the extraction function, **Then** the function raises an error indicating the URL is not valid.
3. **Given** a well-formed URL that returns an HTTP error (e.g., 404 or 503), **When** the function is called, **Then** the function raises an error indicating the page could not be retrieved, including the status code.

---

### User Story 3 — Install and Use the Library via Standard Package Manager (Priority: P3)

A developer installs the `mdfetch` library from PyPI using pip, imports the extraction function, and immediately begins converting Medium URLs to Markdown without any additional configuration or setup steps.

**Why this priority**: Packaging and distribution correctness determine whether users can adopt the library at all. This story validates the full publish-to-install lifecycle.

**Independent Test**: Can be tested by building the package distribution artifact and verifying it installs cleanly into a fresh virtual environment, after which the extraction function is importable and functional.

**Acceptance Scenarios**:

1. **Given** the library is published to PyPI, **When** a developer runs `pip install mdfetch`, **Then** the installation completes without errors and all required dependencies are resolved automatically.
2. **Given** the library is installed, **When** the developer writes `from mdfetch import extract`, **Then** the import succeeds and the function is callable.

---

### Edge Cases

- What happens when the Medium article is behind a paywall and the content is not in the public HTML?
- What happens when Medium's HTML structure changes and the article body cannot be located?
- When the article body is found but contains no extractable text, the library raises a descriptive error (resolved — see FR-011).
- What happens when the network request times out?
- When the URL points to a Medium profile or tag page rather than an article, the library raises a distinct "unsupported content type" error (resolved — see FR-012).

## Clarifications

### Session 2026-05-14

- Q: Does routing cover only `medium.com`, or also custom-domain Medium publications? → A: Only `medium.com` and its subdomains (e.g., `username.medium.com`). Custom domains out of scope for v1.
- Q: When the article body is found but contains no extractable text, what should the library do? → A: Raise a descriptive error indicating no extractable text was found.
- Q: When a `medium.com` URL points to a profile or tag page (not an article), what should the library do? → A: Raise a distinct error indicating the domain is supported but the page type is not an extractable article.
- Q: Should the library emit any logging or diagnostic output? → A: No logging; all failure information communicated exclusively through exceptions. No verbose mode in v1.
- Q: How should the library identify itself in HTTP requests, and should it respect robots.txt? → A: Use the default browser-like User-Agent string provided by the HTTP client; no custom header, no robots.txt checking in v1.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The library MUST expose a single primary function that accepts a URL string and returns the extracted article content as a Markdown string.
- **FR-002**: The library MUST enforce a provider pattern: a shared abstract base defines the extraction contract, and each supported platform is implemented as a separate, independent provider that fulfils that contract.
- **FR-003**: The library MUST include a Medium provider that fetches the article page, isolates the main article body, removes all non-content elements (navigation, social sharing widgets, reader interaction components, author biographies), and returns the body as Markdown.
- **FR-004**: The library MUST route extraction requests to the correct provider based on the URL's domain without requiring the caller to specify the provider explicitly. For v1, routing recognises only `medium.com` and its subdomains (e.g., `username.medium.com`); custom-domain Medium publications are out of scope.
- **FR-005**: The library MUST raise a descriptive error when given a URL whose domain has no registered provider.
- **FR-006**: The library MUST raise a descriptive error when a network request fails (connection error, timeout, non-2xx HTTP status).
- **FR-007**: The library MUST raise a descriptive error when given a URL that is syntactically invalid.
- **FR-008**: The library MUST produce Markdown that preserves the structural hierarchy of the source article, including headings, code blocks, inline code, lists, and blockquotes.
- **FR-009**: The library MUST be packaged and distributed via PyPI using modern Python packaging best practices, enabling installation through the standard package manager without additional steps.
- **FR-010**: The test suite MUST include integration tests that supply real Medium article URLs to the extraction function and assert that the output matches expected Markdown structure and content.
- **FR-011**: The library MUST raise a descriptive error when the article body is located but yields no extractable text content (e.g., the page contains only images or embeds with no readable text).
- **FR-012**: The library MUST raise a distinct error — separate from the "unsupported platform" error — when a `medium.com` URL is provided but the page is not an article (e.g., an author profile or tag page). The error must indicate that the domain is recognised but the content type cannot be extracted.
- **FR-013**: The library MUST NOT emit any logging, print output, or diagnostic messages. All failure information is communicated exclusively through raised exceptions.
- **FR-014**: HTTP requests made by the library MUST use the default browser-like User-Agent string provided by the HTTP client. No custom User-Agent header is set, and the library does not check or respect `robots.txt` in v1.

### Key Entities

- **URL**: A string input identifying the article to be extracted. Carries the domain used for provider routing and the path used to retrieve the page.
- **Provider**: A unit of platform-specific extraction logic. Each provider knows how to retrieve, clean, and convert content from one supported domain.
- **Extracted Article**: The output of extraction — a Markdown-formatted string representing the readable body of the source article, free of navigational or interactive chrome.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A developer can go from installing the library to extracting a real Medium article in fewer than 5 minutes with zero configuration.
- **SC-002**: The extraction function returns a result for a standard Medium article in under 10 seconds on a stable internet connection.
- **SC-003**: The returned Markdown for a standard Medium article contains no raw HTML tags (verified by automated assertion).
- **SC-004**: The returned Markdown for an article with headings, lists, and code blocks preserves all three structural element types in correct Markdown syntax.
- **SC-005**: 100% of integration tests pass against a curated set of real Medium article URLs at the time of initial release.
- **SC-006**: Adding support for a second platform in the future requires creating exactly one new file (one new provider class) with no modifications to shared library code.

## Assumptions

- The library targets developers as its primary users; no graphical interface or configuration file is required.
- Medium articles used in integration testing are publicly accessible (not behind a paywall); paywalled content handling is out of scope for this initial release.
- The library does not cache responses; each call to the extraction function performs a fresh network request.
- Rate limiting or authentication with Medium's servers is out of scope for this initial release.
- The library supports Python 3.10 and later; compatibility with older Python versions is not required.
- The initial release supports only the Medium platform; the provider pattern ensures future platforms can be added without changing existing code.
- Network timeouts will use a sensible default (e.g., 30 seconds); this value is not user-configurable in v1.
- The library operates on publicly accessible HTML; it does not execute JavaScript or render dynamic content.
