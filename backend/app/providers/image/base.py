"""SpiderGPT Unified Image Provider Base Interface."""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class ImageProvider(ABC):
    @property
    @abstractmethod
    def provider_name(self) -> str:
        pass

    @property
    @abstractmethod
    def is_configured(self) -> bool:
        pass

    @abstractmethod
    async def generate_image(
        self,
        prompt: str,
        size: str = "1024x1024",
        quality: str = "standard",
        aspect_ratio: Optional[str] = "1:1",
    ) -> Dict[str, Any]:
        """Generates an image from prompt.

        Returns:
            {
                "image_url": str,
                "provider": str,
                "model": str,
                "metadata": dict
            }
        """
        pass
