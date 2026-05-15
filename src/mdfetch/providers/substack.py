"""Substack platform extractor."""

from __future__ import annotations

import re

from bs4 import BeautifulSoup
from bs4.element import Tag
from markdownify import markdownify

from mdfetch.base import BaseExtractor
from mdfetch.exceptions import EmptyContentError, UnsupportedContentTypeError
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
        for iframe in body.find_all("iframe"):
            src = str(iframe.get("src") or iframe.get("data-src") or "")
            if src:
                link = soup.new_tag("a", href=src)
                link.string = src
                iframe.replace_with(link)
            else:
                iframe.decompose()

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
                body.insert(0, subtitle_el.__copy__())

        # Prepend article title as top-level heading (FR-004)
        # h1.post-title is structurally outside div.body.markup; unconditional prepend
        # achieves exactly-once inclusion without a body-scan deduplication step.
        if isinstance(header, Tag):
            title_el = header.find("h1", class_="post-title")
            if isinstance(title_el, Tag):
                body.insert(0, title_el.__copy__())

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
