"""Unit tests for the mdfetch CLI (no network)."""

from __future__ import annotations

import pathlib

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


def test_output_refuses_to_clobber_existing_file(
    mocker: pytest_mock.MockerFixture, runner: CliRunner, tmp_path: pathlib.Path
) -> None:
    mocker.patch("mdfetch.cli.extract", return_value="# Test")
    out = tmp_path / "out.md"
    out.write_text("existing content")
    result = runner.invoke(main, ["https://dev.to/test", "-o", str(out)])
    assert result.exit_code == 1
    assert "already exists" in result.output
    assert out.read_text() == "existing content"


def test_output_force_overwrites_existing_file(
    mocker: pytest_mock.MockerFixture, runner: CliRunner, tmp_path: pathlib.Path
) -> None:
    mocker.patch("mdfetch.cli.extract", return_value="# Test")
    out = tmp_path / "out.md"
    out.write_text("existing content")
    result = runner.invoke(main, ["https://dev.to/test", "-o", str(out), "--force"])
    assert result.exit_code == 0
    assert out.read_text() == "# Test"


def test_list_platforms_lists_every_domain(runner: CliRunner) -> None:
    from mdfetch.router import supported_domains

    result = runner.invoke(main, ["--list-platforms"])
    assert result.exit_code == 0
    assert "Supported platforms:" in result.output
    for domain in supported_domains():
        assert domain in result.output


def test_list_platforms_makes_no_network_call(
    mocker: pytest_mock.MockerFixture, runner: CliRunner
) -> None:
    mock_extract = mocker.patch("mdfetch.cli.extract")
    result = runner.invoke(main, ["--list-platforms"])
    assert result.exit_code == 0
    mock_extract.assert_not_called()


def test_list_platforms_takes_precedence_over_url(
    mocker: pytest_mock.MockerFixture, runner: CliRunner
) -> None:
    # FR-008: when both --list-platforms and a URL are supplied, the list wins
    # and no extraction occurs.
    mock_extract = mocker.patch("mdfetch.cli.extract")
    result = runner.invoke(main, ["--list-platforms", "https://dev.to/test"])
    assert result.exit_code == 0
    assert "Supported platforms:" in result.output
    mock_extract.assert_not_called()


def test_missing_url_without_flag_is_usage_error(runner: CliRunner) -> None:
    result = runner.invoke(main, [])
    assert result.exit_code == 2
    assert "URL" in result.output


def test_list_platforms_annotates_subdomain_support(runner: CliRunner) -> None:
    # FR-006: multi-tenant platforms show a wildcard; exact-match ones do not.
    result = runner.invoke(main, ["--list-platforms"])
    assert result.exit_code == 0
    assert "*.medium.com" in result.output
    # dev.to is exact-match only — it must appear without a wildcard prefix.
    assert "*.dev.to" not in result.output
