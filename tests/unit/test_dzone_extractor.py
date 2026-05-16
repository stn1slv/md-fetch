"""Unit tests for DZoneExtractor."""

from __future__ import annotations

import pytest
from bs4 import BeautifulSoup
from bs4.element import Tag

from mdfetch.exceptions import EmptyContentError, UnsupportedContentTypeError
from mdfetch.providers.dzone import DZoneExtractor

ARTICLE_HTML = """
<html><body>
  <div class="title">
    <div class="header-title">
      <h1 class="article-title">Test Article Title</h1>
    </div>
  </div>
  <div class="content-html">
    <p>First paragraph with a <a href="https://example.com">link</a>.</p>
    <h2>Section Heading</h2>
    <ul><li>Item one</li><li>Item two</li></ul>
    <img src="https://example.com/image.png" alt="An image"/>
  </div>
</body></html>
"""

ARTICLE_WITH_CODE_HTML = """
<html><body>
  <h1 class="article-title">Code Article</h1>
  <div class="content-html">
    <p>Intro paragraph.</p>
    <div class="codeMirror-wrapper">
      <div class="codeHeader">
        <div class="nameLanguage">Java</div>
        <i class="cm-remove"></i>
      </div>
      <div class="codeMirror-code--wrapper">
        <pre><code>public class Hello {}</code></pre>
      </div>
    </div>
  </div>
</body></html>
"""

ARTICLE_WITH_PLAIN_TEXT_CODE_HTML = """
<html><body>
  <h1 class="article-title">Plain Text Code Article</h1>
  <div class="content-html">
    <p>Intro paragraph.</p>
    <div class="codeMirror-wrapper">
      <div class="codeHeader">
        <div class="nameLanguage">Plain Text</div>
        <i class="cm-remove"></i>
      </div>
      <div class="codeMirror-code--wrapper">
        <pre><code>some plain text content</code></pre>
      </div>
    </div>
  </div>
</body></html>
"""

NO_ARTICLE_HTML = """
<html><body>
  <div class="refcard-header">
    <h1>Some Refcard Title</h1>
  </div>
  <div class="refcard-body">
    <p>Refcard content, no article body.</p>
  </div>
</body></html>
"""

EMPTY_BODY_HTML = """
<html><body>
  <div class="content-html">

  </div>
</body></html>
"""


@pytest.fixture
def extractor() -> DZoneExtractor:
    return DZoneExtractor()


class TestCleanHtml:
    def test_clean_html_returns_content_html_div(self, extractor: DZoneExtractor) -> None:
        soup = BeautifulSoup(ARTICLE_HTML, "lxml")
        result = extractor.clean_html(soup)
        assert isinstance(result, Tag)
        assert "content-html" in result.get("class", [])

    def test_clean_html_prepends_title(self, extractor: DZoneExtractor) -> None:
        soup = BeautifulSoup(ARTICLE_HTML, "lxml")
        result = extractor.clean_html(soup)
        first_child = next((c for c in result.children if isinstance(c, Tag)), None)
        assert first_child is not None
        assert first_child.name == "h1"
        assert "article-title" in first_child.get("class", [])
        assert "Test Article Title" in first_child.get_text()

    def test_clean_html_raises_on_no_article_body(self, extractor: DZoneExtractor) -> None:
        soup = BeautifulSoup(NO_ARTICLE_HTML, "lxml")
        with pytest.raises(UnsupportedContentTypeError):
            extractor.clean_html(soup)

    def test_clean_html_code_block_java_language(self, extractor: DZoneExtractor) -> None:
        soup = BeautifulSoup(ARTICLE_WITH_CODE_HTML, "lxml")
        result = extractor.clean_html(soup)
        code_el = result.find("code")
        assert isinstance(code_el, Tag)
        assert "language-java" in code_el.get("class", [])

    def test_clean_html_code_block_plain_text_no_language(self, extractor: DZoneExtractor) -> None:
        soup = BeautifulSoup(ARTICLE_WITH_PLAIN_TEXT_CODE_HTML, "lxml")
        result = extractor.clean_html(soup)
        code_el = result.find("code")
        assert isinstance(code_el, Tag)
        classes = code_el.get("class", [])
        assert not any(c.startswith("language-") for c in classes)

    def test_clean_html_strips_code_header(self, extractor: DZoneExtractor) -> None:
        soup = BeautifulSoup(ARTICLE_WITH_CODE_HTML, "lxml")
        result = extractor.clean_html(soup)
        assert result.find("div", class_="codeHeader") is None


class TestConvertToMarkdown:
    def test_convert_to_markdown_starts_with_title(self, extractor: DZoneExtractor) -> None:
        soup = BeautifulSoup(ARTICLE_HTML, "lxml")
        tag = extractor.clean_html(soup)
        md = extractor.convert_to_markdown(tag)
        assert md.startswith("# Test Article Title")

    def test_convert_to_markdown_no_triple_blank_lines(self, extractor: DZoneExtractor) -> None:
        soup = BeautifulSoup(ARTICLE_HTML, "lxml")
        tag = extractor.clean_html(soup)
        md = extractor.convert_to_markdown(tag)
        assert "\n\n\n" not in md

    def test_convert_to_markdown_preserves_links(self, extractor: DZoneExtractor) -> None:
        soup = BeautifulSoup(ARTICLE_HTML, "lxml")
        tag = extractor.clean_html(soup)
        md = extractor.convert_to_markdown(tag)
        assert "[link](https://example.com)" in md

    def test_convert_to_markdown_raises_on_empty_body(self, extractor: DZoneExtractor) -> None:
        soup = BeautifulSoup(EMPTY_BODY_HTML, "lxml")
        tag = extractor.clean_html(soup)
        with pytest.raises(EmptyContentError):
            extractor.convert_to_markdown(tag)

    def test_convert_to_markdown_fenced_code_block_with_language(
        self, extractor: DZoneExtractor
    ) -> None:
        soup = BeautifulSoup(ARTICLE_WITH_CODE_HTML, "lxml")
        tag = extractor.clean_html(soup)
        md = extractor.convert_to_markdown(tag)
        assert "```java\n" in md
