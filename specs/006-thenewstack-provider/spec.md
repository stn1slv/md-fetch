# Feature Specification: The New Stack Platform Provider

**Feature Branch**: `006-thenewstack-provider`

**Created**: 2026-05-16

**Status**: Draft

**Input**: User description: "Let's add support of thenewstack.io articles"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Extract a Public Article (Priority: P1)

A developer calls the `extract()` function with a thenewstack.io article URL. The function fetches the article and returns its content as clean Markdown, with no navigation menus, subscription banners, poll widgets, author bios, social share buttons, related articles sections, or any other page chrome.

**Why this priority**: Core value of the feature — reading public thenewstack.io articles is the primary use case and a prerequisite for all other stories.

**Independent Test**: Can be fully tested by passing a public article URL (e.g., `https://thenewstack.io/using-a-developer-portal-for-api-management/`) to `extract()` and verifying the returned Markdown contains the article title and body text but no navigation links, subscription CTAs, or poll widget text.

**Acceptance Scenarios**:

1. **Given** a valid URL pointing to a public thenewstack.io article, **When** `extract()` is called, **Then** it returns a non-empty Markdown string containing the article title as a top-level heading followed by the body content.
2. **Given** a thenewstack.io article with multiple headings, paragraphs, lists, and inline links, **When** `extract()` is called, **Then** the returned Markdown preserves all headings, paragraphs, lists, code blocks, and hyperlinks while stripping navigation, subscription CTAs, poll widgets, and social share buttons.
3. **Given** a thenewstack.io article containing images, **When** `extract()` is called, **Then** images appear in the output as Markdown image syntax (`![alt](url)`).

---

### User Story 2 - Reject Non-Article Pages (Priority: P2)

A developer passes a thenewstack.io URL that does not point to an article (e.g., the homepage, a category listing page, or a tag archive). The function raises a typed exception rather than returning empty or garbage Markdown.

**Why this priority**: Without this guard, callers could receive empty strings or malformed content silently; a typed exception lets them handle the error path explicitly.

**Independent Test**: Can be fully tested by passing the thenewstack.io homepage (`https://thenewstack.io/`) to `extract()` and verifying that `UnsupportedContentTypeError` is raised.

**Acceptance Scenarios**:

1. **Given** the thenewstack.io homepage URL, **When** `extract()` is called, **Then** `UnsupportedContentTypeError` is raised.
2. **Given** a thenewstack.io category/tag listing page URL, **When** `extract()` is called, **Then** `UnsupportedContentTypeError` is raised.
3. **Given** an article page whose extractable body text is empty after stripping all chrome, **When** `extract()` is called, **Then** `EmptyContentError` is raised.

---

### Edge Cases

- What happens when the URL points to a category listing, tag archive, or author profile page rather than an article?
- What happens when the article body is present but contains no extractable text after stripping (e.g., media-only post)?
- How does the system behave when the platform returns an HTTP error (404, 429, 503)?
- What happens when the article contains embedded content (tweets, YouTube videos, iframes)?
- What happens when VoxPop poll widgets are present mid-article — are they stripped without leaving gaps?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST route all `thenewstack.io` URLs to the new provider using the existing domain-registration mechanism (`@register` decorator + `DOMAINS` frozenset).
- **FR-002**: The system MUST extract the main article body from a thenewstack.io page and return it as clean Markdown.
- **FR-003**: The system MUST strip all non-content elements before Markdown conversion, including: site navigation headers, subscription CTAs and newsletter signup forms, VoxPop poll widgets, social share buttons, author bio sections, related articles sections, sidebar content, sponsored content banners, and page footers.
- **FR-004**: The system MUST prepend the article title as a top-level Markdown heading (`# Title`), followed immediately by the article deck/subtitle as a plain paragraph when one is present on the page.
- **FR-005**: The system MUST preserve the article's structural content: headings (all levels), paragraphs, ordered and unordered lists, inline code, fenced code blocks, blockquotes, hyperlinks, and images.
- **FR-006**: The system MUST raise `UnsupportedContentTypeError` when the fetched page does not contain a recognisable article body element.
- **FR-007**: The system MUST raise `EmptyContentError` when the article body is present but yields no extractable text after stripping.
- **FR-008**: The system MUST collapse runs of three or more consecutive blank lines to a single blank line in the output Markdown.
- **FR-009**: The system MUST convert embedded third-party content (e.g., tweet embeds, YouTube video iframes, and similar rich-media widgets) to plain anchor links using the embed's source URL, discarding the embed wrapper — matching the pattern used by existing providers for iframe and liquid-tag embeds.
- **FR-010**: The system MUST treat sponsored and native-advertising article pages identically to editorial articles — extracting content as-is with no special detection, marking, or rejection.

### Key Entities

- **thenewstack.io Article**: A single article page at a `thenewstack.io/<slug>/` URL. Key attributes: title, author, publication date, body content (always publicly accessible — no paywall).
- **DOM Element Taxonomy**: Mapping of HTML elements to actions (keep, strip) for thenewstack.io's page structure. Article body resides in `<article>` or equivalent main content container; non-content elements include navigation, VoxPop polls, subscription forms, social buttons, related posts, and footer.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A public thenewstack.io article returns Markdown that contains the full article title and body text with zero non-content element fragments (navigation link text, subscription prompts, poll questions, author bio text).
- **SC-002**: Extraction completes within the base class 30-second fetch timeout on stable internet.
- **SC-003**: A thenewstack.io homepage URL raises `UnsupportedContentTypeError` within the normal fetch timeout.
- **SC-004**: The extracted Markdown for any article contains no consecutive blank-line runs of three or more lines.
- **SC-005**: The new provider is exercised by at least one integration test using a real network request against both reference article URLs, matching the pattern established by existing providers.

## Clarifications

### Session 2026-05-16

- Q: How should sponsored/native content article pages be handled? → A: Treat identically to editorial articles — extract as-is, no special detection or marking.
- Q: Should the article deck/subtitle (short descriptive sentence below the title) be included in the output? → A: Yes — include as a plain paragraph immediately after the `# Title` heading.

## Assumptions

- thenewstack.io does not operate a paywall; all articles are publicly accessible without authentication. No paywall handling is required.
- thenewstack.io does not use contributor subdomains (unlike Substack or Medium); only the primary `thenewstack.io` hostname needs to be registered.
- The platform's public HTML page structure (article body container element) is stable enough for CSS-selector-based extraction; a major redesign would require an extractor update.
- VoxPop poll widgets embedded mid-article are non-content and MUST be stripped entirely; their removal should not introduce extra blank lines beyond the collapsed-blank-line rule.
- The implementation follows the existing provider pattern: one new file `src/mdfetch/providers/thenewstack.py`, no changes to shared infrastructure.
- The base class retry/timeout behaviour (3 retries, 30-second timeout) is inherited without modification.
- Integration tests use the five reference article URLs: `https://thenewstack.io/using-a-developer-portal-for-api-management/`, `https://thenewstack.io/api-management-for-asynchronous-apis/`, `https://thenewstack.io/json-schema-ai-reliability/`, `https://thenewstack.io/mcp-api-governance-readiness/`, and `https://thenewstack.io/api-mcp-agent-integration/`. All five were verified to share identical HTML structure.
