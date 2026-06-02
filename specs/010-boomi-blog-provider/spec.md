# Feature Specification: Boomi Blog Provider

**Feature Branch**: `010-boomi-blog-provider`

**Created**: 2026-06-02

**Status**: Draft

**Input**: User description: "I would like to add support of the articles from https://boomi.com/blog/. Please use the following ones as references: 1. https://boomi.com/blog/gartner-magic-quadrant-ipaas-2026/ 2. https://boomi.com/blog/real-time-vs-batch-data-integration-choosing-the-right-approach/ 3. https://boomi.com/blog/how-to-maintain-data-consistency-across-saas-and-on-prem-systems/"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Extract a Boomi blog article as clean Markdown (Priority: P1)

A user passes the URL of a public Boomi blog article to the library and receives the article's title and full body rendered as clean Markdown, with all site chrome (navigation, CTAs, share buttons, related-post links, footer) removed.

**Why this priority**: This is the core value of the feature — without it, Boomi blog articles cannot be consumed at all. It is the minimum viable slice and delivers the complete user benefit on its own.

**Independent Test**: Can be fully tested by calling `extract()` with one of the three reference URLs and verifying the returned Markdown begins with the article title as a top-level heading and contains the body's section headings and paragraph text, with no navigation, subscription/demo CTAs, or footer text.

**Acceptance Scenarios**:

1. **Given** a public Boomi blog article URL, **When** `extract()` is called, **Then** the result is Markdown whose first line is `# <article title>` followed by the body content.
2. **Given** a Boomi blog article containing H2 sections and bullet lists, **When** extracted, **Then** the headings and lists are preserved as Markdown headings and lists in document order.
3. **Given** a Boomi blog article, **When** extracted, **Then** the output contains none of: top navigation, language selector, login/demo CTAs, "on this page" jump links, social share buttons, related/previous/next post links, sidebar report promotions, or footer links.

---

### User Story 2 - Reject non-article Boomi URLs cleanly (Priority: P2)

A user passes a Boomi URL that is not a readable blog article (the blog index, a category listing, or a marketing page on `boomi.com`). The library raises a typed error rather than returning garbage or partial chrome.

**Why this priority**: Protects users from silently receiving meaningless output and keeps behavior consistent with existing providers. Valuable but secondary to the happy path.

**Independent Test**: Can be tested by calling `extract()` with a non-article Boomi URL (e.g., the blog index `https://boomi.com/blog/`) and asserting that a typed extraction error is raised.

**Acceptance Scenarios**:

1. **Given** the Boomi blog index URL, **When** `extract()` is called, **Then** an `UnsupportedContentTypeError` is raised because no single article body is present.
2. **Given** a Boomi article whose body element is present but yields no text after stripping, **When** `extract()` is called, **Then** an `EmptyContentError` is raised.

---

### Edge Cases

- **Non-article pages**: The Boomi blog index (`/blog/`), category/tag listings, and non-blog marketing pages on `boomi.com` do not contain a single recognizable article body → `UnsupportedContentTypeError`.
- **Hero/inline images**: Reference articles include a featured hero image and may include inline images. Only images inside the article body container are preserved as Markdown images; the featured hero/banner image (rendered outside the body) and other chrome images are stripped with their containers.
- **Blockquotes**: Some articles embed pull quotes (e.g., the Gartner quote in reference #1). These are preserved as Markdown blockquotes.
- **Legal disclaimers**: Trailing legal/attribution text that is part of the article body (e.g., the Gartner disclaimer) is preserved as body content; site-wide footer legal links are not.
- **HTTP errors**: A 404/410 for a removed article, or a 429/503 transient error, is surfaced via the base class's existing fetch/error behavior — this feature introduces no new network handling.
- **No embedded media in references**: The reference articles contain no code blocks, videos, tweets, or iframes; should such embeds appear in other Boomi articles, they are handled by the inherited base conversion behavior, not by feature-specific logic.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST route `boomi.com` blog URLs to the new provider using the existing domain-registration mechanism (`@register` decorator + `DOMAINS` frozenset).
- **FR-002**: The system MUST extract the main article body from a Boomi blog post page and return it as clean Markdown.
- **FR-003**: The system MUST strip all non-content elements before conversion: top navigation, language selector, login/demo CTAs, "on this page" jump links, social share buttons, related/previous/next post navigation, sidebar report/promo callouts, and the site footer.
- **FR-004**: The system MUST prepend the article title as a top-level Markdown heading (`# Title`).
- **FR-005**: The system MUST preserve structural body content: section headings, paragraphs, ordered and unordered lists, blockquotes, hyperlinks, and images located inside the article body container. Images outside the body container (e.g., a featured hero/banner image rendered in a page header) MUST be treated as page chrome and excluded.
- **FR-006**: The system MUST raise `UnsupportedContentTypeError` when the page does not contain a recognizable single article body element (e.g., the blog index or a non-article page).
- **FR-007**: The system MUST raise `EmptyContentError` when the article body yields no extractable text after stripping.
- **FR-008**: The system MUST collapse runs of three or more consecutive blank lines to a single blank line.
- **FR-009**: The system MUST yield article output only for pages that contain a recognizable article body container. Pages on `boomi.com` without one — the blog index, category/tag listings, and non-blog pages — MUST NOT yield article output and MUST raise `UnsupportedContentTypeError`. (In practice all article pages live under `boomi.com/blog/<slug>/`; scoping is enforced by body-container presence rather than URL path matching.)

### Key Entities *(include if feature involves data)*

- **Boomi Blog Post**: A single article page under `https://boomi.com/blog/<slug>/`. Key attributes: title, body content, author (e.g., "Ed Macosky", "Boomi"), publication date, category, optional hero image. Subtitle/deck is generally absent.
- **DOM Element Taxonomy**: Mapping of CSS selectors for the Boomi blog layout to actions (keep the article body container; strip navigation, language selector, CTAs, jump links, share buttons, related-post navigation, sidebar promos, and footer).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Each of the three reference articles returns Markdown containing the full title and all body section headings and paragraph text, with zero non-content elements (navigation, CTAs, share buttons, related-post links, footer).
- **SC-002**: Extraction completes within the base class 30-second fetch timeout on a stable connection.
- **SC-003**: A non-article Boomi URL (the blog index) raises `UnsupportedContentTypeError` within the normal fetch timeout.
- **SC-004**: The extracted Markdown contains no consecutive blank-line runs of three or more lines.
- **SC-005**: The new provider is exercised by at least one integration test using a real network request against a reference URL, matching the pattern established by existing providers.

## Clarifications

### Session 2026-06-02

- Q: How should the featured/hero image be handled? → A: Body-only images — include only images inside the article body container; the featured hero/banner image (outside the body) is treated as page chrome and excluded.

## Assumptions

- The Boomi blog's public HTML structure is stable enough for CSS-selector-based extraction; a major redesign would require an extractor update.
- All target content is freely readable; no authentication or paywall handling is required (confirmed across the three reference articles).
- Only the primary `boomi.com` domain is in scope. Extraction is limited to article pages under the `/blog/` path; the blog index and other `boomi.com` pages are treated as unsupported content rather than routed to a different provider.
- Subtitle/deck handling is best-effort: when no deck is present (as in the references), only the title heading is prepended.
- The implementation follows the existing provider pattern: one new file under `src/mdfetch/providers/` subclassing `BaseExtractor` and reusing its shared conversion methods, with no changes to shared infrastructure.
- The base class retry/timeout behavior (existing defaults) is inherited without modification.
- The `test_router.py` unsupported-domain fixture remains valid (Boomi registers `boomi.com`, which is not currently used as the unsupported-domain example — `wordpress.com` is); no fixture update is required unless that changes.
