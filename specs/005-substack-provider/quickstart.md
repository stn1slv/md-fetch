# Quickstart: Substack Platform Provider

## Usage

```python
from mdfetch import extract

# Free article
md = extract("https://getkafkanated.substack.com/p/kafka-deserves-topic-types")
print(md[:200])
# # Kafka deserves topic types
# ...

# Paywalled article — returns free preview silently
md = extract("https://pragmaticapi.substack.com/p/api-trends-for-2025-the-evolution")

# Publication homepage — raises UnsupportedContentTypeError
from mdfetch.exceptions import UnsupportedContentTypeError
try:
    md = extract("https://getkafkanated.substack.com/")
except UnsupportedContentTypeError:
    print("Not an article page")
```

## Running Tests

```bash
# Unit tests (no network)
make test

# Integration tests (requires network)
make integration
```

## Adding a New Provider (reference)

Substack follows the same pattern as all providers:

1. Create `src/mdfetch/providers/substack.py`
2. Define `class SubstackExtractor(BaseExtractor)` decorated with `@register`
3. Set `DOMAINS: frozenset[str] = frozenset({"substack.com"})`
4. Implement `clean_html(soup)` and `convert_to_markdown(tag)`
5. Add unit tests in `tests/unit/test_substack.py`
6. Add integration tests in `tests/integration/test_substack_integration.py`
