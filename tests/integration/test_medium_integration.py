"""Integration tests for Medium article extraction using real URLs."""

from __future__ import annotations

import time
from pathlib import Path

import pytest

from mdfetch import extract
from mdfetch.exceptions import FetchError


def _extract_with_retry(url: str, *, retries: int = 3, delay: float = 2.0) -> str:
    """Call extract(), retrying up to *retries* times on transient FetchError."""
    last_exc: FetchError | None = None
    for attempt in range(retries):
        try:
            return extract(url)
        except FetchError as exc:
            last_exc = exc
            if attempt < retries - 1:
                time.sleep(delay)
    assert last_exc is not None
    raise last_exc

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
def test_extract_contains_snapshot(url: str, snapshot: str) -> None:
    """Assert the extracted article body contains all content stored in the snapshot.

    Snapshots hold only the article body (header stripped). Since extract() returns
    header + body, ``snapshot_body in full_result`` is the natural containment check
    and requires no fragile marker-based stripping in the test itself.
    """
    expected = (SNAPSHOTS_DIR / snapshot).read_text(encoding="utf-8")
    result = _extract_with_retry(url)
    assert expected in result, (
        f"Extracted content for {snapshot!r} does not contain the stored snapshot body.\n"
        f"To regenerate the snapshot, run:\n"
        f'  uv run python -c "'
        f"from mdfetch import extract; "
        f"open('tests/integration/snapshots/{snapshot}', 'w').write(extract('{url}'))"
        f'"'
    )
