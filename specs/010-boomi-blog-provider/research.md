# Phase 0 Research: Boomi Blog Provider

All findings below come from live DOM inspection (2026-06-02) of the three reference
articles plus the `/blog/` index, using the project's browser-like User-Agent.

## Decision: Article body container = `div.post-content`

- **Decision**: Isolate the article body by selecting `soup.find("div", class_="post-content")`.
- **Rationale**: Present on every article page; its direct children are exactly
  `section.wysiwyg-section.bullet-styled` (the real content) and `div.blog-nav`
  (prev/next chrome). Crucially, the `/blog/` **index page does NOT contain
  `div.post-content`** (it has a `wysiwyg-section` intro but no `post-content`),
  so the selector doubles as the article-vs-non-article discriminator.
- **Alternatives considered**:
  - `section.wysiwyg-section` — **rejected**: also present on the blog index, so it
    would fail to raise `UnsupportedContentTypeError` for non-articles.
  - `<article>` / `<main>` landmarks — **rejected**: not emitted with usable classes
    in this WordPress theme.

## Decision: Strip `div.blog-nav`

- **Decision**: `decompose()` every `div.blog-nav` inside the body before conversion.
- **Rationale**: It is the only chrome element living *inside* `post-content`; it holds
  the "Previous / Next" post links. All other chrome (top nav, language selector,
  login/demo CTAs, "On this page" TOC, social share, sidebar report promos, footer)
  lives **outside** `post-content` and is excluded automatically by isolating the body.
- **Alternatives considered**: Stripping each chrome class individually — **rejected** as
  unnecessary; isolating `post-content` already removes everything except `blog-nav`.

## Decision: Title from hero `<h1>`, prepended to body

- **Decision**: `soup.find("h1")` and prepend a copy to the body as the top-level heading.
- **Rationale**: The title `<h1>` is rendered in `section.post-detail-hero` (the page hero),
  structurally outside `post-content`, so an unconditional prepend includes it exactly once
  with no body-scan deduplication (same approach as `SubstackExtractor`). There is exactly
  one `<h1>` per page. No subtitle/deck element is present on any reference article.
- **Alternatives considered**: `og:title` meta — **rejected**: prefer the on-page `<h1>` for
  consistency with other providers and to avoid meta/visible-title drift.

## Decision: Image handling — body-only (Option A)

- **Decision**: Convert only images inside `post-content`; do not hoist the hero image.
- **Rationale**: Matches the spec clarification (2026-06-02). The hero/banner image lives in
  `section.post-detail-hero` (outside the body) and is excluded automatically; genuine inline
  content images (e.g., 1 image inside reference #1's body) are preserved by default markdownify.
  No image-specific code required.
- **Evidence**: img count inside `post-content` — ref#1 (gartner): 1; ref#2 (real-time-vs-batch): 0;
  ref#3 (data-consistency): 0. All have 1 blockquote (Gartner / pull-quotes), converted natively.

## Decision: No URL path filtering; route by domain only

- **Decision**: Register `DOMAINS = frozenset({"boomi.com"})`, `MATCH_SUBDOMAINS = False`.
  Rely on `post-content` presence to reject non-`/blog/` pages.
- **Rationale**: Consistent with the codebase's route-by-domain + validate-body pattern. Non-blog
  `boomi.com` pages and the blog index lack `post-content` → `UnsupportedContentTypeError`,
  satisfying FR-009 without bespoke path logic.

## Decision: No new infrastructure / markdownify overrides

- **Decision**: Inherit `fetch_html`, `convert_to_markdown`, and default markdownify kwargs.
- **Rationale**: No code blocks observed in references (so no `code_language_callback` like DZone),
  no embeds requiring link conversion. Keeps the provider minimal per the Provider Pattern principle.

## Platform facts summary

| Fact | Value |
|------|-------|
| CMS | WordPress 6.9.4 |
| Domain | `boomi.com` (articles under `/blog/<slug>/`) |
| Body container | `div.post-content` |
| Real content | `section.wysiwyg-section.bullet-styled` |
| In-body chrome | `div.blog-nav` (prev/next) |
| Title | single `<h1>` in `section.post-detail-hero` (outside body) |
| Subtitle/deck | none |
| Paywall | none (freely readable) |
| Index page has `post-content`? | No (→ clean non-article detection) |
