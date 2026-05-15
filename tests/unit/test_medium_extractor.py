"""Unit tests for MediumExtractor."""

from __future__ import annotations

import re
from unittest.mock import patch

import pytest
from bs4 import BeautifulSoup

from mdfetch.exceptions import EmptyContentError, HTTPStatusError, UnsupportedContentTypeError
from mdfetch.providers.medium import MediumExtractor


@pytest.fixture()
def extractor() -> MediumExtractor:
    return MediumExtractor()


@pytest.fixture()
def article_html() -> str:
    return """
    <html>
    <body>
        <nav>Navigation menu</nav>
        <article>
            <h1>Test Article Title</h1>
            <p>First paragraph of the article.</p>
            <h2>A Section Heading</h2>
            <ul>
                <li>Item one</li>
                <li>Item two</li>
            </ul>
            <pre><code>def hello(): pass</code></pre>
            <button aria-label="clap for this story">Clap</button>
            <div data-testid="post-sidebar">Sidebar</div>
            <div data-testid="share-button">Share</div>
            <section class="author-bio">Author bio section</section>
            <div data-testid="post-footer">Comments prompt</div>
        </article>
    </body>
    </html>
    """


@pytest.fixture()
def no_article_html() -> str:
    return """
    <html>
    <body>
        <div class="tag-page">
            <h1>Tag: Python</h1>
            <p>Browse stories tagged Python.</p>
        </div>
    </body>
    </html>
    """


@pytest.fixture()
def empty_article_html() -> str:
    return """
    <html>
    <body>
        <article>
        </article>
    </body>
    </html>
    """


class TestCleanHtml:
    def test_removes_nav(self, extractor: MediumExtractor, article_html: str) -> None:
        soup = BeautifulSoup(article_html, "lxml")
        cleaned = extractor.clean_html(soup)
        assert cleaned.find("nav") is None

    def test_removes_clap_button(self, extractor: MediumExtractor, article_html: str) -> None:
        soup = BeautifulSoup(article_html, "lxml")
        cleaned = extractor.clean_html(soup)
        buttons = cleaned.find_all("button")
        clap_buttons = [b for b in buttons if "clap" in (b.get("aria-label") or "").lower()]
        assert len(clap_buttons) == 0

    def test_removes_post_sidebar(self, extractor: MediumExtractor, article_html: str) -> None:
        soup = BeautifulSoup(article_html, "lxml")
        cleaned = extractor.clean_html(soup)
        assert cleaned.find(attrs={"data-testid": "post-sidebar"}) is None

    def test_removes_share_elements(self, extractor: MediumExtractor, article_html: str) -> None:
        soup = BeautifulSoup(article_html, "lxml")
        cleaned = extractor.clean_html(soup)
        share_elements = cleaned.find_all(attrs={"data-testid": re.compile("share")})
        assert len(share_elements) == 0

    def test_removes_post_footer(self, extractor: MediumExtractor, article_html: str) -> None:
        soup = BeautifulSoup(article_html, "lxml")
        cleaned = extractor.clean_html(soup)
        assert cleaned.find(attrs={"data-testid": "post-footer"}) is None

    def test_preserves_article_content(self, extractor: MediumExtractor, article_html: str) -> None:
        soup = BeautifulSoup(article_html, "lxml")
        cleaned = extractor.clean_html(soup)
        assert cleaned.find("h1") is not None
        assert cleaned.find("p") is not None

    def test_raises_when_no_article(self, extractor: MediumExtractor, no_article_html: str) -> None:
        soup = BeautifulSoup(no_article_html, "lxml")
        with pytest.raises(UnsupportedContentTypeError):
            extractor.clean_html(soup)


class TestConvertToMarkdown:
    def test_produces_heading(self, extractor: MediumExtractor, article_html: str) -> None:
        soup = BeautifulSoup(article_html, "lxml")
        cleaned = extractor.clean_html(soup)
        md = extractor.convert_to_markdown(cleaned)
        assert "# " in md

    def test_produces_code_block(self, extractor: MediumExtractor, article_html: str) -> None:
        soup = BeautifulSoup(article_html, "lxml")
        cleaned = extractor.clean_html(soup)
        md = extractor.convert_to_markdown(cleaned)
        assert "```" in md

    def test_produces_list_items(self, extractor: MediumExtractor, article_html: str) -> None:
        soup = BeautifulSoup(article_html, "lxml")
        cleaned = extractor.clean_html(soup)
        md = extractor.convert_to_markdown(cleaned)
        assert "- " in md or "* " in md

    def test_no_raw_html_tags(self, extractor: MediumExtractor, article_html: str) -> None:
        soup = BeautifulSoup(article_html, "lxml")
        cleaned = extractor.clean_html(soup)
        md = extractor.convert_to_markdown(cleaned)
        # Exclude Markdown autolinks (<https://...>) which are valid output
        assert not re.search(r"<(?!https?://|ftp://)[a-zA-Z][^>]*>", md)

    def test_raises_on_empty_content(
        self, extractor: MediumExtractor, empty_article_html: str
    ) -> None:
        soup = BeautifulSoup(empty_article_html, "lxml")
        cleaned = extractor.clean_html(soup)
        with pytest.raises(EmptyContentError):
            extractor.convert_to_markdown(cleaned)


_FREEDIUM_ARTICLE_HTML = """
<html><body>
<div class="main-content">
    <h4>Section One</h4>
    <p>First paragraph of the article.</p>
    <h4>Section Two</h4>
    <p>Second paragraph with more content.</p>
    <pre><code>print("hello")</code></pre>
</div>
</body></html>
"""

_FREEDIUM_NO_CONTENT_HTML = """
<html><body>
<div class="header">No main-content div here</div>
</body></html>
"""


class TestParseFreedium:
    def test_returns_markdown_from_main_content(self, extractor: MediumExtractor) -> None:
        soup = BeautifulSoup(_FREEDIUM_ARTICLE_HTML, "lxml")
        md = extractor._parse_freedium(soup)
        assert "Section One" in md
        assert "First paragraph" in md

    def test_headings_remapped_to_h3(self, extractor: MediumExtractor) -> None:
        soup = BeautifulSoup(_FREEDIUM_ARTICLE_HTML, "lxml")
        md = extractor._parse_freedium(soup)
        assert "###" in md
        assert "####" not in md

    def test_raises_when_main_content_missing(self, extractor: MediumExtractor) -> None:
        soup = BeautifulSoup(_FREEDIUM_NO_CONTENT_HTML, "lxml")
        with pytest.raises(UnsupportedContentTypeError, match="main-content"):
            extractor._parse_freedium(soup)


def _do_fetch_router(url_map: dict[str, str | Exception]) -> object:
    """Return a _do_fetch side_effect that routes by URL substring match."""

    def _side_effect(url: str) -> str:
        for pattern, response in url_map.items():
            if pattern in url:
                if isinstance(response, Exception):
                    raise response
                return response
        raise HTTPStatusError(f"HTTP 404 fetching {url}", status_code=404, url=url)

    return _side_effect


class TestFreediumFallback:
    def test_403_triggers_freedium_fallback(self, extractor: MediumExtractor) -> None:
        original_url = "https://medium.com/some/article"
        router = _do_fetch_router({
            "freedium-mirror.cfd": _FREEDIUM_ARTICLE_HTML,
            "medium.com": HTTPStatusError("HTTP 403", status_code=403, url=original_url),
        })
        with patch.object(extractor, "_do_fetch", side_effect=router):
            result = extractor.extract(original_url, retries=1)

        assert "Section One" in result

    def test_403_freedium_url_construction(self, extractor: MediumExtractor) -> None:
        original_url = "https://stn1slv.medium.com/some-article-abc123"
        captured_urls: list[str] = []

        def capturing_router(url: str) -> str:
            captured_urls.append(url)
            if "freedium" in url:
                return _FREEDIUM_ARTICLE_HTML
            raise HTTPStatusError("HTTP 403", status_code=403, url=url)

        with patch.object(extractor, "_do_fetch", side_effect=capturing_router):
            extractor.extract(original_url, retries=1)

        assert any("freedium-mirror.cfd" in u for u in captured_urls)
        assert any(original_url in u for u in captured_urls)
        expected_freedium = f"https://freedium-mirror.cfd/{original_url}"
        assert expected_freedium in captured_urls

    def test_both_fail_raises_with_original_url(self, extractor: MediumExtractor) -> None:
        original_url = "https://medium.com/some/article"
        router = _do_fetch_router({
            "medium.com": HTTPStatusError("HTTP 403", status_code=403, url=original_url),
            "freedium-mirror.cfd": HTTPStatusError("HTTP 503", status_code=503, url=None),
        })
        with patch.object(extractor, "_do_fetch", side_effect=router):
            with pytest.raises(HTTPStatusError) as exc_info:
                extractor.extract(original_url, retries=1)

        assert exc_info.value.url == original_url

    def test_non_fallback_status_propagates_without_freedium(
        self, extractor: MediumExtractor
    ) -> None:
        call_count = 0

        def router(url: str) -> str:
            nonlocal call_count
            call_count += 1
            raise HTTPStatusError("HTTP 404", status_code=404, url=url)

        with patch.object(extractor, "_do_fetch", side_effect=router):
            with pytest.raises(HTTPStatusError) as exc_info:
                extractor.extract("https://medium.com/missing", retries=1)

        assert exc_info.value.status_code == 404
        assert call_count == 1  # no Freedium attempt


class TestRateLimitFallback:
    def test_429_triggers_freedium_fallback(self, extractor: MediumExtractor) -> None:
        router = _do_fetch_router({
            "freedium-mirror.cfd": _FREEDIUM_ARTICLE_HTML,
            "medium.com": HTTPStatusError("HTTP 429", status_code=429, url=None),
        })
        with patch.object(extractor, "_do_fetch", side_effect=router):
            result = extractor.extract("https://medium.com/article", retries=1)

        assert "Section One" in result

    def test_429_no_sleep_before_freedium(self, extractor: MediumExtractor) -> None:
        router = _do_fetch_router({
            "freedium-mirror.cfd": _FREEDIUM_ARTICLE_HTML,
            "medium.com": HTTPStatusError("HTTP 429", status_code=429, url=None),
        })
        with patch.object(extractor, "_do_fetch", side_effect=router):
            with patch("mdfetch.base.time.sleep") as mock_sleep:
                extractor.extract("https://medium.com/article", retries=3)

        mock_sleep.assert_not_called()


class TestNoFallbackOnSuccess:
    def test_successful_primary_fetch_makes_one_request(
        self, extractor: MediumExtractor
    ) -> None:
        article_html = """
        <html><body><article>
            <h1>Test</h1><p>Content here.</p>
        </article></body></html>
        """
        call_count = 0

        def router(url: str) -> str:
            nonlocal call_count
            call_count += 1
            return article_html

        with patch.object(extractor, "_do_fetch", side_effect=router):
            extractor.extract("https://medium.com/article", retries=1)

        assert call_count == 1  # only the medium.com request, no Freedium
