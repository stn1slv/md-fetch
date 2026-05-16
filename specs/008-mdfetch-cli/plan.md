# Implementation Plan: mdfetch-cli

**Branch**: `008-mdfetch-cli` | **Date**: 2026-05-16 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/008-mdfetch-cli/spec.md`

## Summary

Add a CLI entry point named `md-fetch` using the `click` framework. This CLI will accept a single URL, fetch the Markdown utilizing the existing library, and print it to standard output or save it to a specified file while providing graceful error handling.

## Technical Context

**Language/Version**: Python 3.12+

**Primary Dependencies**: `httpx`, `BeautifulSoup`, `markdownify`, `pytest`, `click` (new dependency for CLI)

**Target Platform**: PyPI library (cross-platform CLI tool)

**Project Type**: Library + CLI

**Performance Goals**: Inherits base class 30-second fetch timeout.

**Constraints**: Must use `click` framework. Handle `MdfetchError` subclasses explicitly without tracebacks.

## Constitution Check

*GATE: Must pass before implementation. Re-check after design phase.*

- [x] Validates Provider Pattern Architecture (N/A - does not create a new provider, but wraps existing logic cleanly)
- [x] Confirms Technology Stack (Using `click` as per application blueprint for CLI frameworks)
- [x] Adheres to Coding Standards (PEP 8, Type Hinting, Clear Vocabulary)
- [x] Incorporates Integration Testing (Requires CLI invocation tests, though it's mainly wrapping tested logic)
- [x] Respects Packaging and Distribution standards (`pyproject.toml` integration via `[project.scripts]`)

## Project Structure

### Documentation (this feature)

```text
specs/008-mdfetch-cli/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (future)
```

### Source Code

```text
src/mdfetch/
└── cli.py                 # NEW: click command implementation

tests/integration/
└── test_cli_integration.py # NEW: testing the CLI entry point
```

**Non-runtime changes**: Update `pyproject.toml` to add `click` dependency and `project.scripts` configuration. Update `README.md` to document CLI usage.

## Extraction Algorithm (CLI Wrapper)

```python
import click
from mdfetch import extract
from mdfetch.exceptions import MdfetchError

@click.command()
@click.argument("url")
@click.option("-o", "--output", type=click.Path(writable=True, dir_okay=False), help="Save Markdown to this file")
def main(url, output):
    try:
        content = extract(url)
        if output:
            with open(output, "w", encoding="utf-8") as f:
                f.write(content)
        else:
            click.echo(content)
    except MdfetchError as e:
        click.secho(str(e), err=True, fg="red")
        raise click.Abort()
```

## Error Mapping

| Condition | Exception | CLI Behavior |
|-----------|-----------|--------------|
| Any `MdfetchError` | `MdfetchError` subclasses | Catch, print `str(e)` to stderr, exit code `1` |
| File write error | `IOError` / `OSError` | Propagated or caught by Click Path validation |
| Invalid URL option | N/A | Click usage error, exits with `2` |

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| None | N/A | N/A |
