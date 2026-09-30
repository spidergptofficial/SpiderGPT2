"""SpiderGPT Unified Web Search Provider Base Interface."""
from abc import ABC, abstractmethod
from typing import Dict, Any, List


class WebSearchProvider(ABC):
    @property
    @abstractmethod
    def provider_name(self) -> str:
        pass

    @property
    @abstractmethod
    def is_configured(self) -> bool:
        pass

    @abstractmethod
    async def search(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """Performs a web search and returns normalized results:

        [
            {
                "title": str,
                "url": str,
                "snippet": str,
                "score": Optional[float]
            }
        ]
        """
        pass
