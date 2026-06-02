"""Kong blog platform extractor."""

from __future__ import annotations

import copy
import re

from bs4 import BeautifulSoup
from bs4.element import Tag

from mdfetch.base import BaseExtractor
from mdfetch.exceptions import UnsupportedContentTypeError
from mdfetch.router import register

# The hero renders the publication date as a class-less ``<div>`` (e.g. "May 26, 2026")
# alongside a "N min read" div and author divs. This pattern selects the date while
# skipping the read-time, category, and author elements (clarification: keep date only).
_DATE_RE = re.compile(r"^[A-Z][a-z]+ \d{1,2}, \d{4}$")

# Chrome blocks that render *inside* the article content section and must be removed.
# All selectors use stable, human-authored companion classes — never the Next.js
# CSS-module hash suffixes (e.g. ``Section_section__Grz_Y``), which change per build.
_IN_BODY_CHROME_SELECTORS = (
    ".component.video",  # "video which can not be displayed" placeholder
    ".component.more-on-this",  # related-content widget
    ".toc-wrap",  # sticky "on this page" table-of-contents sidebar
    ".order-top",  # inline topic-tag list
)


@register
class KongExtractor(BaseExtractor):
    """Extracts article content from konghq.com/blog."""

    DOMAINS: frozenset[str] = frozenset({"konghq.com"})

    def clean_html(self, soup: BeautifulSoup) -> Tag:
        """Isolate the Kong article body and strip non-content elements.

        Article pages render ``<main class="... type-article">``; the blog index and
        category listings omit ``type-article``, so its absence signals a non-article
        URL. The body is the ``<section>`` richest in ``.rich-text-block`` blocks; the
        title and publication date live in the preceding hero section.
        """
        main = soup.find("main")
        if not isinstance(main, Tag) or "type-article" not in main.get_attribute_list("class"):
            raise UnsupportedContentTypeError(
                "URL is not an article page — no article body element found",
            )

        sections = main.find_all("section", recursive=False)
        content = max(
            sections,
            key=lambda s: len(s.select(".rich-text-block")),
            default=None,
        )
        if not isinstance(content, Tag) or not content.select(".rich-text-block"):
            raise UnsupportedContentTypeError(
                "URL is not an article page — no article body element found",
            )

        # Strip chrome blocks that live inside the content section.
        for selector in _IN_BODY_CHROME_SELECTORS:
            for el in content.select(selector):
                el.decompose()
        # The opening TL;DR is ``.section-header-block.intro`` (kept); the trailing
        # "See Kong in action" CTA is a ``.section-header-block`` without ``intro``.
        for el in content.select(".section-header-block:not(.intro)"):
            el.decompose()

        # Locate the hero by content, not position: it is the first non-content
        # <section> that contains the article <h1>. Searching for the <h1> (rather
        # than assuming ``sections[0]``) survives a prepended banner/announcement
        # section; the hero always precedes the recommended-posts carousel, whose
        # cards also contain <h1>s, so document order keeps this correct.
        hero = next(
            (s for s in sections if s is not content and s.find("h1") is not None),
            None,
        )

        # Build the output: title, then publication date, then the cleaned body.
        wrapper = soup.new_tag("div")
        if isinstance(hero, Tag):
            title_el = hero.find("h1")
            if isinstance(title_el, Tag):
                wrapper.append(copy.copy(title_el))
            date_el = next(
                (d for d in hero.find_all("div") if _DATE_RE.match(d.get_text(strip=True))),
                None,
            )
            if isinstance(date_el, Tag):
                date_p = soup.new_tag("p")
                date_p.string = date_el.get_text(strip=True)
                wrapper.append(date_p)
        wrapper.append(content)

        # Strip "agent mode" affordances: ``<span class="agent">`` elements inject
        # literal Markdown syntax (``**``, ``- ``, ``# ``) that duplicates the styled
        # content and would corrupt the conversion.
        for el in wrapper.select(".agent"):
            if not el.decomposed:
                el.decompose()

        return wrapper
