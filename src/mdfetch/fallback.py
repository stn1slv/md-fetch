"""Fallback extraction mechanisms for mdfetch."""

from __future__ import annotations

from typing import Any

from mdfetch.exceptions import EmptyContentError, FetchError, MissingAPIKeyError


def _extract(client: Any, url: str, depth: str, timeout: float) -> str:
    response = client.extract(urls=[url], extract_depth=depth, timeout=timeout)
    results = response.get("results", [])
    if not results:
        raise EmptyContentError(f"Tavily returned no results for {url}", url=url)

    raw_content = results[0].get("raw_content")
    if not raw_content:
        raise EmptyContentError(f"Tavily returned empty content for {url}", url=url)

    return str(raw_content)


def tavily_extract(url: str, timeout: float = 30.0) -> str:
    """Extract content using the Tavily API fallback.

    Tries the cheaper "basic" depth first. If it fails or returns nothing, retries
    once with "advanced". Empty content from the retry raises EmptyContentError;
    any other failure raises FetchError.
    """
    try:
        from tavily import TavilyClient  # type: ignore[import-untyped]
    except ImportError as e:
        raise MissingAPIKeyError(
            "tavily-python package is not installed. Please install it "
            f"to use the fallback feature. {e}"
        ) from e

    try:
        client = TavilyClient()
    except Exception as e:
        raise MissingAPIKeyError(str(e)) from e

    try:
        return _extract(client, url, "basic", timeout)
    except Exception:
        pass  # any basic-depth failure is retried with advanced below

    try:
        return _extract(client, url, "advanced", timeout)
    except EmptyContentError:
        raise
    except Exception as e:
        raise FetchError(f"Tavily fallback failed: {e}", url=url) from e
