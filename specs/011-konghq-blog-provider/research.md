# Phase 0 Research: Kong Blog Provider

All findings below come from live DOM inspection (2026-06-02) of the three reference
articles plus the `/blog` index and the `/blog/product-releases` category listing,
fetched with the project's browser-like User-Agent. Kong runs a **Next.js** front end:
most per-component class names are CSS-module hashes (e.g. `Section_section__Grz_Y`,
`Article_toc__LOyCI`) that can change between builds, so every decision below pins to a
**stable, human-authored companion class** instead.

## Decision: Article discriminator = `main.type-article`

- **Decision**: Treat a page as an article only when `soup.find("main")` exists and its
  class list contains `type-article`; otherwise raise `UnsupportedContentTypeError`.
- **Rationale**: Verified present on all three reference articles and **absent** on both
  the blog index (`/blog`, `main` classes `[Layout_main__…]`) and the
  `/blog/product-releases` category listing (`[Layout_main__…, product-releases]`). Both
  non-article pages also have **zero** `.rich-text-block` elements, giving a second,
  corroborating signal. `type-article` is a stable, semantic class (not a hash).
- **Alternatives considered**:
  - URL-path matching (`/blog/<cat>/<slug>`) — **rejected**: inconsistent with the
    codebase's route-by-domain + validate-body pattern; brittle to new category slugs.
  - Hashed section classes (`Article_…`) — **rejected**: change per build.

## Decision: Body = the `<main>` `<section>` richest in `.rich-text-block`

- **Decision**: Among the direct `<section>` children of `main`, select the one with the
  most `.rich-text-block` descendants as the article body.
- **Rationale**: On every reference article the content lives in a single `<section>`
  (index 1, right after the hero) holding all `.rich-text-block` blocks (counts: insomnia
  12, litellm 16, gw-3.14 7). The other sections — hero, topics/author meta,
  recommended-posts carousel, footer CTA — are separate siblings with **zero**
  `.rich-text-block`, so the max-count rule isolates the body and excludes all of them
  without per-class stripping. `.rich-text-block` is a stable companion class.
- **Alternatives considered**:
  - Selecting the hashed `section.Article_toc__…` — **rejected**: hash churn.
  - Selecting `<main>` wholesale then stripping every chrome section — **rejected**: more
    selectors, more fragile; the content-section rule already drops sibling chrome.

## Decision: Strip in-body chrome blocks by stable class

- **Decision**: Inside the content section, `decompose()` these blocks before conversion:
  `.component.video`, `.component.more-on-this`, `[class*="TableOfContents"]`,
  `.order-top`, and any `.section-header-block` **without** the `intro` class.
- **Rationale**: These are the only chrome elements that render *inside* the content
  section:
  - `.component.video` → a "This content contains a video which can not be displayed"
    placeholder with no usable URL → decompose (do not link).
  - `.component.more-on-this` → a "More on this topic" related-content widget.
  - `[class*="TableOfContents"]` → the optional on-page TOC (not present on every article).
  - `.order-top` → an inline topic-tag list duplicated from the meta section.
  - trailing `.section-header-block` (non-`intro`) → the "See Kong in action" CTA banner.
  The opening TL;DR is `.section-header-block.intro` and is **kept** (it is article lead),
  which is why the `intro` class must be excluded from the CTA strip.
- **Alternatives considered**: Keeping the video placeholder as a link — **rejected**: no
  resolvable media URL on the placeholder element.

## Decision: Title + publication date from the hero; authors/read-time dropped

- **Decision**: Take the single `<h1>` from the hero section as the title and prepend a
  copy. Take the publication date — a class-less `<div>` whose text matches
  `^[A-Z][a-z]+ \d{1,2}, \d{4}$` (e.g. "May 26, 2026") — and render it as a paragraph
  under the title. Do **not** include the category link, the `… min read` text, or the
  author `<div>`s.
- **Rationale**: Implements the spec clarification (2026-06-02, Option B: keep date only).
  The hero holds, in order, a category link, the date, a read-time div, the `<h1>`, and
  author name/title divs. The date has no stable class of its own, so a month-name date
  regex is the most robust selector; read-time (`… min read`) and category (a link) are
  excluded by not matching that pattern, and authors are excluded because they are not
  prepended at all.
- **Alternatives considered**:
  - `<time datetime>` tag — **rejected**: the hero date is plain text (no `<time>`); the
    page's `<time>` tags belong to recommended-post cards, not the article.
  - `article:published_time` meta — **rejected**: prefer the on-page visible date for
    consistency with other providers and to avoid meta/visible drift.

## Decision: No URL path filtering; route by domain only

- **Decision**: Register `DOMAINS = frozenset({"konghq.com"})`, `MATCH_SUBDOMAINS = False`.
  Rely on `main.type-article` to reject non-article pages.
- **Rationale**: Consistent with the route-by-domain + validate-body pattern. The index,
  category listings, and other `konghq.com` pages lack `type-article` →
  `UnsupportedContentTypeError`, satisfying FR-009 without bespoke path logic.

## Decision: No new infrastructure / markdownify overrides

- **Decision**: Inherit `fetch_html`, `convert_to_markdown`, and default markdownify kwargs.
- **Rationale**: In-body images and pull-quotes convert natively; inline code (`git status`)
  needs no `code_language_callback`. Keeps the provider minimal per the Provider Pattern
  principle. (`_replace_iframes_with_links` exists in the base class if a future article
  needs it, but no reference article requires it.)

## Platform facts summary

| Fact | Value |
|------|-------|
| Front end | Next.js (CSS-module hashed class names) |
| Domain | `konghq.com` (articles under `/blog/<category>/<slug>`) |
| Article discriminator | `<main>` with stable class `type-article` |
| Body container | the `main` `<section>` richest in `.rich-text-block` |
| Body blocks kept | `.section-header-block.intro` (TL;DR), `.rich-text-block`, `.component.image`, `.component.pull-quote` |
| In-body chrome stripped | `.component.video`, `.component.more-on-this`, `[class*=TableOfContents]`, `.order-top`, trailing non-`intro` `.section-header-block` |
| Title | single `<h1>` in the hero section (outside the body) |
| Publication date | class-less hero `<div>`, text like "May 26, 2026" — kept under title |
| Authors / read time | hero `<div>`s — dropped (per clarification) |
| Subtitle/deck | none |
| Paywall | none (freely readable) |
| Index / category page has `type-article`? | No (→ clean non-article detection; also 0 rich-text-blocks) |
