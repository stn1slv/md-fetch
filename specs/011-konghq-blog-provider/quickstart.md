# Quickstart: Kong Blog Provider

## Use it

```python
from mdfetch import extract

md = extract("https://konghq.com/blog/product-releases/insomnia-12-6")
print(md)  # "# Insomnia 12.6: ..." then the date, then the article body
```

## Develop it (TDD-friendly order)

```bash
make setup            # uv sync --all-extras

# 1. Add src/mdfetch/providers/kong.py (KongExtractor) — see plan.md "Extraction Algorithm"
# 2. Write tests/unit/test_kong_extractor.py (no network) using sample HTML fixtures
make test             # unit tests only — should pass without network
make typecheck        # mypy src/ — zero errors
make lint             # ruff check

# 3. Add integration test + snapshots
make integration      # network required; hits real konghq.com URLs
```

## Reference URLs

| Slug | Use |
|------|-----|
| `product-releases/insomnia-12-6` | TL;DR lead, code snippets, in-body images, pull-quote, video placeholder (stripped) |
| `enterprise/kong-ai-gateway-vs-litellm` | many headings/lists, FAQ, comparison-chart link |
| `product-releases/kong-gateway-3-14` | five authors (dropped), in-body images |
| `https://konghq.com/blog` (index) | non-article → expect `UnsupportedContentTypeError` |
| `https://konghq.com/blog/product-releases` (category) | non-article → expect `UnsupportedContentTypeError` |

## Generate a snapshot (first 30 lines, blank lines preserved)

```bash
uv run python -c "from mdfetch import extract; c=extract('<url>'); \
open('tests/integration/snapshots/kong-<slug>.md','w',encoding='utf-8').write('\n'.join(c.split('\n')[:30]).rstrip())"
```

## Done when

- `make test`, `make typecheck`, `make lint` all green.
- `make integration` passes (snapshot containment for the 3 articles; index and a category
  listing both raise `UnsupportedContentTypeError`).
- Output keeps the publication date under the title and contains no author byline / read time.
- `README.md` Supported platforms table includes a `Kong | konghq.com` row.

## Watch out (CSS-module fragility)

Kong is a Next.js site; per-component class names like `Section_section__Grz_Y` are build
hashes and will change. Pin selectors only to the stable companion classes (`type-article`,
`rich-text-block`, `component`, `video`, `more-on-this`, `section-header-block`, `intro`,
`order-top`) plus the `TableOfContents` substring match and the date regex — never the
hashed `__xxxxx` suffixes. Record this as a `CLAUDE.md` gotcha during implementation.
