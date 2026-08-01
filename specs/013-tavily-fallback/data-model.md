# Data Model & Interfaces

## CLI Interface
- New flag: `--tavily-fallback` (boolean flag, default False)
- Added to `mdfetch/cli.py` via `@click.option('--tavily-fallback', is_flag=True, help="Enable Tavily extraction fallback for unsupported platforms or on provider failures.")`

## Core API Contract
The main entry point `extract` in `mdfetch/__init__.py` is updated:
```python
def extract(
    url: str, 
    *, 
    retries: int = 3, 
    retry_delay: float = 2.0, 
    tavily_fallback: bool = False
) -> str:
    ...
```

## Exceptions
A new exception can be defined or an existing one reused:
- `MissingAPIKeyError` (inherits from `MdfetchError`): Raised if `tavily_fallback=True` but `TAVILY_API_KEY` is not found in the environment.

## Extraction Flow State (Tavily)
- `extract_depth="basic"`
- If failure -> `extract_depth="advanced"`
- If failure -> `TavilyFallbackError` (or `FetchError` / `EmptyContentError` wrapped).
