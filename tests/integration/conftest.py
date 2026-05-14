"""Shared fixtures for integration tests."""

from __future__ import annotations

import os

import pytest


@pytest.fixture
def http_retries() -> int:
    return int(os.environ.get("MDFETCH_RETRIES", "3"))


@pytest.fixture
def http_retry_delay() -> float:
    return float(os.environ.get("MDFETCH_RETRY_DELAY", "2.0"))
