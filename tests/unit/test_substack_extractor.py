"""Unit tests for SubstackExtractor."""

from __future__ import annotations

import pytest
from bs4 import BeautifulSoup

from mdfetch.exceptions import EmptyContentError, UnsupportedContentTypeError
from mdfetch.providers.substack import SubstackExtractor
from mdfetch.router import route


@pytest.fixture()
def extractor() -> SubstackExtractor:
    return SubstackExtractor()


# ---------------------------------------------------------------------------
# Routing (T005)
# ---------------------------------------------------------------------------


def test_route_subdomain_returns_substack_extractor() -> None:
    assert isinstance(route("https://getkafkanated.substack.com/p/x"), SubstackExtractor)


def test_route_root_domain_returns_substack_extractor() -> None:
    assert isinstance(route("https://substack.com/"), SubstackExtractor)


def test_no_retry_status_codes_is_empty_frozenset() -> None:
    """FR-010: HTTP 429 must be retried, not raised immediately."""
    assert SubstackExtractor._no_retry_status_codes == frozenset()


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

ARTICLE_HTML = """
<html><body>
  <article class="newsletter-post post">
    <div class="post-header">
      <h1 class="post-title published">Test Article Title</h1>
      <h3 class="subtitle">Test subtitle text</h3>
    </div>
    <div class="available-content">
      <div class="body markup">
        <p>First paragraph of the article.</p>
        <p>Second paragraph with a <a href="https://example.com">link</a>.</p>
        <ul><li>Item one</li><li>Item two</li></ul>
        <div class="subscription-widget-wrap">
          <div data-component-name="SubscribeWidget" class="subscribe-widget">
            Subscribe now!
          </div>
        </div>
        <p>Third paragraph after the CTA.</p>
        <img src="https://example.com/image.png" alt="A diagram"/>
      </div>
    </div>
  </article>
</body></html>
"""

PAYWALLED_HTML = """
<html><body>
  <article class="newsletter-post post">
    <div class="post-header">
      <h1 class="post-title published">Paywalled Article</h1>
    </div>
    <div class="available-content">
      <div class="body markup">
        <p>Free preview paragraph one.</p>
        <p>Free preview paragraph two.</p>
        <div class="subscription-widget-wrap">
          Subscribe to read the full post. This post is for paid subscribers.
        </div>
      </div>
    </div>
  </article>
</body></html>
"""

NO_ARTICLE_HTML = """
<html><body>
  <div class="publication-homepage">
    <h1>My Newsletter</h1>
    <p>Welcome to the homepage.</p>
  </div>
</body></html>
"""

EMPTY_BODY_HTML = """
<html><body>
  <div class="available-content">
    <div class="body markup">   </div>
  </div>
</body></html>
"""

IFRAME_EMBED_HTML = """
<html><body>
  <div class="post-header">
    <h1 class="post-title published">Embed Test</h1>
  </div>
  <div class="available-content">
    <div class="body markup">
      <p>Before embed.</p>
      <iframe src="https://www.youtube.com/embed/abc123"></iframe>
      <p>After embed.</p>
    </div>
  </div>
</body></html>
"""

COMPONENT_EMBED_HTML = """
<html><body>
  <div class="post-header">
    <h1 class="post-title published">Component Embed Test</h1>
  </div>
  <div class="available-content">
    <div class="body markup">
      <p>Before component embed.</p>
      <div data-component-name="EmbedPost" data-url="https://other.substack.com/p/some-post">
        Linked post preview content
      </div>
      <p>After component embed.</p>
    </div>
  </div>
</body></html>
"""


# ---------------------------------------------------------------------------
# clean_html — happy path (T009)
# ---------------------------------------------------------------------------


def test_clean_html_returns_body_markup_tag(extractor: SubstackExtractor) -> None:
    soup = BeautifulSoup(ARTICLE_HTML, "lxml")
    result = extractor.clean_html(soup)
    assert isinstance(result, __import__("bs4").element.Tag)
    assert "body" in (result.get("class") or [])
    assert "markup" in (result.get("class") or [])


def test_clean_html_strips_subscription_widget(extractor: SubstackExtractor) -> None:
    soup = BeautifulSoup(ARTICLE_HTML, "lxml")
    result = extractor.clean_html(soup)
    assert result.find("div", class_="subscription-widget-wrap") is None


def test_clean_html_prepends_title(extractor: SubstackExtractor) -> None:
    soup = BeautifulSoup(ARTICLE_HTML, "lxml")
    result = extractor.clean_html(soup)
    children = [c for c in result.children if hasattr(c, "name") and c.name]
    assert children[0].name == "h1"
    assert "Test Article Title" in children[0].get_text()


def test_clean_html_prepends_subtitle_after_title(extractor: SubstackExtractor) -> None:
    soup = BeautifulSoup(ARTICLE_HTML, "lxml")
    result = extractor.clean_html(soup)
    children = [c for c in result.children if hasattr(c, "name") and c.name]
    assert children[1].name == "h3"
    assert "Test subtitle text" in children[1].get_text()


def test_clean_html_preserves_prose_after_stripping(extractor: SubstackExtractor) -> None:
    soup = BeautifulSoup(ARTICLE_HTML, "lxml")
    result = extractor.clean_html(soup)
    text = result.get_text()
    assert "Third paragraph after the CTA" in text
    assert "Subscribe now" not in text


def test_clean_html_converts_iframe_to_anchor(extractor: SubstackExtractor) -> None:
    soup = BeautifulSoup(IFRAME_EMBED_HTML, "lxml")
    result = extractor.clean_html(soup)
    assert result.find("iframe") is None
    link = result.find("a", href="https://www.youtube.com/embed/abc123")
    assert link is not None


def test_clean_html_converts_component_embed_to_anchor(extractor: SubstackExtractor) -> None:
    """FR-011: non-safe data-component-name divs are replaced with anchor links."""
    soup = BeautifulSoup(COMPONENT_EMBED_HTML, "lxml")
    result = extractor.clean_html(soup)
    assert result.find(attrs={"data-component-name": "EmbedPost"}) is None
    link = result.find("a", href="https://other.substack.com/p/some-post")
    assert link is not None


def test_convert_to_markdown_renders_component_embed_as_link(extractor: SubstackExtractor) -> None:
    """FR-011: component embed URL appears as a Markdown link in the output."""
    soup = BeautifulSoup(COMPONENT_EMBED_HTML, "lxml")
    tag = extractor.clean_html(soup)
    md = extractor.convert_to_markdown(tag)
    assert "https://other.substack.com/p/some-post" in md


# ---------------------------------------------------------------------------
# convert_to_markdown (T010)
# ---------------------------------------------------------------------------


def test_convert_to_markdown_starts_with_title(extractor: SubstackExtractor) -> None:
    soup = BeautifulSoup(ARTICLE_HTML, "lxml")
    tag = extractor.clean_html(soup)
    md = extractor.convert_to_markdown(tag)
    assert md.startswith("# Test Article Title")


def test_convert_to_markdown_no_triple_blank_lines(extractor: SubstackExtractor) -> None:
    soup = BeautifulSoup(ARTICLE_HTML, "lxml")
    tag = extractor.clean_html(soup)
    md = extractor.convert_to_markdown(tag)
    assert "\n\n\n" not in md


def test_convert_to_markdown_renders_images(extractor: SubstackExtractor) -> None:
    soup = BeautifulSoup(ARTICLE_HTML, "lxml")
    tag = extractor.clean_html(soup)
    md = extractor.convert_to_markdown(tag)
    assert "![A diagram](https://example.com/image.png)" in md


def test_convert_to_markdown_preserves_links(extractor: SubstackExtractor) -> None:
    soup = BeautifulSoup(ARTICLE_HTML, "lxml")
    tag = extractor.clean_html(soup)
    md = extractor.convert_to_markdown(tag)
    assert "[link](https://example.com)" in md


# ---------------------------------------------------------------------------
# US2 — Paywalled post (T012)
# ---------------------------------------------------------------------------


def test_paywalled_post_returns_nonempty_markdown(extractor: SubstackExtractor) -> None:
    soup = BeautifulSoup(PAYWALLED_HTML, "lxml")
    tag = extractor.clean_html(soup)
    md = extractor.convert_to_markdown(tag)
    assert md.strip() != ""


def test_paywalled_post_strips_subscribe_cta(extractor: SubstackExtractor) -> None:
    soup = BeautifulSoup(PAYWALLED_HTML, "lxml")
    tag = extractor.clean_html(soup)
    md = extractor.convert_to_markdown(tag)
    assert "Subscribe" not in md
    assert "paid subscribers" not in md


def test_paywalled_post_contains_free_preview(extractor: SubstackExtractor) -> None:
    soup = BeautifulSoup(PAYWALLED_HTML, "lxml")
    tag = extractor.clean_html(soup)
    md = extractor.convert_to_markdown(tag)
    assert "Free preview paragraph one" in md
    assert "Free preview paragraph two" in md


# ---------------------------------------------------------------------------
# US3 — Non-article pages (T014, T015)
# ---------------------------------------------------------------------------


def test_clean_html_raises_on_no_article_body(extractor: SubstackExtractor) -> None:
    soup = BeautifulSoup(NO_ARTICLE_HTML, "lxml")
    with pytest.raises(UnsupportedContentTypeError):
        extractor.clean_html(soup)


def test_convert_to_markdown_raises_on_empty_body(extractor: SubstackExtractor) -> None:
    soup = BeautifulSoup(EMPTY_BODY_HTML, "lxml")
    tag = extractor.clean_html(soup)
    with pytest.raises(EmptyContentError):
        extractor.convert_to_markdown(tag)
