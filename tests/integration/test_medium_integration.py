"""Integration tests for Medium article extraction using real URLs."""

from __future__ import annotations

from pathlib import Path

import pytest

from mdfetch import extract

SNAPSHOTS_DIR = Path(__file__).parent / "snapshots"

MEDIUM_TEST_CASES = [
    (
        "https://stn1slv.medium.com/from-drift-to-parity-building-a-feedback-loop-for-spec-driven-development-b3bd3d9c0021",
        "from-drift-to-parity.md",
    ),
    (
        "https://stn1slv.medium.com/architecting-the-asynchronous-agent-a-guide-to-mcp-tasks-7348c6527233",
        "architecting-the-asynchronous-agent.md",
    ),
    (
        "https://stn1slv.medium.com/integration-digest-december-2025-5339cb35e609",
        "integration-digest-december-2025.md",
    ),
]


@pytest.mark.integration
@pytest.mark.parametrize("url,snapshot", MEDIUM_TEST_CASES)
def test_extract_contains_snapshot(
    url: str, snapshot: str, http_retries: int, http_retry_delay: float
) -> None:
    """Assert the extracted Markdown contains all content stored in the snapshot.

    Snapshots are subsets of the full extraction output. The containment check
    ``expected in result`` verifies the snapshot content is present without
    requiring an exact match, making tests resilient to minor structural changes.

    Retry count and delay are controlled via MDFETCH_RETRIES and MDFETCH_RETRY_DELAY
    environment variables (defaults: 3 total attempts, 2.0 s base delay, exponential backoff).
    """
    expected = (SNAPSHOTS_DIR / snapshot).read_text(encoding="utf-8")
    result = extract(url, retries=http_retries, retry_delay=http_retry_delay)
    assert expected in result, (
        f"Extracted content for {snapshot!r} does not contain the stored snapshot body.\n"
        f"To regenerate the snapshot, run:\n"
        f'  uv run python -c "'
        f"from mdfetch import extract; "
        f"open('tests/integration/snapshots/{snapshot}', 'w').write(extract('{url}'))"
        f'"'
    )
