# Phase 1 Data Model: Kong Blog Provider

This library is stateless; there are no persisted entities. The "data model" describes
the DOM structures the extractor reads and the in-memory shapes it produces. All selectors
pin to stable, human-authored classes (not Next.js CSS-module hashes).

## Entity: Kong Blog Post (input DOM)

A single article page at `https://konghq.com/blog/<category>/<slug>`.

| Field | Source selector | Notes |
|-------|-----------------|-------|
| is-article | `main.type-article` | Stable discriminator; presence ⇒ "is an article" |
| body | content `<section>` (most `.rich-text-block` under `main`) | Body container |
| content blocks | `.section-header-block.intro`, `.rich-text-block`, `.component.image`, `.component.pull-quote` | Kept, in document order |
| title | `h1` (within the hero `<section>`) | Exactly one per page; outside the body section |
| publication date | hero `<div>` matching `^[A-Z][a-z]+ \d{1,2}, \d{4}$` | Kept; rendered under the title |
| read time (chrome) | hero `<div>` "… min read" | Dropped (clarification) |
| authors (chrome) | hero author `<div>`s + meta `Article_authors` block | Dropped (clarification) |
| category/topics (chrome) | hero category link, `.order-top`, meta section | Stripped/excluded |
| TOC (chrome) | `[class*="TableOfContents"]` (when present) | Stripped |
| video placeholder (chrome) | `.component.video` | Stripped (no usable URL) |
| more-on-this (chrome) | `.component.more-on-this` | Stripped |
| footer CTA (chrome) | trailing `.section-header-block` (non-`intro`) + `section.footer-cta` | Stripped/excluded |
| recommended posts (chrome) | `section.section-carousel` | Excluded (separate section) |
| breadcrumbs (chrome) | `nav.breadcrumbs` | Excluded (separate `<main>` child) |
| subtitle/deck | — | Not present on any reference article |

**Validation rules**:
- `main.type-article` MUST exist → else `UnsupportedContentTypeError`.
- A content `<section>` with ≥1 `.rich-text-block` MUST exist → else `UnsupportedContentTypeError`.
- After stripping and conversion, Markdown MUST be non-empty → else `EmptyContentError`.

## Entity: Extraction Result (output)

A single Markdown `str` (the public `extract()` return value):
- Line 1: `# <title>` (top-level ATX heading).
- Then the publication date (when present) as a short paragraph.
- Then the converted body: TL;DR lead, section headings, paragraphs, lists, blockquotes,
  inline/block code, links, and in-body images, in document order.
- No runs of 3+ consecutive blank lines (collapsed by base `convert_to_markdown`).
- Contains no site chrome (breadcrumbs, category/topics, read time, authors, TOC, video
  placeholder, more-on-this, recommended-posts carousel, footer CTA).

## DOM Element Taxonomy (selector → action)

| Selector | Action | Reason |
|----------|--------|--------|
| `main.type-article` | **gate** | Article discriminator; absence ⇒ non-article |
| content `<section>` (max `.rich-text-block`) | **keep** (body root) | Article body |
| `.section-header-block.intro` | **keep** | Opening TL;DR / lead |
| `.rich-text-block`, `.component.image`, `.component.pull-quote` | **keep** | Body prose, images, pull-quotes |
| `h1` (hero) | **prepend** (copy) | Article title heading |
| hero date `<div>` (date regex) | **prepend** (as `<p>`) | Publication date (clarification) |
| `.component.video` | **strip** (`decompose`) | Undisplayable video placeholder |
| `.component.more-on-this` | **strip** | Related-content widget |
| `[class*="TableOfContents"]` | **strip** | On-page TOC |
| `.order-top` | **strip** | Inline topic-tag list |
| trailing `.section-header-block` (non-`intro`) | **strip** | "See Kong in action" CTA |
| every other `<section>` / `nav` under `main` | **excluded** implicitly | Hero meta, topics/authors, carousel, footer CTA, breadcrumbs |

## State Transitions

None. Each `extract(url)` call is independent: `fetch → parse → clean → convert → return | raise`.
