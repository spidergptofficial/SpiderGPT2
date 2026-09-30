"""SpiderGPT Unified AI Provider Base Interface.

All LLM provider implementations (Gemini, OpenAI, OpenRouter, DeepSeek)
must adhere to this abstract contract.
"""
from abc import ABC, abstractmethod
from typing import AsyncIterator, Dict, Any, List, Optional


class AIProvider(ABC):
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Returns the canonical provider name (e.g. 'gemini', 'openai', 'openrouter', 'deepseek')."""
        pass

    @property
    @abstractmethod
    def is_configured(self) -> bool:
        """Returns True if required credentials exist."""
        pass

    @abstractmethod
    async def chat(
        self,
        messages: List[Dict[str, str]],
        system_instruction: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> Dict[str, Any]:
        """Generates a non-streaming chat completion.

        Returns:
            {
                "content": str,
                "model": str,
                "provider": str,
                "token_usage": {"prompt_tokens": int, "completion_tokens": int, "total_tokens": int}
            }
        """
        pass

    @abstractmethod
    async def stream_chat(
        self,
        messages: List[Dict[str, str]],
        system_instruction: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> AsyncIterator[str]:
        """Streams response tokens or text chunks asynchronously."""
        pass

    async def embeddings(self, text: str) -> List[float]:
        """Optional embeddings generation."""
        return []

    async def moderate(self, text: str) -> Dict[str, Any]:
        """Optional content moderation check."""
        return {"flagged": False, "categories": {}}
