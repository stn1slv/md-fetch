# Research: DZone Platform Provider

**Branch**: `007-dzone-provider` | **Date**: 2026-05-16

## Reference URLs (all verified)

1. `https://dzone.com/articles/integration-patterns-fail-production`
2. `https://dzone.com/articles/kiro-feature-to-requirements-design-tasks`
3. `https://dzone.com/articles/image-classification-pipeline-camel-djl`

All three articles confirmed identical HTML structure: same selectors, same element presence. Live HTTP fetch performed with browser-like User-Agent (Chrome/120 on Mac) which the base class already sets.

## HTML Structure Analysis

All findings derived from live HTTP fetch and BeautifulSoup parsing of all three reference article URLs.

### Article Body Container

**Decision**: Use `div.content-html` as the article body selector.

**Rationale**: `div.content-html` is the innermost container that holds only article prose. Confirmed text length of ~5,000–6,000 characters across all three articles. Its parent chain is: `div.content` → anonymous `div` → `div.content-html`. All non-content elements (sidebar, ads, author actions, sign-in prompt, tag pills, attribution, trending links) are siblings of `div.content-html` within `div.content`, not children.

**Alternatives considered**: `div.content` — rejected because it contains non-content siblings (`div.author-n-useraction`, `div.signin-prompt`, `div.article-tag-pill-container`, `div.attribution`, `div.trending.goto`). `div.trending-article-body` — rejected because it wraps the full article section including sidebar (`div.trending-sidebar`) and sticky ads.

### Article Title

**Decision**: `h1.article-title`, located inside `div.title` inside `div.header-title`.

**Rationale**: Single `h1.article-title` per article page, consistently placed. Prepend via `copy.copy()` matching the existing provider pattern (TheNewStack, Substack).

### Article Subtitle

**Decision**: Exclude the subtitle (`div.subhead > h3`).

**Rationale**: The subtitle is structural metadata displayed between the title and author byline. It is inside `div.header-title` which is a sibling of the body container, not inside `div.content-html`. Excluding it is consistent with the project convention of extracting only body content. The spec Assumptions section documents this decision.

### CodeMirror Code Blocks

**Decision**: For each `div.codeMirror-wrapper` inside `div.content-html`:
1. Read the programming language from `div.nameLanguage` (strip whitespace, lowercase, map "plain text" → empty string).
2. Annotate the `code` element with `class="language-<lang>"` so markdownify emits the correct fence info string.
3. Decompose `div.codeHeader` (contains `div.nameLanguage` and the `i.cm-remove` cancel icon — both pure UI chrome).
4. The remaining `pre > code` is handled by markdownify as a standard fenced code block.

**Rationale**: markdownify reads the `language-X` CSS class on `code` elements to determine the fence language. The code content is server-rendered in `pre > code` (confirmed: no JavaScript execution required). Observed language labels across the three articles: `reStructuredText`, `Groovy`, `Java`, `Plain Text`.

**Alternative considered**: Manually constructing fenced code block strings — rejected as it bypasses markdownify and requires reimplementing escaping logic. Using `data-code` attribute — rejected because `pre > code` already contains the rendered code; `data-code` is the editor source and may differ in whitespace.

**Language normalisation table** (observed):

| Raw label | Normalised (lowercase) | Fence info string |
|-----------|----------------------|-------------------|
| `Java` | `java` | `java` |
| `Groovy` | `groovy` | `groovy` |
| `Plain Text` | `plain text` | _(empty — bare backticks)_ |
| `reStructuredText` | `restructuredtext` | `restructuredtext` |
| _(empty / absent)_ | `""` | _(empty — bare backticks)_ |

### Elements to Strip

**Decision**: Only `div.codeHeader` within each `div.codeMirror-wrapper` requires explicit decomposition. All other non-content elements are outside `div.content-html` and are naturally excluded when the body container is isolated.

**Rationale**: `div.content-html` is clean — confirmed by live inspection. Its children are: standard prose elements (`p`, `h2`, `h3`, `ul`, `ol`), `div.codeMirror-wrapper` (code blocks), `div.table-responsive > table` (comparison tables). No ads, nav, or social widgets are injected inside it.

### URL Pattern & Routing

**Decision**: Register domain `dzone.com` only (no subdomain pattern).

**Rationale**: DZone does not use contributor subdomains for article content. All article URLs follow `dzone.com/articles/<slug>`. Confirmed from live HTML (`<link rel="canonical">` confirms single-domain structure).

### Unsupported Content Type Detection

**Decision**: Raise `UnsupportedContentTypeError` when `div.content-html` is absent.

**Rationale**: Non-article DZone pages (refcards at `/refcardz/`, topic listings at `/topics/`, user profiles) do not render `div.content-html`. The selector is specific enough that its presence reliably indicates an article page.

### HTTP Compatibility

**Decision**: No override needed — inherit base class headers as-is.

**Rationale**: The base class already sets `User-Agent: Mozilla/5.0 ... Chrome/120.0.0.0 Safari/537.36` (FR-014). Live HTTP fetch with this User-Agent returns HTTP 200 for all three reference articles. No additional headers (Accept, Referer, Cookie) are required for public article pages.

### Router Test Update

Per CLAUDE.md "Known Issues & Gotchas": the `test_raises_for_unsupported_domain` and `test_unsupported_error_includes_domain` fixtures in `tests/unit/test_router.py` currently use `wordpress.com` as the unsupported domain. Adding `dzone.com` does not conflict — `wordpress.com` remains unregistered. No change needed.
