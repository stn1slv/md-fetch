# Feature Specification: Kong Blog Provider

**Feature Branch**: `011-konghq-blog-provider`

**Created**: 2026-06-02

**Status**: Completed

**Input**: User description: "I would like to add support of the articles from https://konghq.com/blog. Please use the following ones as references: 1. https://konghq.com/blog/product-releases/insomnia-12-6 2. https://konghq.com/blog/enterprise/kong-ai-gateway-vs-litellm 3. https://konghq.com/blog/product-releases/kong-gateway-3-14"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Extract a Kong blog article as clean Markdown (Priority: P1)

A user passes the URL of a public Kong (konghq.com) blog article to the library and receives the article's title and full body rendered as clean Markdown, with all site chrome (navigation, breadcrumbs, table-of-contents, demo CTAs, social share, related-post carousel, author bios, newsletter signup, footer) removed.

**Why this priority**: This is the core value of the feature — without it, Kong blog articles cannot be consumed at all. It is the minimum viable slice and delivers the complete user benefit on its own.

**Independent Test**: Can be fully tested by calling `extract()` with one of the three reference URLs and verifying the returned Markdown begins with the article title as a top-level heading and contains the body's section headings, paragraph text, lists, and code snippets, with no navigation, table-of-contents, demo CTAs, related-post carousel, or footer text.

**Acceptance Scenarios**:

1. **Given** a public Kong blog article URL, **When** `extract()` is called, **Then** the result is Markdown whose first line is `# <article title>` followed by the body content.
2. **Given** a Kong blog article containing H2/H3 sections, bullet lists, and inline code snippets, **When** extracted, **Then** the headings, lists, and code are preserved as Markdown in document order.
3. **Given** a Kong blog article, **When** extracted, **Then** the output contains none of: top/product navigation, breadcrumbs, topic tags, the "on this page"/table-of-contents block, social share buttons, "Get a Demo"/"Book Demo" CTAs, the recommended/related posts carousel, author bio blocks, read-time estimate, newsletter signup, or footer links.
4. **Given** a Kong blog article with a visible publication date, **When** extracted, **Then** the publication date appears directly under the `# Title` heading and no author byline or read-time text is present.

---

### User Story 2 - Reject non-article Kong URLs cleanly (Priority: P2)

A user passes a Kong URL that is not a readable blog article (the blog index, a category listing such as `/blog/product-releases`, or a marketing page on `konghq.com`). The library raises a typed error rather than returning garbage or partial chrome.

**Why this priority**: Protects users from silently receiving meaningless output and keeps behavior consistent with existing providers. Valuable but secondary to the happy path.

**Independent Test**: Can be tested by calling `extract()` with a non-article Kong URL (e.g., the blog index `https://konghq.com/blog`) and asserting that a typed extraction error is raised.

**Acceptance Scenarios**:

1. **Given** the Kong blog index or a category listing URL, **When** `extract()` is called, **Then** an `UnsupportedContentTypeError` is raised because no single article body is present.
2. **Given** a Kong article whose body element is present but yields no text after stripping, **When** `extract()` is called, **Then** an `EmptyContentError` is raised.

---

### Edge Cases

- **Non-article pages**: The Kong blog index (`/blog`), category/tag listings (`/blog/product-releases`, `/blog/enterprise`), and non-blog marketing pages on `konghq.com` do not contain a single recognizable article body → `UnsupportedContentTypeError`.
- **Multiple authors**: Reference articles have one to five authors. Author/byline blocks, author bios, and the read-time estimate are treated as chrome and stripped. The publication date is retained and rendered under the title (see FR-004).
- **TL;DR / lead section**: An opening TL;DR or summary list that is part of the article body is preserved as body content.
- **Table of contents**: The "on this page" / table-of-contents block is page chrome and is stripped, even though it mirrors the body's H2 headings.
- **Inline images vs. hero/featured image**: Only images inside the article body container (e.g., feature screenshots, diagrams) are preserved as Markdown images; a featured hero/banner image rendered outside the body is treated as chrome and excluded.
- **Embedded media**: Some articles embed videos or downloadable comparison-chart CTAs (linked PDFs). Embedded video/iframe players are not converted to body text; an in-body hyperlink to a downloadable asset is preserved as a normal link. No feature-specific media handling beyond inherited base behavior is introduced.
- **Code snippets**: Inline and block code (e.g., `git status`, `git commit`) are preserved as Markdown code.
- **"Agent mode" duplicate content**: The platform renders a hidden alternate ("agent mode") copy of much of the page that embeds literal Markdown punctuation. This duplicate is treated as non-content and excluded so the output is not doubled or corrupted.
- **HTTP errors**: A 404/410 for a removed article, or a 429/503 transient error, is surfaced via the base class's existing fetch/error behavior — this feature introduces no new network handling.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST route `konghq.com` blog URLs to the new provider using the existing domain-registration mechanism (`@register` decorator + `DOMAINS` frozenset).
- **FR-002**: The system MUST extract the main article body from a Kong blog post page and return it as clean Markdown.
- **FR-003**: The system MUST strip all non-content elements before conversion: top/product navigation, breadcrumbs, topic tags, the table-of-contents/"on this page" block, social share buttons, "Get a Demo"/"Book Demo" CTAs, the recommended/related posts carousel, author byline/bio blocks, the read-time estimate, newsletter signup, and the site footer.
- **FR-004**: The system MUST prepend the article title as a top-level Markdown heading (`# Title`), followed by the article's publication date when present. Author bylines and read time MUST NOT be included.
- **FR-005**: The system MUST preserve structural body content: section headings (H2/H3), paragraphs, ordered and unordered lists, inline and block code, blockquotes, hyperlinks, and images located inside the article body container. Images outside the body container (e.g., a featured hero/banner image) MUST be treated as page chrome and excluded.
- **FR-006**: The system MUST raise `UnsupportedContentTypeError` when the page does not contain a recognizable single article body element (e.g., the blog index, a category listing, or a non-article page).
- **FR-007**: The system MUST raise `EmptyContentError` when the article body yields no extractable text after stripping.
- **FR-008**: The system MUST collapse runs of three or more consecutive blank lines to a single blank line.
- **FR-009**: The system MUST yield article output only for pages that contain a recognizable article body container. Pages on `konghq.com` without one — the blog index, category/tag listings, and non-blog pages — MUST NOT yield article output and MUST raise `UnsupportedContentTypeError`. (In practice all article pages live under `konghq.com/blog/<category>/<slug>`; scoping is enforced by body-container presence rather than URL path matching.)

### Key Entities *(include if feature involves data)*

- **Kong Blog Post**: A single article page under `https://konghq.com/blog/<category>/<slug>` (categories include `product-releases`, `enterprise`). Key attributes: title, publication date (retained in output), body content, one or more authors (stripped), read time (stripped), category, topic tags, optional hero image. A short TL;DR/lead may precede the first section.
- **DOM Element Taxonomy**: Mapping of CSS selectors for the Kong blog layout to actions (keep the article body container; strip navigation, breadcrumbs, topic tags, table-of-contents, share buttons, demo CTAs, related-post carousel, author bios, newsletter signup, and footer).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Each of the three reference articles returns Markdown containing the full title and all body section headings and paragraph text, with zero non-content elements (navigation, table-of-contents, demo CTAs, related-post carousel, footer).
- **SC-002**: Extraction completes within the base class 30-second fetch timeout on a stable connection.
- **SC-003**: A non-article Kong URL (the blog index) raises `UnsupportedContentTypeError` within the normal fetch timeout.
- **SC-004**: The extracted Markdown contains no consecutive blank-line runs of three or more lines.
- **SC-005**: The new provider is exercised by at least one integration test using a real network request against a reference URL, matching the pattern established by existing providers.
- **SC-006**: For a reference article with a visible publication date, the extracted Markdown contains the publication date directly beneath the title and contains no author byline or read-time text.

## Clarifications

### Session 2026-06-02

- Q: How should article metadata (author bylines, publication date, read time) be handled? → A: Keep the publication date only (rendered under the title); strip author bylines/bios and the read-time estimate as chrome.

## Assumptions

- The Kong blog's public HTML structure is stable enough for CSS-selector-based extraction; a major redesign would require an extractor update.
- All target content is freely readable; no authentication or paywall handling is required (confirmed across the three reference articles).
- Only the primary `konghq.com` domain is in scope. Extraction is limited to article pages under the `/blog/<category>/<slug>` path; the blog index and other `konghq.com` pages are treated as unsupported content rather than routed to a different provider.
- Author bylines/bios and the read-time estimate are treated as chrome and excluded; the publication date is retained and rendered under the title. No subtitle/deck is reliably present across references.
- Body-only images: include only images inside the article body container; the featured hero/banner image (outside the body) is treated as page chrome and excluded — following the precedent set by the Boomi provider.
- The implementation follows the existing provider pattern: one new file under `src/mdfetch/providers/` subclassing `BaseExtractor` and reusing its shared conversion methods, with no changes to shared infrastructure.
- The base class retry/timeout behavior (existing defaults) is inherited without modification.
- The `test_router.py` unsupported-domain fixture remains valid (Kong registers `konghq.com`, which is not currently used as the unsupported-domain example — `wordpress.com` is); no fixture update is required.

### Revision: Implementation Sync 2026-06-02
- Reason: Post-implementation audit ("please check all the things"). The shipped extraction satisfies all functional requirements; one edge case was added to document the platform's "agent mode" duplicate-content quirk (stripped during extraction). No requirements changed. Selector-level reconciliation (TOC = `.toc-wrap`, `.agent` stripping) was recorded in plan.md / research.md / data-model.md / contracts.
