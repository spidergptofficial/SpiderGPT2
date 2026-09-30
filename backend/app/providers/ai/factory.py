"""SpiderGPT AI Provider Factory & Dynamic Dispatcher.

Handles multi-provider resolution, automatic key detection, and graceful fallback routing.
"""
from typing import AsyncIterator, Dict, Any, List, Optional
from backend.app.core.config import settings
from backend.app.core.exceptions import AIProviderException, ProviderUnavailableException
from backend.app.core.logging import logger
from backend.app.providers.ai.base import AIProvider
from backend.app.providers.ai.gemini import GeminiProvider
from backend.app.providers.ai.openai import OpenAIProvider
from backend.app.providers.ai.openrouter import OpenRouterProvider
from backend.app.providers.ai.deepseek import DeepSeekProvider


class AIFactory:
    @staticmethod
    def get_provider_instance(name: str) -> AIProvider:
        clean_name = (name or "").lower().strip()
        if clean_name == "gemini":
            return GeminiProvider()
        elif clean_name == "openai":
            return OpenAIProvider()
        elif clean_name == "openrouter":
            return OpenRouterProvider()
        elif clean_name == "deepseek":
            return DeepSeekProvider()
        else:
            return GeminiProvider()

    @classmethod
    def resolve_active_provider_name(cls) -> str:
        """Determines best active provider based on configuration and available keys."""
        configured = (settings.AI_PROVIDER or "").lower().strip()

        # If explicitly configured and configured key exists
        if configured == "gemini" and settings.GEMINI_API_KEY:
            return "gemini"
        if configured == "openai" and settings.OPENAI_API_KEY:
            return "openai"
        if configured == "openrouter" and settings.OPENROUTER_API_KEY:
            return "openrouter"
        if configured == "deepseek" and settings.DEEPSEEK_API_KEY:
            return "deepseek"

        # Auto-detect if only one key exists
        if settings.GEMINI_API_KEY:
            return "gemini"
        if settings.OPENAI_API_KEY:
            return "openai"
        if settings.OPENROUTER_API_KEY:
            return "openrouter"
        if settings.DEEPSEEK_API_KEY:
            return "deepseek"

        # Default fallback to configured provider (handles mock/offline simulation)
        return configured or "gemini"

    @classmethod
    def get_primary_provider(cls) -> AIProvider:
        name = cls.resolve_active_provider_name()
        return cls.get_provider_instance(name)

    @classmethod
    def get_fallback_provider(cls) -> Optional[AIProvider]:
        if not settings.FALLBACK_AI_PROVIDER:
            return None
        fb_name = settings.FALLBACK_AI_PROVIDER.lower().strip()
        active = cls.resolve_active_provider_name()
        if fb_name == active:
            return None
        return cls.get_provider_instance(fb_name)

    @classmethod
    async def chat_with_fallback(
        cls,
        messages: List[Dict[str, str]],
        system_instruction: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        provider_override: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Executes chat on primary provider, with optional graceful fallback if primary encounters provider errors."""
        primary = cls.get_provider_instance(provider_override) if provider_override else cls.get_primary_provider()

        try:
            return await primary.chat(
                messages=messages,
                system_instruction=system_instruction,
                temperature=temperature,
                max_tokens=max_tokens,
            )
        except AIProviderException as primary_err:
            logger.warning("Primary AI Provider '%s' failed: %s", primary.provider_name, primary_err.message)
            fallback = cls.get_fallback_provider()
            if fallback and fallback.is_configured:
                logger.info("Attempting fallback AI Provider: '%s'", fallback.provider_name)
                try:
                    res = await fallback.chat(
                        messages=messages,
                        system_instruction=system_instruction,
                        temperature=temperature,
                        max_tokens=max_tokens,
                    )
                    res["provider_fallback"] = True
                    return res
                except Exception as fb_err:
                    logger.error("Fallback AI Provider '%s' also failed: %s", fallback.provider_name, str(fb_err))
                    raise primary_err
            raise primary_err

    @classmethod
    async def stream_chat_with_fallback(
        cls,
        messages: List[Dict[str, str]],
        system_instruction: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        provider_override: Optional[str] = None,
    ) -> AsyncIterator[str]:
        """Streams chat tokens with fallback support."""
        primary = cls.get_provider_instance(provider_override) if provider_override else cls.get_primary_provider()

        try:
            async for chunk in primary.stream_chat(
                messages=messages,
                system_instruction=system_instruction,
                temperature=temperature,
                max_tokens=max_tokens,
            ):
                yield chunk
        except AIProviderException as primary_err:
            # A stream may already have been sent to the client. Switching providers
            # here would splice two responses together and can duplicate content.
            logger.warning(
                "AI stream failed on '%s'; refusing mid-stream fallback: %s",
                primary.provider_name,
                primary_err.message,
            )
            raise primary_err
