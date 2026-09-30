"""SpiderGPT Web Search Providers Module Export."""
from backend.app.providers.search.base import WebSearchProvider
from backend.app.providers.search.tavily import TavilySearchProvider, SerperSearchProvider, DuckDuckGoSearchProvider
from backend.app.providers.search.factory import SearchFactory

__all__ = [
    "WebSearchProvider",
    "TavilySearchProvider",
    "SerperSearchProvider",
    "DuckDuckGoSearchProvider",
    "SearchFactory",
]
