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


def _strip_header(md: str) -> str:
    """Drop the Medium article header (avatar, byline, date, listen link, cover image).

    The header consistently ends with an empty cover image placeholder ![]() before
    the article body begins. Returns the original string unchanged if not found.
    """
    marker = "\n\n![]()"
    idx = md.find(marker)
    if idx == -1:
        return md
    return md[idx + len(marker):].lstrip("\n")


@pytest.mark.integration
@pytest.mark.parametrize("url,snapshot", MEDIUM_TEST_CASES)
def test_extract_contains_snapshot(url: str, snapshot: str) -> None:
    expected = (SNAPSHOTS_DIR / snapshot).read_text(encoding="utf-8")
    result = _strip_header(extract(url))
    assert expected in result, (
        f"Extracted body for {snapshot!r} does not contain the stored snapshot content.\n"
        f"Run the following to update the snapshot if the change is intentional:\n"
        f"  uv run python -c \""
        f"from mdfetch import extract; "
        f"open('tests/integration/snapshots/{snapshot}', 'w').write("
        f"extract('{url}').split('\\n\\n![]()')[1].lstrip('\\n'))"
        f"\""
    )
