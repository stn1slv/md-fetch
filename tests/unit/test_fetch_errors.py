"""Unit tests for HTTP error propagation in BaseExtractor.fetch_html."""

from __future__ import annotations

from unittest.mock import call, patch

import httpx
import pytest

from mdfetch.exceptions import FetchError, HTTPStatusError, UnsupportedContentTypeError
from mdfetch.providers.medium import MediumExtractor
from tests.conftest import make_stream_mock


@pytest.fixture()
def extractor() -> MediumExtractor:
    return MediumExtractor()


class TestFetchErrors:
    def test_raises_http_status_error_on_404(self, extractor: MediumExtractor) -> None:
        mock = make_stream_mock(status_code=404, is_success=False)
        with patch("httpx.Client", return_value=mock):
            with pytest.raises(HTTPStatusError) as exc_info:
                extractor.fetch_html("https://medium.com/article", retries=1)

        assert exc_info.value.status_code == 404

    def test_raises_http_status_error_on_503(self, extractor: MediumExtractor) -> None:
        mock = make_stream_mock(status_code=503, is_success=False)
        with patch("httpx.Client", return_value=mock):
            with pytest.raises(HTTPStatusError) as exc_info:
                extractor.fetch_html("https://medium.com/article", retries=1)

        assert exc_info.value.status_code == 503

    def test_raises_fetch_error_on_timeout(self, extractor: MediumExtractor) -> None:
        with patch(
            "httpx.Client",
            return_value=make_stream_mock(stream_side_effect=httpx.TimeoutException("timed out")),
        ):
            with pytest.raises(FetchError):
                extractor.fetch_html("https://medium.com/article", retries=1)

    def test_raises_fetch_error_on_connection_error(self, extractor: MediumExtractor) -> None:
        mock = make_stream_mock(stream_side_effect=httpx.ConnectError("connection refused"))
        with patch("httpx.Client", return_value=mock):
            with pytest.raises(FetchError):
                extractor.fetch_html("https://medium.com/article", retries=1)

    def test_http_status_error_is_fetch_error(self, extractor: MediumExtractor) -> None:
        """HTTPStatusError must be a subclass of FetchError for callers catching FetchError."""
        mock = make_stream_mock(status_code=404, is_success=False)
        with patch("httpx.Client", return_value=mock):
            with pytest.raises(FetchError):
                extractor.fetch_html("https://medium.com/article", retries=1)

    def test_raises_fetch_error_when_response_exceeds_size_limit(
        self, extractor: MediumExtractor
    ) -> None:
        oversized_body = b"x" * (11 * 1024 * 1024)  # 11 MB — over the 10 MB cap
        with patch("httpx.Client", return_value=make_stream_mock(body=oversized_body)):
            with pytest.raises(FetchError, match="exceeded"):
                extractor.fetch_html("https://medium.com/article", retries=1)

    def test_no_retry_status_codes_raises_immediately_without_sleep(
        self, extractor: MediumExtractor
    ) -> None:
        """Status codes in _no_retry_status_codes must raise immediately, no retry sleep."""
        mock = make_stream_mock(status_code=403, is_success=False)
        with patch("httpx.Client", return_value=mock):
            with patch("mdfetch.base.time.sleep") as mock_sleep:
                with pytest.raises(HTTPStatusError) as exc_info:
                    extractor.fetch_html("https://medium.com/article", retries=3)

        assert exc_info.value.status_code == 403
        mock_sleep.assert_not_called()

    def test_no_retry_status_codes_raises_immediately_for_429(
        self, extractor: MediumExtractor
    ) -> None:
        mock = make_stream_mock(status_code=429, is_success=False)
        with patch("httpx.Client", return_value=mock):
            with patch("mdfetch.base.time.sleep") as mock_sleep:
                with pytest.raises(HTTPStatusError) as exc_info:
                    extractor.fetch_html("https://medium.com/article", retries=3)

        assert exc_info.value.status_code == 429
        mock_sleep.assert_not_called()

    def test_status_code_not_in_no_retry_set_still_retries(
        self, extractor: MediumExtractor
    ) -> None:
        """Status codes NOT in _no_retry_status_codes must still trigger retry with fixed delay."""
        mock = make_stream_mock(status_code=503, is_success=False)
        with patch("httpx.Client", return_value=mock):
            with patch("mdfetch.base.time.sleep") as mock_sleep:
                with pytest.raises(HTTPStatusError):
                    extractor.fetch_html("https://medium.com/article", retries=3, retry_delay=1.0)

        assert mock_sleep.call_count == 2  # 3 attempts → 2 sleeps
        assert mock_sleep.call_args_list == [call(1.0), call(1.0)]  # fixed delay, not exponential

    def test_raises_unsupported_content_type_for_json(self, extractor: MediumExtractor) -> None:
        mock = make_stream_mock(content_type="application/json")
        with patch("httpx.Client", return_value=mock):
            with pytest.raises(UnsupportedContentTypeError, match="application/json"):
                extractor.fetch_html("https://medium.com/article", retries=1)

    def test_raises_unsupported_content_type_for_pdf(self, extractor: MediumExtractor) -> None:
        mock = make_stream_mock(content_type="application/pdf")
        with patch("httpx.Client", return_value=mock):
            with pytest.raises(UnsupportedContentTypeError, match="application/pdf"):
                extractor.fetch_html("https://medium.com/article", retries=1)

    def test_accepts_xhtml_content_type(self, extractor: MediumExtractor) -> None:
        body = b"<html><body><article><p>Test</p></article></body></html>"
        mock = make_stream_mock(body=body, content_type="application/xhtml+xml; charset=utf-8")
        with patch("httpx.Client", return_value=mock):
            result = extractor.fetch_html("https://medium.com/article", retries=1)
        assert "Test" in result

    def test_accepts_empty_content_type(self, extractor: MediumExtractor) -> None:
        """Servers that omit Content-Type should not trigger the check."""
        body = b"<html><body><article><p>Test</p></article></body></html>"
        mock = make_stream_mock(body=body, content_type="")
        with patch("httpx.Client", return_value=mock):
            result = extractor.fetch_html("https://medium.com/article", retries=1)
        assert "Test" in result
