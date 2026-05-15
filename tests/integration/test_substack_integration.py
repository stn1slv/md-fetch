"""Integration tests for Substack article extraction using real URLs."""

from __future__ import annotations

from pathlib import Path

import pytest

from mdfetch import extract
from mdfetch.exceptions import UnsupportedContentTypeError

SNAPSHOTS_DIR = Path(__file__).parent / "snapshots"

SUBSTACK_TEST_CASES = [
    (
        "https://getkafkanated.substack.com/p/kafka-deserves-topic-types",
        "substack-kafka-topic-types.md",
    ),
    (
        "https://pragmaticapi.substack.com/p/api-trends-for-2025-the-evolution",
        "substack-api-trends-2025.md",
    ),
]


@pytest.mark.integration
@pytest.mark.parametrize("url,snapshot", SUBSTACK_TEST_CASES)
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
        f"open('tests/integration/snapshots/{snapshot}', 'w').write(extract('{url}'))"
        f'"'
    )


@pytest.mark.integration
def test_homepage_raises_unsupported_content_type_error() -> None:
    """US3: A Substack publication homepage raises UnsupportedContentTypeError."""
    with pytest.raises(UnsupportedContentTypeError):
        extract("https://getkafkanated.substack.com/", retries=1, retry_delay=0.0)
