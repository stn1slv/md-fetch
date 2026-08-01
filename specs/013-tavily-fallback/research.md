# Research

## Technical Approach for Tavily Fallback

### Integration Point
- **Decision**: Update `mdfetch.extract` to intercept extraction errors and `UnsupportedPlatformError` from the router. Add a `--tavily-fallback` CLI option.
- **Rationale**: This centralizes the fallback logic and keeps the router focused on supported platforms. The `--tavily-fallback` flag defaults to False, and when True, `extract()` requires `TAVILY_API_KEY` to be present.
- **Alternatives considered**: Making a catch-all "Tavily" provider in the router. Rejected because a catch-all provider breaks the router's explicit domain-mapping contract.

### Tavily Extraction Workflow
- **Decision**: Create a `TavilyFallbackExtractor` or just a function in `mdfetch.fallback` that uses the `tavily-python` client. It calls `client.extract(urls=[url], extract_depth="basic")`. If that raises an exception or returns empty content, it retries with `extract_depth="advanced"`.
- **Rationale**: Matches the user's explicit functional requirements (FR-008). 
- **Alternatives considered**: Raw HTTP calls to Tavily API. Rejected because the user specifically requested the use of the `tavily-python` library.

### Dependency Management
- **Decision**: Add `tavily-python` as a standard production dependency in `pyproject.toml` (using `uv`).
- **Rationale**: User assumed standard dependency in the spec.

## Constitution Verification
- **Provider Pattern Architecture**: The fallback does not modify existing providers. It acts as a safety net in the `extract` entrypoint.
- **Technology Stack**: Introduces `tavily-python` alongside `httpx`, `BeautifulSoup`, `Markdownify`, `pytest`, `uv`. This is acceptable given the spec explicit request.
- **Integration Testing**: We must mock the Tavily API or provide a real test for the fallback functionality.
