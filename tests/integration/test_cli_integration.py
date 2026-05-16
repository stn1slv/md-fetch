"""
Integration tests for the mdfetch CLI.
"""

from __future__ import annotations

import pathlib
import subprocess

import pytest
import pytest_mock


@pytest.mark.integration
def test_fetch_to_stdout() -> None:
    """Test fetching a URL and printing it to standard output."""
    url = "https://dev.to/stn1slv/integration-digest-for-december-2025-5dlp"
    result = subprocess.run(
        ["uv", "run", "md-fetch", url], capture_output=True, text=True, check=False
    )
    assert result.returncode == 0
    assert "Integration Digest for December 2025" in result.stdout


@pytest.mark.integration
def test_fetch_to_file(tmp_path: pathlib.Path) -> None:
    """Test fetching a URL and saving it to a file."""
    url = "https://dev.to/stn1slv/integration-digest-for-december-2025-5dlp"
    output_file = tmp_path / "output.md"
    result = subprocess.run(
        ["uv", "run", "md-fetch", url, "-o", str(output_file)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert result.stdout == ""
    assert output_file.exists()
    assert "Integration Digest for December 2025" in output_file.read_text()


@pytest.mark.integration
def test_unsupported_url_error() -> None:
    """Test fetching an unsupported URL prints to stderr and exits 1."""
    url = "https://unsupported.com"
    result = subprocess.run(
        ["uv", "run", "md-fetch", url], capture_output=True, text=True, check=False
    )
    assert result.returncode == 1
    assert "No provider registered for domain 'unsupported.com'" in result.stderr
    assert result.stdout == ""


def test_error_handling_with_runner(mocker: pytest_mock.MockerFixture) -> None:
    from click.testing import CliRunner

    from mdfetch.cli import main
    from mdfetch.exceptions import FetchError

    mocker.patch("mdfetch.cli.extract", side_effect=FetchError("Network timeout after 3 retries"))
    runner = CliRunner()
    result = runner.invoke(main, ["https://dev.to/test"])

    assert result.exit_code == 1
    assert "Network timeout after 3 retries" in result.stderr


def test_version_flag() -> None:
    from click.testing import CliRunner

    from mdfetch.cli import main

    runner = CliRunner()
    result = runner.invoke(main, ["--version"])
    assert result.exit_code == 0
    assert "mdfetch" in result.output
    assert "version" in result.output


def test_retries_flag(mocker: pytest_mock.MockerFixture) -> None:
    from click.testing import CliRunner

    from mdfetch.cli import main

    mock_extract = mocker.patch("mdfetch.cli.extract", return_value="# Test")
    runner = CliRunner()
    runner.invoke(main, ["https://dev.to/test", "--retries", "5", "--retry-delay", "0.5"])

    mock_extract.assert_called_once_with("https://dev.to/test", retries=5, retry_delay=0.5)
