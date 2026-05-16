"""The New Stack platform extractor."""

from __future__ import annotations

import copy
import re

from bs4 import BeautifulSoup
from bs4.element import Tag
from markdownify import markdownify

from mdfetch.base import BaseExtractor
from mdfetch.exceptions import EmptyContentError, UnsupportedContentTypeError
from mdfetch.router import register


@register
class TheNewStackExtractor(BaseExtractor):
    """Extracts article content from thenewstack.io."""

    DOMAINS: frozenset[str] = frozenset({"thenewstack.io"})

    def clean_html(self, soup: BeautifulSoup) -> Tag:
        """Isolate the article body and strip all non-content elements."""
        body = soup.find("div", id="tns-post-body-content")
        if not isinstance(body, Tag):
            raise UnsupportedContentTypeError(
                "URL is not an article page — no article body element found",
            )

        # Strip sponsored content disclosures and injected sponsor notes (FR-003)
        for cls in (
            "sponsored-post-disclosure",
            "tns-sponsored-post-disclosure",
            "sponsor-disclosure",
            "tns-sponsor-note",
        ):
            for el in body.find_all("div", class_=cls):
                el.decompose()

        # Convert iframes to plain anchor links (FR-009)
        for iframe in body.find_all("iframe"):
            src = str(iframe.get("src") or iframe.get("data-src") or "")
            if src:
                link = soup.new_tag("a", href=src)
                link.string = src
                iframe.replace_with(link)
            else:
                iframe.decompose()

        # Prepend deck and title from headline container (FR-004)
        headline = soup.find("div", id="tns-post-headline")
        if isinstance(headline, Tag):
            deck = headline.find("div", class_="post-excerpt")
            if isinstance(deck, Tag):
                p = soup.new_tag("p")
                p.string = deck.get_text(strip=True)
                body.insert(0, p)
            title_el = headline.find("h1", class_="title")
            if isinstance(title_el, Tag):
                body.insert(0, copy.copy(title_el))

        return body

    def convert_to_markdown(self, tag: Tag) -> str:
        """Convert cleaned article Tag to Markdown."""
        md = markdownify(str(tag), heading_style="ATX", code_language="", strip=["script", "style"])
        md = md.strip()
        md = re.sub(r"\n{3,}", "\n\n", md)

        if not md:
            raise EmptyContentError(
                "Article body contained no extractable text content",
            )

        return md
