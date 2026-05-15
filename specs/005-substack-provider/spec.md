# Feature Specification: Substack Platform Provider

**Feature Branch**: `005-substack-provider`

**Created**: 2026-05-15

**Status**: Draft

**Input**: User description: "let's add a support of substack.com platform"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Extract a Free Substack Article (Priority: P1)

A developer calls the `extract()` function with a Substack article URL (a `*.substack.com/p/...` address). The function fetches the article and returns its content as clean Markdown, with no subscription banners, navigation menus, author bios, share buttons, or any other page chrome.

**Why this priority**: Core value of the feature — reading free Substack articles is the primary use case and a prerequisite for all other stories.

**Independent Test**: Can be fully tested by passing any free public Substack article URL (e.g., `https://getkafkanated.substack.com/p/kafka-deserves-topic-types`) to `extract()` and verifying the returned Markdown contains article headings and body text but no "Subscribe" prompts, author bios, or navigation links.

**Acceptance Scenarios**:

1. **Given** a valid URL pointing to a free public Substack post, **When** `extract()` is called, **Then** it returns a non-empty Markdown string containing the article title as a top-level heading followed by the body content.
2. **Given** a Substack post with multiple headings, paragraphs, lists, and inline links, **When** `extract()` is called, **Then** the returned Markdown preserves all headings, paragraphs, lists, and hyperlinks while stripping subscription CTAs and navigation elements.
3. **Given** a Substack post containing images, **When** `extract()` is called, **Then** images appear in the output as Markdown image syntax (`![alt](url)`).

---

### User Story 2 - Handle a Paywalled Substack Post (Priority: P2)

A developer calls `extract()` with a URL for a subscriber-only Substack post. Because only the free preview is publicly visible, the function returns the visible preview content as Markdown rather than raising an error.

**Why this priority**: Paywalled posts are common on Substack. Returning the free preview gracefully is significantly better than failing with an error when the article partially loads.

**Independent Test**: Can be fully tested by passing a URL for a known paywalled Substack post to `extract()` and confirming the result is non-empty Markdown containing the free-preview portion and no paywall nag element text.

**Acceptance Scenarios**:

1. **Given** a Substack post that is subscriber-only, **When** `extract()` is called, **Then** it returns the freely available preview section as Markdown without raising an exception.
2. **Given** a paywalled post whose free preview contains at least one paragraph, **When** `extract()` is called, **Then** the output does not contain the paywall call-to-action text (e.g., "Subscribe to read the full post").

---

### User Story 3 - Reject Non-Article Pages (Priority: P3)

A developer accidentally passes a Substack URL that does not point to an article (e.g., a publication homepage, a podcast-only episode with no transcript, or an archive page). The function raises a typed exception rather than returning empty or garbage Markdown.

**Why this priority**: Without this guard, callers could receive empty strings or malformed content silently; a typed exception lets them handle the error path explicitly.

**Independent Test**: Can be fully tested by passing a Substack homepage URL (e.g., `https://getkafkanated.substack.com/`) to `extract()` and verifying that `UnsupportedContentTypeError` is raised.

**Acceptance Scenarios**:

1. **Given** a Substack publication homepage URL, **When** `extract()` is called, **Then** `UnsupportedContentTypeError` is raised.
2. **Given** a Substack post whose extractable text is empty after stripping all chrome, **When** `extract()` is called, **Then** `EmptyContentError` is raised.

---

### Edge Cases

- What happens when a Substack post contains only an embedded video (no prose)?
- How does the system handle Substack posts with footnotes — are they preserved or stripped?
- How does the system behave when a post's images are behind a CDN that requires authentication (subscriber-only images)?
- What happens when a valid `*.substack.com` URL returns an HTTP error (404, 503)?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST route all `substack.com` and `*.substack.com` URLs to the Substack provider using the existing domain-registration mechanism.
- **FR-002**: The system MUST extract the main article body from a Substack post page and return it as clean Markdown.
- **FR-003**: The system MUST strip all non-content elements from the article page before conversion, including: navigation headers, subscription call-to-action blocks, paywall nag prompts, social share buttons, author bio sections, comment sections, and page footers.
- **FR-004**: The system MUST ensure the article title appears exactly once as a top-level Markdown heading (`# Title`) in the output: prepend it from the page header element only when the article body does not already contain an `<h1>` matching the title; if the title is already present in the body, it MUST NOT be duplicated.
- **FR-005**: The system MUST preserve the article's structural content: headings (all levels), paragraphs, ordered and unordered lists, inline code, fenced code blocks, blockquotes, hyperlinks, and images.
- **FR-006**: The system MUST raise `UnsupportedContentTypeError` when the fetched page does not contain a recognisable Substack article body element.
- **FR-007**: The system MUST raise `EmptyContentError` when the article body is present but yields no extractable text after stripping.
- **FR-008**: For paywalled posts, the system MUST silently extract only the publicly visible free-preview section (content before the paywall divider) without raising an exception and without appending any truncation marker, provided the preview contains at least some text.
- **FR-009**: The system MUST collapse runs of three or more consecutive blank lines to a single blank line in the output Markdown.
- **FR-010**: The system MUST NOT treat HTTP 429 responses from Substack as a non-retryable condition; 429 MUST be retried up to the configured retry count with the standard fixed delay, identical to other transient HTTP errors.
- **FR-011**: The system MUST convert embedded third-party content (e.g., tweet embeds, YouTube video iframes, and similar rich-media widgets) to plain anchor links using the embed's source URL, discarding the embed wrapper — matching the pattern used by the dev.to provider for iframe and liquid-tag embeds.

### Key Entities

- **Substack Post**: A single article page at a `*.substack.com/p/<slug>` URL (or equivalent custom-domain path). Key attributes: title, subtitle (optional), author, publication date, body content (free or paywalled preview).
- **Free Preview**: The portion of a paywalled post that is publicly readable without a subscription. Bounded in the DOM by a paywall divider element.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A free public Substack article returns Markdown that contains the full article title and body text with zero subscription prompt phrases (e.g., "Subscribe", "This post is for paid subscribers").
- **SC-002**: A paywalled Substack post returns a non-empty Markdown string (the free preview) without raising an exception, provided the free preview contains at least one paragraph.
- **SC-003**: A Substack homepage URL raises `UnsupportedContentTypeError` within the normal fetch timeout.
- **SC-004**: The extracted Markdown for any article contains no consecutive blank-line runs of three or more lines.
- **SC-005**: The new provider is exercised by at least one integration test using a real network request, matching the pattern established by existing providers.

## Clarifications

### Session 2026-05-15

- Q: When `extract()` encounters a paywalled post, what should it return? → A: Return only the free-preview content silently (no truncation marker, no exception).
- Q: Should HTTP 429 from Substack be retried or raised immediately? → A: Retry up to the configured retry count (treat 429 like any transient error).
- Q: What should the extractor do with rich embeds (tweets, YouTube videos, etc.)? → A: Convert embeds to plain anchor links (same as dev.to iframe handling).
- Q: If the article title appears inside the body HTML, should the extractor still prepend it from the header? → A: Include title exactly once — prepend from header only when not already present in the body.

## Assumptions

- Substack's public HTML page structure (article body container class/element) is stable enough for CSS-selector-based extraction; if Substack performs a major redesign, the extractor will require an update.
- Custom Substack domains (e.g., a publication hosted at `newsletter.example.com` rather than `*.substack.com`) are **out of scope for v1**; only `substack.com` and `*.substack.com` hostnames are supported.
- The third example URL provided (`netapinotes.com`) is hosted on Ghost, not Substack, and is therefore out of scope for this feature.
- Substack podcast episode pages that include a written transcript are treated the same as regular article posts; episodes with no transcript text will trigger `EmptyContentError`.
- Footnotes rendered in Substack's HTML will be handled on a best-effort basis by `markdownify`; no special footnote normalisation (beyond what markdownify provides by default) is required for v1.
- No authentication is required; only publicly accessible (free or free-preview) content is targeted.
- The implementation follows the existing provider pattern: one new file `src/mdfetch/providers/substack.py`, no changes to shared infrastructure.
