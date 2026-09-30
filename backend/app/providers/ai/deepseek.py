"""SpiderGPT DeepSeek AI Provider Implementation."""
from typing import Optional
from backend.app.core.config import settings
from backend.app.providers.ai.openai import OpenAIProvider


class DeepSeekProvider(OpenAIProvider):
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        super().__init__(
            api_key=api_key or settings.DEEPSEEK_API_KEY,
            model=model or settings.DEEPSEEK_MODEL or "deepseek-chat",
            base_url="https://api.deepseek.com/v1",
            custom_provider_name="deepseek",
        )
