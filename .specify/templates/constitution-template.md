# [PROJECT_NAME] Constitution
<!-- Example: mdfetch Constitution -->

## Core Principles

### [PRINCIPLE_1_NAME]
<!-- Example: I. Provider Pattern Architecture -->
[PRINCIPLE_1_DESCRIPTION]
<!-- Example: The system MUST enforce a strict Provider Pattern. An abstract base class MUST be defined for all extractors. Adding new platforms MUST only require creating a new subclass, adhering to the Open/Closed Principle. Code duplication is PROHIBITED; shared logic MUST reside in the base class. -->

### [PRINCIPLE_2_NAME]
<!-- Example: II. Technology Stack -->
[PRINCIPLE_2_DESCRIPTION]
<!-- Example: The project MUST exclusively use: httpx (network), BeautifulSoup (parsing), Markdownify (conversion), pytest (testing), uv (package management). Direct use of pip, venv, or pip-tools is PROHIBITED. -->

### [PRINCIPLE_3_NAME]
<!-- Example: III. Coding Standards -->
[PRINCIPLE_3_DESCRIPTION]
<!-- Example: All functions MUST use strict Python type hinting. Codebase MUST adhere to PEP 8. Variable names, docstrings, and comments MUST use clear English vocabulary. -->

### [PRINCIPLE_4_NAME]
<!-- Example: IV. Testing Requirements -->
[PRINCIPLE_4_DESCRIPTION]
<!-- Example: The test suite MUST include integration tests. These tests MUST verify functionality by providing real links and asserting returned Markdown matches expected output. -->

### [PRINCIPLE_5_NAME]
<!-- Example: V. Packaging and Distribution -->
[PRINCIPLE_5_DESCRIPTION]
<!-- Example: The project MUST use pyproject.toml and src/ layout. All Makefile targets MUST invoke uv run <tool> rather than calling tools directly. -->

## [SECTION_2_NAME]
<!-- Example: Additional Constraints, Error Handling Policy, etc. -->

[SECTION_2_CONTENT]
<!-- Example: All failures communicated via typed exceptions only (no logging). Custom exception hierarchy with MdfetchError as base. -->

## Governance
<!-- Constitution supersedes all other practices; Amendments require documentation, approval, migration plan -->

[GOVERNANCE_RULES]
<!-- Example: All PRs must verify compliance. Complexity must be justified. Amendment procedure: increment constitution version. Semantic versioning for governance changes. -->

**Version**: [CONSTITUTION_VERSION] | **Ratified**: [RATIFICATION_DATE] | **Last Amended**: [LAST_AMENDED_DATE]
<!-- Example: Version: 1.0.0 | Ratified: 2026-05-14 | Last Amended: 2026-05-14 -->
