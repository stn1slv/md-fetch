# Quickstart: Boomi Blog Provider

## Use it

```python
from mdfetch import extract

md = extract("https://boomi.com/blog/real-time-vs-batch-data-integration-choosing-the-right-approach/")
print(md)  # "# Real-Time vs Batch Data Integration: ..." followed by the article body
```

## Develop it (TDD-friendly order)

```bash
make setup            # uv sync --all-extras

# 1. Add src/mdfetch/providers/boomi.py (BoomiExtractor) — see plan.md "Extraction Algorithm"
# 2. Write tests/unit/test_boomi_extractor.py (no network) using sample HTML fixtures
make test             # unit tests only — should pass without network
make typecheck        # mypy src/ — zero errors
make lint             # ruff check

# 3. Add integration test + snapshots
make integration      # network required; hits real boomi.com URLs
```

## Reference URLs

| Slug | Use |
|------|-----|
| `gartner-magic-quadrant-ipaas-2026` | has 1 in-body image + blockquote |
| `real-time-vs-batch-data-integration-choosing-the-right-approach` | headings + lists |
| `how-to-maintain-data-consistency-across-saas-and-on-prem-systems` | headings + blockquote |
| `https://boomi.com/blog/` (index) | non-article → expect `UnsupportedContentTypeError` |

## Generate a snapshot (first 30 lines, blank lines preserved)

```bash
uv run python -c "from mdfetch import extract; c=extract('<url>'); \
open('tests/integration/snapshots/boomi-<slug>.md','w',encoding='utf-8').write('\n'.join(c.split('\n')[:30]).rstrip())"
```

## Done when

- `make test`, `make typecheck`, `make lint` all green.
- `make integration` passes (snapshot containment for the 3 articles; index raises `UnsupportedContentTypeError`).
- `README.md` Supported platforms table includes a `Boomi | boomi.com` row.
