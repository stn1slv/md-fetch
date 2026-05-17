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
            route("https://wordpress.com/some-post")

    def test_routes_dev_to(self) -> None:
        from mdfetch.providers.devto import DevToExtractor

        provider = route("https://dev.to/username/some-article")
        assert isinstance(provider, DevToExtractor)

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
            route("https://wordpress.com/post")
        assert "wordpress.com" in exc_info.value.message

    def test_routes_thenewstack_io(self) -> None:
        from mdfetch.providers.thenewstack import TheNewStackExtractor

        provider = route("https://thenewstack.io/some-article/")
        assert isinstance(provider, TheNewStackExtractor)

    def test_routes_dzone_com(self) -> None:
        from mdfetch.providers.dzone import DZoneExtractor

        provider = route("https://dzone.com/articles/some-article")
        assert isinstance(provider, DZoneExtractor)

    def test_rejects_subdomain_of_single_tenant_domain(self) -> None:
        # dev.to does not opt in to MATCH_SUBDOMAINS, so foo.dev.to must not
        # be routed to DevToExtractor — it should raise UnsupportedPlatformError.
        with pytest.raises(UnsupportedPlatformError):
            route("https://foo.dev.to/some-article")

    def test_rejects_subdomain_of_dzone(self) -> None:
        with pytest.raises(UnsupportedPlatformError):
            route("https://blog.dzone.com/articles/some-article")

    def test_rejects_subdomain_of_thenewstack(self) -> None:
        with pytest.raises(UnsupportedPlatformError):
            route("https://blog.thenewstack.io/some-article")

    def test_routes_substack_subdomain(self) -> None:
        from mdfetch.providers.substack import SubstackExtractor

        provider = route("https://newsletter.substack.com/p/post")
        assert isinstance(provider, SubstackExtractor)


class TestSupportedDomains:
    def test_returns_frozenset(self) -> None:
        from mdfetch.router import supported_domains

        result = supported_domains()
        assert isinstance(result, frozenset)

    def test_contains_known_domains(self) -> None:
        from mdfetch.router import supported_domains

        result = supported_domains()
        assert "medium.com" in result
        assert "dev.to" in result
        assert "substack.com" in result
        assert "thenewstack.io" in result
        assert "dzone.com" in result

    def test_does_not_contain_unregistered_domain(self) -> None:
        from mdfetch.router import supported_domains

        result = supported_domains()
        assert "wordpress.com" not in result

    def test_public_api_import(self) -> None:
        from mdfetch import supported_domains

        result = supported_domains()
        assert isinstance(result, frozenset)
        assert "medium.com" in result
