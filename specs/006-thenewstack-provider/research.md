# Research: The New Stack Platform Provider

**Branch**: `006-thenewstack-provider` | **Date**: 2026-05-16

## Reference URLs (all verified)

1. `https://thenewstack.io/using-a-developer-portal-for-api-management/`
2. `https://thenewstack.io/api-management-for-asynchronous-apis/`
3. `https://thenewstack.io/json-schema-ai-reliability/`
4. `https://thenewstack.io/mcp-api-governance-readiness/`
5. `https://thenewstack.io/api-mcp-agent-integration/`

All five articles confirmed identical HTML structure: same selectors, same element presence, consistent VoxPop placement outside body.

## HTML Structure Analysis

All findings derived from live HTTP fetch of all five reference article URLs.

### Article Body Container

**Decision**: Use `div#tns-post-body-content` as the article body selector.

**Rationale**: This `<div id="tns-post-body-content">` is the innermost element that contains only prose — 29 direct `<p>` tags in the reference article. Its parent chain is: `div.copy-column → div.row → div#tns-post-body → div.content-column.content-column-post-body → div#tns-post`. All other major page elements (sidebar, navigation, subscription forms) are outside this container.

**Alternatives considered**: `div#tns-post-body` — rejected because it wraps `div.row` and `div.copy-column` intermediaries that add no content, making the selector more fragile. `article` and `main` tags — not present on this WordPress-based site.

### Article Title

**Decision**: `h1.title` located inside `div#tns-post-headline`.

**Rationale**: Single `<h1 class="title">` per page, consistently placed in the `#tns-post-headline` container alongside the breadcrumb and byline. Prepend via `copy.copy()` matching existing provider pattern.

### Article Subtitle / Deck

**Decision**: `div.post-excerpt` — sibling of `h1.title` inside `div#tns-post-headline`. Insert as a new `<p>` tag before the body content.

**Rationale**: The deck is structurally a `<div>` not a semantic subtitle element; creating a plain `<p>` wrapper before inserting avoids markdownify emitting a bare block of text without paragraph separation.

**Alternatives considered**: Copying the div directly — rejected because `div.post-excerpt` would render as a div, not a paragraph, and may pick up class-based CSS noise.

### VoxPop Poll Widgets

**Decision**: No stripping required inside the body extractor.

**Rationale**: `div.tns-voxpop-screen` and `div.tns-voxpop-modal` are rendered at the page level outside `div#tns-post-body-content`. Confirmed via live DOM inspection — `bc.find(class_=lambda …'vox'…)` returns `None` inside the body container. VoxPop is injected as a full-page overlay modal, not mid-article content.

### Elements to Strip from Body

**Decision**: Decompose the following from `div#tns-post-body-content` before conversion:

| Selector | Purpose |
|----------|---------|
| `div.sponsored-post-disclosure` | Sponsored article disclosure banner |
| `div.tns-sponsored-post-disclosure` | TNS-namespaced variant of disclosure |
| `div.sponsor-disclosure` | Generic sponsor disclosure |
| `div.tns-sponsor-note` | Injected mid-article sponsor note (appears after certain paragraphs) |
| `script` tags | Handled by markdownify `strip=["script","style"]` — no explicit decompose needed |

**Rationale**: These elements appear inside `div#tns-post-body-content` confirmed by live inspection. The `div.tns-sponsor-note` contains sponsor logo, links, and CTA — all non-editorial.

### URL Pattern & Routing

**Decision**: Register domain `thenewstack.io` only (no subdomain pattern).

**Rationale**: thenewstack.io does not use contributor subdomains. All article URLs follow `thenewstack.io/<slug>/`. Confirmed from both reference URLs and site structure (WordPress single-site install, not multisite).

### Unsupported Content Type Detection

**Decision**: Raise `UnsupportedContentTypeError` when `div#tns-post-body-content` is absent.

**Rationale**: Non-article pages (homepage, category listings, author archives) do not render this `div`. The selector is specific enough that its presence reliably indicates an article page.

### iframe / Embed Handling

**Decision**: Convert iframes to plain anchor links (same pattern as substack.py / devto.py). No iframes observed in reference articles, but pattern should be included defensively.

## Router Test Update

Per CLAUDE.md "Known Issues & Gotchas": the `test_raises_for_unsupported_domain` fixture in `tests/unit/test_router.py` already uses `wordpress.com` as the unsupported domain (updated after the substack provider was added). No change needed when adding `thenewstack.io`.
