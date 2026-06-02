"""Integration tests for Kong blog article extraction using real URLs."""

from __future__ import annotations

from pathlib import Path

import pytest

from mdfetch import extract
from mdfetch.exceptions import UnsupportedContentTypeError

SNAPSHOTS_DIR = Path(__file__).parent / "snapshots"

KONG_TEST_CASES: list[tuple[str, str]] = [
    (
        "https://konghq.com/blog/product-releases/insomnia-12-6",
        "kong-insomnia-12-6.md",
    ),
    (
        "https://konghq.com/blog/enterprise/kong-ai-gateway-vs-litellm",
        "kong-ai-gateway-vs-litellm.md",
    ),
    (
        "https://konghq.com/blog/product-releases/kong-gateway-3-14",
        "kong-gateway-3-14.md",
    ),
]

NON_ARTICLE_URLS: list[str] = [
    "https://konghq.com/blog",
    "https://konghq.com/blog/product-releases",
]


@pytest.mark.integration
@pytest.mark.parametrize("url,snapshot", KONG_TEST_CASES)
def test_extract_contains_snapshot(url: str, snapshot: str) -> None:
    """Assert the extracted Markdown contains all content stored in the snapshot.

    Snapshots are subsets of the full extraction output. The containment check
    ``expected in result`` verifies the snapshot content is present without
    requiring an exact match, making tests resilient to minor structural changes.
    """
    expected = (SNAPSHOTS_DIR / snapshot).read_text(encoding="utf-8")
    result = extract(url, retries=3, retry_delay=2.0)
    assert expected in result, (
        f"Extracted content for {snapshot!r} does not contain the stored snapshot body.\n"
        f"To regenerate the snapshot, run:\n"
        f'  uv run python -c "'
        f"from mdfetch import extract; "
        f"content = extract('{url}'); snapshot = '\\n'.join(content.split('\\n')[:30]).rstrip(); "
        f"open('tests/integration/snapshots/{snapshot}', 'w', encoding='utf-8').write(snapshot)"
        f'"'
    )


@pytest.mark.integration
@pytest.mark.parametrize("url", NON_ARTICLE_URLS)
def test_non_article_url_raises_unsupported_content_type_error(url: str) -> None:
    """US2: konghq.com non-article URLs (index, category listing) raise the typed error."""
    with pytest.raises(UnsupportedContentTypeError):
        extract(url, retries=1, retry_delay=0.0)
