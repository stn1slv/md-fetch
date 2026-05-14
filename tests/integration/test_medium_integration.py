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
def test_extract_matches_snapshot(url: str, snapshot: str) -> None:
    expected = (SNAPSHOTS_DIR / snapshot).read_text(encoding="utf-8")
    result = extract(url)
    assert result == expected, (
        f"Extracted content for {snapshot!r} does not match the stored snapshot.\n"
        f"Run `uv run python -c \"from mdfetch import extract; "
        f"open('tests/integration/snapshots/{snapshot}', 'w').write(extract('{url}'))\"` "
        f"to update the snapshot if the article content has legitimately changed."
    )
