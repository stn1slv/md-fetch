# Feature Specification: mdfetch-cli

**Feature Branch**: `[###-feature-name]`

**Created**: Saturday, May 16, 2026

**Status**: Draft

**Input**: User description: "I would like have run mdfetch as cli command"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Fetch to Standard Output (Priority: P1)

As a terminal user, I want to run `md-fetch <URL>` so that I can see the extracted Markdown content directly in my terminal.

**Why this priority**: This is the core minimal use case for a CLI tool—providing immediate access to the extraction logic without writing Python code.

**Independent Test**: Can be tested by running `md-fetch` with a valid, supported URL and verifying that the stdout contains the expected Markdown content and exits with code 0.

**Acceptance Scenarios**:

1. **Given** a valid URL from a supported provider, **When** I run `md-fetch <URL>`, **Then** the extracted Markdown is printed to stdout and the process exits with code 0.

---

### User Story 2 - Fetch and Save to File (Priority: P2)

As a terminal user, I want to specify an output file using an `--output` or `-o` flag so that I can easily save the extracted Markdown without relying on shell redirection.

**Why this priority**: Shell redirection (`>`) works, but a built-in output flag provides a better user experience and can prevent issues with encoding or partial outputs.

**Independent Test**: Can be tested by running `md-fetch <URL> -o output.md`, verifying the file is created with the correct content, and that stdout is empty.

**Acceptance Scenarios**:

1. **Given** a valid URL, **When** I run `md-fetch <URL> -o article.md`, **Then** the content is saved to `article.md`, nothing is printed to stdout, and the process exits with code 0.

---

### User Story 3 - Graceful Error Handling (Priority: P1)

As a terminal user, I want to see clear, human-readable error messages when something goes wrong (e.g., unsupported URL, network timeout) instead of raw Python tracebacks, so that I understand how to fix the issue.

**Why this priority**: Raw tracebacks are hostile to CLI users. Proper error handling ensures the tool feels like a polished product.

**Independent Test**: Can be tested by providing an unsupported URL and verifying that a clean error message is printed to stderr and the process exits with a non-zero code.

**Acceptance Scenarios**:

1. **Given** an unsupported URL, **When** I run `md-fetch <URL>`, **Then** a clear error message is printed to stderr and the process exits with a non-zero code.
2. **Given** a URL that times out, **When** I run `md-fetch <URL>`, **Then** a clear network error message is printed to stderr and the process exits with a non-zero code.

### Edge Cases

- What happens when no arguments are provided? (Should print help text and exit with an error code).
- What happens when an invalid URL string (not a URL at all) is provided?
- How does the system handle an `--output` path that points to a non-existent or read-only directory?
  *Decision: The CLI must print the standard OS/Click file error to stderr and exit with a non-zero code.*
- What happens if the `mdfetch` library raises an unexpected exception not in the `MdfetchError` hierarchy?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST provide a CLI entry point named `md-fetch` that can be executed directly from the terminal after installation.
- **FR-002**: The CLI MUST accept a single positional argument for the target URL.
- **FR-003**: The CLI MUST accept an optional `-o` / `--output` parameter to specify an output file path.
- **FR-004**: If `--output` is not provided, the CLI MUST print the extracted Markdown to standard output (stdout).
- **FR-005**: If `--output` is provided, the CLI MUST write the Markdown to the specified file and MUST NOT print the content to stdout.
- **FR-006**: The CLI MUST handle all `MdfetchError` exceptions (and subclasses) gracefully, printing a clean error message to standard error (stderr) without a traceback.
- **FR-007**: The CLI MUST return an exit code of `0` on success, and a non-zero exit code (e.g., `1`) on any failure.
- **FR-008**: The CLI MUST provide a standard `--help` interface explaining the usage and available options.

### Key Entities

- **CLI Application**: The command-line interface wrapping the core `mdfetch` extraction logic.
- **Input URL**: The web address provided by the user.
- **Output Destination**: Either standard output or a specified file path.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: After package installation/sync, typing `md-fetch --help` in the terminal successfully displays usage instructions.
- **SC-002**: Running `md-fetch` against a supported test URL successfully outputs Markdown to the terminal and exits with code 0.
- **SC-003**: Running `md-fetch` with an unsupported domain returns a non-zero exit code and prints a friendly error message to stderr (no Python traceback).
- **SC-004**: The `--output` flag successfully writes the correct Markdown string to the specified file path.

## Clarifications

### Session 2026-05-16

- Q: What should the CLI command be named? → A: `md-fetch` (to align with the user's existing `md-paste` command).

## Assumptions

- The CLI will be built using a standard Python CLI framework (e.g., `click` or `typer` as per the project's Python Application Blueprint).
- We will register the CLI command in `pyproject.toml` under `[project.scripts]`.
- The CLI will utilize the existing `mdfetch.extract()` function without modifying the core extraction logic.
- Standard output encoding will be handled natively by Python/CLI framework (typically UTF-8).