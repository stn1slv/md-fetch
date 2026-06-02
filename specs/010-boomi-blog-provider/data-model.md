# Phase 1 Data Model: Boomi Blog Provider

This library is stateless; there are no persisted entities. The "data model" describes
the DOM structures the extractor reads and the in-memory shapes it produces.

## Entity: Boomi Blog Post (input DOM)

A single article page at `https://boomi.com/blog/<slug>/`.

| Field | Source selector | Notes |
|-------|-----------------|-------|
| title | `h1` (within `section.post-detail-hero`) | Exactly one per page; outside the body container |
| body | `div.post-content` | Body container; presence = "is an article" |
| content | `section.wysiwyg-section.bullet-styled` | Real article content (child of body) |
| nav (chrome) | `div.blog-nav` | Prev/next post links (child of body) — stripped |
| images | `img` inside `div.post-content` | Preserved (body-only, per clarification) |
| blockquotes | `blockquote` inside content | Preserved natively |
| subtitle/deck | — | Not present on any reference article |

**Validation rules**:
- `div.post-content` MUST exist → else `UnsupportedContentTypeError`.
- After stripping and conversion, Markdown MUST be non-empty → else `EmptyContentError`.

## Entity: Extraction Result (output)

A single Markdown `str` (the public `extract()` return value):
- Line 1: `# <title>` (top-level ATX heading).
- Followed by the converted body: headings, paragraphs, lists, blockquotes, links, and
  any in-body images, in document order.
- No runs of 3+ consecutive blank lines (collapsed by base `convert_to_markdown`).
- Contains no site chrome (nav, language selector, CTAs, TOC, share buttons, blog-nav,
  sidebar promos, footer).

## DOM Element Taxonomy (selector → action)

| Selector | Action | Reason |
|----------|--------|--------|
| `div.post-content` | **keep** (body root) | Article body; absence ⇒ non-article |
| `div.blog-nav` (inside body) | **strip** (`decompose`) | Prev/next post chrome |
| `h1` (hero) | **prepend** (copy into body) | Article title heading |
| everything outside `div.post-content` | **excluded** implicitly | Nav, TOC, share, sidebar promos, footer, hero image |

## State Transitions

None. Each `extract(url)` call is independent: `fetch → parse → clean → convert → return | raise`.
