"""SpiderGPT OpenRouter AI Provider Implementation."""
from typing import Optional
from backend.app.core.config import settings
from backend.app.providers.ai.openai import OpenAIProvider


class OpenRouterProvider(OpenAIProvider):
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        super().__init__(
            api_key=api_key or settings.OPENROUTER_API_KEY,
            model=model or settings.OPENROUTER_MODEL or "anthropic/claude-3.5-sonnet",
            base_url="https://openrouter.ai/api/v1",
            custom_provider_name="openrouter",
        )
