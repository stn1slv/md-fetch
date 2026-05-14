# Developer Quickstart: mdfetch

**Date**: 2026-05-14 | **Plan**: [plan.md](plan.md)

## Install

```bash
pip install mdfetch
```

## Extract a Medium article

```python
from mdfetch import extract

markdown = extract("https://medium.com/@author/article-title-slug")
print(markdown)
```

That's it. No configuration, no API keys, no setup beyond the install.

## Handle errors

```python
from mdfetch import (
    extract,
    MdfetchError,
    UnsupportedPlatformError,
    UnsupportedContentTypeError,
    FetchError,
    HTTPStatusError,
    EmptyContentError,
)

try:
    markdown = extract(url)
except UnsupportedPlatformError:
    print("This domain is not supported yet.")
except UnsupportedContentTypeError:
    print("This Medium URL is not an article (try a profile or tag page URL?)")
except HTTPStatusError as e:
    print(f"Server returned HTTP {e.status_code}")
except FetchError:
    print("Network error — check your connection or try again.")
except EmptyContentError:
    print("The article body appears to be empty or image-only.")
except MdfetchError as e:
    print(f"Something went wrong: {e.message}")
```

## Run the test suite

```bash
# Unit tests only (fast, offline)
make test

# Include integration tests (requires internet access, uses real Medium URLs)
pytest -m integration
```

## Project layout

```text
src/mdfetch/         ← library source (installed by pip)
  __init__.py        ← exposes extract() and all exception classes
  exceptions.py      ← MdfetchError hierarchy
  router.py          ← maps URL domains to providers
  base.py            ← BaseExtractor ABC
  providers/
    medium.py        ← MediumExtractor (the only provider in v1)

tests/
  unit/              ← fast, no network
  integration/       ← requires internet; marked with @pytest.mark.integration
```

## Extend with a new platform

1. Create `src/mdfetch/providers/<platform>.py`
2. Inherit from `BaseExtractor`, set `DOMAINS`, implement `clean_html` and `convert_to_markdown`
3. Register the new class in `src/mdfetch/router.py`
4. No other files need to change
