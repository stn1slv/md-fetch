# Data Model: Substack Platform Provider

This feature introduces no persistent data. The entities below describe in-memory objects used during extraction.

## SubstackPost (in-memory, read-only)

Represents the parsed structure of a single Substack article page as observed in the DOM.

| Field | Source element | Required | Notes |
|-------|---------------|----------|-------|
| `title` | `h1.post-title` in `div.post-header` | Yes | Prepended as `# Title` in output |
| `subtitle` | `h3.subtitle` in `div.post-header` | No | Prepended as `### Subtitle` if present |
| `body` | `div.body.markup` | Yes | Prose content after stripping chrome |

## DOM Element Taxonomy

| Element | CSS selector | Action |
|---------|-------------|--------|
| Article body | `div.body.markup` | **Keep** — extraction root |
| Post title | `div.post-header h1.post-title` | **Prepend** to body before conversion |
| Subtitle/deck | `div.post-header h3.subtitle` | **Prepend** (after title) if present |
| Section headings | `h1.header-anchor-post` inside body | **Keep** at original `h1` level |
| Captioned images | `div.captioned-image-container` | **Keep** — markdownify handles `img` tags |
| Inline CTA / paywall boundary | `div.subscription-widget-wrap` | **Strip** |
| Subscribe widget | `div[data-component-name=SubscribeWidget]` | **Strip** (child of above; covered by parent strip) |
| Image link wrapper | `a[data-component-name=Image2ToDOM]` | **Keep** — transparent anchor around `img` |
| iframe embeds | `iframe` | **Replace** with `<a href=src>src</a>` |
| Other embed containers | `div[data-component-name]` (excluding known safe values) | **Replace** with anchor link |
| Post footer | `div.post-footer` | Outside `div.body.markup`; not encountered |
| Byline / author bio | `div.post-header div` (byline wrapper) | Outside extraction root; not encountered |

## State Transitions

None — the extractor is stateless. Each `extract()` call is independent.
