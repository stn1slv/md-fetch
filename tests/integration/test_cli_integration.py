"""
Integration tests for the mdfetch CLI.
"""

from __future__ import annotations

import pathlib
import subprocess

import pytest


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
    assert "'unsupported.com' is not a supported platform." in result.stderr
    assert "Supported domains:" in result.stderr
    assert result.stdout == ""
