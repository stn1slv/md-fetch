"""dev.to platform extractor."""

from __future__ import annotations

import copy
import re

from bs4 import BeautifulSoup
from bs4.element import Tag

from mdfetch.base import BaseExtractor
from mdfetch.exceptions import UnsupportedContentTypeError
from mdfetch.router import register


@register
class DevToExtractor(BaseExtractor):
    """Extracts article content from dev.to."""

    DOMAINS: frozenset[str] = frozenset({"dev.to"})

    def clean_html(self, soup: BeautifulSoup) -> Tag:
        """Isolate the article body and strip all non-content elements."""
        body = soup.find("div", id="article-body")
        if not isinstance(body, Tag):
            raise UnsupportedContentTypeError(
                "URL is not an article page — no article body element found",
            )

        # Replace iframes with plain anchor links (FR-008)
        self._replace_iframes_with_links(body, soup)

        # Replace dev.to liquid-tag embeds with plain anchor links (FR-008)
        for embed in body.find_all(class_=re.compile(r"ltag", re.IGNORECASE)):
            src = str(embed.get("data-url") or embed.get("data-src") or embed.get("src") or "")
            if src:
                link = soup.new_tag("a", href=src)
                link.string = src
                embed.replace_with(link)
            else:
                embed.decompose()

        # Strip empty anchor-name links inserted before headings
        for anchor in body.find_all("a", attrs={"name": True}):
            if not anchor.get_text(strip=True):
                anchor.decompose()

        # Prepend title and cover image from article header
        header = soup.find("header", class_="crayons-article__header")
        if isinstance(header, Tag):
            cover_img = header.find("img", class_="crayons-article__cover__image")
            h1 = header.find("h1")
            # Insert in reverse order so final order is h1 → cover_img → body content
            if isinstance(cover_img, Tag):
                body.insert(0, copy.copy(cover_img))
            if isinstance(h1, Tag):
                body.insert(0, copy.copy(h1))

        return body
