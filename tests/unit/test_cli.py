"""Unit tests for the mdfetch CLI (no network)."""

from __future__ import annotations

import pytest
import pytest_mock
from click.testing import CliRunner

from mdfetch.cli import main
from mdfetch.exceptions import FetchError


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


def test_error_handling_with_runner(mocker: pytest_mock.MockerFixture, runner: CliRunner) -> None:
    mocker.patch("mdfetch.cli.extract", side_effect=FetchError("Network timeout after 3 retries"))
    result = runner.invoke(main, ["https://dev.to/test"])
    assert result.exit_code == 1
    assert "Network timeout after 3 retries" in result.output


def test_version_flag(runner: CliRunner) -> None:
    result = runner.invoke(main, ["--version"])
    assert result.exit_code == 0
    assert "md-fetch" in result.output
    assert "version" in result.output


def test_retries_flag(mocker: pytest_mock.MockerFixture, runner: CliRunner) -> None:
    mock_extract = mocker.patch("mdfetch.cli.extract", return_value="# Test")
    result = runner.invoke(main, ["https://dev.to/test", "--retries", "5", "--retry-delay", "0.5"])
    assert result.exit_code == 0
    mock_extract.assert_called_once_with("https://dev.to/test", retries=5, retry_delay=0.5)


def test_unsupported_domain_error_message(runner: CliRunner) -> None:
    result = runner.invoke(main, ["https://google.com/article"])
    assert result.exit_code == 1
    assert "'google.com' is not a supported platform." in result.output
    assert "Supported domains:" in result.output
