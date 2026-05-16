"""DZone platform extractor."""

from __future__ import annotations

import copy
import re
from typing import Any

from bs4 import BeautifulSoup
from bs4.element import AttributeValueList, Tag
from markdownify import markdownify

from mdfetch.base import BaseExtractor
from mdfetch.exceptions import EmptyContentError, UnsupportedContentTypeError
from mdfetch.router import register


def _code_language_callback(el: Any) -> str:
    """Return the language from a language-X class on the inner <code> element."""
    if not isinstance(el, Tag):
        return ""
    code_el = el.find("code")
    if not isinstance(code_el, Tag):
        return ""
    raw = code_el.get("class")
    if not raw:
        return ""
    cls_list: list[str] = [raw] if isinstance(raw, str) else list(raw)
    for cls in cls_list:
        if isinstance(cls, str) and cls.startswith("language-"):
            return cls[len("language-") :]
    return ""


@register
class DZoneExtractor(BaseExtractor):
    """Extracts article content from dzone.com."""

    DOMAINS: frozenset[str] = frozenset({"dzone.com"})

    def clean_html(self, soup: BeautifulSoup) -> Tag:
        """Isolate the article body and strip non-content elements."""
        body = soup.find("div", class_="content-html")
        if not isinstance(body, Tag):
            raise UnsupportedContentTypeError(
                "URL is not an article page — no article body element found",
            )

        for wrapper in body.find_all("div", class_="codeMirror-wrapper"):
            name_lang_el = wrapper.find("div", class_="nameLanguage")
            lang = (
                name_lang_el.get_text(strip=True).lower() if isinstance(name_lang_el, Tag) else ""
            )
            if lang == "plain text":
                lang = ""

            code_el = wrapper.find("code")
            if isinstance(code_el, Tag) and lang:
                code_el["class"] = AttributeValueList([f"language-{lang}"])

            code_header = wrapper.find("div", class_="codeHeader")
            if isinstance(code_header, Tag):
                code_header.decompose()

        title_el = soup.find("h1", class_="article-title")
        if isinstance(title_el, Tag):
            body.insert(0, copy.copy(title_el))

        return body

    def convert_to_markdown(self, tag: Tag) -> str:
        """Convert cleaned article Tag to Markdown."""
        md = markdownify(
            str(tag),
            heading_style="ATX",
            code_language="",
            code_language_callback=_code_language_callback,
            strip=["script", "style"],
        )
        md = md.strip()
        md = re.sub(r"\n{3,}", "\n\n", md)

        if not md:
            raise EmptyContentError(
                "Article body contained no extractable text content",
            )

        return md
