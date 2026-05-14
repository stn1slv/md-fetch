# Data Model: mdfetch — Medium Extractor

**Phase**: 1 | **Date**: 2026-05-14 | **Plan**: [plan.md](plan.md)

> `mdfetch` is a stateless library. There is no database, no persistence layer, and no mutable shared state between calls. All entities below are in-memory, call-scoped objects.

---

## Entity: URL (Input)

**Description**: A string provided by the caller identifying the web page to extract.

**Attributes**:

| Attribute | Type | Description |
|---|---|---|
| `raw` | `str` | The original string as supplied by the caller |
| `scheme` | `str` | Must be `http` or `https`; any other value triggers `InvalidURLError` |
| `netloc` | `str` | The hostname used for provider routing (e.g., `medium.com`, `username.medium.com`) |
| `path` | `str` | The path portion, used to distinguish article pages from profile/tag pages |

**Validation rules**:
- `raw` must be parseable by the standard URL parser; if not, raise `InvalidURLError`
- `scheme` must be `http` or `https`; bare domain strings without a scheme are invalid
- `netloc` must match a registered provider; if not, raise `UnsupportedPlatformError`

**Lifecycle**: Created at the boundary of `extract()`, validated immediately, discarded after routing.

---

## Entity: Provider (Internal)

**Description**: A platform-specific extraction unit. Each provider is a class that fulfils the `BaseExtractor` contract.

**Attributes**:

| Attribute | Type | Description |
|---|---|---|
| `DOMAINS` | `frozenset[str]` | Class-level set of domain suffixes this provider handles (e.g., `{"medium.com"}`) |

**Relationships**:
- One-to-many with URL: a single provider handles all URLs matching its `DOMAINS`
- Produced by: the router, which maps a parsed URL's `netloc` to a provider class

**Invariants**:
- Each domain suffix is registered to exactly one provider; no overlapping registrations
- A provider never stores state between calls; every `extract()` invocation is independent

**Lifecycle**: Instantiated per call in the router; discarded after extraction completes.

---

## Entity: ExtractionResult (Output)

**Description**: The return value of a successful `extract()` call — a clean Markdown string.

**Attributes**:

| Attribute | Type | Description |
|---|---|---|
| `content` | `str` | The extracted article body as Markdown text |

**Validation rules** (asserted by integration tests):
- Non-empty string (length > 0)
- Contains no raw HTML tags (no `<tag>` patterns)
- Preserves structural elements: at least one heading, or at least one paragraph, depending on the source article

**Lifecycle**: Returned directly to the caller as a plain `str`. The library does not wrap the output in a container object; `extract()` returns `str` for simplicity.

---

## Entity: Exception (Output — failure path)

**Description**: A typed exception raised instead of returning content when extraction cannot complete.

**Hierarchy**:

```
MdfetchError (base)
├── InvalidURLError             — raised when URL string is syntactically invalid
├── UnsupportedPlatformError    — raised when domain has no registered provider
├── UnsupportedContentTypeError — raised when domain is recognised but page is not an article
├── FetchError                  — raised on network/HTTP failure
│   └── HTTPStatusError         — subclass; carries .status_code (int) attribute
└── EmptyContentError           — raised when article body yields no extractable text
```

**Attributes common to all exceptions**:

| Attribute | Type | Description |
|---|---|---|
| `message` | `str` | Human-readable explanation of the failure |
| `url` | `str \| None` | The URL that triggered the failure (where available) |

**`HTTPStatusError` additional attribute**:

| Attribute | Type | Description |
|---|---|---|
| `status_code` | `int` | The HTTP status code returned by the server |

---

## State Transitions

Because the library is stateless, the only "state machine" is the call lifecycle:

```
caller provides URL string
        │
        ▼
[VALIDATE URL] ──── invalid syntax ────► InvalidURLError
        │
        ▼
[ROUTE by domain] ── no provider ──────► UnsupportedPlatformError
        │
        ▼
[FETCH HTML] ─────── network failure ──► FetchError / HTTPStatusError
        │
        ▼
[LOCATE ARTICLE] ─── not an article ───► UnsupportedContentTypeError
        │
        ▼
[CLEAN & CONVERT] ── empty result ─────► EmptyContentError
        │
        ▼
   return str (Markdown)
```
