# Feature Specification: List Supported Platforms

**Feature Branch**: `012-list-platforms`

**Created**: 2026-06-02

**Status**: Completed

**Input**: User description: "I would like to add operation to cli tool for listing all supported platforms"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Discover supported platforms before fetching (Priority: P1)

A user who has just installed the CLI wants to know which web platforms it can
extract articles from, so they can confirm a site is supported before pasting a
URL. They run a dedicated "list" operation and receive a readable list of the
supported platform domains, printed to standard output, with a success exit
code.

**Why this priority**: This is the entire feature. Without it the user has no
way to discover supported platforms except by triggering an error on an
unsupported URL or reading the README. It delivers the complete value on its
own and is the MVP.

**Independent Test**: Invoke the CLI's list operation with no article URL and
verify it prints every supported domain and exits with code 0, without making
any network request.

**Acceptance Scenarios**:

1. **Given** the CLI is installed, **When** the user invokes the list operation, **Then** the CLI prints all supported platform domains to standard output and exits with code 0.
2. **Given** the list operation is invoked, **When** the output is produced, **Then** no network request is made and no URL argument is required.
3. **Given** a new provider has been registered in the codebase, **When** the user invokes the list operation, **Then** the newly supported domain appears in the output without any change to the list operation itself.

---

### User Story 2 - Understand multi-tenant (subdomain) support (Priority: P2)

A user knows the CLI supports Medium and Substack, which host content on
per-author subdomains (e.g. `someone.medium.com`, `someone.substack.com`). When
listing platforms, they want to understand that subdomains of those platforms
are supported too, not just the bare domain.

**Why this priority**: Useful clarity for the two multi-tenant providers, but
the core discovery value (Story 1) is already delivered without it. It refines
the output rather than enabling a new capability.

**Independent Test**: Invoke the list operation and verify that platforms which
accept subdomains are visibly distinguished from those that match an exact
domain only.

**Acceptance Scenarios**:

1. **Given** a provider that matches subdomains (Medium, Substack), **When** the user lists platforms, **Then** the output indicates that subdomains of that platform are also supported.
2. **Given** a provider that matches an exact domain only, **When** the user lists platforms, **Then** the output shows the domain without a subdomain indicator.

---

### Edge Cases

- The list operation requires no URL; invoking it together with a URL argument should have a well-defined, non-contradictory behavior (the list operation takes precedence and no extraction occurs).
- The output ordering MUST be stable and deterministic across runs (e.g. alphabetical) so output can be reasoned about and tested.
- The operation MUST succeed offline, because it reports static configuration rather than fetching anything.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The CLI MUST provide a discoverable operation, exposed as a flag/option on the existing single command, that lists all currently supported platform domains.
- **FR-001a**: When the list flag is supplied, the `URL` argument MUST be optional; supplying the flag without a URL MUST NOT be an error. Without the flag, the existing `md-fetch <URL>` behavior (URL required) MUST be unchanged.
- **FR-002**: The list operation MUST derive its output from the live provider registry, so adding or removing a provider changes the output with no separate maintenance of a hard-coded list.
- **FR-003**: The list operation MUST print results to standard output and exit with a success code (0).
- **FR-004**: The list operation MUST NOT require an article URL and MUST NOT perform any network request.
- **FR-005**: The output ordering MUST be deterministic (alphabetical by domain).
- **FR-006**: The output MUST indicate, for multi-tenant platforms, that subdomains are also supported, while showing exact-match-only platforms plainly.
- **FR-007**: The list operation MUST be documented in the CLI's own help text so users can discover it without external documentation.
- **FR-008**: When the list operation is requested, the CLI MUST NOT also attempt extraction in the same invocation.

### Key Entities

- **Supported Platform**: A domain registered to a provider. Key attributes: domain name, whether subdomains of that domain are also matched.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A user can list every supported platform with a single CLI invocation and no URL, completing in well under one second with no network access.
- **SC-002**: The listed domains exactly match the set of domains registered to providers — no missing entries and no extras.
- **SC-003**: After a new provider is added to the codebase, its domain appears in the list output with no edit to the list operation's code.
- **SC-004**: Multi-tenant platforms (those accepting subdomains) are visually distinguishable from exact-match platforms in the output.
- **SC-005**: The list operation is exercised by at least one automated test that asserts the output contains the known supported domains and exits successfully, matching the project's existing CLI test conventions.

## Clarifications

### Session 2026-06-02

- Q: How should the list operation be exposed on the CLI, given the existing required `URL` argument? → A: A flag/option on the existing single command (e.g. `--list-platforms`); the `URL` argument becomes optional when the flag is present, preserving the current `md-fetch <URL>` contract with no breaking change.

## Assumptions

- The operation is exposed as a flag/option on the existing single-command CLI (per the 2026-06-02 clarification), not a separate sub-command structure; the `URL` argument becomes optional when the flag is present. The exact flag name is an implementation detail for planning.
- "Supported platforms" means the set of registered domains exposed by the router's existing registry accessor; no new provider metadata (display names, descriptions, URLs) is introduced for v1.
- Output is plain text, one platform per line, intended for human reading in a terminal; structured formats (JSON, etc.) are out of scope for v1.
- Subdomain support is surfaced using a simple, human-readable convention (for example a wildcard prefix such as `*.medium.com`); the precise rendering is an implementation detail.
- This is a user-facing change and therefore requires a SemVer minor version bump in `pyproject.toml` and a README update, per project conventions.
