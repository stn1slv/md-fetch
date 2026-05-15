"""Unit tests for HTTP error propagation in BaseExtractor.fetch_html."""

from __future__ import annotations

from unittest.mock import MagicMock, call, patch

import httpx
import pytest

from mdfetch.exceptions import FetchError, HTTPStatusError
from mdfetch.providers.medium import MediumExtractor


@pytest.fixture()
def extractor() -> MediumExtractor:
    return MediumExtractor()


def _make_stream_mock(
    *,
    status_code: int = 200,
    is_success: bool = True,
    body: bytes = b"<html></html>",
    stream_side_effect: Exception | None = None,
) -> MagicMock:
    """Build a mock httpx.Client whose .stream() behaves like a real streaming response."""
    mock_response = MagicMock()
    mock_response.is_success = is_success
    mock_response.status_code = status_code
    mock_response.encoding = "utf-8"
    mock_response.iter_bytes.return_value = iter([body])

    mock_stream_ctx = MagicMock()
    mock_stream_ctx.__enter__ = MagicMock(return_value=mock_response)
    mock_stream_ctx.__exit__ = MagicMock(return_value=False)

    mock_client = MagicMock()
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=False)

    if stream_side_effect is not None:
        mock_client.stream.side_effect = stream_side_effect
    else:
        mock_client.stream.return_value = mock_stream_ctx

    return mock_client


class TestFetchErrors:
    def test_raises_http_status_error_on_404(self, extractor: MediumExtractor) -> None:
        mock = _make_stream_mock(status_code=404, is_success=False)
        with patch("httpx.Client", return_value=mock):
            with pytest.raises(HTTPStatusError) as exc_info:
                extractor.fetch_html("https://medium.com/article", retries=1)

        assert exc_info.value.status_code == 404

    def test_raises_http_status_error_on_503(self, extractor: MediumExtractor) -> None:
        mock = _make_stream_mock(status_code=503, is_success=False)
        with patch("httpx.Client", return_value=mock):
            with pytest.raises(HTTPStatusError) as exc_info:
                extractor.fetch_html("https://medium.com/article", retries=1)

        assert exc_info.value.status_code == 503

    def test_raises_fetch_error_on_timeout(self, extractor: MediumExtractor) -> None:
        with patch(
            "httpx.Client",
            return_value=_make_stream_mock(stream_side_effect=httpx.TimeoutException("timed out")),
        ):
            with pytest.raises(FetchError):
                extractor.fetch_html("https://medium.com/article", retries=1)

    def test_raises_fetch_error_on_connection_error(self, extractor: MediumExtractor) -> None:
        mock = _make_stream_mock(stream_side_effect=httpx.ConnectError("connection refused"))
        with patch("httpx.Client", return_value=mock):
            with pytest.raises(FetchError):
                extractor.fetch_html("https://medium.com/article", retries=1)

    def test_http_status_error_is_fetch_error(self, extractor: MediumExtractor) -> None:
        """HTTPStatusError must be a subclass of FetchError for callers catching FetchError."""
        mock = _make_stream_mock(status_code=404, is_success=False)
        with patch("httpx.Client", return_value=mock):
            with pytest.raises(FetchError):
                extractor.fetch_html("https://medium.com/article", retries=1)

    def test_raises_fetch_error_when_response_exceeds_size_limit(
        self, extractor: MediumExtractor
    ) -> None:
        oversized_body = b"x" * (11 * 1024 * 1024)  # 11 MB — over the 10 MB cap
        with patch("httpx.Client", return_value=_make_stream_mock(body=oversized_body)):
            with pytest.raises(FetchError, match="exceeded"):
                extractor.fetch_html("https://medium.com/article", retries=1)

    def test_exponential_backoff_sleep_sequence(self, extractor: MediumExtractor) -> None:
        mock = _make_stream_mock(status_code=503, is_success=False)
        with patch("httpx.Client", return_value=mock):
            with patch("mdfetch.base.time.sleep") as mock_sleep:
                with pytest.raises(HTTPStatusError):
                    extractor.fetch_html("https://medium.com/article", retries=4, retry_delay=1.0)

        # 4 attempts → 3 inter-attempt sleeps: 1.0 * 2^0, 2^1, 2^2
        assert mock_sleep.call_args_list == [call(1.0), call(2.0), call(4.0)]

    def test_exponential_backoff_capped_at_max_delay(self, extractor: MediumExtractor) -> None:
        mock = _make_stream_mock(status_code=503, is_success=False)
        with patch("httpx.Client", return_value=mock):
            with patch("mdfetch.base.time.sleep") as mock_sleep:
                with pytest.raises(HTTPStatusError):
                    # 7 attempts, retry_delay=2.0: uncapped sequence would be
                    # 2, 4, 8, 16, 32, 64 — last value must be clamped to 60
                    extractor.fetch_html("https://medium.com/article", retries=7, retry_delay=2.0)

        delays = [c.args[0] for c in mock_sleep.call_args_list]
        assert delays == [2.0, 4.0, 8.0, 16.0, 32.0, 60.0]

    def test_no_retry_status_codes_raises_immediately_without_sleep(
        self, extractor: MediumExtractor
    ) -> None:
        """Status codes in _no_retry_status_codes must raise immediately, no backoff sleep."""
        mock = _make_stream_mock(status_code=403, is_success=False)
        with patch("httpx.Client", return_value=mock):
            with patch("mdfetch.base.time.sleep") as mock_sleep:
                with pytest.raises(HTTPStatusError) as exc_info:
                    extractor.fetch_html("https://medium.com/article", retries=3)

        assert exc_info.value.status_code == 403
        mock_sleep.assert_not_called()

    def test_no_retry_status_codes_raises_immediately_for_429(
        self, extractor: MediumExtractor
    ) -> None:
        mock = _make_stream_mock(status_code=429, is_success=False)
        with patch("httpx.Client", return_value=mock):
            with patch("mdfetch.base.time.sleep") as mock_sleep:
                with pytest.raises(HTTPStatusError) as exc_info:
                    extractor.fetch_html("https://medium.com/article", retries=3)

        assert exc_info.value.status_code == 429
        mock_sleep.assert_not_called()

    def test_status_code_not_in_no_retry_set_still_retries(
        self, extractor: MediumExtractor
    ) -> None:
        """Status codes NOT in _no_retry_status_codes (e.g. 503) must still trigger backoff."""
        mock = _make_stream_mock(status_code=503, is_success=False)
        with patch("httpx.Client", return_value=mock):
            with patch("mdfetch.base.time.sleep") as mock_sleep:
                with pytest.raises(HTTPStatusError):
                    extractor.fetch_html("https://medium.com/article", retries=3, retry_delay=1.0)

        assert mock_sleep.call_count == 2  # 3 attempts → 2 sleeps
