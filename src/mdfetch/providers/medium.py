"""Medium platform extractor."""

from __future__ import annotations

import re
import unicodedata

from bs4 import BeautifulSoup
from bs4.element import Tag
from markdownify import markdownify

from mdfetch.base import BaseExtractor
from mdfetch.exceptions import (
    EmptyContentError,
    HTTPStatusError,
    MdfetchError,
    UnsupportedContentTypeError,
)
from mdfetch.router import register


@register
class MediumExtractor(BaseExtractor):
    """Extracts article content from medium.com and its subdomains."""

    DOMAINS: frozenset[str] = frozenset({"medium.com"})
    _FREEDIUM_BASE = "https://freedium-mirror.cfd/"
    _no_retry_status_codes: frozenset[int] = frozenset({403, 429})
    # Smart-quote characters that Medium serves but Freedium replaces with ASCII;
    # canonicalize so both extraction paths yield identical text.
    _SMART_QUOTE_MAP = str.maketrans({"‘": "'", "’": "'", "“": '"', "”": '"'})

    def clean_html(self, soup: BeautifulSoup) -> Tag:
        """Isolate the article body and strip all non-content elements."""
        article = soup.find("article")
        if not isinstance(article, Tag):
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

        for section in article.find_all("section"):
            raw = section.get("class")
            classes: list[str] = raw if isinstance(raw, list) else ([raw] if raw else [])
            if classes and any("author" in c.lower() or "bio" in c.lower() for c in classes):
                section.decompose()

        return article

    def convert_to_markdown(self, tag: Tag) -> str:
        """Convert cleaned article Tag to Markdown.

        Mutates *tag* in place by rewriting ``<br>`` elements inside ``<pre>``/
        ``<code>`` to literal ``\\n`` text nodes before conversion.  Callers must
        not reuse *tag* after this method returns.
        """
        # Medium emits <br> inside <pre>/<code> for code-block line breaks;
        # markdownify would render those as trailing-two-space hard-break syntax,
        # which Freedium (using plain '\n') does not produce.  Rewrite at the DOM
        # level so the two paths yield identical fenced-code output, while
        # leaving <br> in prose untouched (preserving its hard-break semantics).
        for br in tag.select("pre br, code br"):
            br.replace_with("\n")

        md = markdownify(str(tag), heading_style="ATX", code_language="", strip=["script", "style"])
        md = md.strip()
        md = re.sub(r"\n{3,}", "\n\n", md)
        md = self._normalize(md)

        if not md:
            raise EmptyContentError(
                "Article body contained no extractable text content",
            )

        return md

    def _normalize(self, md: str) -> str:
        """Canonicalize text so direct-Medium and Freedium-fallback paths agree.

        Medium serves typographic quotes (``’ “ ”``); Freedium's mirror serves
        ASCII quotes.  Without normalization the two paths produce inequivalent
        Markdown for the same article.  NFC ensures equivalent codepoint
        sequences compare equal.
        """
        md = unicodedata.normalize("NFC", md)
        md = md.translate(self._SMART_QUOTE_MAP)
        return md

    def _parse_freedium(self, soup: BeautifulSoup) -> str:
        """Parse Freedium mirror HTML, which uses div.main-content instead of <article>."""
        content = soup.find("div", class_="main-content")
        if not isinstance(content, Tag):
            raise UnsupportedContentTypeError(
                "Fallback page missing main-content element",
            )
        # Freedium renders section headings one level deeper than medium.com (h4 vs h3).
        # Remap so the output heading levels match the medium.com direct path.
        for level in (4, 5, 6):
            for tag in list(content.find_all(f"h{level}")):
                tag.name = f"h{level - 1}"
        return self.convert_to_markdown(content)

    def extract(self, url: str, *, retries: int = 3, retry_delay: float = 2.0) -> str:
        """Extract article, falling back to Freedium mirror on HTTP 403 or 429."""
        try:
            return super().extract(url, retries=retries, retry_delay=retry_delay)
        except HTTPStatusError as exc:
            if exc.status_code not in self._no_retry_status_codes:
                raise
        freedium_url = f"{self._FREEDIUM_BASE}{url}"
        # Pass _no_retry_codes=frozenset() so a 429 from Freedium is retried
        # with backoff rather than raised immediately (thread-safe: no mutation).
        try:
            html = self.fetch_html(
                freedium_url, retries=retries, retry_delay=retry_delay, _no_retry_codes=frozenset()
            )
            soup = BeautifulSoup(html, "lxml")
            return self._parse_freedium(soup)
        except MdfetchError as inner_exc:
            inner_exc.url = url
            raise
