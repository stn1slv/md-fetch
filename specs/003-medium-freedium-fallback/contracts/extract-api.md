# Contract: `extract()` Public API

**Feature**: Medium Freedium Fallback | **Status**: Unchanged

## Signature

```python
def extract(url: str, *, retries: int = 3, retry_delay: float = 2.0) -> str
```

## Behaviour (unchanged)

| Input | Output |
|---|---|
| Valid Medium URL, article accessible | Clean Markdown string |
| Valid Medium URL, 403 or 429 from medium.com, Freedium succeeds | Clean Markdown string (source is transparent) |
| Valid Medium URL, 403 or 429 from medium.com, Freedium also fails | Raises `FetchError` or `HTTPStatusError` |
| Valid Medium URL, other HTTP error (404, 500, …) | Raises `HTTPStatusError` after retries |
| Valid Medium URL, network timeout/error | Raises `FetchError` after retries |
| Non-Medium URL | Raises `UnsupportedPlatformError` |
| Invalid URL | Raises `InvalidURLError` |

## Exception Hierarchy (unchanged)

```
MdfetchError
├── InvalidURLError
├── UnsupportedPlatformError
├── UnsupportedContentTypeError
├── EmptyContentError
└── FetchError
    └── HTTPStatusError  (status_code: int, url: str | None)
```

## Guarantees introduced by this feature

- When fallback is invoked, `exc.url` on any raised exception contains the **original Medium URL**, not the Freedium mirror URL.
- No new exception types are introduced.
- No new parameters are added to `extract()`.
- The Freedium mirror URL is never exposed in return values or the `exc.url` field.
- `exc.url` is the authoritative public URL field and is always set to the original Medium URL when fallback fails. `exc.message` is an internal implementation detail and may contain transport-level information (e.g. the URL that was actually fetched); callers MUST NOT rely on its contents.
