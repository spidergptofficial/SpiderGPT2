"""SpiderGPT Gemini Image Provider (Imagen)."""
from typing import Dict, Any, Optional
import httpx

from backend.app.core.config import settings
from backend.app.core.exceptions import ImageProviderException
from backend.app.core.logging import logger
from backend.app.providers.image.base import ImageProvider


class GeminiImageProvider(ImageProvider):
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model = "imagen-3.0-generate-002"
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"

    @property
    def provider_name(self) -> str:
        return "gemini"

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
            return {
                "image_url": f"https://placehold.co/1024x1024/png?text={prompt[:20]}",
                "provider": self.provider_name,
                "model": self.model,
                "metadata": {"simulated": True, "prompt": prompt},
            }

        url = f"{self.base_url}/models/{self.model}:predict?key={self.api_key}"
        payload = {
            "instances": [{"prompt": prompt}],
            "parameters": {
                "sampleCount": 1,
                "aspectRatio": aspect_ratio or "1:1",
            },
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                resp = await client.post(url, json=payload)
                if resp.status_code != 200:
                    logger.error("Gemini Imagen Error (%d): %s", resp.status_code, resp.text[:200])
                    # Fallback to simulated placeholder instead of crashing
                    return {
                        "image_url": f"https://placehold.co/1024x1024/png?text={prompt[:20]}",
                        "provider": self.provider_name,
                        "model": self.model,
                        "metadata": {"fallback": True, "prompt": prompt},
                    }
                data = resp.json()
                predictions = data.get("predictions", [])
                if predictions and "bytesBase64Encoded" in predictions[0]:
                    b64 = predictions[0]["bytesBase64Encoded"]
                    data_url = f"data:image/png;base64,{b64}"
                    return {
                        "image_url": data_url,
                        "provider": self.provider_name,
                        "model": self.model,
                        "metadata": {"prompt": prompt},
                    }
                return {
                    "image_url": f"https://placehold.co/1024x1024/png?text={prompt[:20]}",
                    "provider": self.provider_name,
                    "model": self.model,
                    "metadata": {"simulated": True},
                }
            except Exception as e:
                logger.error("Gemini Imagen network error: %s", str(e))
                raise ImageProviderException(f"Imagen error: {str(e)}", provider=self.provider_name)
