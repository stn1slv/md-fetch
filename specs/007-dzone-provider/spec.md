# Feature Specification: DZone Provider

**Feature Branch**: `007-dzone-provider`

**Created**: 2026-05-16

**Status**: Draft

**Input**: User description: "Let's add Dzone provider support."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Extract a Standard Article (Priority: P1)

A developer calls `extract("https://dzone.com/articles/integration-patterns-fail-production")` and receives a clean Markdown document containing the full article title and body with no ads, no navigation, no sidebar, and no UI chrome.

**Why this priority**: This is the core value proposition — extracting readable article content. All other stories build on top of this capability.

**Independent Test**: Can be fully tested by calling `extract()` with a public DZone article URL and asserting that the returned Markdown starts with a `# ` heading matching the article title and contains expected body text.

**Acceptance Scenarios**:

1. **Given** a public DZone article URL (`dzone.com/articles/<slug>`), **When** `extract()` is called, **Then** the result is a Markdown string beginning with `# <article title>` followed by the article body.
2. **Given** the article contains H2 and H3 headings, **When** `extract()` is called, **Then** the headings are preserved as `##` and `###` in the Markdown output.
3. **Given** the article contains bullet lists or numbered lists, **When** `extract()` is called, **Then** lists are preserved in Markdown list format.
4. **Given** the article contains hyperlinks, **When** `extract()` is called, **Then** links are preserved as `[text](url)` Markdown syntax.
5. **Given** the article has sidebar trending links, ads, author action buttons, sign-in prompts, tags, attribution, and footer navigation, **When** `extract()` is called, **Then** none of these elements appear in the output.

---

### User Story 2 - Extract an Article With Code Blocks (Priority: P2)

A developer extracts a DZone article that contains code blocks (rendered via the site's CodeMirror editor widget). The returned Markdown preserves all code blocks as fenced code blocks, with the programming language annotation where the page specifies one.

**Why this priority**: DZone is a technical platform; many articles contain code. Losing code blocks or mangling them would make the extracted content unusable.

**Independent Test**: Call `extract()` on `https://dzone.com/articles/image-classification-pipeline-camel-djl` and verify the Markdown contains fenced code blocks (triple backtick) with correct language tags (e.g., `java`, `groovy`).

**Acceptance Scenarios**:

1. **Given** a DZone article with code blocks in a CodeMirror widget, **When** `extract()` is called, **Then** each code block appears as a fenced Markdown code block (triple backtick).
2. **Given** a CodeMirror widget has a language label (e.g., "Java", "Groovy"), **When** `extract()` is called, **Then** the fenced code block uses the lowercased language identifier as its info string.
3. **Given** a CodeMirror widget has a language label of "Plain Text", **When** `extract()` is called, **Then** the fenced code block uses no language info string (bare backticks).
4. **Given** the article contains inline `code` elements, **When** `extract()` is called, **Then** inline code is preserved as backtick-wrapped text.
5. **Given** the CodeMirror widget contains a UI cancel icon and a code header div, **When** `extract()` is called, **Then** these UI elements do not appear in the Markdown output.

---

### User Story 3 - Unsupported or Non-Article URL (Priority: P3)

A developer accidentally passes a DZone URL that is not a standard article page (e.g., a refcard, a topic listing, a user profile). The system raises `UnsupportedContentTypeError` rather than returning empty or garbled content.

**Why this priority**: Error hygiene prevents silent failures. Users relying on the extracted content for downstream processing need to know when no article was found.

**Independent Test**: Call `extract()` with a DZone non-article URL (e.g., a refcard page) and assert `UnsupportedContentTypeError` is raised.

**Acceptance Scenarios**:

1. **Given** a DZone URL where no `div.content-html` element exists on the page, **When** `extract()` is called, **Then** `UnsupportedContentTypeError` is raised with a descriptive message.
2. **Given** a DZone article URL that resolves to a page with `div.content-html` containing no extractable text, **When** `extract()` is called, **Then** `EmptyContentError` is raised.

---

### Edge Cases

- What happens when the URL points to a DZone refcard (`/refcardz/`), topic listing (`/topics/`), or user profile? The page will not contain `div.content-html` → `UnsupportedContentTypeError`.
- How does the system handle paywalled or subscriber-only content? DZone public articles are freely accessible; no paywall gate was detected on public article pages. If a future gate hides `div.content-html`, `UnsupportedContentTypeError` is raised naturally.
- What happens when the article body is present but contains no extractable text? `EmptyContentError` is raised.
- How does the system behave when the platform returns an HTTP error (404, 429, 503)? The base class handles HTTP errors via its existing retry/timeout mechanism and raises `FetchError`.
- What happens when a code block's language label is empty or whitespace? The fenced code block is emitted with no language info string.
- What happens when the article contains a comparison table (`div.table-responsive`)? Tables inside `div.content-html` are rendered as Markdown tables via markdownify.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST route all `dzone.com` URLs to the new provider using the existing domain-registration mechanism (`@register` decorator + `DOMAINS` frozenset).
- **FR-002**: The system MUST extract the article body from `div.content-html` and return it as clean Markdown.
- **FR-003**: The system MUST prepend the article title as a top-level Markdown heading (`# Title`) sourced from `h1.article-title`.
- **FR-004**: The system MUST raise `UnsupportedContentTypeError` when no `div.content-html` element is found on the fetched page.
- **FR-005**: The system MUST raise `EmptyContentError` when `div.content-html` yields no extractable text after stripping.
- **FR-006**: The system MUST strip all UI chrome within `div.codeMirror-wrapper` blocks — specifically `div.codeHeader` (which contains the language label div and the cancel icon) — leaving only the code content in `pre > code`.
- **FR-007**: The system MUST emit fenced Markdown code blocks for each `div.codeMirror-wrapper`, using the language identifier from `div.nameLanguage` (normalised to lowercase), or no language identifier when the label is absent, empty, or "plain text".
- **FR-008**: The system MUST collapse runs of three or more consecutive blank lines in the output to a single blank line.
- **FR-009**: The system MUST NOT include non-content page elements in the output: sidebar trending links, ads, author action buttons, sign-in prompts, tag pills, attribution footers, breadcrumbs, and publish metadata.

### Key Entities

- **DZone Article**: A single article page at `dzone.com/articles/<slug>`. Key attributes: title (`h1.article-title`), body (`div.content-html`), code blocks (`div.codeMirror-wrapper`).
- **CodeMirror Block**: A code block widget contained in `div.codeMirror-wrapper`. Contains `div.codeHeader` (UI chrome to strip) with `div.nameLanguage` (language label), and `div.codeMirror-code--wrapper` wrapping the server-rendered `pre > code` element.
- **DOM Element Taxonomy**:
  - Keep: `div.content-html` (article body); `h1.article-title` (title); `pre > code` within CodeMirror blocks (code content); all standard inline/block elements within content-html (p, h2, h3, ul, ol, blockquote, a, img, table).
  - Strip (UI within code blocks): `div.codeHeader` inside each `div.codeMirror-wrapper`.
  - Not targeted (outside `div.content-html`, naturally excluded): `div.trending-sidebar`, `div.author-n-useraction`, `div.signin-prompt`, `div.article-tag-pill-container`, `div.attribution`, ad divs, modal divs, breadcrumb `ol`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A free public DZone article returns Markdown containing the full title and body text with zero non-content elements (navigation, ads, sign-in prompts, sidebar, tag pills).
- **SC-002**: Extraction completes within the base class 30-second fetch timeout on stable internet.
- **SC-003**: A DZone URL that is not an article page raises `UnsupportedContentTypeError` within the normal fetch timeout.
- **SC-004**: The extracted Markdown contains no consecutive blank-line runs of three or more lines.
- **SC-005**: Articles containing CodeMirror code blocks have all code blocks preserved as fenced Markdown code blocks with the correct language tag.
- **SC-006**: The new provider is exercised by at least three integration tests using real network requests to the three reference article URLs provided by the user, matching the snapshot-based pattern established by existing providers.

## Assumptions

- DZone public articles are freely accessible without authentication; only `dzone.com/articles/<slug>` URLs are in scope for v1.
- The `div.content-html` selector is stable across standard article pages. Non-article paths (refcards at `/refcardz/`, topic pages at `/topics/`, etc.) do not use this container and naturally raise `UnsupportedContentTypeError`.
- The code content in CodeMirror blocks is server-rendered inside `pre > code` elements (confirmed via live DOM inspection across two reference articles); JavaScript execution is not required.
- DZone does not use subdomains for article content (no `*.dzone.com` pattern needed); only the primary domain `dzone.com` is registered.
- The implementation follows the existing provider pattern: one new file under `src/mdfetch/providers/dzone.py`, no changes to shared infrastructure.
- The base class retry/timeout behaviour (3 retries, 30-second timeout) is inherited without modification.
- The article subtitle (`div.subhead > h3`) is intentionally excluded from the extracted output; it is structural metadata, not body content.
