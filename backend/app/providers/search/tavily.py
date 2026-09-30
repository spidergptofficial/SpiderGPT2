"""SpiderGPT Tavily & Serper Web Search Providers."""
from typing import Dict, Any, List, Optional
import httpx

from backend.app.core.config import settings
from backend.app.core.exceptions import SearchProviderException
from backend.app.core.logging import logger
from backend.app.providers.search.base import WebSearchProvider


class TavilySearchProvider(WebSearchProvider):
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.WEB_SEARCH_API_KEY
        self.base_url = "https://api.tavily.com"

    @property
    def provider_name(self) -> str:
        return "tavily"

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key)

    async def search(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        if not self.is_configured:
            return []

        url = f"{self.base_url}/search"
        payload = {
            "api_key": self.api_key,
            "query": query,
            "max_results": max_results,
            "search_depth": "basic",
        }

        async with httpx.AsyncClient(timeout=20.0) as client:
            try:
                resp = await client.post(url, json=payload)
                if resp.status_code != 200:
                    logger.error("Tavily error (%d): %s", resp.status_code, resp.text[:200])
                    raise SearchProviderException(f"Tavily returned error {resp.status_code}", provider=self.provider_name)
                data = resp.json()
                results = []
                for item in data.get("results", []):
                    results.append({
                        "title": item.get("title", ""),
                        "url": item.get("url", ""),
                        "snippet": item.get("content", ""),
                        "score": item.get("score"),
                    })
                return results
            except httpx.RequestError as e:
                logger.error("Tavily network request failure: %s", str(e))
                raise SearchProviderException(f"Tavily network error: {str(e)}", provider=self.provider_name)


class SerperSearchProvider(WebSearchProvider):
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.WEB_SEARCH_API_KEY
        self.base_url = "https://google.serper.dev"

    @property
    def provider_name(self) -> str:
        return "serper"

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key)

    async def search(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        if not self.is_configured:
            return []

        url = f"{self.base_url}/search"
        headers = {
            "X-API-KEY": self.api_key,
            "Content-Type": "application/json",
        }
        payload = {"q": query, "num": max_results}

        async with httpx.AsyncClient(timeout=20.0) as client:
            try:
                resp = await client.post(url, headers=headers, json=payload)
                if resp.status_code != 200:
                    logger.error("Serper error (%d): %s", resp.status_code, resp.text[:200])
                    raise SearchProviderException(f"Serper returned error {resp.status_code}", provider=self.provider_name)
                data = resp.json()
                results = []
                for item in data.get("organic", [])[:max_results]:
                    results.append({
                        "title": item.get("title", ""),
                        "url": item.get("link", ""),
                        "snippet": item.get("snippet", ""),
                        "score": None,
                    })
                return results
            except httpx.RequestError as e:
                logger.error("Serper network error: %s", str(e))
                raise SearchProviderException(f"Serper network error: {str(e)}", provider=self.provider_name)


class DuckDuckGoSearchProvider(WebSearchProvider):
    """Zero-credential fallback web search provider using instant answer API."""
    def __init__(self):
        pass

    @property
    def provider_name(self) -> str:
        return "duckduckgo"

    @property
    def is_configured(self) -> bool:
        return True

    async def search(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        url = "https://api.duckduckgo.com/"
        params = {"q": query, "format": "json", "no_html": "1", "skip_disambig": "1"}

        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                resp = await client.get(url, params=params)
                results = []
                if resp.status_code == 200:
                    data = resp.json()
                    abstract = data.get("AbstractText")
                    source_url = data.get("AbstractURL")
                    heading = data.get("Heading")
                    if abstract and source_url:
                        results.append({
                            "title": heading or query,
                            "url": source_url,
                            "snippet": abstract,
                            "score": 1.0,
                        })
                    for topic in data.get("RelatedTopics", []):
                        if isinstance(topic, dict) and topic.get("Text") and topic.get("FirstURL"):
                            results.append({
                                "title": topic.get("Text")[:60] + "...",
                                "url": topic.get("FirstURL"),
                                "snippet": topic.get("Text"),
                                "score": 0.8,
                            })
                            if len(results) >= max_results:
                                break
                return results[:max_results]

            except httpx.RequestError as e:
                logger.warning("DuckDuckGo instant search network warning: %s", str(e))
                return []
            except ValueError as e:
                logger.warning("DuckDuckGo response parsing warning: %s", str(e))
                return []
