# Quickstart: DZone Provider Implementation

**Branch**: `007-dzone-provider` | **Date**: 2026-05-16

## Implementation Steps (in order)

### 1. Create the provider

```
src/mdfetch/providers/dzone.py
```

- Class: `DZoneExtractor(BaseExtractor)`
- Decorator: `@register`
- `DOMAINS = frozenset({"dzone.com"})`
- Implement `clean_html()` — see extraction algorithm in plan.md
- Implement `convert_to_markdown()` — identical to existing providers

Key `clean_html()` logic:
1. Find `div.content-html` → raise `UnsupportedContentTypeError` if absent
2. For each `div.codeMirror-wrapper` in the body:
   a. Read language from `div.nameLanguage` (strip, lowercase; "plain text" → `""`)
   b. If non-empty, set `class="language-<lang>"` on the `code` element inside
   c. Decompose `div.codeHeader` (removes language label div + cancel icon)
3. Find `h1.article-title` → prepend a copy as the first child of the body
4. Return the body tag

### 2. Create unit tests

```
tests/unit/test_dzone_extractor.py
```

Required HTML fixtures (inline strings):

- `ARTICLE_HTML` — full article with title, body paragraphs, headings, link, image
- `ARTICLE_WITH_CODE_HTML` — article with `div.codeMirror-wrapper` containing language "Java"
- `ARTICLE_WITH_PLAIN_TEXT_CODE_HTML` — article with language "Plain Text" (bare fence expected)
- `NO_ARTICLE_HTML` — page without `div.content-html` (refcard-like, triggers error)
- `EMPTY_BODY_HTML` — body present but whitespace-only (triggers EmptyContentError)

Required test cases:

- `test_routes_dzone_com` (add to `tests/unit/test_router.py`)
- `test_clean_html_returns_content_html_div`
- `test_clean_html_prepends_title`
- `test_clean_html_code_block_java_language`
- `test_clean_html_code_block_plain_text_no_language`
- `test_clean_html_strips_code_header`
- `test_convert_to_markdown_starts_with_title`
- `test_convert_to_markdown_no_triple_blank_lines`
- `test_convert_to_markdown_preserves_links`
- `test_convert_to_markdown_fenced_code_block_with_language`
- `test_clean_html_raises_on_no_article_body`
- `test_convert_to_markdown_raises_on_empty_body`

### 3. Generate snapshots (requires network)

For each of the 3 reference articles, generate a snapshot:

```bash
uv run python -c "
from mdfetch import extract
content = extract('https://dzone.com/articles/integration-patterns-fail-production')
snapshot = '\n'.join(content.split('\n')[:30]).rstrip()
open('tests/integration/snapshots/dzone-integration-patterns-fail-production.md', 'w', encoding='utf-8').write(snapshot)
"

uv run python -c "
from mdfetch import extract
content = extract('https://dzone.com/articles/kiro-feature-to-requirements-design-tasks')
snapshot = '\n'.join(content.split('\n')[:30]).rstrip()
open('tests/integration/snapshots/dzone-kiro-feature-to-requirements-design-tasks.md', 'w', encoding='utf-8').write(snapshot)
"

uv run python -c "
from mdfetch import extract
content = extract('https://dzone.com/articles/image-classification-pipeline-camel-djl')
snapshot = '\n'.join(content.split('\n')[:30]).rstrip()
open('tests/integration/snapshots/dzone-image-classification-pipeline-camel-djl.md', 'w', encoding='utf-8').write(snapshot)
"
```

Snapshots are verbatim first-30-line prefixes. The containment check `expected in result` verifies the snapshot is present in the full extraction output.

### 4. Create integration tests

```
tests/integration/test_dzone_integration.py
```

Pattern: identical to `test_thenewstack_integration.py` — parametrized over URL/snapshot pairs, `@pytest.mark.integration`, snapshot containment check.

Also include: `test_non_article_url_raises_unsupported_content_type_error` using a DZone refcard URL.

### 5. Run verification

```bash
make test                    # all unit tests must pass
make lint                    # ruff check
uv run mypy src/             # zero type errors
make integration             # network required; all 3 snapshots must match
```
