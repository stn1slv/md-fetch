# Implementation Plan: [FEATURE]

**Branch**: `[###-feature-name]` | **Date**: [DATE] | **Spec**: [link]

**Input**: Feature specification from `/specs/[###-feature-name]/spec.md`

**Note**: This template is filled in by the `/speckit-plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

Add a CLI flag `--tavily-fallback` to use the `tavily-python` library as a fallback extraction mechanism. This fallback will be triggered when an unsupported platform URL is requested or when a registered provider fails, starting with `extract_depth="basic"` and retrying with `advanced` on failure.

## Technical Context

<!--
  The values below reflect mdfetch's established stack.
  Override only if this feature deviates from the norm.
-->

**Language/Version**: Python 3.12+ (matches CI matrix: 3.12–3.14)

**Primary Dependencies**: `httpx`, `BeautifulSoup` / `lxml`, `markdownify`, `pytest`, `tavily-python`

**Storage**: N/A — stateless extraction library

**Testing**: `pytest` via `uv run pytest` — unit tests (no network) + integration tests (`-m integration`)

**Target Platform**: PyPI library (cross-platform)

**Project Type**: Library & CLI

**Performance Goals**: Inherits base class 30-second fetch timeout for standard providers; Tavily fallback speed relies on Tavily's latency.

**Constraints**: Fallback logic should be integrated into `mdfetch.extract` or a new fallback handler, leaving the strict domain-mapping `router` untouched.

**Scale/Scope**: Single-article extraction per call, adds external API dependency.

## Constitution Check

*GATE: Must pass before implementation. Re-check after design phase.*

- [x] Validates Provider Pattern Architecture (No code duplication, adheres to Open/Closed Principle)
- [x] Confirms Technology Stack (`httpx`, `BeautifulSoup`, `Markdownify`, `pytest`, plus explicit exception for `tavily-python`)
- [x] Adheres to Coding Standards (PEP 8, Type Hinting, Clear Vocabulary)
- [x] Incorporates Integration Testing (Real links matching expected Markdown)
- [x] Respects Packaging and Distribution standards (`pyproject.toml`, `src/` layout, `uv` for all dev workflow commands)

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md        # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
├── contracts/           # Phase 1 output (/speckit-plan command)
└── tasks.md             # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code
<!--
  ACTION REQUIRED: Replace the placeholder tree below with the concrete file
  list for this feature. The layout always follows the established provider pattern.
-->

```text
src/mdfetch/
├── cli.py                 # UPDATE: Add --tavily-fallback flag
├── __init__.py            # UPDATE: extract() to accept tavily_fallback flag and wrap with try/except
├── exceptions.py          # UPDATE: Add MissingAPIKeyError
└── fallback.py            # NEW: TavilyFallbackExtractor implementation

tests/unit/
└── test_fallback.py       # NEW: unit tests (mocked tavily client)

tests/integration/
└── test_fallback_integration.py    # NEW: integration tests (real URLs if possible)
```

**Non-runtime changes** (if any): `pyproject.toml` (add `tavily-python` dependency)

## Extraction Algorithm

<!--
  ACTION REQUIRED: Replace the pseudocode below with the actual extraction
  pipeline for this platform, derived from research.md analysis.
-->

```
extract(url, tavily_fallback=False):
  if tavily_fallback and TAVILY_API_KEY not set:
      raise MissingAPIKeyError

  try:
      provider = route(url)
      return provider.extract(url)
  except Exception as e:
      if not tavily_fallback:
          raise e
      return tavily_extract(url, timeout=30.0)

tavily_extract(url, timeout):
  client = TavilyClient(timeout=timeout)
  try:
      response = client.extract(urls=[url], extract_depth="basic")
      return parse_tavily_response(response)
  except (EmptyContentError, APIError):
      try:
          response = client.extract(urls=[url], extract_depth="advanced")
          return parse_tavily_response(response)
      except Exception as advanced_e:
          raise FetchError(f"Tavily fallback failed: {advanced_e}")

parse_tavily_response(response):
  result = response["results"][0]
  if not result.get("raw_content"):
      raise EmptyContentError
  return result["raw_content"]
```

## Error Mapping

| Condition | Exception |
|-----------|-----------|
| Fallback requested but TAVILY_API_KEY missing | `MissingAPIKeyError` |
| Fallback not requested and platform unsupported | `UnsupportedPlatformError` |
| Tavily returns empty content for both depths | `EmptyContentError` |
| Tavily API failure after all depths | `FetchError` |

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| Extends base stack dependencies | `tavily-python` needed for fallback | Raw HTTP calls rejected as spec requires the official SDK. |
