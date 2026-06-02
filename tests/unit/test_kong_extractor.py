"""Unit tests for KongExtractor."""

from __future__ import annotations

import pytest
from bs4 import BeautifulSoup
from bs4.element import Tag

from mdfetch.exceptions import EmptyContentError, UnsupportedContentTypeError
from mdfetch.providers.kong import KongExtractor

# Mirrors the real Kong (Next.js) layout: <main class="... type-article"> holds a
# breadcrumb nav (chrome), a hero <section> (category, publication date, "N min read",
# the <h1> title with a decorative agent-mode "#", and author divs), and a content
# <section> richest in .rich-text-block. The content section also embeds chrome blocks
# (.toc-wrap, .component.video, .component.more-on-this, .order-top, and a trailing
# non-intro .section-header-block CTA) plus a kept .section-header-block.intro TL;DR.
# Selectors pin to stable companion classes only — never the hashed CSS-module suffixes.
ARTICLE_HTML = """
<html><body>
<main class="Layout_main__abc some-slug type-article">
  <nav class="breadcrumbs"><a href="/blog">Blog</a> Test Article</nav>
  <section class="Section_section__x Article_heroSection__y">
    <div class="block hero">
      <span class="agent">[ Category ] ( /blog/category )</span>
      <span class="not-agent">Category</span>
      <div>May 26, 2026</div>
      <div class="not-agent">5 min read</div>
      <h1 class="Heading_heading__z heading"><span class="agent"># </span>Test Article Title</h1>
      <div class="body-xs">Jane Doe Staff Writer, Kong</div>
    </div>
  </section>
  <section class="Section_section__x Article_toc__w">
    <div class="toc-wrap sticky">
      <h3 class="head-xs">On this page</h3>
      <ul class="TableOfContents_tocList__t"><li><a href="#s">Section Heading</a></li></ul>
    </div>
    <div class="block section-header-block intro">
      <div class="richtext">
        <p><strong><span class="agent">**</span>TL;DR:<span class="agent">**</span></strong></p>
        <ul role="list"><li><span class="agent">- </span>A concise summary point.</li></ul>
      </div>
    </div>
    <div class="block rich-text-block">
      <h2>Section Heading</h2>
      <p>First paragraph with a <a href="https://example.com">link</a>.</p>
      <ul><li>Item one</li><li>Item two</li></ul>
      <p>Run <code>git status</code> to check.</p>
    </div>
    <div class="block component video">
      <p>This content contains a video which can not be displayed.</p>
    </div>
    <div class="block component image">
      <img src="https://example.com/inline.png" alt="An inline image"/>
    </div>
    <div class="block component pull-quote"><blockquote>A notable pull quote.</blockquote></div>
    <div class="block body-s order-top"><ul><li><a href="/blog/tag/x">Topic</a></li></ul></div>
    <div class="block component more-on-this">
      <h2>More on this topic</h2><a href="/blog/other">Other post</a>
    </div>
    <div class="block section-header-block">
      <h2>See Kong in action</h2><a href="/demo">Get a Demo</a>
    </div>
  </section>
  <section class="Section_section__x">
    <div class="block Article_authors__a">Jane Doe Staff Writer, Kong</div>
  </section>
  <section class="Section_section__x section-carousel not-agent">
    Recommended posts<article><h1>Some Other Post</h1></article>
  </section>
</main>
</body></html>
"""

# A category listing / index page: <main> WITHOUT the type-article class and with no
# .rich-text-block. This is the discriminator that rejects non-article pages.
NO_ARTICLE_HTML = """
<html><body>
<main class="Layout_main__abc product-releases">
  <nav class="breadcrumbs"><a href="/blog">Blog</a></nav>
  <section class="section-cards"><article><h1>A Listed Post</h1></article></section>
</main>
</body></html>
"""

# type-article present, but no <section> contains a .rich-text-block.
NO_BODY_HTML = """
<html><body>
<main class="Layout_main__abc type-article">
  <section class="Section_section__x">
    <div class="block component image"><img src="x.png"/></div>
  </section>
</main>
</body></html>
"""

# type-article present with a .rich-text-block that yields no text after stripping,
# and no title/date in the hero, so the converted Markdown is empty.
EMPTY_BODY_HTML = """
<html><body>
<main class="Layout_main__abc type-article">
  <section class="Section_section__x"><div class="block hero"></div></section>
  <section class="Section_section__x"><div class="block rich-text-block">   </div></section>
</main>
</body></html>
"""


@pytest.fixture
def extractor() -> KongExtractor:
    return KongExtractor()


class TestRouting:
    def test_routes_konghq_com(self) -> None:
        from mdfetch.router import route

        provider = route("https://konghq.com/blog/product-releases/some-slug")
        assert isinstance(provider, KongExtractor)


class TestCleanHtml:
    def test_clean_html_prepends_title_then_date(self, extractor: KongExtractor) -> None:
        soup = BeautifulSoup(ARTICLE_HTML, "lxml")
        result = extractor.clean_html(soup)
        children = [c for c in result.children if isinstance(c, Tag)]
        assert children[0].name == "h1"
        assert "Test Article Title" in children[0].get_text()
        assert children[1].name == "p"
        assert children[1].get_text(strip=True) == "May 26, 2026"

    def test_clean_html_strips_chrome_blocks(self, extractor: KongExtractor) -> None:
        soup = BeautifulSoup(ARTICLE_HTML, "lxml")
        result = extractor.clean_html(soup)
        assert result.select_one(".toc-wrap") is None
        assert result.select_one(".component.video") is None
        assert result.select_one(".component.more-on-this") is None
        assert result.select_one(".order-top") is None
        # The trailing non-intro CTA is removed; the intro TL;DR is kept.
        assert result.select_one(".section-header-block:not(.intro)") is None
        assert result.select_one(".section-header-block.intro") is not None

    def test_clean_html_strips_agent_affordances(self, extractor: KongExtractor) -> None:
        soup = BeautifulSoup(ARTICLE_HTML, "lxml")
        result = extractor.clean_html(soup)
        assert result.select_one(".agent") is None

    def test_clean_html_preserves_body_blocks(self, extractor: KongExtractor) -> None:
        soup = BeautifulSoup(ARTICLE_HTML, "lxml")
        result = extractor.clean_html(soup)
        assert result.select_one(".section-header-block.intro") is not None
        assert result.select_one(".rich-text-block") is not None
        img = result.select_one(".component.image img")
        assert isinstance(img, Tag)
        assert img.get("src") == "https://example.com/inline.png"
        assert result.select_one(".component.pull-quote blockquote") is not None

    def test_clean_html_raises_without_type_article(self, extractor: KongExtractor) -> None:
        soup = BeautifulSoup(NO_ARTICLE_HTML, "lxml")
        with pytest.raises(UnsupportedContentTypeError):
            extractor.clean_html(soup)

    def test_clean_html_raises_without_rich_text_block(self, extractor: KongExtractor) -> None:
        soup = BeautifulSoup(NO_BODY_HTML, "lxml")
        with pytest.raises(UnsupportedContentTypeError):
            extractor.clean_html(soup)


class TestConvertToMarkdown:
    def test_markdown_starts_with_title_then_date(self, extractor: KongExtractor) -> None:
        soup = BeautifulSoup(ARTICLE_HTML, "lxml")
        md = extractor.convert_to_markdown(extractor.clean_html(soup))
        lines = [line for line in md.split("\n") if line.strip()]
        assert lines[0] == "# Test Article Title"
        assert lines[1] == "May 26, 2026"

    def test_markdown_preserves_structure_and_code(self, extractor: KongExtractor) -> None:
        soup = BeautifulSoup(ARTICLE_HTML, "lxml")
        md = extractor.convert_to_markdown(extractor.clean_html(soup))
        assert "## Section Heading" in md
        assert "[link](https://example.com)" in md
        assert "Item one" in md
        assert "`git status`" in md
        assert "> A notable pull quote." in md
        assert "**TL;DR:**" in md

    def test_markdown_excludes_chrome_and_authors(self, extractor: KongExtractor) -> None:
        soup = BeautifulSoup(ARTICLE_HTML, "lxml")
        md = extractor.convert_to_markdown(extractor.clean_html(soup))
        for leaked in (
            "On this page",
            "video which can not be displayed",
            "More on this topic",
            "See Kong in action",
            "Get a Demo",
            "Recommended posts",
            "5 min read",
            "Staff Writer",
        ):
            assert leaked not in md

    def test_markdown_no_triple_blank_lines(self, extractor: KongExtractor) -> None:
        soup = BeautifulSoup(ARTICLE_HTML, "lxml")
        md = extractor.convert_to_markdown(extractor.clean_html(soup))
        assert "\n\n\n" not in md

    def test_markdown_raises_on_empty_body(self, extractor: KongExtractor) -> None:
        soup = BeautifulSoup(EMPTY_BODY_HTML, "lxml")
        tag = extractor.clean_html(soup)
        with pytest.raises(EmptyContentError):
            extractor.convert_to_markdown(tag)
