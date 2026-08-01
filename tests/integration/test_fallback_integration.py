"""Integration tests for Tavily fallback."""

from __future__ import annotations

import os
from unittest.mock import MagicMock, patch

import pytest

from mdfetch import extract
from mdfetch.exceptions import FetchError


@pytest.mark.integration
class TestTavilyIntegration:
    @pytest.fixture(autouse=True)
    def check_api_key(self) -> None:
        if not os.environ.get("TAVILY_API_KEY"):
            pytest.skip("TAVILY_API_KEY not set")

    def test_fallback_on_unsupported_blog(self) -> None:
        url = "https://example.com"
        content = extract(url, tavily_fallback=True)
        assert content
        assert len(content) > 10

    @patch("mdfetch.providers.medium.MediumExtractor.extract")
    def test_fallback_on_supported_failure(self, mock_extract: MagicMock) -> None:
        mock_extract.side_effect = FetchError("Forced failure")

        url = "https://medium.com/@username/test-article"
        content = extract(url, tavily_fallback=True)

        assert content
        mock_extract.assert_called_once()
