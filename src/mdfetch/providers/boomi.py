"""Boomi blog platform extractor."""

from __future__ import annotations

import copy

from bs4 import BeautifulSoup
from bs4.element import Tag

from mdfetch.base import BaseExtractor
from mdfetch.exceptions import UnsupportedContentTypeError
from mdfetch.router import register


@register
class BoomiExtractor(BaseExtractor):
    """Extracts article content from boomi.com/blog."""

    DOMAINS: frozenset[str] = frozenset({"boomi.com"})

    def clean_html(self, soup: BeautifulSoup) -> Tag:
        """Isolate the article body and strip non-content elements.

        The body container ``div.post-content`` is present only on article pages;
        the blog index and other ``boomi.com`` pages lack it, so its absence signals
        a non-article URL.
        """
        body = soup.find("div", class_="post-content")
        if not isinstance(body, Tag):
            raise UnsupportedContentTypeError(
                "URL is not an article page — no article body element found",
            )

        # Strip previous/next post navigation — the only chrome inside post-content.
        for nav in body.find_all("div", class_="blog-nav"):
            nav.decompose()

        # Prepend the article title, which is rendered in the page hero (outside body).
        title_el = soup.find("h1")
        if isinstance(title_el, Tag):
            body.insert(0, copy.copy(title_el))

        return body
