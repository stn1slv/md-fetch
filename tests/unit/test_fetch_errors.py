"""Unit tests for HTTP error propagation in BaseExtractor.fetch_html."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import httpx
import pytest

from mdfetch.exceptions import FetchError, HTTPStatusError
from mdfetch.providers.medium import MediumExtractor


@pytest.fixture()
def extractor() -> MediumExtractor:
    return MediumExtractor()


class TestFetchErrors:
    def test_raises_http_status_error_on_404(self, extractor: MediumExtractor) -> None:
        mock_response = MagicMock()
        mock_response.is_success = False
        mock_response.status_code = 404

        with patch("httpx.Client") as mock_client_cls:
            mock_client = MagicMock()
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=False)
            mock_client.get.return_value = mock_response
            mock_client_cls.return_value = mock_client

            with pytest.raises(HTTPStatusError) as exc_info:
                extractor.fetch_html("https://medium.com/article")

        assert exc_info.value.status_code == 404

    def test_raises_http_status_error_on_503(self, extractor: MediumExtractor) -> None:
        mock_response = MagicMock()
        mock_response.is_success = False
        mock_response.status_code = 503

        with patch("httpx.Client") as mock_client_cls:
            mock_client = MagicMock()
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=False)
            mock_client.get.return_value = mock_response
            mock_client_cls.return_value = mock_client

            with pytest.raises(HTTPStatusError) as exc_info:
                extractor.fetch_html("https://medium.com/article")

        assert exc_info.value.status_code == 503

    def test_raises_fetch_error_on_timeout(self, extractor: MediumExtractor) -> None:
        with patch("httpx.Client") as mock_client_cls:
            mock_client = MagicMock()
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=False)
            mock_client.get.side_effect = httpx.TimeoutException("timed out")
            mock_client_cls.return_value = mock_client

            with pytest.raises(FetchError):
                extractor.fetch_html("https://medium.com/article")

    def test_raises_fetch_error_on_connection_error(self, extractor: MediumExtractor) -> None:
        with patch("httpx.Client") as mock_client_cls:
            mock_client = MagicMock()
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=False)
            mock_client.get.side_effect = httpx.ConnectError("connection refused")
            mock_client_cls.return_value = mock_client

            with pytest.raises(FetchError):
                extractor.fetch_html("https://medium.com/article")

    def test_http_status_error_is_fetch_error(self, extractor: MediumExtractor) -> None:
        """HTTPStatusError must be a subclass of FetchError for callers catching FetchError."""
        mock_response = MagicMock()
        mock_response.is_success = False
        mock_response.status_code = 404

        with patch("httpx.Client") as mock_client_cls:
            mock_client = MagicMock()
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=False)
            mock_client.get.return_value = mock_response
            mock_client_cls.return_value = mock_client

            with pytest.raises(FetchError):
                extractor.fetch_html("https://medium.com/article")
