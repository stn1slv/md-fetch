# CLI Contract

The `md-fetch` CLI command now accepts a new flag:

```
--tavily-fallback    Enable Tavily extraction fallback for unsupported platforms or on provider failures.
```

If the flag is provided but the `TAVILY_API_KEY` environment variable is missing, the CLI will output an error and exit with a non-zero status code.
