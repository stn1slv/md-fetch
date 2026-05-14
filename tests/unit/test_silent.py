"""FR-013: The library must not emit any logging, print, or diagnostic output."""

from __future__ import annotations

import logging
from unittest.mock import MagicMock, patch

import pytest

from mdfetch import extract


@pytest.fixture()
def mock_medium_response() -> str:
    return """
    <html>
    <body>
      <article>
        <h1>Silent Article</h1>
        <p>This article produces no library output.</p>
      </article>
    </body>
    </html>
    """


def test_no_stdout_during_successful_extraction(
    capsys: pytest.CaptureFixture[str], mock_medium_response: str
) -> None:
    mock_resp = MagicMock()
    mock_resp.is_success = True
    mock_resp.status_code = 200
    mock_resp.text = mock_medium_response

    with patch("httpx.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.get.return_value = mock_resp
        mock_client_cls.return_value = mock_client

        extract("https://medium.com/article")

    captured = capsys.readouterr()
    assert captured.out == "", "Library must not write to stdout"
    assert captured.err == "", "Library must not write to stderr"


def test_no_logging_during_extraction(mock_medium_response: str) -> None:
    mock_resp = MagicMock()
    mock_resp.is_success = True
    mock_resp.status_code = 200
    mock_resp.text = mock_medium_response

    log_records: list[logging.LogRecord] = []

    class CapturingHandler(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            log_records.append(record)

    root_logger = logging.getLogger()
    handler = CapturingHandler()
    root_logger.addHandler(handler)
    old_level = root_logger.level
    root_logger.setLevel(logging.DEBUG)

    try:
        with patch("httpx.Client") as mock_client_cls:
            mock_client = MagicMock()
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=False)
            mock_client.get.return_value = mock_resp
            mock_client_cls.return_value = mock_client

            extract("https://medium.com/article")
    finally:
        root_logger.removeHandler(handler)
        root_logger.setLevel(old_level)

    mdfetch_records = [r for r in log_records if r.name.startswith("mdfetch")]
    assert len(mdfetch_records) == 0, "Library must not emit logging output"
