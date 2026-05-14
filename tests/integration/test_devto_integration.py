"""Integration tests for dev.to article extraction using real URLs."""

from __future__ import annotations

from pathlib import Path

import pytest

from mdfetch import extract

SNAPSHOTS_DIR = Path(__file__).parent / "snapshots"

DEVTO_TEST_CASES = [
    (
        "https://dev.to/stn1slv/integration-digest-for-december-2025-5dlp",
        "devto-integration-digest-december-2025.md",
    ),
    (
        "https://dev.to/stn1slv/integration-digest-for-july-2025-4lk9",
        "devto-integration-digest-july-2025.md",
    ),
    (
        "https://dev.to/stn1slv/integration-digest-for-march-2026-599p",
        "devto-integration-digest-march-2026.md",
    ),
]


@pytest.mark.integration
@pytest.mark.parametrize("url,snapshot", DEVTO_TEST_CASES)
def test_extract_contains_snapshot(url: str, snapshot: str) -> None:
    """Assert the extracted Markdown contains all content stored in the snapshot.

    Snapshots are subsets of the full extraction output. The containment check
    ``expected in result`` verifies the snapshot content is present without
    requiring an exact match, making tests resilient to minor structural changes.

    Transient network failures (403, timeout) are handled by extract()'s built-in
    retry logic (3 retries, 2-second delay by default).
    """
    expected = (SNAPSHOTS_DIR / snapshot).read_text(encoding="utf-8")
    result = extract(url)
    assert expected in result, (
        f"Extracted content for {snapshot!r} does not contain the stored snapshot body.\n"
        f"To regenerate the snapshot, run:\n"
        f'  uv run python -c "'
        f"from mdfetch import extract; "
        f"open('tests/integration/snapshots/{snapshot}', 'w').write(extract('{url}'))"
        f'"'
    )
