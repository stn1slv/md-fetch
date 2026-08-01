"""Unit tests for Tavily fallback."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from mdfetch import extract
from mdfetch.exceptions import FetchError, MissingAPIKeyError
from mdfetch.fallback import tavily_extract


class TestTavilyExtract:
    @patch("tavily.TavilyClient")
    def test_basic_depth_success(self, mock_tavily_client: MagicMock) -> None:
        mock_instance = mock_tavily_client.return_value
        mock_instance.extract.return_value = {"results": [{"raw_content": "# Hello"}]}

        result = tavily_extract("https://example.com")

        assert result == "# Hello"
        mock_instance.extract.assert_called_once_with(
            urls=["https://example.com"], extract_depth="basic"
        )

    @patch("tavily.TavilyClient")
    def test_fallback_to_advanced_on_empty(self, mock_tavily_client: MagicMock) -> None:
        mock_instance = mock_tavily_client.return_value
        # First call fails (empty), second call succeeds
        mock_instance.extract.side_effect = [
            {"results": [{"raw_content": ""}]},
            {"results": [{"raw_content": "# Advanced"}]},
        ]

        result = tavily_extract("https://example.com")

        assert result == "# Advanced"
        assert mock_instance.extract.call_count == 2
        mock_instance.extract.assert_any_call(
            urls=["https://example.com"], extract_depth="advanced"
        )

    @patch("tavily.TavilyClient")
    def test_fallback_to_advanced_on_exception(self, mock_tavily_client: MagicMock) -> None:
        mock_instance = mock_tavily_client.return_value
        # First call raises exception, second call succeeds
        mock_instance.extract.side_effect = [
            Exception("API Error"),
            {"results": [{"raw_content": "# Advanced"}]},
        ]

        result = tavily_extract("https://example.com")

        assert result == "# Advanced"
        assert mock_instance.extract.call_count == 2

    @patch("tavily.TavilyClient")
    def test_advanced_failure_raises_fetch_error(self, mock_tavily_client: MagicMock) -> None:
        mock_instance = mock_tavily_client.return_value
        mock_instance.extract.side_effect = Exception("API Error")

        with pytest.raises(FetchError):
            tavily_extract("https://example.com")


class TestExtractRouting:
    @patch("mdfetch.tavily_extract")
    @patch.dict("os.environ", {"TAVILY_API_KEY": "fake-key"})
    def test_unsupported_platform_routes_to_fallback(self, mock_tavily: MagicMock) -> None:
        mock_tavily.return_value = "# Fallback content"

        # example.com is not supported
        result = extract("https://example.com", tavily_fallback=True)

        assert result == "# Fallback content"
        mock_tavily.assert_called_once_with("https://example.com", timeout=30.0)

    @patch.dict("os.environ", {}, clear=True)
    def test_missing_api_key_raises(self) -> None:
        with pytest.raises(MissingAPIKeyError):
            extract("https://example.com", tavily_fallback=True)

    @patch("mdfetch.router.route")
    @patch("mdfetch.tavily_extract")
    @patch.dict("os.environ", {"TAVILY_API_KEY": "fake-key"})
    def test_provider_failure_routes_to_fallback(
        self, mock_tavily: MagicMock, mock_route: MagicMock
    ) -> None:
        mock_tavily.return_value = "# Fallback content"

        mock_provider = MagicMock()
        mock_provider.extract.side_effect = FetchError("Provider failed")
        mock_route.return_value = mock_provider

        result = extract("https://medium.com/test", tavily_fallback=True)

        assert result == "# Fallback content"
        mock_tavily.assert_called_once_with("https://medium.com/test", timeout=30.0)
