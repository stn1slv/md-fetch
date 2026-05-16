# Quickstart: The New Stack Provider Implementation

**Branch**: `006-thenewstack-provider` | **Date**: 2026-05-16

## Implementation Steps (in order)

### 1. Create the provider

```
src/mdfetch/providers/thenewstack.py
```

- Class: `TheNewStackExtractor(BaseExtractor)`
- Decorator: `@register`
- `DOMAINS = frozenset({"thenewstack.io"})`
- Implement `clean_html()` — see extraction algorithm in plan.md
- Implement `convert_to_markdown()` — identical to existing providers

### 2. Create unit tests

```
tests/unit/test_thenewstack_extractor.py
```

Required HTML fixtures (inline strings):
- `ARTICLE_HTML` — full article with title, deck, body paragraphs, image, link
- `ARTICLE_NO_DECK_HTML` — article without `div.post-excerpt`
- `NO_ARTICLE_HTML` — page without `div#tns-post-body-content` (homepage-like)
- `EMPTY_BODY_HTML` — body present but whitespace-only
- `IFRAME_EMBED_HTML` — article with an embedded iframe
- `SPONSOR_NOTE_HTML` — article with `div.tns-sponsor-note` mid-content

Required test cases:
- `test_routes_thenewstack_io` (in `test_router.py`)
- `test_clean_html_returns_body_content_div`
- `test_clean_html_prepends_title`
- `test_clean_html_prepends_deck_as_paragraph`
- `test_clean_html_no_deck_when_absent`
- `test_clean_html_strips_sponsor_note`
- `test_clean_html_strips_sponsor_disclosure`
- `test_clean_html_converts_iframe_to_anchor`
- `test_convert_to_markdown_starts_with_title`
- `test_convert_to_markdown_no_triple_blank_lines`
- `test_convert_to_markdown_renders_images`
- `test_convert_to_markdown_preserves_links`
- `test_clean_html_raises_on_no_article_body`
- `test_convert_to_markdown_raises_on_empty_body`

### 3. Generate snapshots (requires network)

For each of the 5 reference articles, generate a snapshot by running:

```bash
uv run python -c "
from mdfetch import extract
content = extract('https://thenewstack.io/using-a-developer-portal-for-api-management/')
# Save a representative excerpt (not full content) as snapshot
lines = content.split('\n')
# Use first 20 non-empty lines as snapshot
snapshot = '\n'.join(l for l in lines if l.strip())[:800]
open('tests/integration/snapshots/thenewstack-developer-portal-api.md', 'w').write(snapshot)
"
```

Repeat for each of the 5 articles. Snapshots are subset-match assertions (not full content).

### 4. Create integration tests

```
tests/integration/test_thenewstack_integration.py
```

Pattern: identical to `test_substack_integration.py` — parametrized over URL/snapshot pairs, `@pytest.mark.integration`, snapshot containment check.

Also include: `test_homepage_raises_unsupported_content_type_error`.

### 5. Run verification

```bash
make test                    # all unit tests must pass
make lint                    # ruff check
uv run mypy src/             # zero type errors
make integration             # network required; all 5 snapshots must match
```
