# Research: mdfetch-cli

## CLI Framework Decision

- **Decision**: Use `click`.
- **Rationale**: The project's Python Application Blueprint mandates `click` or `typer`. `click` is a lightweight, widely adopted standard for CLI tools in Python. It handles argument parsing, standard help interfaces, and exit codes elegantly.
- **Alternatives considered**:
  - `typer`: Adds type-hint-based parsing but introduces another dependency layer (Pydantic). `click` is simpler for a single-command tool.
  - `argparse`: Built-in, but the project blueprint specifically prefers `click` or `typer` for consistency across tools.

## Error Handling

- **Decision**: Catch `mdfetch.exceptions.MdfetchError` (and its subclasses) in the CLI entry point, print `str(err)` to `sys.stderr` via `click.secho(err='red')`, and call `sys.exit(1)`.
- **Rationale**: `mdfetch` already encapsulates all expected failures in the `MdfetchError` hierarchy. We avoid exposing tracebacks to end users unless an unexpected bug occurs.
- **Alternatives considered**: Silently returning empty output or logging the error. However, CLI tools should clearly indicate failure via non-zero exit codes and standard error.
