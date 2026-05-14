"""Unit tests for DevToExtractor."""

from __future__ import annotations

import re

import pytest
from bs4 import BeautifulSoup

from mdfetch.exceptions import EmptyContentError, UnsupportedContentTypeError
from mdfetch.providers.devto import DevToExtractor


@pytest.fixture()
def extractor() -> DevToExtractor:
    return DevToExtractor()


@pytest.fixture()
def article_html() -> str:
    return """
    <html>
    <body>
        <header class="crayons-article__header" id="main-title">
            <a class="crayons-article__cover" href="https://example.com/cover-link">
                <img alt="Cover image for Test Article"
                     class="crayons-article__cover__image"
                     src="https://media.dev.to/cover.png"
                     width="1000" height="420"/>
            </a>
            <div class="crayons-article__header__meta">
                <h1 class="fs-3xl fw-bold">Test Article Title</h1>
                <p>Author info — should be stripped</p>
            </div>
        </header>
        <div class="crayons-article__main">
            <div id="article-body" class="crayons-article__body text-styles spec__body"
                 data-article-id="12345">
                <h2>
                    <a href="#section" name="section"></a>
                    A Section Heading
                </h2>
                <p>First paragraph of the article.</p>
                <ul>
                    <li>Item one</li>
                    <li>Item two</li>
                </ul>
                <pre><code>def hello(): pass</code></pre>
                <p>
                    <img alt="inline diagram" src="https://media.dev.to/inline.png"/>
                </p>
            </div>
        </div>
    </body>
    </html>
    """


@pytest.fixture()
def profile_html() -> str:
    """Simulates a dev.to author profile page — no article body element."""
    return """
    <html>
    <body>
        <div class="profile-header">
            <h1>Stanislav Deviatov</h1>
            <p>Profile page — no article body here.</p>
        </div>
    </body>
    </html>
    """


@pytest.fixture()
def tag_listing_html() -> str:
    """Simulates a dev.to tag listing page (https://dev.to/t/kafka) — no article body element."""
    return """
    <html>
    <body>
        <div class="tag-header">
            <h1>#kafka</h1>
            <p>Browse stories tagged kafka.</p>
        </div>
    </body>
    </html>
    """


@pytest.fixture()
def empty_article_html() -> str:
    return """
    <html>
    <body>
        <div id="article-body" class="crayons-article__body">
        </div>
    </body>
    </html>
    """


@pytest.fixture()
def iframe_article_html() -> str:
    return """
    <html>
    <body>
        <div id="article-body" class="crayons-article__body">
            <p>Some text before embed.</p>
            <iframe src="https://gist.github.com/user/abc123"></iframe>
            <p>Some text after embed.</p>
        </div>
    </body>
    </html>
    """


@pytest.fixture()
def liquid_tag_article_html() -> str:
    return """
    <html>
    <body>
        <div id="article-body" class="crayons-article__body">
            <p>Some text before embed.</p>
            <div class="ltag__github-readme" data-url="https://github.com/user/repo"></div>
            <p>Some text after embed.</p>
        </div>
    </body>
    </html>
    """


class TestCleanHtml:
    def test_preserves_title(self, extractor: DevToExtractor, article_html: str) -> None:
        soup = BeautifulSoup(article_html, "lxml")
        cleaned = extractor.clean_html(soup)
        assert cleaned.find("h1") is not None
        assert "Test Article Title" in cleaned.get_text()

    def test_preserves_cover_image(self, extractor: DevToExtractor, article_html: str) -> None:
        soup = BeautifulSoup(article_html, "lxml")
        cleaned = extractor.clean_html(soup)
        cover = cleaned.find("img", class_="crayons-article__cover__image")
        assert cover is not None
        assert "cover.png" in str(cover.get("src", ""))

    def test_preserves_heading(self, extractor: DevToExtractor, article_html: str) -> None:
        soup = BeautifulSoup(article_html, "lxml")
        cleaned = extractor.clean_html(soup)
        assert cleaned.find("h2") is not None

    def test_preserves_body_image(self, extractor: DevToExtractor, article_html: str) -> None:
        soup = BeautifulSoup(article_html, "lxml")
        cleaned = extractor.clean_html(soup)
        imgs = cleaned.find_all("img")
        src_values = [str(img.get("src", "")) for img in imgs]
        assert any("inline.png" in src for src in src_values)

    def test_strips_empty_anchor_links(self, extractor: DevToExtractor, article_html: str) -> None:
        soup = BeautifulSoup(article_html, "lxml")
        cleaned = extractor.clean_html(soup)
        # No empty anchor-name links should remain
        empty_anchors = [
            a for a in cleaned.find_all("a", attrs={"name": True}) if not a.get_text(strip=True)
        ]
        assert len(empty_anchors) == 0

    def test_raises_when_no_article_body(
        self, extractor: DevToExtractor, profile_html: str
    ) -> None:
        soup = BeautifulSoup(profile_html, "lxml")
        with pytest.raises(UnsupportedContentTypeError):
            extractor.clean_html(soup)

    def test_raises_for_tag_listing_page(
        self, extractor: DevToExtractor, tag_listing_html: str
    ) -> None:
        soup = BeautifulSoup(tag_listing_html, "lxml")
        with pytest.raises(UnsupportedContentTypeError):
            extractor.clean_html(soup)

    def test_iframe_replaced_with_link(
        self, extractor: DevToExtractor, iframe_article_html: str
    ) -> None:
        soup = BeautifulSoup(iframe_article_html, "lxml")
        cleaned = extractor.clean_html(soup)
        assert cleaned.find("iframe") is None
        link = cleaned.find("a", href="https://gist.github.com/user/abc123")
        assert link is not None

    def test_liquid_tag_replaced_with_link(
        self, extractor: DevToExtractor, liquid_tag_article_html: str
    ) -> None:
        soup = BeautifulSoup(liquid_tag_article_html, "lxml")
        cleaned = extractor.clean_html(soup)
        ltag_divs = cleaned.find_all(class_=re.compile(r"ltag", re.IGNORECASE))
        assert len(ltag_divs) == 0
        link = cleaned.find("a", href="https://github.com/user/repo")
        assert link is not None


class TestConvertToMarkdown:
    def test_produces_h1_heading(self, extractor: DevToExtractor, article_html: str) -> None:
        soup = BeautifulSoup(article_html, "lxml")
        cleaned = extractor.clean_html(soup)
        md = extractor.convert_to_markdown(cleaned)
        assert "# Test Article Title" in md

    def test_produces_h2_heading(self, extractor: DevToExtractor, article_html: str) -> None:
        soup = BeautifulSoup(article_html, "lxml")
        cleaned = extractor.clean_html(soup)
        md = extractor.convert_to_markdown(cleaned)
        assert "## " in md

    def test_produces_code_block(self, extractor: DevToExtractor, article_html: str) -> None:
        soup = BeautifulSoup(article_html, "lxml")
        cleaned = extractor.clean_html(soup)
        md = extractor.convert_to_markdown(cleaned)
        assert "```" in md

    def test_produces_list_items(self, extractor: DevToExtractor, article_html: str) -> None:
        soup = BeautifulSoup(article_html, "lxml")
        cleaned = extractor.clean_html(soup)
        md = extractor.convert_to_markdown(cleaned)
        assert "- " in md or "* " in md

    def test_preserves_cover_image_as_markdown(
        self, extractor: DevToExtractor, article_html: str
    ) -> None:
        soup = BeautifulSoup(article_html, "lxml")
        cleaned = extractor.clean_html(soup)
        md = extractor.convert_to_markdown(cleaned)
        assert "![" in md
        assert "cover.png" in md

    def test_preserves_body_image_as_markdown(
        self, extractor: DevToExtractor, article_html: str
    ) -> None:
        soup = BeautifulSoup(article_html, "lxml")
        cleaned = extractor.clean_html(soup)
        md = extractor.convert_to_markdown(cleaned)
        assert "inline.png" in md

    def test_no_raw_html_tags(self, extractor: DevToExtractor, article_html: str) -> None:
        soup = BeautifulSoup(article_html, "lxml")
        cleaned = extractor.clean_html(soup)
        md = extractor.convert_to_markdown(cleaned)
        # Exclude valid Markdown autolinks (<https://...>)
        assert not re.search(r"<(?!https?://|ftp://)[a-zA-Z][^>]*>", md)

    def test_raises_on_empty_content(
        self, extractor: DevToExtractor, empty_article_html: str
    ) -> None:
        soup = BeautifulSoup(empty_article_html, "lxml")
        cleaned = extractor.clean_html(soup)
        with pytest.raises(EmptyContentError):
            extractor.convert_to_markdown(cleaned)
