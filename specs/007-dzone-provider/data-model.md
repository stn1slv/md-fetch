# Data Model: DZone Platform Provider

**Branch**: `007-dzone-provider` | **Date**: 2026-05-16

## Entities

### DZone Article

A single published article page at `dzone.com/articles/<slug>`.

| Attribute | Source (DOM selector) | Type | Notes |
|-----------|----------------------|------|-------|
| `title` | `h1.article-title` in `div.title > div.header-title` | `str` | Always present; prepended as `# Title` |
| `body` | `div.content-html` | `Tag` | Main article prose; standard HTML elements + `div.codeMirror-wrapper` blocks |

### CodeMirror Block

A code block widget inside `div.content-html`, rendered by the DZone editor.

| Attribute | Source (DOM selector) | Type | Notes |
|-----------|----------------------|------|-------|
| `language` | `div.nameLanguage` inside `div.codeHeader` | `str \| None` | Lowercased; "plain text" → `""` (no fence info) |
| `code` | `pre > code` inside `div.codeMirror-code--wrapper` | `str` | Server-rendered; no JS required |

### Structural Elements to Preserve

| Element | Representation in Markdown |
|---------|---------------------------|
| `<h2>`, `<h3>` | `## Heading`, `### Heading` |
| `<p>` | Paragraph block |
| `<ul>`, `<ol>`, `<li>` | Unordered / ordered lists |
| `<a>` | `[text](url)` |
| `<img>` | `![alt](url)` |
| `<code>` (inline) | `` `code` `` |
| `<pre><code>` (in codeMirror-wrapper) | Fenced code block with language info |
| `<table>` (inside `div.table-responsive`) | Markdown table |
| `<blockquote>` | `> quote` |

### Elements to Decompose (strip entirely)

| Element | CSS Identifier | Reason |
|---------|---------------|--------|
| Code block UI header | `div.codeHeader` (inside `div.codeMirror-wrapper`) | Contains language label div + cancel icon — pure UI chrome |

### Elements Outside Body (naturally excluded by container isolation)

| Element | Location |
|---------|---------|
| Sidebar trending links | `div.trending-sidebar` — sibling of `div.content-html`'s ancestor |
| Author action buttons | `div.author-n-useraction` — sibling of `div.content-html`'s ancestor |
| Sign-in prompt | `div.signin-prompt` — sibling of `div.content-html`'s ancestor |
| Article tag pills | `div.article-tag-pill-container` — sibling of `div.content-html`'s ancestor |
| Attribution footer | `div.attribution` — sibling of `div.content-html`'s ancestor |
| Trending article links | `div.trending.goto` — sibling of `div.content-html`'s ancestor |
| Breadcrumb navigation | `ol.breadcrumb` — in `div.header` (outside `div.content-html`) |
| Author / date metadata | `div.publish-meta` — in `div.header-title` (outside `div.content-html`) |
| Ad units | `div.ads-*`, `div.sidebar-ad` — outside `div.content-html` |
| Modal dialogs | `div.modal.fade` — outside `div.content-html` |
| Bottom sticky ad | `div.bottom-sticky-ad-container` — outside `div.content-html` |

## State Transitions

Not applicable — stateless single-call extraction. Each `extract()` call is independent.

## Validation Rules

- `div.content-html` must be present → else `UnsupportedContentTypeError`
- Final Markdown must be non-empty after strip → else `EmptyContentError`
- Output Markdown must not contain runs of 3+ consecutive blank lines
- Language label "plain text" (case-insensitive) and absent/empty label → no fence info string
