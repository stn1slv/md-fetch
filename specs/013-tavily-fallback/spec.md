# Feature Specification: tavily-fallback

**Feature Branch**: `013-tavily-fallback`

**Created**: 2026-08-01

**Status**: Draft

**Input**: User description: "add an additional mode where it would be used tavily-python as for fallback option for downloading articles from supported platforms and use it for non-supported platforms. It will load TAVILY_API_KEY from env variable"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Tavily for Non-Supported Platforms (Priority: P1)

As a user, I want to extract content from URLs that don't belong to any supported platform so that I can still get Markdown for arbitrary blogs.

**Why this priority**: Core request functionality. Enables the tool to handle a long tail of domains without writing custom extractors for each.

**Independent Test**: Can be fully tested by calling the main extraction function with an unsupported URL while `TAVILY_API_KEY` is set, verifying it returns valid Markdown.

**Acceptance Scenarios**:

1. **Given** `TAVILY_API_KEY` is set in the environment, **When** content extraction is requested for an unsupported URL, **Then** it fetches content via Tavily and returns it as Markdown.
2. **Given** `TAVILY_API_KEY` is not set, **When** content extraction is requested for an unsupported URL, **Then** it raises an error indicating the platform is unsupported.

---

### User Story 2 - Tavily as Fallback for Supported Platforms (Priority: P2)

As a user, I want the system to fall back to Tavily if the dedicated provider for a supported platform fails to extract content so that I have a higher success rate.

**Why this priority**: Secondary requirement, increases robustness for supported platforms when their HTML structure changes unexpectedly.

**Independent Test**: Can be tested by mocking a supported provider to raise an exception, and verifying the main extraction workflow catches it and successfully uses Tavily (given `TAVILY_API_KEY` is set).

**Acceptance Scenarios**:

1. **Given** `TAVILY_API_KEY` is set, **When** extraction by a supported provider fails, **Then** it fetches content via Tavily and returns it as Markdown.
2. **Given** `TAVILY_API_KEY` is not set, **When** extraction by a supported provider fails, **Then** the original provider's error is propagated.

### Edge Cases

- What happens if the Tavily API key is invalid or the quota is exceeded? (System should raise a descriptive exception).
- What happens if Tavily itself returns an error or empty content? (System should raise an appropriate error indicating content could not be extracted).
- Does the fallback mode respect the same timeout settings as primary providers? (It should respect the global or configured timeout).
- If the original provider raises a timeout error, should it still fall back to Tavily? (Yes, any extraction failure should trigger the fallback).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST implement a fallback mechanism that is triggered when a URL is not matched to any registered provider OR when a registered provider fails during extraction.
- **FR-002**: The fallback mechanism MUST utilize the `tavily-python` integration to extract article content.
- **FR-003**: The fallback mechanism MUST be enabled only if the `TAVILY_API_KEY` environment variable is present and non-empty.
- **FR-004**: If `TAVILY_API_KEY` is missing and a URL is not matched to a provider, the system MUST behave as it did previously (e.g., raise an error indicating the platform is unsupported).
- **FR-005**: If `TAVILY_API_KEY` is missing and a registered provider fails, the system MUST propagate the provider's original error.
- **FR-006**: When using the Tavily fallback, the system MUST extract the main content and return it as clean Markdown.
- **FR-007**: The system MUST handle Tavily API errors gracefully, wrapping them in appropriate domain-specific errors.

### Key Entities

- **Fallback Provider**: A handler that wraps the Tavily client to provide fallback extraction capabilities.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: An unsupported platform URL successfully returns Markdown content when `TAVILY_API_KEY` is present.
- **SC-002**: A supported platform URL where the provider is intentionally forced to fail successfully returns Markdown content via Tavily when `TAVILY_API_KEY` is present.
- **SC-003**: When `TAVILY_API_KEY` is missing, the system correctly raises exceptions for unsupported platforms and provider failures without attempting to call the fallback mechanism.
- **SC-004**: The system uses the `tavily-python` library for the fallback extraction process.

## Clarifications

### Session 2026-08-01

- None needed; all assumptions use reasonable defaults.

## Assumptions

- The `tavily-python` package will be added as a dependency managed by `uv`. We will assume it's added as a standard dependency to simplify the implementation, unless specified otherwise in planning.
- Tavily's extraction response provides content that can be easily converted to Markdown or is already in a suitable format.
- "Fallback mode" applies to all extraction exceptions raised by dedicated providers.
