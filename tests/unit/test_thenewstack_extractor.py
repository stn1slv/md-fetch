"""Unit tests for TheNewStackExtractor."""

from __future__ import annotations

import pytest
from bs4 import BeautifulSoup
from bs4.element import Tag

from mdfetch.exceptions import EmptyContentError, UnsupportedContentTypeError
from mdfetch.providers.thenewstack import TheNewStackExtractor


@pytest.fixture()
def extractor() -> TheNewStackExtractor:
    return TheNewStackExtractor()


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

ARTICLE_HTML = """
<html><body>
  <div id="tns-post-headline">
    <h1 class="title">Test Article Title</h1>
    <div class="post-excerpt">This is the deck subtitle text.</div>
  </div>
  <div id="tns-post-body-content">
    <p>First paragraph of the article.</p>
    <p>Second paragraph with a <a href="https://example.com">link text</a>.</p>
    <img src="https://example.com/image.png" alt="alt text"/>
    <div class="tns-sponsor-note">Sponsor note content.</div>
  </div>
</body></html>
"""

ARTICLE_NO_DECK_HTML = """
<html><body>
  <div id="tns-post-headline">
    <h1 class="title">Test Article Title</h1>
  </div>
  <div id="tns-post-body-content">
    <p>First paragraph of the article.</p>
  </div>
</body></html>
"""

SPONSOR_DISCLOSURE_HTML = """
<html><body>
  <div id="tns-post-headline">
    <h1 class="title">Sponsored Article Title</h1>
  </div>
  <div id="tns-post-body-content">
    <div class="sponsored-post-disclosure">Sponsored disclosure.</div>
    <div class="tns-sponsored-post-disclosure">TNS sponsored disclosure.</div>
    <div class="sponsor-disclosure">Generic disclosure.</div>
    <p>Article content.</p>
  </div>
</body></html>
"""

IFRAME_EMBED_HTML = """
<html><body>
  <div id="tns-post-headline">
    <h1 class="title">Embed Article</h1>
  </div>
  <div id="tns-post-body-content">
    <p>Before embed.</p>
    <iframe src="https://www.youtube.com/embed/abc"></iframe>
    <p>After embed.</p>
  </div>
</body></html>
"""

EMPTY_BODY_HTML = """
<html><body>
  <div id="tns-post-body-content">   </div>
</body></html>
"""

NO_ARTICLE_HTML = """
<html><body>
  <div class="publication-homepage">
    <h1>The New Stack</h1>
    <p>Welcome to the homepage.</p>
  </div>
</body></html>
"""


# ---------------------------------------------------------------------------
# clean_html — happy path (T010)
# ---------------------------------------------------------------------------


def test_clean_html_returns_body_content_div(extractor: TheNewStackExtractor) -> None:
    soup = BeautifulSoup(ARTICLE_HTML, "lxml")
    result = extractor.clean_html(soup)
    assert isinstance(result, Tag)
    assert result.get("id") == "tns-post-body-content"


def test_clean_html_prepends_title(extractor: TheNewStackExtractor) -> None:
    soup = BeautifulSoup(ARTICLE_HTML, "lxml")
    result = extractor.clean_html(soup)
    children = [c for c in result.children if hasattr(c, "name") and c.name]
    assert children[0].name == "h1"
    assert "Test Article Title" in children[0].get_text()


def test_clean_html_prepends_deck_as_paragraph(extractor: TheNewStackExtractor) -> None:
    soup = BeautifulSoup(ARTICLE_HTML, "lxml")
    result = extractor.clean_html(soup)
    children = [c for c in result.children if hasattr(c, "name") and c.name]
    assert children[1].name == "p"
    assert "This is the deck subtitle text." in children[1].get_text()


def test_clean_html_no_deck_when_absent(extractor: TheNewStackExtractor) -> None:
    soup = BeautifulSoup(ARTICLE_NO_DECK_HTML, "lxml")
    result = extractor.clean_html(soup)
    children = [c for c in result.children if hasattr(c, "name") and c.name]
    assert children[0].name == "h1"
    assert children[1].name == "p"
    assert "First paragraph" in children[1].get_text()


def test_clean_html_strips_sponsor_note(extractor: TheNewStackExtractor) -> None:
    soup = BeautifulSoup(ARTICLE_HTML, "lxml")
    result = extractor.clean_html(soup)
    assert result.find("div", class_="tns-sponsor-note") is None


def test_clean_html_strips_all_disclosure_variants(extractor: TheNewStackExtractor) -> None:
    soup = BeautifulSoup(SPONSOR_DISCLOSURE_HTML, "lxml")
    result = extractor.clean_html(soup)
    assert result.find("div", class_="sponsored-post-disclosure") is None
    assert result.find("div", class_="tns-sponsored-post-disclosure") is None
    assert result.find("div", class_="sponsor-disclosure") is None


def test_clean_html_converts_iframe_to_anchor(extractor: TheNewStackExtractor) -> None:
    soup = BeautifulSoup(IFRAME_EMBED_HTML, "lxml")
    result = extractor.clean_html(soup)
    assert result.find("iframe") is None
    link = result.find("a", href="https://www.youtube.com/embed/abc")
    assert link is not None


# ---------------------------------------------------------------------------
# convert_to_markdown (T011)
# ---------------------------------------------------------------------------


def test_convert_to_markdown_starts_with_title(extractor: TheNewStackExtractor) -> None:
    soup = BeautifulSoup(ARTICLE_HTML, "lxml")
    tag = extractor.clean_html(soup)
    md = extractor.convert_to_markdown(tag)
    assert md.startswith("# Test Article Title")


def test_convert_to_markdown_deck_paragraph_after_title(extractor: TheNewStackExtractor) -> None:
    soup = BeautifulSoup(ARTICLE_HTML, "lxml")
    tag = extractor.clean_html(soup)
    md = extractor.convert_to_markdown(tag)
    title_pos = md.index("# Test Article Title")
    deck_pos = md.index("This is the deck subtitle text.")
    assert deck_pos > title_pos


def test_convert_to_markdown_no_triple_blank_lines(extractor: TheNewStackExtractor) -> None:
    soup = BeautifulSoup(ARTICLE_HTML, "lxml")
    tag = extractor.clean_html(soup)
    md = extractor.convert_to_markdown(tag)
    assert "\n\n\n" not in md


def test_convert_to_markdown_renders_images(extractor: TheNewStackExtractor) -> None:
    soup = BeautifulSoup(ARTICLE_HTML, "lxml")
    tag = extractor.clean_html(soup)
    md = extractor.convert_to_markdown(tag)
    assert "![alt text](https://example.com/image.png)" in md


def test_convert_to_markdown_preserves_links(extractor: TheNewStackExtractor) -> None:
    soup = BeautifulSoup(ARTICLE_HTML, "lxml")
    tag = extractor.clean_html(soup)
    md = extractor.convert_to_markdown(tag)
    assert "[link text](https://example.com)" in md


# ---------------------------------------------------------------------------
# US2 — Non-article pages (T014, T015)
# ---------------------------------------------------------------------------


def test_clean_html_raises_on_no_article_body(extractor: TheNewStackExtractor) -> None:
    soup = BeautifulSoup(NO_ARTICLE_HTML, "lxml")
    with pytest.raises(UnsupportedContentTypeError):
        extractor.clean_html(soup)


def test_convert_to_markdown_raises_on_empty_body(extractor: TheNewStackExtractor) -> None:
    soup = BeautifulSoup(EMPTY_BODY_HTML, "lxml")
    tag = extractor.clean_html(soup)
    with pytest.raises(EmptyContentError):
        extractor.convert_to_markdown(tag)
