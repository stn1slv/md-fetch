# mdfetch

A Python library that extracts article content from web platforms and returns it as clean Markdown.

## Install

```bash
pip install mdfetch
```

## Usage

```python
from mdfetch import extract

# Works with any supported platform — just pass the URL
markdown = extract("https://medium.com/some-publication/article-slug-abc123")
markdown = extract("https://dev.to/username/article-slug")
markdown = extract("https://example.substack.com/p/article-slug")
print(markdown)
```

## Error handling

```python
from mdfetch import (
    extract,
    InvalidURLError,
    UnsupportedPlatformError,
    UnsupportedContentTypeError,
    FetchError,
    HTTPStatusError,
    EmptyContentError,
)

url = "https://medium.com/some-publication/article-slug-abc123"

try:
    markdown = extract(url)
except InvalidURLError as e:
    print(f"Bad URL: {e.message}")
except UnsupportedPlatformError as e:
    print(f"Platform not supported: {e.message}")
except UnsupportedContentTypeError as e:
    print(f"Not an article page: {e.message}")
except HTTPStatusError as e:
    print(f"HTTP {e.status_code}: {e.message}")
except FetchError as e:
    print(f"Network error: {e.message}")
except EmptyContentError as e:
    print(f"No content: {e.message}")
```

## Supported platforms

| Platform | Domains |
|----------|---------|
| Medium   | `medium.com`, `*.medium.com` |
| dev.to   | `dev.to` |
| Substack | `substack.com`, `*.substack.com` |

## Development

Requires [uv](https://docs.astral.sh/uv/).

```bash
make setup        # install dependencies
make test         # run unit tests
make integration  # run integration tests (requires network access)
make lint         # ruff check
make format       # ruff format
make build        # build wheel + sdist
make upgrade-deps # upgrade all dependencies
make clean        # remove build artifacts
```

## Requirements

- Python 3.12+
