"""Unit tests for BoomiExtractor."""

from __future__ import annotations

import pytest
from bs4 import BeautifulSoup
from bs4.element import Tag

from mdfetch.exceptions import EmptyContentError, UnsupportedContentTypeError
from mdfetch.providers.boomi import BoomiExtractor

# Mirrors the real Boomi layout: the <h1> title sits in the page hero (outside the
# body), the article body is div.post-content > section.wysiwyg-section, and a
# div.blog-nav (prev/next links) is the only chrome inside the body container.
ARTICLE_HTML = """
<html><body>
  <section class="post-detail-hero landing-hero bg-dark">
    <div class="container"><div class="row"><div class="cell-lg-6 col-left">
      <div class="lh-left p-lg"><h1>Test Article Title</h1></div>
    </div></div></div>
  </section>
  <div class="cell-lg-7 post-content">
    <section class="wysiwyg-section bullet-styled">
      <div class="ws-container">
        <p>First paragraph with a <a href="https://example.com">link</a>.</p>
        <h2>Section Heading</h2>
        <ul><li>Item one</li><li>Item two</li></ul>
        <blockquote>A notable quote.</blockquote>
        <img src="https://example.com/inline.png" alt="An inline image"/>
      </div>
    </section>
    <div class="blog-nav">
      <a href="/blog/prev/">Previous Some Other Post</a>
      <a href="/blog/next/">Next Yet Another Post</a>
    </div>
  </div>
</body></html>
"""

# The blog index has a wysiwyg-section but NO post-content — this is the
# discriminator that distinguishes an article from a listing/non-article page.
NO_ARTICLE_HTML = """
<html><body>
  <section class="wysiwyg-section bullet-styled">
    <div class="ws-container"><p>Blog index intro, not an article body.</p></div>
  </section>
</body></html>
"""

EMPTY_BODY_HTML = """
<html><body>
  <div class="cell-lg-7 post-content">

  </div>
</body></html>
"""


@pytest.fixture
def extractor() -> BoomiExtractor:
    return BoomiExtractor()


class TestRouting:
    def test_routes_boomi_com(self) -> None:
        from mdfetch.router import route

        provider = route("https://boomi.com/blog/some-article-slug/")
        assert isinstance(provider, BoomiExtractor)


class TestCleanHtml:
    def test_clean_html_returns_post_content_div(self, extractor: BoomiExtractor) -> None:
        soup = BeautifulSoup(ARTICLE_HTML, "lxml")
        result = extractor.clean_html(soup)
        assert isinstance(result, Tag)
        assert "post-content" in result.get("class", [])

    def test_clean_html_prepends_title(self, extractor: BoomiExtractor) -> None:
        soup = BeautifulSoup(ARTICLE_HTML, "lxml")
        result = extractor.clean_html(soup)
        first_child = next((c for c in result.children if isinstance(c, Tag)), None)
        assert first_child is not None
        assert first_child.name == "h1"
        assert "Test Article Title" in first_child.get_text()

    def test_clean_html_strips_blog_nav(self, extractor: BoomiExtractor) -> None:
        soup = BeautifulSoup(ARTICLE_HTML, "lxml")
        result = extractor.clean_html(soup)
        assert result.find("div", class_="blog-nav") is None

    def test_clean_html_preserves_body_image(self, extractor: BoomiExtractor) -> None:
        soup = BeautifulSoup(ARTICLE_HTML, "lxml")
        result = extractor.clean_html(soup)
        img = result.find("img")
        assert isinstance(img, Tag)
        assert img.get("src") == "https://example.com/inline.png"

    def test_clean_html_raises_on_no_post_content(self, extractor: BoomiExtractor) -> None:
        soup = BeautifulSoup(NO_ARTICLE_HTML, "lxml")
        with pytest.raises(UnsupportedContentTypeError):
            extractor.clean_html(soup)


class TestConvertToMarkdown:
    def test_convert_to_markdown_starts_with_title(self, extractor: BoomiExtractor) -> None:
        soup = BeautifulSoup(ARTICLE_HTML, "lxml")
        tag = extractor.clean_html(soup)
        md = extractor.convert_to_markdown(tag)
        assert md.startswith("# Test Article Title")

    def test_convert_to_markdown_no_triple_blank_lines(self, extractor: BoomiExtractor) -> None:
        soup = BeautifulSoup(ARTICLE_HTML, "lxml")
        tag = extractor.clean_html(soup)
        md = extractor.convert_to_markdown(tag)
        assert "\n\n\n" not in md

    def test_convert_to_markdown_preserves_structure(self, extractor: BoomiExtractor) -> None:
        soup = BeautifulSoup(ARTICLE_HTML, "lxml")
        tag = extractor.clean_html(soup)
        md = extractor.convert_to_markdown(tag)
        assert "[link](https://example.com)" in md
        assert "## Section Heading" in md
        assert "Item one" in md
        assert "> A notable quote." in md

    def test_convert_to_markdown_excludes_blog_nav(self, extractor: BoomiExtractor) -> None:
        soup = BeautifulSoup(ARTICLE_HTML, "lxml")
        tag = extractor.clean_html(soup)
        md = extractor.convert_to_markdown(tag)
        assert "Previous" not in md
        assert "Next" not in md

    def test_convert_to_markdown_raises_on_empty_body(self, extractor: BoomiExtractor) -> None:
        soup = BeautifulSoup(EMPTY_BODY_HTML, "lxml")
        tag = extractor.clean_html(soup)
        with pytest.raises(EmptyContentError):
            extractor.convert_to_markdown(tag)
