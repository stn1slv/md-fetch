# Python API Contract

The `mdfetch.extract` function accepts a new keyword-only argument:

```python
def extract(
    url: str, 
    *, 
    retries: int = 3, 
    retry_delay: float = 2.0, 
    tavily_fallback: bool = False
) -> str:
```

## Exceptions

- `MissingAPIKeyError`: Raised if `tavily_fallback=True` and `TAVILY_API_KEY` is not set in the environment. Inherits from `MdfetchError`.
- `EmptyContentError`: Raised if Tavily fallback is used but returns empty content after trying both basic and advanced depths.
- `FetchError`: Raised if Tavily API calls fail for both basic and advanced depths.
