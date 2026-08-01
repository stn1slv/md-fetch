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

1. **Given** `TAVILY_API_KEY` is set in the environment AND the `--tavily-fallback` CLI flag is provided, **When** content extraction is requested for an unsupported URL, **Then** it fetches content via Tavily and returns it as Markdown.
2. **Given** the `--tavily-fallback` CLI flag is not provided (regardless of `TAVILY_API_KEY`), **When** content extraction is requested for an unsupported URL, **Then** it raises an error indicating the platform is unsupported.

---

### User Story 2 - Tavily as Fallback for Supported Platforms (Priority: P2)

As a user, I want the system to fall back to Tavily if the dedicated provider for a supported platform fails to extract content so that I have a higher success rate.

**Why this priority**: Secondary requirement, increases robustness for supported platforms when their HTML structure changes unexpectedly.

**Independent Test**: Can be tested by mocking a supported provider to raise an exception, and verifying the main extraction workflow catches it and successfully uses Tavily (given `TAVILY_API_KEY` is set).

**Acceptance Scenarios**:

1. **Given** `TAVILY_API_KEY` is set AND the `--tavily-fallback` CLI flag is provided, **When** extraction by a supported provider fails, **Then** it fetches content via Tavily and returns it as Markdown.
2. **Given** the `--tavily-fallback` CLI flag is not provided, **When** extraction by a supported provider fails, **Then** the original provider's error is propagated.

### Edge Cases

- What happens if the `--tavily-fallback` CLI flag is provided but the `TAVILY_API_KEY` environment variable is missing? (System should fail immediately with a configuration error).
- What happens if the Tavily API key is invalid or the quota is exceeded? (System should raise a descriptive exception).
- What happens if Tavily itself returns an error or empty content? (System should raise an appropriate error indicating content could not be extracted).
- Does the fallback mode respect the same timeout settings as primary providers? (It should respect the global or configured timeout).
- If the original provider raises a timeout error, should it still fall back to Tavily? (Yes, any extraction failure should trigger the fallback).
- What happens if Tavily extraction fails with `extract_depth="basic"`? (The system automatically retries the extraction using `extract_depth="advanced"` before finally failing).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST implement a fallback mechanism that is triggered when a URL is not matched to any registered provider OR when a registered provider fails during extraction.
- **FR-002**: The fallback mechanism MUST utilize the `tavily-python` integration to extract article content.
- **FR-003**: The fallback mechanism MUST be enabled ONLY if explicitly requested via the `--tavily-fallback` CLI flag AND the `TAVILY_API_KEY` environment variable is present and non-empty.
- **FR-004**: If the `--tavily-fallback` CLI flag is provided but the `TAVILY_API_KEY` environment variable is missing or empty, the system MUST fail immediately with a configuration error (e.g., `MissingAPIKeyError`).
- **FR-005**: If the `--tavily-fallback` CLI flag is not provided and a URL is not matched to a provider, the system MUST behave as it did previously (e.g., raise an error indicating the platform is unsupported).
- **FR-006**: If the `--tavily-fallback` CLI flag is not provided and a registered provider fails, the system MUST propagate the provider's original error.
- **FR-007**: When using the Tavily fallback, the system MUST extract the main content and return it as clean Markdown.
- **FR-008**: The system MUST first attempt extraction using `extract_depth="basic"`. If this attempt is unsuccessful (returns an error or empty content), the system MUST automatically retry the extraction using `extract_depth="advanced"`.
- **FR-009**: The system MUST handle Tavily API errors gracefully, wrapping them in appropriate domain-specific errors only after all depth retry attempts are exhausted.

### Key Entities

- **Fallback Provider**: A handler that wraps the Tavily client to provide fallback extraction capabilities.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: An unsupported platform URL successfully returns Markdown content when the `--tavily-fallback` CLI flag is provided and `TAVILY_API_KEY` is present.
- **SC-002**: A supported platform URL where the provider is intentionally forced to fail successfully returns Markdown content via Tavily when the `--tavily-fallback` CLI flag is provided and `TAVILY_API_KEY` is present.
- **SC-003**: When the `--tavily-fallback` CLI flag is missing, the system correctly raises exceptions for unsupported platforms and provider failures without attempting to call the fallback mechanism.
- **SC-004**: The system uses the `tavily-python` library for the fallback extraction process.

## Clarifications

### Session 2026-08-01

- Q: If the fallback CLI flag is provided but the `TAVILY_API_KEY` environment variable is missing, how should the system behave? → A: Fail immediately with a configuration error (e.g., `MissingAPIKeyError`)
- Q: What should be the exact name of the new CLI flag to enable the Tavily fallback? → A: `--tavily-fallback`
- Q: What extraction depth should be used for Tavily? → A: Start with `extract_depth="basic"` and if unsuccessful, switch to `extract_depth="advanced"`

## Assumptions

- The `tavily-python` package will be added as a dependency managed by `uv`. We will assume it's added as a standard dependency to simplify the implementation, unless specified otherwise in planning.
- Tavily's extraction response provides content that can be easily converted to Markdown or is already in a suitable format.
- "Fallback mode" applies to all extraction exceptions raised by dedicated providers.
