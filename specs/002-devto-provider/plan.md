# Implementation Plan: mdfetch — dev.to Extractor

**Branch**: `002-devto-provider` | **Date**: 2026-05-14 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/002-devto-provider/spec.md`

## Summary

Add a `DevToExtractor` provider that fetches dev.to article pages, extracts the article body from `<div id="article-body">`, prepends the title and cover image from the page header, converts embedded resources to plain Markdown links, and returns clean Markdown. The provider is one new file; no shared library code is modified.

## Technical Context

**Language/Version**: Python 3.12+

**Primary Dependencies**: `httpx` (HTTP fetch), `BeautifulSoup` / `lxml` (HTML parsing), `markdownify` (Markdown conversion), `pytest` (testing)

**Storage**: N/A — stateless extraction library

**Testing**: `pytest` — unit tests (no network) + integration tests (`-m integration`, real URLs)

**Target Platform**: PyPI library (cross-platform)

**Project Type**: library

**Performance Goals**: Extraction in under 10 seconds per article on stable internet (SC-002)

**Constraints**: One new provider file; no changes to existing shared code

**Scale/Scope**: Single-article extraction per call; no volume concerns

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- [x] Validates Provider Pattern Architecture — `DevToExtractor` inherits `BaseExtractor`; uses `@register`; one new file only; no shared code changes
- [x] Confirms Technology Stack — `httpx`, `BeautifulSoup`, `markdownify`, `pytest` (all already in use; no new deps needed)
- [x] Adheres to Coding Standards — strict type hints, PEP 8, clear English naming
- [x] Incorporates Integration Testing — three reference dev.to URLs verified in `tests/integration/test_devto_integration.py`
- [x] Respects Packaging and Distribution standards — `pyproject.toml` + `src/` layout unchanged; `uv` for all dev commands

All constitution gates pass. No violations to justify.

## Project Structure

### Documentation (this feature)

```text
specs/002-devto-provider/
├── plan.md              # This file
├── research.md          # Phase 0 output — dev.to HTML structure analysis
├── data-model.md        # Phase 1 output — entities and error cases
├── quickstart.md        # Phase 1 output — usage examples
├── contracts/
│   └── public-api.md    # Phase 1 output — API contract (unchanged from Medium)
└── tasks.md             # Phase 2 output (/speckit-tasks — not created here)
```

### Source Code Changes

```text
src/mdfetch/providers/
├── __init__.py          # UNCHANGED — auto-discovery handles new file
└── devto.py             # NEW — DevToExtractor (single new file)

tests/unit/
└── test_devto_extractor.py   # NEW — unit tests (no network)

tests/integration/
├── snapshots/
│   ├── devto-integration-digest-december-2025.md   # NEW — snapshot
│   ├── devto-integration-digest-july-2025.md        # NEW — snapshot
│   └── devto-integration-digest-march-2026.md       # NEW — snapshot
└── test_devto_integration.py   # NEW — integration tests (real URLs)
```

No existing library source files are modified (`src/mdfetch/` unchanged).

**Side effect documented**: `tests/unit/test_router.py` required a one-line update — its "unsupported domain" example used `dev.to`, which became a supported domain once this provider was registered. The two test cases were updated to use `substack.com` instead. This is an expected consequence of any new provider registration.

**Version**: Library version bumped from `0.1.0` to `0.2.0` in `pyproject.toml` at time of release.

## Implementation Specification

### `src/mdfetch/providers/devto.py`

```python
@register
class DevToExtractor(BaseExtractor):
    DOMAINS: frozenset[str] = frozenset({"dev.to"})

    def clean_html(self, soup: BeautifulSoup) -> Tag:
        # 1. Locate article body — absence means non-article page
        body = soup.find("div", id="article-body")
        if not isinstance(body, Tag):
            raise UnsupportedContentTypeError(...)

        # 2. Handle embedded content: replace iframes with anchor links
        for iframe in body.find_all("iframe"):
            src = iframe.get("src") or iframe.get("data-src") or ""
            link = soup.new_tag("a", href=src)
            link.string = src
            iframe.replace_with(link)

        # 3. Handle liquid tag embeds (class containing "ltag")
        for embed in body.find_all(class_=re.compile(r"ltag", re.I)):
            src = embed.get("data-src") or embed.get("src") or str(embed.get("data-url", ""))
            if src:
                link = soup.new_tag("a", href=src)
                link.string = src
                embed.replace_with(link)
            else:
                embed.decompose()

        # 4. Strip empty anchor-name links inserted before headings
        for anchor in body.find_all("a", attrs={"name": True}):
            if not anchor.get_text(strip=True):
                anchor.decompose()

        # 5. Extract title and cover image from header; prepend to body
        header = soup.find("header", class_="crayons-article__header")
        if header:
            h1 = header.find("h1")
            cover_img = header.find("img", class_="crayons-article__cover__image")
            if h1:
                body.insert(0, h1)       # prepend <h1> as first child of body
            if cover_img:
                body.insert(1, cover_img) # prepend cover image after title

        return body

    def convert_to_markdown(self, tag: Tag) -> str:
        md = markdownify(str(tag), heading_style="ATX", code_language="", strip=["script", "style"])
        md = md.strip()
        md = re.sub(r"\n{3,}", "\n\n", md)
        if not md:
            raise EmptyContentError(...)
        return md
```

### `tests/unit/test_devto_extractor.py`

Unit tests cover (no network):
- `clean_html` raises `UnsupportedContentTypeError` when `div#article-body` absent
- `clean_html` raises `UnsupportedContentTypeError` for profile-page HTML (no article-body)
- `clean_html` preserves `<h1>` title and cover image
- `clean_html` replaces `<iframe>` with anchor link
- `clean_html` strips empty anchor-name links
- `convert_to_markdown` produces ATX headings, code blocks, lists
- `convert_to_markdown` raises `EmptyContentError` on blank body
- No raw HTML tags in converted Markdown

### `tests/integration/test_devto_integration.py`

Integration tests mirror the Medium pattern:
- Parametrized over 3 reference URLs + snapshot filenames
- `@pytest.mark.integration` marker
- Snapshot containment check: `expected in result`
- Snapshots generated by running extraction once and saving output

## Complexity Tracking

*No constitution violations — section left intentionally blank.*

### Revision: Implementation Sync 2026-05-14
- Reason: Documented two implementation side-effects not captured in the original plan: (1) `tests/unit/test_router.py` required domain-example update when dev.to became a registered provider; (2) library version bumped from 0.1.0 to 0.2.0 at release. `pyproject.toml` keywords gap (missing "dev.to") tracked as T013.
