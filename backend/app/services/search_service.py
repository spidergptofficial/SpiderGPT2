"""SpiderGPT Search Service."""
from typing import Dict, Any, List
from backend.app.core.exceptions import SearchProviderException
from backend.app.providers.search.factory import SearchFactory


class SearchService:
    @staticmethod
    async def perform_search(query: str, max_results: int = 5) -> Dict[str, Any]:
        provider = SearchFactory.get_search_provider()
        try:
            results = await provider.search(query, max_results=max_results)
            return {
                "query": query,
                "provider": provider.provider_name,
                "results": results,
                "total_results": len(results),
            }
        except SearchProviderException as e:
            return {
                "query": query,
                "provider": provider.provider_name,
                "results": [],
                "total_results": 0,
                "error": e.message,
            }
