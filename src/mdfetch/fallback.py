"""Fallback extraction mechanisms for mdfetch."""

from __future__ import annotations

from tavily import TavilyClient  # type: ignore[import-untyped]

from mdfetch.exceptions import EmptyContentError, FetchError, MissingAPIKeyError


def tavily_extract(url: str, timeout: float = 30.0) -> str:
    """Extract content using the Tavily API fallback."""
    try:
        client = TavilyClient()
    except Exception as e:
        raise MissingAPIKeyError(str(e)) from e

    try:
        response = client.extract(urls=[url], extract_depth="basic")
        results = response.get("results", [])
        if not results:
            raise EmptyContentError(f"Tavily returned no results for {url}", url=url)

        raw_content = results[0].get("raw_content")
        if not raw_content:
            raise EmptyContentError(f"Tavily returned empty content for {url}", url=url)

        return str(raw_content)
    except EmptyContentError:
        try:
            response = client.extract(urls=[url], extract_depth="advanced")
            results = response.get("results", [])
            if not results:
                raise EmptyContentError(f"Tavily returned no results for {url}", url=url)

            raw_content = results[0].get("raw_content")
            if not raw_content:
                raise EmptyContentError(f"Tavily returned empty content for {url}", url=url)

            return str(raw_content)
        except Exception as e:
            if isinstance(e, EmptyContentError):
                raise
            raise FetchError(f"Tavily fallback failed: {e}", url=url) from e
    except Exception:
        # If basic threw an API error, fallback to advanced as well
        try:
            response = client.extract(urls=[url], extract_depth="advanced")
            results = response.get("results", [])
            if not results:
                raise EmptyContentError(f"Tavily returned no results for {url}", url=url)

            raw_content = results[0].get("raw_content")
            if not raw_content:
                raise EmptyContentError(f"Tavily returned empty content for {url}", url=url)

            return str(raw_content)
        except Exception as e:
            raise FetchError(f"Tavily fallback failed: {e}", url=url) from e
