# Implementation Plan: Kong Blog Provider

**Branch**: `011-konghq-blog-provider` | **Date**: 2026-06-02 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/011-konghq-blog-provider/spec.md`

## Summary

Add a provider that extracts public Kong blog articles (`konghq.com/blog/<category>/<slug>`) and returns them as clean Markdown. The site is a Next.js app whose article pages render a `<main>` element carrying the stable `type-article` class — present on every article, absent on the blog index and category listings, so it is the article-vs-non-article discriminator. Inside `<main>` the body is the `<section>` richest in `.rich-text-block` blocks; the title `<h1>` and the publication date live in the preceding hero section, and all chrome (breadcrumbs, topics/author meta, recommended-posts carousel, footer CTA) lives in separate sibling sections that are excluded simply by selecting only the content section + hero title/date. A few chrome blocks live *inside* the content section and are stripped by stable class (`.component.video`, `.component.more-on-this`, a trailing non-`intro` `.section-header-block` CTA, the `.order-top` inline topic tags, and the `.toc-wrap` TOC sidebar); all `.agent` "agent mode" spans are also removed. Per the spec clarification, the publication date is kept (rendered under the title); author bylines and read time are dropped. The implementation is a single new provider file subclassing `BaseExtractor`, reusing all shared fetch/convert logic.

## Technical Context

**Language/Version**: Python 3.12+ (matches CI matrix: 3.12–3.14)

**Primary Dependencies**: `httpx` (HTTP fetch), `BeautifulSoup` / `lxml` (HTML parsing), `markdownify` (Markdown conversion), `pytest` (testing)

**Storage**: N/A — stateless extraction library

**Testing**: `pytest` via `uv run pytest` — unit tests (no network) + integration tests (`-m integration`, real URLs + snapshots)

**Target Platform**: PyPI library (cross-platform)

**Project Type**: Library

**Performance Goals**: Inherits base class 30-second fetch timeout; no additional targets

**Constraints**: One new provider file; no changes to shared infrastructure

**Scale/Scope**: Single-article extraction per call

## Constitution Check

*GATE: Must pass before implementation. Re-check after design phase.*

- [x] Validates Provider Pattern Architecture (new `KongExtractor(BaseExtractor)`; no base-class changes; reuses `fetch_html`/`convert_to_markdown` — no code duplication)
- [x] Confirms Technology Stack (`httpx`, `BeautifulSoup`, `Markdownify`, `pytest` — all inherited)
- [x] Adheres to Coding Standards (PEP 8, strict type hints, clear vocabulary)
- [x] Incorporates Integration Testing (real reference URLs + snapshot containment, matching existing providers)
- [x] Respects Packaging and Distribution standards (`pyproject.toml`, `src/` layout, `uv` for all dev commands)

**Result**: PASS — no violations. Complexity Tracking not required.

## Project Structure

### Documentation (this feature)

```text
specs/011-konghq-blog-provider/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   └── extractor-contract.md   # Phase 1 output (provider contract)
└── tasks.md             # Phase 2 output (/speckit-tasks — NOT created here)
```

### Source Code

```text
src/mdfetch/providers/
└── kong.py                              # NEW: KongExtractor

tests/unit/
└── test_kong_extractor.py               # NEW: unit tests (no network)

tests/integration/
├── snapshots/
│   ├── kong-insomnia-12-6.md                    # NEW
│   ├── kong-ai-gateway-vs-litellm.md            # NEW
│   └── kong-gateway-3-14.md                     # NEW
└── test_kong_integration.py             # NEW: integration tests (real URLs)
```

**Non-runtime changes**: `README.md` (add Kong row to Supported platforms table + usage example); `pyproject.toml` (version bump `0.6.0` → `0.7.0`, new provider = minor per dev.to/Substack/Boomi precedent); `CLAUDE.md` (provider tree + integration-test description + Kong discriminator/CSS-module gotcha). No `test_router.py` fixture change required — the unsupported-domain fixture uses `wordpress.com`, which Kong does not register.

## Extraction Algorithm

```
extract(url):                                  # inherited from BaseExtractor
  html ← fetch_html(url)                        # 30s timeout, 3 retries on transient errors
  soup ← BeautifulSoup(html, "lxml")
  body_tag ← clean_html(soup)
  return convert_to_markdown(body_tag)          # ATX headings, collapse 3+ blank lines, EmptyContentError if blank

clean_html(soup):                              # KongExtractor implementation
  1. main ← soup.find("main")
        → if not a Tag or "type-article" not in its classes:
              raise UnsupportedContentTypeError        # index / category listing / non-article
  2. sections ← direct <section> children of main
  3. content ← the section with the most ".rich-text-block" descendants
        → if none / zero rich-text-blocks: raise UnsupportedContentTypeError
  4. strip chrome blocks inside content (decompose):
        ".component.video"            (undisplayable embedded-video placeholder)
        ".component.more-on-this"     (related-content widget)
        ".toc-wrap"                   (sticky "on this page" TOC sidebar)
        ".order-top"                  (inline topic-tag list)
        ".section-header-block" without "intro"   (trailing "See Kong in action" CTA)
  5. hero ← sections[0]
        title ← hero.find("h1")                       # exactly one; the article title
        date  ← first hero <div> whose text matches DATE_RE  (e.g. "May 26, 2026")
  6. wrapper ← new <div>; append copy(title); if date: append <p>date</p>; append content
  7. strip every ".agent" span in wrapper (agent-mode affordances injecting literal Markdown)
  8. return wrapper
```

**Design notes**:
- **Discriminator** is `main.type-article` (verified live: present on all 3 reference articles; absent on the blog index *and* on the `/blog/product-releases` category listing, both of which also have zero `.rich-text-block`). This satisfies FR-009 without URL-path filtering, consistent with the codebase's route-by-domain + validate-body pattern.
- **Content section selection** uses the stable `.rich-text-block` class and a "max count" rule rather than the hashed `Article_toc__…` section class, so it survives CSS-module hash churn. The chrome sections (breadcrumbs, topics/authors meta, recommended-posts carousel, footer CTA) are *separate* `<section>` siblings and are excluded automatically by selecting only the content section.
- **Publication date** (spec clarification, Option B): kept and rendered as a paragraph under the title. The date is a class-less `<div>` in the hero, so it is matched by a month-name date pattern (`^[A-Z][a-z]+ \d{1,2}, \d{4}$`); the category link, `… min read` text, and author `<div>`s are not prepended.
- **Body media**: in-body images (`.component.image`) and pull-quotes (`.component.pull-quote`) live inside the content section and convert natively (FR-005). The hero/banner is in a separate section and is excluded. The "video which can not be displayed" placeholder block carries no usable URL and is decomposed rather than linked.
- **Code**: inline code (e.g., `git status`, `git commit`) converts via default markdownify; no `code_language_callback` needed.
- **TOC sidebar** is `.toc-wrap` (a stable companion class), NOT `[class*=TableOfContents]`: the `TableOfContents` component is the layout *wrapper* around the whole body, so matching it by substring would delete the article. (Discovered during implementation.)
- **Agent-mode affordances**: `<span class="agent">` elements inject literal Markdown (`**`, `- `, `# `) that duplicates the styled content (and would produce a `# #` double-heading on the title). All `.agent` spans are decomposed after the body is assembled. (Discovered during implementation.)
- `MATCH_SUBDOMAINS` stays `False` (default): only `konghq.com` is in scope.

## CSS-Module Fragility (key risk)

Unlike the WordPress-based providers, Kong's per-component class names are Next.js CSS-module hashes (e.g., `Article_toc__LOyCI`, `Section_section__Grz_Y`) that change between site builds. The implementation depends **only** on stable, human-authored companion classes (`type-article`, `rich-text-block`, `component`, `video`, `more-on-this`, `section-header-block`, `intro`, `order-top`, `toc-wrap`, `agent`) and one date regex. No selector relies on a hashed `__xxxxx` suffix. This is the single biggest maintenance risk and is recorded as a `CLAUDE.md` gotcha.

## Error Mapping

| Condition | Exception |
|-----------|-----------|
| `main.type-article` absent (index / category listing / non-article) | `UnsupportedContentTypeError` |
| No content section with `.rich-text-block` | `UnsupportedContentTypeError` |
| Body found but no extractable text after conversion | `EmptyContentError` |
| HTTP error (any non-2xx after retries) | `HTTPStatusError` |
| Network / timeout failure | `FetchError` |

## Complexity Tracking

> No Constitution Check violations — section intentionally empty.

### Revision: Implementation Sync 2026-06-02
- Reason: Reconciled algorithm drift found after implementation. Two selectors changed vs. the original plan: (1) the TOC strip is `.toc-wrap`, not `[class*=TableOfContents]` — the `TableOfContents` component wraps the entire body, so substring-matching it deleted the article; (2) a new step strips all `.agent` "agent mode" spans, which inject literal Markdown duplicating the styled content (and caused a `# #` double-heading). Both are covered by unit tests and the `CLAUDE.md` gotcha. No requirement, contract, or error-mapping behavior changed; extraction verified clean against all 3 reference articles.
