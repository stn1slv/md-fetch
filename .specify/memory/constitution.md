<!--
Sync Impact Report:
- Version change: N/A → 1.0.0
- List of modified principles:
  - Added: I. Provider Pattern Architecture
  - Added: II. Technology Stack
  - Added: III. Coding Standards
  - Added: IV. Testing Requirements
  - Added: V. Packaging and Distribution
- Added sections: Core Principles, Governance
- Removed sections: N/A
- Templates requiring updates:
  - .specify/templates/plan-template.md: ✅ updated
  - .specify/templates/spec-template.md: ✅ updated
  - .specify/templates/tasks-template.md: ✅ updated
- Follow-up TODOs:
  - TODO(RATIFICATION_DATE): Exact ratification date is unknown, using today's date tentatively.
-->
# mdfetch Constitution

## Core Principles

### I. Provider Pattern Architecture
The system MUST enforce a strict Provider Pattern. An abstract base class or interface MUST be defined for all extractors. Adding support for new platforms MUST only require creating a new class that inherits from the base extractor, strictly adhering to the Open/Closed Principle. Code duplication is explicitly PROHIBITED. All shared logic for downloading, cleaning, or formatting MUST reside in the base class or shared utilities.
Rationale: Ensures high extensibility and maintainability as new blogging platforms are supported.

### II. Technology Stack
The project MUST exclusively use the following technologies for core operations:
- **Network Requests:** `httpx` (or `requests`)
- **HTML Parsing:** `BeautifulSoup`
- **Markdown Conversion:** `Markdownify`
- **Testing:** `pytest`
Rationale: Standardizing the stack prevents dependency bloat and ensures consistency across extractor implementations.

### III. Coding Standards
All functions and methods MUST use strict Python type hinting. The codebase MUST adhere to PEP 8 style guidelines. Variable names, docstrings, and comments MUST use clear, straightforward English vocabulary.
Rationale: Guarantees complete readability, enables static analysis, and ensures long-term maintainability.

### IV. Testing Requirements
The test suite MUST mandate the creation of integration tests. These tests MUST verify functionality by providing real links from supported platforms to the library and asserting that the returned string accurately matches the expected Markdown output.
Rationale: End-to-end integration tests are the only way to prove the extractors successfully parse real-world web pages.

### V. Packaging and Distribution
The project directory structure MUST follow modern Python packaging best practices for distribution on PyPI. It MUST utilize a `pyproject.toml` file and a `src/` layout.
Rationale: Conforms to modern Python ecosystem standards, ensuring frictionless installation for users.

## Governance
This Constitution supersedes all other practices. Amendments require documentation, approval, and a migration plan.

- **Amendment Procedure:** Any changes to these principles must increment the constitution version.
- **Versioning Policy:** Semantic versioning applies (MAJOR for incompatible governance changes, MINOR for new principles, PATCH for wording fixes).
- **Compliance Review:** All Pull Requests MUST be reviewed against these core principles.

**Version**: 1.0.0 | **Ratified**: TODO(RATIFICATION_DATE): Unknown, tentatively 2026-05-14 | **Last Amended**: 2026-05-14
