"""Medium platform extractor."""

from __future__ import annotations

import re

from bs4 import BeautifulSoup
from markdownify import markdownify

from mdfetch.base import BaseExtractor
from mdfetch.exceptions import EmptyContentError, UnsupportedContentTypeError


class MediumExtractor(BaseExtractor):
    """Extracts article content from medium.com and its subdomains."""

    DOMAINS: frozenset[str] = frozenset({"medium.com", "www.medium.com"})

    def clean_html(self, soup: BeautifulSoup) -> BeautifulSoup:
        """Isolate the article body and strip all non-content elements."""
        article = soup.find("article")
        if article is None:
            raise UnsupportedContentTypeError(
                "URL is not an article page — no <article> element found",
            )

        for nav in article.find_all("nav"):
            nav.decompose()

        for button in article.find_all(
            "button",
            attrs={"aria-label": re.compile(r"clap|applaud", re.IGNORECASE)},
        ):
            button.decompose()

        for element in article.find_all(attrs={"data-testid": "post-sidebar"}):
            element.decompose()

        for element in article.find_all(attrs={"data-testid": re.compile(r"share", re.IGNORECASE)}):
            element.decompose()

        for element in article.find_all(attrs={"data-testid": "post-footer"}):
            element.decompose()

        # Remove author biography sections appended after article body
        for section in article.find_all("section"):
            raw = section.get("class")
            classes: list[str] = raw if isinstance(raw, list) else []
            if classes and any("author" in c.lower() or "bio" in c.lower() for c in classes):
                section.decompose()

        return article  # type: ignore[return-value]

    def convert_to_markdown(self, soup: BeautifulSoup) -> str:
        """Convert cleaned BeautifulSoup article to Markdown."""
        md = markdownify(str(soup), heading_style="ATX", strip=["script", "style"])
        md = md.strip()
        # Collapse 3+ consecutive blank lines to 2
        md = re.sub(r"\n{3,}", "\n\n", md)

        if not md:
            raise EmptyContentError(
                "Article body contained no extractable text content",
            )

        return md
