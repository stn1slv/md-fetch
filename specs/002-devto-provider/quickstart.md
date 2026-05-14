# Quickstart: dev.to Extraction

**Branch**: `002-devto-provider` | **Date**: 2026-05-14

## Usage

No configuration change is required. Pass any `dev.to` article URL to the existing `extract()` function:

```python
from mdfetch import extract

markdown = extract("https://dev.to/stn1slv/integration-digest-for-december-2025-5dlp")
print(markdown)
```

The library routes the request to `DevToExtractor` automatically based on the domain.

## What the output looks like

```markdown
# Integration Digest for December 2025

![Cover image for Integration Digest for December 2025](https://media2.dev.to/...)

## Articles

🔍 [10 Tips for Improving Agentic Experience (AX)](https://nordicapis.com/...)

*Presents ten actionable integration patterns...*

## Videos

[https://www.youtube.com/watch?v=...](https://www.youtube.com/watch?v=...)
```

## Error handling

```python
from mdfetch import extract
from mdfetch.exceptions import UnsupportedContentTypeError, UnsupportedPlatformError

try:
    markdown = extract("https://dev.to/stn1slv")   # profile page, not an article
except UnsupportedContentTypeError as e:
    print(f"Not an article: {e.message}")

try:
    markdown = extract("https://example.com/article")
except UnsupportedPlatformError as e:
    print(f"Platform not supported: {e.message}")
```

## Running integration tests

```bash
uv run pytest -m integration tests/integration/test_devto_integration.py -v
```
