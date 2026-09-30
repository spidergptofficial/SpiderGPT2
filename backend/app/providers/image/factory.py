"""SpiderGPT Image Provider Factory."""
from backend.app.core.config import settings
from backend.app.providers.image.base import ImageProvider
from backend.app.providers.image.openai_image import OpenAIImageProvider
from backend.app.providers.image.gemini_image import GeminiImageProvider


class ImageFactory:
    @staticmethod
    def get_image_provider(provider_override: str = None) -> ImageProvider:
        name = (provider_override or settings.IMAGE_PROVIDER or "openai").lower().strip()
        if name == "gemini":
            return GeminiImageProvider()
        return OpenAIImageProvider()
