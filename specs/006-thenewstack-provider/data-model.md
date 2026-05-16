# Data Model: The New Stack Platform Provider

**Branch**: `006-thenewstack-provider` | **Date**: 2026-05-16

## Entities

### TheNewStack Article

A single published article page at `thenewstack.io/<slug>/`.

| Attribute | Source (DOM selector) | Type | Notes |
|-----------|----------------------|------|-------|
| `title` | `h1.title` in `div#tns-post-headline` | `str` | Always present; prepended as `# Title` |
| `deck` | `div.post-excerpt` in `div#tns-post-headline` | `str \| None` | Optional subtitle; rendered as plain paragraph after title |
| `body` | `div#tns-post-body-content` | `Tag` | Main article prose; 26–30 direct `<p>` children in reference articles |

### Structural Elements to Preserve

| Element | Representation in Markdown |
|---------|---------------------------|
| `<h2>`, `<h3>` | `## Heading`, `### Heading` |
| `<p>` | Paragraph block |
| `<ul>`, `<ol>`, `<li>` | Unordered / ordered lists |
| `<a>` | `[text](url)` |
| `<img>` | `![alt](url)` |
| `<code>` (inline) | `` `code` `` |
| `<pre><code>` | Fenced code block |
| `<blockquote>` | `> quote` |
| `<iframe>` (embeds) | Plain anchor link `[url](url)` |

### Elements to Decompose (strip entirely)

| Element | CSS Identifier |
|---------|---------------|
| Sponsored post disclosure | `div.sponsored-post-disclosure` |
| TNS-namespaced disclosure | `div.tns-sponsored-post-disclosure` |
| Generic sponsor disclosure | `div.sponsor-disclosure` |
| Injected sponsor note | `div.tns-sponsor-note` |
| Scripts | `<script>` (via markdownify strip param) |
| Styles | `<style>` (via markdownify strip param) |

### Elements Outside Body (no action required)

| Element | Location |
|---------|---------|
| VoxPop poll | `div.tns-voxpop-screen` — page-level modal, not inside `div#tns-post-body-content` |
| Site navigation | `div#tns-post-headline` breadcrumb, `div.content-column` nav wrappers |
| Author byline | `span.author`, `span.date` in `div#tns-post-headline` |
| Related articles | Outside `div#tns-post-body-content` |
| Footer / sidebar | Outside `div#tns-post-body-content` |

## State Transitions

Not applicable — stateless single-call extraction. Each `extract()` call is independent.

## Validation Rules

- `div#tns-post-body-content` must be present → else `UnsupportedContentTypeError`
- Final Markdown must be non-empty after strip → else `EmptyContentError`
- Output Markdown must not contain runs of 3+ consecutive blank lines
