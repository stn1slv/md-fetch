# Feature Specification: [FEATURE NAME]

**Feature Branch**: `[###-feature-name]`

**Created**: [DATE]

**Status**: Draft

**Input**: User description: "$ARGUMENTS"

## User Scenarios & Testing *(mandatory)*

<!--
  IMPORTANT: User stories should be PRIORITIZED as user journeys ordered by importance.
  Each user story/journey must be INDEPENDENTLY TESTABLE - meaning if you implement just ONE of them,
  you should still have a viable MVP (Minimum Viable Product) that delivers value.

  Assign priorities (P1, P2, P3, etc.) to each story, where P1 is the most critical.
  Think of each story as a standalone slice of functionality that can be:
  - Developed independently
  - Tested independently
  - Deployed independently
  - Demonstrated to users independently
-->

### User Story 1 - [Brief Title] (Priority: P1)

[Describe this user journey in plain language]

**Why this priority**: [Explain the value and why it has this priority level]

**Independent Test**: [Describe how this can be tested independently - e.g., "Can be fully tested by calling `extract()` with a specific URL and verifying the returned Markdown contains expected content"]

**Acceptance Scenarios**:

1. **Given** [initial state], **When** [action], **Then** [expected outcome]
2. **Given** [initial state], **When** [action], **Then** [expected outcome]

---

### User Story 2 - [Brief Title] (Priority: P2)

[Describe this user journey in plain language]

**Why this priority**: [Explain the value and why it has this priority level]

**Independent Test**: [Describe how this can be tested independently]

**Acceptance Scenarios**:

1. **Given** [initial state], **When** [action], **Then** [expected outcome]

---

### User Story 3 - [Brief Title] (Priority: P3)

[Describe this user journey in plain language]

**Why this priority**: [Explain the value and why it has this priority level]

**Independent Test**: [Describe how this can be tested independently]

**Acceptance Scenarios**:

1. **Given** [initial state], **When** [action], **Then** [expected outcome]

---

[Add more user stories as needed, each with an assigned priority]

### Edge Cases

<!--
  ACTION REQUIRED: The content in this section represents placeholders.
  Fill them out with the right edge cases for the specific platform/feature.
-->

- What happens when the URL points to a non-article page (homepage, profile, tag listing)?
- How does the system handle paywalled or subscriber-only content?
- What happens when the article body is present but contains no extractable text?
- How does the system behave when the platform returns an HTTP error (404, 429, 503)?
- What happens when the article contains embedded content (tweets, videos, iframes)?

## Requirements *(mandatory)*

<!--
  ACTION REQUIRED: The content in this section represents placeholders.
  Fill them out with the right functional requirements.
-->

### Functional Requirements

- **FR-001**: The system MUST route all `[platform domain]` URLs to the new provider using the existing domain-registration mechanism (`@register` decorator + `DOMAINS` frozenset).
- **FR-002**: The system MUST extract the main article body from the platform's page and return it as clean Markdown.
- **FR-003**: The system MUST strip all non-content elements (navigation, subscription CTAs, author bios, social buttons, footers) before Markdown conversion.
- **FR-004**: The system MUST prepend the article title as a top-level Markdown heading (`# Title`).
- **FR-005**: The system MUST preserve structural content: headings, paragraphs, lists, code blocks, blockquotes, hyperlinks, and images.
- **FR-006**: The system MUST raise `UnsupportedContentTypeError` when the page does not contain a recognisable article body element.
- **FR-007**: The system MUST raise `EmptyContentError` when the article body yields no extractable text after stripping.
- **FR-008**: The system MUST collapse runs of three or more consecutive blank lines to a single blank line.

*Example of marking unclear requirements:*

- **FR-009**: System MUST handle [NEEDS CLARIFICATION: paywalled content — return preview or raise error?]
- **FR-010**: System MUST treat HTTP 429 as [NEEDS CLARIFICATION: retryable or non-retryable?]

### Key Entities *(include if feature involves data)*

- **[Platform] Post**: A single article page at a specific URL pattern. Key attributes: title, subtitle (optional), body content, author, publication date.
- **DOM Element Taxonomy**: Mapping of CSS selectors to actions (keep, strip, replace) for the platform's HTML structure.

## Success Criteria *(mandatory)*

<!--
  ACTION REQUIRED: Define measurable success criteria.
  These must be technology-agnostic and measurable.
-->

### Measurable Outcomes

- **SC-001**: A free public article returns Markdown containing the full title and body text with zero non-content elements (navigation, subscription prompts, author bios).
- **SC-002**: Extraction completes within the base class 30-second fetch timeout on stable internet.
- **SC-003**: Non-article URLs raise `UnsupportedContentTypeError` within the normal fetch timeout.
- **SC-004**: The extracted Markdown contains no consecutive blank-line runs of three or more lines.
- **SC-005**: The new provider is exercised by at least one integration test using a real network request, matching the pattern established by existing providers.

## Clarifications

<!--
  Record Q&A decisions made during spec refinement sessions here.
  Format: Q: [question] → A: [decision]
  Each entry should include the session date for traceability.
-->

### Session [DATE]

- Q: [Question about ambiguous requirement] → A: [Decision made]

## Assumptions

<!--
  ACTION REQUIRED: The content in this section represents placeholders.
  Fill them out with the right assumptions based on reasonable defaults
  chosen when the feature description did not specify certain details.
-->

- The platform's public HTML page structure is stable enough for CSS-selector-based extraction; a major redesign would require an extractor update.
- Custom domains for the platform (e.g., `newsletter.example.com`) are out of scope for v1; only the primary domain and its subdomains are supported.
- No authentication is required; only publicly accessible content is targeted.
- The implementation follows the existing provider pattern: one new file under `src/mdfetch/providers/`, no changes to shared infrastructure.
- The base class retry/timeout behaviour (3 retries, 30-second timeout) is inherited without modification unless the spec explicitly overrides it.
