# Research: Substack Platform Provider

> All findings verified against live Substack pages via raw HTML inspection:
> - `getkafkanated.substack.com/p/kafka-deserves-topic-types`
> - `pragmaticapi.substack.com/p/api-trends-for-2025-the-evolution`

## Substack HTML Structure (verified)

### Article container

The page renders:

```
article.newsletter-post.post
├── div.post-header
│   ├── h1.post-title.published          ← article title (outside body)
│   ├── h3.subtitle                       ← subtitle/deck (optional)
│   └── div (byline: author + date)
├── div.available-content
│   └── div.body.markup                   ← article prose (FREE CONTENT ONLY)
│       ├── p, h1.header-anchor-post, …   ← article headings + paragraphs
│       ├── div.subscription-widget-wrap  ← inline subscribe CTA (strip)
│       ├── div.captioned-image-container ← images (keep)
│       └── …
└── div.post-footer                       ← like/share/comment buttons (strip)
```

Key observations from live inspection:
- `div.body.markup` is the sole child of `div.available-content`.
- For paywalled posts, Substack serves only the free-preview content inside `div.body.markup`. The paywall CTA (`div.subscription-widget-wrap`) appears as the **last element** in the body at the truncation point — stripping it achieves silent truncation (FR-008).
- `div.subscription-widget-wrap` appears 1–2 times per article (once mid-article as a paid-upgrade prompt, once at the end). Each contains a `div[data-component-name=SubscribeWidget]`.

### Decision: `div.body.markup` as extraction root

**Rationale**: Contains article prose only; `div.available-content` is just a transparent wrapper. Using `div.body.markup` is the most precise selector.
**Alternatives considered**: `article.newsletter-post` — too broad (includes header and footer).

### Decision: Title from `h1.post-title` in `div.post-header`

**Rationale**: The article title is `<h1 class="post-title published …">` inside `div.post-header`, always outside `div.body.markup`. Section headings inside the body use the distinct class `header-anchor-post`. No deduplication logic needed: `h1.post-title` never appears inside `div.body.markup`.
**Alternatives considered**: First `h1` on the page — unreliable; publication name also uses `h1` (class `title-oOnUGd`).

### Decision: Subtitle included after title

**Rationale**: `div.post-header` contains an `h3.subtitle` element (the article deck). Including it preserves author intent and adds value. It is rendered as a `### subtitle` heading by markdownify, placed immediately after the `# Title`.

### Decision: Strip `div.subscription-widget-wrap` (and `div[data-component-name=SubscribeWidget]`)

**Rationale**: Both selectors refer to the same DOM node (the outer `div.subscription-widget-wrap` contains the inner `div[data-component-name=SubscribeWidget]`). Removing by class `subscription-widget-wrap` is sufficient. Stripping this also strips the paywall CTA for paywalled posts, satisfying FR-008.

### Decision: Strip `div.post-footer` and visibility-check

**Rationale**: `div.post-footer` contains all engagement buttons (like, comment, share, restack). `div.visibility-check` is a Substack analytics stub with no user-visible content. Both are siblings of `div.available-content` in the article, not inside `div.body.markup`, so they are never encountered when using `div.body.markup` as the root. No explicit stripping is required if the extractor uses `div.body.markup` directly.

### Decision: Embed handling — `iframe` + Substack embed containers

**Rationale**: This article has no iframes, but the general Substack embed pattern uses `<iframe>` for YouTube/Spotify and Substack-specific `<div class="embed-post">` or similar containers for linked Substack posts. The implementation should:
1. Replace `<iframe>` elements with plain anchor links using `src`.
2. Replace known Substack embed `<div>` containers (identified by class prefix `embed` or `data-component-name` values other than `SubscribeWidget` and `Image2ToDOM`) with anchor links using the first `href` or `data-url` found.

### Decision: `h1.header-anchor-post` headings preserved at `h1` level

**Rationale**: In-body section headings all use `<h1 class="header-anchor-post">`. After prepending `h1.post-title` as `# Title`, these render as additional `# Section` headings. This matches existing provider behaviour (Medium, dev.to do not remap heading levels).

## Routing

### Decision: Register `"substack.com"` in `DOMAINS`

**Rationale**: The existing router suffix-matches all `*.substack.com` subdomains from a single `"substack.com"` entry. No additional entries needed. Custom Substack domains are out of scope (spec Assumptions).

## HTTP Error Handling

### Decision: No `_no_retry_status_codes` override

**Rationale**: Per clarification Q2, HTTP 429 from Substack is retried (not raised immediately). The base-class default `_no_retry_status_codes = frozenset()` applies — no override needed. This contrasts with `MediumExtractor`, which overrides to `{403, 429}` to trigger its Freedium fallback.
