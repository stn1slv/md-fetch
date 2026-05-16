"""Integration tests for The New Stack article extraction using real URLs."""

from __future__ import annotations

from pathlib import Path

import pytest

from mdfetch import extract
from mdfetch.exceptions import UnsupportedContentTypeError

SNAPSHOTS_DIR = Path(__file__).parent / "snapshots"

THENEWSTACK_TEST_CASES: list[tuple[str, str]] = [
    (
        "https://thenewstack.io/using-a-developer-portal-for-api-management/",
        "thenewstack-developer-portal-api.md",
    ),
    (
        "https://thenewstack.io/api-management-for-asynchronous-apis/",
        "thenewstack-async-apis.md",
    ),
    (
        "https://thenewstack.io/json-schema-ai-reliability/",
        "thenewstack-json-schema-ai.md",
    ),
    (
        "https://thenewstack.io/mcp-api-governance-readiness/",
        "thenewstack-mcp-api-governance.md",
    ),
    (
        "https://thenewstack.io/api-mcp-agent-integration/",
        "thenewstack-api-mcp-agent.md",
    ),
]


@pytest.mark.integration
@pytest.mark.parametrize("url,snapshot", THENEWSTACK_TEST_CASES)
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
        f"open('tests/integration/snapshots/{snapshot}', 'w').write(snapshot)"
        f'"'
    )


@pytest.mark.integration
def test_homepage_raises_unsupported_content_type_error() -> None:
    """US2: A thenewstack.io homepage raises UnsupportedContentTypeError."""
    with pytest.raises(UnsupportedContentTypeError):
        extract("https://thenewstack.io/", retries=1, retry_delay=0.0)
