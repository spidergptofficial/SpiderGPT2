"""SpiderGPT OpenAI Image Provider (DALL-E)."""
from typing import Dict, Any, Optional
import httpx

from backend.app.core.config import settings
from backend.app.core.exceptions import ImageProviderException
from backend.app.core.logging import logger
from backend.app.providers.image.base import ImageProvider


class OpenAIImageProvider(ImageProvider):
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.model = model or settings.IMAGE_MODEL or "dall-e-3"
        self.base_url = "https://api.openai.com/v1"

    @property
    def provider_name(self) -> str:
        return "openai"

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key)

    async def generate_image(
        self,
        prompt: str,
        size: str = "1024x1024",
        quality: str = "standard",
        aspect_ratio: Optional[str] = "1:1",
    ) -> Dict[str, Any]:
        if not self.is_configured:
            # Fallback mock image url
            return {
                "image_url": f"https://placehold.co/1024x1024/png?text={prompt[:20]}",
                "provider": self.provider_name,
                "model": self.model,
                "metadata": {"simulated": True, "prompt": prompt},
            }

        url = f"{self.base_url}/images/generations"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "prompt": prompt,
            "n": 1,
            "size": size,
            "quality": quality,
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                resp = await client.post(url, headers=headers, json=payload)
                if resp.status_code != 200:
                    logger.error("OpenAI Image error (%d): %s", resp.status_code, resp.text[:200])
                    raise ImageProviderException(f"OpenAI Image returned status {resp.status_code}", provider=self.provider_name)
                data = resp.json()
                img_url = data.get("data", [{}])[0].get("url", "")
                revised_prompt = data.get("data", [{}])[0].get("revised_prompt", prompt)
                return {
                    "image_url": img_url,
                    "provider": self.provider_name,
                    "model": self.model,
                    "metadata": {"revised_prompt": revised_prompt},
                }
            except httpx.RequestError as e:
                logger.error("OpenAI image network error: %s", str(e))
                raise ImageProviderException(f"Network error during image generation: {str(e)}", provider=self.provider_name)
