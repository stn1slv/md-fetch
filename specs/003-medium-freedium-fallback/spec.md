# Feature Specification: Medium Freedium Fallback

**Feature Branch**: `003-medium-freedium-fallback`

**Created**: 2026-05-14

**Status**: Clarified

**Input**: User description: "I want implement fallback for medium articles using https://freedium-mirror.cfd/ resource. It should be used when medium.com returns 403 or 429"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Transparent Fallback on Blocked Article (Priority: P1)

A developer calls the library's extract function with a Medium URL. The article is behind a paywall or the user is geo-blocked, causing Medium to return a 403 error. Without any code changes, the library automatically retrieves the same article via the Freedium mirror and returns clean Markdown content.

**Why this priority**: This is the core value of the feature — enabling access to paywalled or geo-restricted Medium articles without any additional effort from the caller.

**Independent Test**: Can be fully tested by calling extract with a known paywalled Medium URL and verifying clean Markdown is returned.

**Acceptance Scenarios**:

1. **Given** a valid Medium article URL that returns 403 from medium.com, **When** the caller invokes extract, **Then** the library returns clean Markdown content retrieved via the Freedium mirror.
2. **Given** a valid Medium article URL that returns 403 from medium.com, **When** the Freedium mirror also fails, **Then** the library raises an appropriate extraction error.
3. **Given** a valid Medium article URL that returns 403 from medium.com, **When** the library falls back to Freedium, **Then** the caller receives the result without any knowledge of which source was used.

---

### User Story 2 - Automatic Retry on Rate Limiting (Priority: P2)

A developer calls the library's extract function for a Medium URL. Medium responds with a 429 Too Many Requests status, indicating rate limiting. The library automatically uses the Freedium mirror as a fallback and returns clean Markdown content without requiring the caller to retry.

**Why this priority**: Rate limiting from Medium is a common operational issue. Transparent fallback prevents unnecessary failures in automated pipelines or batch processing scenarios.

**Independent Test**: Can be fully tested by simulating a 429 response from Medium and verifying the library returns content from the fallback.

**Acceptance Scenarios**:

1. **Given** a valid Medium article URL that returns 429 from medium.com, **When** the caller invokes extract, **Then** the library returns clean Markdown content retrieved via the Freedium mirror.
2. **Given** a valid Medium article URL that returns 429 from medium.com, **When** the Freedium mirror also fails, **Then** the library raises an appropriate extraction error.

---

### User Story 3 - No Fallback When Primary Succeeds (Priority: P3)

A developer calls the library's extract function for a publicly accessible Medium article. Medium responds successfully. The library returns the content directly without involving the Freedium mirror.

**Why this priority**: Preserving the existing happy-path behavior is essential for correctness and performance. The fallback must not be invoked when it is not needed.

**Independent Test**: Can be fully tested by calling extract with a freely accessible Medium URL and verifying no secondary request is made.

**Acceptance Scenarios**:

1. **Given** a valid Medium article URL that returns a successful response, **When** the caller invokes extract, **Then** the library returns clean Markdown content without making any request to the Freedium mirror.

---

### Edge Cases

- What happens when the Freedium mirror itself is unreachable (network error, timeout)?
- What happens when the Freedium mirror returns a non-200 status for an article?
- What happens if the content from the Freedium mirror is structurally different from direct Medium content (e.g., missing metadata)?
- What happens when the original Medium URL is a custom domain mapped to Medium (e.g., `blog.example.com`)?
- What happens if the 403 is due to a non-existent article (vs. paywall)?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: When a Medium article extraction results in an HTTP 403 response, the system MUST immediately attempt extraction via the Freedium mirror — no retries against medium.com are made first.
- **FR-002**: When a Medium article extraction results in an HTTP 429 response, the system MUST immediately attempt extraction via the Freedium mirror — no retries against medium.com are made first.
- **FR-003**: When the Freedium mirror is used as a fallback, the system MUST return content in the same clean Markdown format as direct extraction.
- **FR-004**: When the primary Medium request succeeds, the system MUST NOT make any request to the Freedium mirror.
- **FR-005**: When both the primary Medium request and the Freedium fallback fail, the system MUST raise an error consistent with the existing exception hierarchy.
- **FR-006**: The fallback mechanism MUST require no changes to the caller's code — the public `extract()` interface remains unchanged.
- **FR-007**: The fallback MUST only apply to Medium provider URLs; other providers are unaffected.
- **FR-008**: The fallback MUST be unconditionally active for all Medium URL extractions — no caller configuration, opt-in flag, or extractor parameter is required or supported to enable/disable it.
- **FR-009**: The fallback MUST be fully transparent to the caller — no warning, signal, metadata, or result field shall indicate which source (medium.com or Freedium) provided the content.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Articles that previously failed with a 403 paywall error are successfully extracted in at least 90% of cases where the Freedium mirror has the content available.
- **SC-002**: Articles that previously failed with a 429 rate-limit error are successfully extracted via fallback without requiring the caller to retry.
- **SC-003**: Zero changes are required in existing caller code to benefit from the fallback — existing integrations continue to work as-is.
- **SC-004**: When the primary Medium request succeeds, there is no additional latency attributable to the fallback mechanism.
- **SC-005**: All existing unit and integration tests for the Medium extractor continue to pass without modification.

## Assumptions

- The Freedium mirror constructs its article URLs by prepending its base URL to the original Medium URL (e.g., `https://freedium-mirror.cfd/https://medium.com/...`).
- The Freedium mirror's HTML structure differs from medium.com: content is in `<div class="main-content">` (no `<article>` element) and section headings use `<h4>` instead of `<h2>`/`<h3>`. A dedicated Freedium parser is required. Verified by live inspection.
- The fallback is unconditionally active for all Medium URLs — no opt-in or configuration knob exists. This was an explicit design decision.
- Fallback applies only to 403 and 429 HTTP status codes; other error codes (e.g., 404, 500) are handled by the existing error logic without triggering a fallback.
- Custom domains hosted on Medium (e.g., `*.medium.com` subdomains) are already covered by the existing Medium provider routing and will also benefit from the fallback.
- The Freedium mirror is a publicly accessible service with no authentication requirements.

## Clarifications

### Session 2026-05-14

- Q: Should the Freedium fallback be always active for all callers, or configurable (opt-in via parameter or extractor config)? → A: Always active — fallback happens automatically with no caller configuration required (Option A).
- Q: Should the Freedium fallback trigger immediately on first 403/429, or only after existing retry/backoff logic is exhausted? → A: Immediate — on first 403 or 429, skip retries against medium.com and fall back to Freedium directly (Option A).
- Q: Should the caller receive any signal (warning, metadata, result field) indicating that the Freedium fallback was used? → A: Silent — fallback is a fully internal implementation detail; no signal is exposed to the caller (Option A).
