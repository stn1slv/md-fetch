"""Shared test fixtures and helpers."""

from __future__ import annotations

from unittest.mock import MagicMock


def make_stream_mock(
    *,
    status_code: int = 200,
    is_success: bool = True,
    body: bytes = b"<html></html>",
    content_type: str = "text/html; charset=utf-8",
    stream_side_effect: Exception | None = None,
) -> MagicMock:
    """Build a mock httpx.Client whose .stream() behaves like a real streaming response."""
    mock_response = MagicMock()
    mock_response.is_success = is_success
    mock_response.status_code = status_code
    mock_response.encoding = "utf-8"
    mock_response.iter_bytes.side_effect = lambda: iter([body])
    mock_response.headers = {"content-type": content_type}

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
