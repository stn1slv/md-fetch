"""Integration tests for Medium article extraction using real URLs."""

from __future__ import annotations

import re

import pytest

from mdfetch import extract

MEDIUM_TEST_URLS = [
    "https://stn1slv.medium.com/from-drift-to-parity-building-a-feedback-loop-for-spec-driven-development-b3bd3d9c0021",
    "https://stn1slv.medium.com/architecting-the-asynchronous-agent-a-guide-to-mcp-tasks-7348c6527233",
    "https://stn1slv.medium.com/integration-digest-december-2025-5339cb35e609",
]


@pytest.mark.integration
@pytest.mark.parametrize("url", MEDIUM_TEST_URLS)
def test_extract_returns_markdown(url: str) -> None:
    result = extract(url)

    assert isinstance(result, str), "Result must be a string"
    assert len(result) > 200, "Result must have substantial content"
    # Exclude Markdown autolinks (<https://...>) which are valid output, not HTML tags
    assert not re.search(r"<(?!https?://|ftp://)[a-zA-Z][^>]*>", result), (
        "Result must not contain HTML tags"
    )
    assert "# " in result, "Result must contain at least one Markdown heading"
