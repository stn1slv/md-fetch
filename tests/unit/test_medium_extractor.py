"""Unit tests for MediumExtractor."""

from __future__ import annotations

import re

import pytest
from bs4 import BeautifulSoup

from mdfetch.exceptions import EmptyContentError, UnsupportedContentTypeError
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
