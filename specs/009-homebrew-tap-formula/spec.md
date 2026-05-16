# Feature Specification: Homebrew Tap Formula

**Feature Branch**: `009-homebrew-tap-formula`

**Created**: 2026-05-16

**Status**: Draft

**Input**: User description: "Add a Homebrew formula to stn1slv/homebrew-tap so users can install the md-fetch CLI via `brew install stn1slv/tap/md-fetch`. Automate keeping the formula up to date by extending the existing publish pipeline."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Install md-fetch via Homebrew (Priority: P1)

A macOS or Linux developer who does not want to manage a Python environment can install the `md-fetch` CLI using a single Homebrew command. After installation, the `md-fetch` binary is immediately available on the `PATH` without any additional configuration.

**Why this priority**: This is the core user-facing outcome of the feature. All other stories depend on this working correctly, and it delivers the primary value: frictionless installation for users unfamiliar with Python packaging.

**Independent Test**: Can be fully tested by running `brew install stn1slv/tap/md-fetch` on a clean machine and verifying that `md-fetch --version` exits with code 0 and prints a version string.

**Acceptance Scenarios**:

1. **Given** a macOS or Linux machine with Homebrew installed, **When** the user runs `brew install stn1slv/tap/md-fetch`, **Then** the installation completes without errors and `md-fetch` is available on the PATH.
2. **Given** a successful installation, **When** the user runs `md-fetch --version`, **Then** the command exits with code 0 and outputs the installed package version.
3. **Given** a successful installation, **When** the user runs `md-fetch <url>` with a supported URL, **Then** the command returns Markdown output, confirming all dependencies are correctly bundled.
4. **Given** an existing installation, **When** the user runs `brew upgrade stn1slv/tap/md-fetch`, **Then** the installation upgrades to the latest published version.

---

### User Story 2 - Formula Stays in Sync with PyPI Releases (Priority: P2)

When a new version of `md-fetch` is published to PyPI, the Homebrew formula in `stn1slv/homebrew-tap` is updated automatically without any manual intervention from the maintainer. Users running `brew upgrade` receive the new version promptly.

**Why this priority**: Without automation, every release requires a manual tap update. Automation eliminates this maintenance burden and ensures Homebrew users are never left on outdated versions.

**Independent Test**: Can be tested by triggering a release workflow and verifying that the homebrew-tap repository receives a commit updating the formula's version and checksum before the CI workflow completes.

**Acceptance Scenarios**:

1. **Given** a new version is successfully published to PyPI, **When** the release pipeline completes, **Then** the formula in `stn1slv/homebrew-tap` reflects the new version number and correct integrity checksum.
2. **Given** a new version is successfully published to PyPI, **When** the release pipeline completes, **Then** the tap update is committed and pushed without any manual step from the maintainer.
3. **Given** the automated tap update fails (e.g., token invalid, network error), **When** the pipeline completes, **Then** the failure is reported as a visible CI job failure, alerting the maintainer to intervene manually.
4. **Given** a published package, **When** a user on the previous formula version runs `brew upgrade`, **Then** they receive the newly published version.

---

### User Story 3 - Discover Homebrew Installation via Documentation (Priority: P3)

A new user reading the project README discovers that Homebrew is the recommended installation path on macOS and can install `md-fetch` without reading further instructions.

**Why this priority**: Documentation discoverability ensures users find the simplest installation path. This is lower priority because the formula itself can function without README changes, but documentation completeness is required for the feature to be considered fully shipped.

**Independent Test**: Can be verified by reviewing the README and confirming a `brew install stn1slv/tap/md-fetch` instruction appears in the Install section.

**Acceptance Scenarios**:

1. **Given** the updated README, **When** a user visits the install section, **Then** `brew install stn1slv/tap/md-fetch` is present as an installation option alongside the existing `pip install mdfetch` instruction.
2. **Given** the README install section, **When** a user follows the brew instruction verbatim, **Then** the installation succeeds.

---

### Edge Cases

- What if the Homebrew tap repository is temporarily unavailable when the pipeline tries to push the formula update?
- What if the `TAP_GITHUB_TOKEN` has expired or been revoked at the time of a release?
- What if a PyPI release is subsequently yanked — should the formula be rolled back or left at the yanked version?
- What if two releases are published in rapid succession — will the second pipeline run update the formula correctly even if the first is still running? *(Addressed: `concurrency: group=homebrew-tap-update, cancel-in-progress=false` serializes runs so the second waits for the first to complete.)*
- What if the `brew test` verification step fails after installation (e.g., a missing transitive dependency not declared in the formula)?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: A Homebrew formula for the `md-fetch` package MUST be available in the `stn1slv/homebrew-tap` repository so that users can add the tap and install the tool with standard Homebrew commands.
- **FR-002**: The formula MUST install a working `md-fetch` binary into Homebrew's `bin/` directory, making it immediately available on the user's PATH after installation.
- **FR-003**: The formula MUST bundle all runtime dependencies so that no external Python environment or manual dependency installation is required by the user.
- **FR-004**: The formula MUST include a `brew test` block that verifies the installed binary runs successfully (i.e., `md-fetch --version` exits with code 0).
- **FR-005**: When a new version is published to the PyPI package index, the release pipeline MUST automatically update the formula with the new version number and the correct integrity checksum of the published source archive. The checksum fetch MUST retry up to 3 times with 30-second intervals if PyPI does not yet serve the new release, before treating the step as failed.
- **FR-006**: The automated formula update MUST commit and push the change to `stn1slv/homebrew-tap` using a dedicated access token with write permissions scoped to that repository only.
- **FR-007**: If the automated formula update step fails for any reason (network error, authentication failure, PyPI propagation timeout after 3 retries, push conflict), the failure MUST be surfaced as a failed CI job, preventing silent divergence between PyPI and Homebrew.
- **FR-008**: The project README MUST include the `brew install stn1slv/tap/md-fetch` command in the installation section as a secondary option beneath the existing `pip install mdfetch` instruction, so that Homebrew users can discover it without searching elsewhere.
- **FR-009**: The repository settings MUST document the required `TAP_GITHUB_TOKEN` secret (a personal access token with write access to `stn1slv/homebrew-tap`) so that the automation can be reproduced by any future maintainer.

### Key Entities

- **Homebrew Formula**: A declarative package definition in `stn1slv/homebrew-tap` describing how to install `md-fetch`, including its source URL, integrity checksum, dependencies, and test procedure.
- **PyPI Source Archive (sdist)**: The `.tar.gz` source distribution published to PyPI for each release; the formula uses this archive as its source and verifies it against a SHA-256 checksum.
- **Release Pipeline**: The existing GitHub Actions workflow that publishes `md-fetch` to PyPI; this feature extends it with a post-publish job to keep the Homebrew formula in sync.
- **TAP_GITHUB_TOKEN**: A GitHub Personal Access Token with write access to the `stn1slv/homebrew-tap` repository, stored as a secret in the `md-fetch` repository and consumed exclusively by the tap-update job.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A user with Homebrew installed can complete the full `md-fetch` installation using a single command, with no Python environment setup required, in under 3 minutes on a standard broadband connection.
- **SC-002**: The Homebrew formula's built-in test (`brew test md-fetch`) passes on macOS and Linux after every installation.
- **SC-003**: The formula in `stn1slv/homebrew-tap` is updated within 10 minutes of PyPI publish confirmation — no manual maintainer action is required.
- **SC-004**: Formula update failures produce a visible CI job failure on every failed attempt, with zero silent failures.
- **SC-005**: The README install section includes the Homebrew installation command, enabling users to discover and use it without prior knowledge of the project's Python packaging.

## Clarifications

### Session 2026-05-16

- Q: Should the tap-update job retry if PyPI does not immediately serve the new release's sdist checksum? → A: Retry up to 3 times with 30-second intervals before failing.
- Q: What is the measurable time bound for SC-003 (formula update after PyPI publish)? → A: Within 10 minutes of PyPI publish confirmation.
- Q: Where should the brew install option appear in the README relative to pip? → A: Pip remains first (universal); brew added as a secondary option below.

### Revision: Implementation Sync 2026-05-16
- **Edge Case #4**: Resolved by `concurrency: group=homebrew-tap-update` in the CI job — concurrent release runs are serialized rather than racing.
- **FR-006**: Scoping clarified in implementation — `TAP_GITHUB_TOKEN` must be a fine-grained PAT (`Contents: read+write` on `stn1slv/homebrew-tap` only).

## Assumptions

- Homebrew is already installed on the user's machine; the feature does not cover installing Homebrew itself.
- The formula targets the standard Homebrew installation on both macOS and Linux; Windows (WSL) is out of scope.
- Only the source distribution (sdist) is used as the formula's source artifact; binary wheels are not referenced by the formula.
- A `TAP_GITHUB_TOKEN` PAT will be created and added to the `md-fetch` repository secrets by the maintainer before the automation is first used; this is a one-time manual prerequisite outside the automated workflow.
- If a PyPI release is yanked after the formula has been updated, the formula is not automatically rolled back; the maintainer handles yanked-release scenarios manually.
- The `stn1slv/homebrew-tap` repository already exists and accepts formula files under `Formula/`; no structural changes to the tap are needed.
- The existing release pipeline publishes to PyPI first; the tap-update job runs after a confirmed successful publish and does not block the PyPI publish if it fails.
