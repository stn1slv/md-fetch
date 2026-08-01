# Quickstart Validation Guide

## Prerequisites
- A valid Tavily API key stored in `TAVILY_API_KEY`.
- Project dependencies installed via `uv sync`.

## Validation Scenarios

### Scenario 1: Unsupported Platform with Fallback
Validate that an unsupported platform uses the Tavily fallback when the flag is provided.

```bash
# Ensure the env var is set
export TAVILY_API_KEY="tvly-your-api-key"

# Fetch an unsupported blog url
uv run md-fetch --tavily-fallback https://example-unsupported-blog.com/article
```
**Expected Outcome**: The tool fetches the content via Tavily and prints the extracted Markdown.

### Scenario 2: Missing API Key Error
Validate that the system fails early when the flag is provided but the API key is missing.

```bash
# Unset the env var
unset TAVILY_API_KEY

# Attempt to fetch
uv run md-fetch --tavily-fallback https://example-unsupported-blog.com/article
```
**Expected Outcome**: The tool exits with a clear `MissingAPIKeyError`.

### Scenario 3: Standard Behavior Preserved
Validate that standard domains still work without the fallback flag and without the API key.

```bash
# Unset the env var
unset TAVILY_API_KEY

# Fetch a supported URL (e.g. Medium)
uv run md-fetch https://medium.com/@username/article-slug
```
**Expected Outcome**: The tool fetches the content using the native Medium provider and prints the Markdown.

### Scenario 4: Missing Fallback Flag
Validate that unsupported domains fail when the flag is NOT provided, even if the API key is present.

```bash
export TAVILY_API_KEY="tvly-your-api-key"
uv run md-fetch https://example-unsupported-blog.com/article
```
**Expected Outcome**: The tool exits with an `UnsupportedPlatformError` indicating the platform is not supported.
