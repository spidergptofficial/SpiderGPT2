"""SpiderGPT Search Provider Factory."""
from typing import Optional
from backend.app.core.config import settings
from backend.app.providers.search.base import WebSearchProvider
from backend.app.providers.search.tavily import TavilySearchProvider, SerperSearchProvider, DuckDuckGoSearchProvider


class SearchFactory:
    @staticmethod
    def get_search_provider(override_name: Optional[str] = None) -> WebSearchProvider:
        name = (override_name or settings.WEB_SEARCH_PROVIDER or "duckduckgo").lower().strip()

        if name == "tavily":
            if settings.WEB_SEARCH_API_KEY:
                return TavilySearchProvider()
        elif name == "serper":
            if settings.WEB_SEARCH_API_KEY:
                return SerperSearchProvider()

        # Fallback to zero-credential DuckDuckGo provider
        return DuckDuckGoSearchProvider()
