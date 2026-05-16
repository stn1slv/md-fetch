# Data Model: mdfetch-cli

No new database or internal domain entities are introduced.

## CLI Execution State

- **Input URL** (`str`): The target URL to fetch.
- **Output File** (`str | None`): An optional file path provided via `--output`.
- **Exit Code** (`int`): `0` for success, non-zero (`1`) for failure.
