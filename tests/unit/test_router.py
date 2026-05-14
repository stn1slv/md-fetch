"""Unit tests for URL validation and routing logic."""

from __future__ import annotations

import pytest

from mdfetch.exceptions import InvalidURLError, UnsupportedPlatformError
from mdfetch.router import route


class TestUrlValidation:
    def test_raises_for_plain_string(self) -> None:
        with pytest.raises(InvalidURLError):
            route("not-a-url")

    def test_raises_for_ftp_scheme(self) -> None:
        with pytest.raises(InvalidURLError):
            route("ftp://medium.com/article")

    def test_raises_for_empty_string(self) -> None:
        with pytest.raises(InvalidURLError):
            route("")

    def test_raises_for_no_netloc(self) -> None:
        with pytest.raises(InvalidURLError):
            route("https://")

    def test_raises_for_empty_hostname(self) -> None:
        # netloc is non-empty (":80") but hostname is None — must raise InvalidURLError
        with pytest.raises(InvalidURLError):
            route("https://:80/path")

    def test_raises_for_unsupported_domain(self) -> None:
        with pytest.raises(UnsupportedPlatformError):
            route("https://substack.com/some-post")

    def test_routes_medium_com(self) -> None:
        from mdfetch.providers.medium import MediumExtractor

        provider = route("https://medium.com/some-article")
        assert isinstance(provider, MediumExtractor)

    def test_routes_medium_com_subdomain(self) -> None:
        from mdfetch.providers.medium import MediumExtractor

        provider = route("https://username.medium.com/some-article")
        assert isinstance(provider, MediumExtractor)

    def test_routes_www_medium_com(self) -> None:
        from mdfetch.providers.medium import MediumExtractor

        provider = route("https://www.medium.com/some-article")
        assert isinstance(provider, MediumExtractor)

    def test_error_includes_url(self) -> None:
        bad_url = "not-a-url"
        with pytest.raises(InvalidURLError) as exc_info:
            route(bad_url)
        assert exc_info.value.url == bad_url or bad_url in exc_info.value.message

    def test_unsupported_error_includes_domain(self) -> None:
        with pytest.raises(UnsupportedPlatformError) as exc_info:
            route("https://substack.com/post")
        assert "substack.com" in exc_info.value.message
