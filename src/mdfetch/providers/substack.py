"""Substack platform extractor."""

from __future__ import annotations

import copy
import re

from bs4 import BeautifulSoup
from bs4.element import Tag

from mdfetch.base import BaseExtractor
from mdfetch.exceptions import UnsupportedContentTypeError
from mdfetch.router import register


@register
class SubstackExtractor(BaseExtractor):
    """Extracts article content from substack.com and its subdomains."""

    DOMAINS: frozenset[str] = frozenset({"substack.com"})

    def clean_html(self, soup: BeautifulSoup) -> Tag:
        """Isolate the article body and strip all non-content elements."""
        body = soup.find("div", class_="body markup")
        if not isinstance(body, Tag):
            raise UnsupportedContentTypeError(
                "URL is not an article page — no article body element found",
            )

        # Strip inline subscription CTAs and paywall terminal widget (FR-003, FR-008)
        for widget in body.find_all("div", class_="subscription-widget-wrap"):
            widget.decompose()

        # Convert iframes to plain anchor links (FR-011)
        self._replace_iframes_with_links(body, soup)

        # Convert other Substack embed containers to plain anchor links (FR-011)
        _safe_components = {"SubscribeWidget", "Image2ToDOM"}
        for embed in body.find_all(attrs={"data-component-name": True}):
            if embed.get("data-component-name") in _safe_components:
                continue
            url = str(embed.get("href") or embed.get("data-url") or embed.get("src") or "")
            if url:
                link = soup.new_tag("a", href=url)
                link.string = url
                embed.replace_with(link)
            else:
                embed.decompose()

        # Prepend subtitle from post-header (FR-005)
        header = soup.find("div", class_="post-header")
        if isinstance(header, Tag):
            subtitle_el = header.find("h3", class_=re.compile(r"subtitle"))
            if isinstance(subtitle_el, Tag):
                body.insert(0, copy.copy(subtitle_el))

        # Prepend article title as top-level heading (FR-004)
        # h1.post-title is structurally outside div.body.markup; unconditional prepend
        # achieves exactly-once inclusion without a body-scan deduplication step.
        if isinstance(header, Tag):
            title_el = header.find("h1", class_="post-title")
            if isinstance(title_el, Tag):
                body.insert(0, copy.copy(title_el))

        return body
