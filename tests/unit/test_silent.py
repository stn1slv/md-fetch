"""FR-013: The library must not emit any logging, print, or diagnostic output."""

from __future__ import annotations

import logging
from unittest.mock import patch

import pytest

from mdfetch import extract
from tests.conftest import make_stream_mock


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
    mock_client = make_stream_mock(body=mock_medium_response.encode("utf-8"))
    with patch("httpx.Client", return_value=mock_client):
        extract("https://medium.com/article", retries=1)

    captured = capsys.readouterr()
    assert captured.out == "", "Library must not write to stdout"
    assert captured.err == "", "Library must not write to stderr"


def test_no_logging_during_extraction(mock_medium_response: str) -> None:
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
        mock_client = make_stream_mock(body=mock_medium_response.encode("utf-8"))
        with patch("httpx.Client", return_value=mock_client):
            extract("https://medium.com/article", retries=1)
    finally:
        root_logger.removeHandler(handler)
        root_logger.setLevel(old_level)

    mdfetch_records = [r for r in log_records if r.name.startswith("mdfetch")]
    assert len(mdfetch_records) == 0, "Library must not emit logging output"
