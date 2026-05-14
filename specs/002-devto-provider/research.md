# Research: mdfetch — dev.to Extractor

**Branch**: `002-devto-provider` | **Date**: 2026-05-14

## Findings

### Decision: Article Body Element
- **Decision**: Target `<div id="article-body" class="crayons-article__body ...">` as the primary content container.
- **Rationale**: This div contains exclusively the article's authored text — no chrome, nav, comments, or sidebars are children of this element. It is reliably present on all article pages and absent on profile/tag pages.
- **Alternatives considered**: Targeting `<article id="article-show-container">` and stripping children — rejected because this requires stripping many nested elements and risks keeping unwanted content. Targeting `div#article-body` is precise and requires no child stripping.

### Decision: Title and Cover Image
- **Decision**: Extract the `<h1>` and cover `<img class="crayons-article__cover__image">` from `<header class="crayons-article__header">` and prepend them to the article body content before conversion.
- **Rationale**: The article body div does not include the title or cover image; both live in the separate header element. Omitting them would produce Markdown with no title. A synthetic wrapper containing `h1 + img + body` is passed to markdownify.
- **Alternatives considered**: Skipping cover image — rejected per clarified requirement (FR-003) that cover images are preserved as Markdown image syntax.

### Decision: Article vs. Non-Article Detection
- **Decision**: Check for the presence of `<div id="article-body">`. If absent, raise `UnsupportedContentTypeError`.
- **Rationale**: This element is reliably present on article pages and absent on dev.to profile pages, tag listing pages, organisation pages, and podcast pages. It is a stable, named element (not a class-only selector), making it robust to CSS refactors.
- **Evidence**: HTML inspection of `https://dev.to/stn1slv/integration-digest-for-december-2025-5dlp` confirmed `<div id="article-body" class="crayons-article__body text-styles spec__body" data-article-id="3149624">`.

### Decision: Embedded Content (iframes, liquid tags)
- **Decision**: Before conversion, replace any `<iframe>` elements in the body with `<a href="{src}">{title or src}</a>` tags. Replace any dev.to liquid tag elements (class containing `ltag`) similarly.
- **Rationale**: The reference articles contain no embeds, but other dev.to articles do (GitHub Gists, YouTube). Per FR-008, embeds must not be silently dropped — they must become plain Markdown links. `markdownify` by default drops iframes.
- **Alternatives considered**: Relying on markdownify's `strip` parameter — rejected because it silently drops the element rather than preserving a link.

### Decision: Non-Content Elements to Exclude
Elements confirmed in HTML inspection that are **not** children of `div#article-body` and are thus excluded automatically by scoping to that element:
- `<nav class="series-switcher">` — series navigation above/below body
- `<section id="comments">` — comments section
- `<div class="below-post-bb body-billboard-container">` — advertisement
- `<div class="spec__tags">` (with `<a class="crayons-tag">`) — article tags (confirmed to strip per clarification)
- Header author metadata (avatar, name, date, follow button)

No additional `decompose()` calls are needed for these — they are outside the target div.

### Decision: Anchor Name Links in Headings
- **Decision**: Strip `<a name="...">` anchor links that dev.to inserts before each heading. These appear as empty anchor elements (`<a href="#articles" name="articles"></a>`) immediately inside heading tags.
- **Rationale**: These become empty Markdown fragments after conversion. They carry no content value.
- **Evidence**: `<h2><a href="#articles" name="articles"></a> Articles</h2>` observed in article body.

### Decision: Images in Body
- **Decision**: Standard `<img>` tags in `div#article-body` are converted to Markdown image syntax by markdownify without any special handling.
- **Rationale**: dev.to serves images as standard `<img src="...">` tags (not lazy-loaded `data-src`). markdownify converts these to `![alt](src)` natively.
- **Evidence**: No `data-src` or `loading="lazy"` attributes observed on article body images; cover image uses standard `src` attribute.

## dev.to HTML Structure Reference

```
<article id="article-show-container" class="crayons-card crayons-article ...">
  <header class="crayons-article__header" id="main-title">
    <a class="crayons-article__cover" href="...">
      <img class="crayons-article__cover__image" src="..." alt="Cover image for ...">
    </a>
    <div class="crayons-article__header__meta">
      <h1 class="...">Article Title</h1>
      ... author info, date, actions ...
    </div>
  </header>
  <div class="crayons-article__main">
    <nav class="series-switcher ...">...</nav>          <!-- strip: outside target -->
    <div id="article-body" class="crayons-article__body text-styles spec__body"
         data-article-id="NNNNNN">
      <!-- PURE ARTICLE CONTENT: headings, paragraphs, code, lists, images, iframes -->
    </div>
    <nav class="series-switcher ...">...</nav>          <!-- strip: outside target -->
    <div class="below-post-bb body-billboard-container">...</div>   <!-- strip -->
  </div>
  <section id="comments" class="...">...</section>     <!-- strip: outside target -->
</article>

<!-- Tags section: outside article element -->
<div class="spec__tags flex flex-wrap">
  <a class="crayons-tag" href="/t/kafka">#kafka</a>
  ...
</div>
```
