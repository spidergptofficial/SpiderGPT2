"""SpiderGPT Google Gemini AI Provider Implementation."""
import json
from typing import AsyncIterator, Dict, Any, List, Optional
import httpx

from backend.app.core.config import settings
from backend.app.core.exceptions import AIProviderException
from backend.app.core.logging import logger
from backend.app.providers.ai.base import AIProvider


class GeminiProvider(AIProvider):
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model = model or settings.GEMINI_MODEL or "gemini-3.8-flash"
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"

    @property
    def provider_name(self) -> str:
        return "gemini"

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key)

    def _convert_messages(self, messages: List[Dict[str, str]], system_instruction: Optional[str] = None):
        contents = []
        for msg in messages:
            role = msg.get("role", "user")
            if role == "assistant":
                gemini_role = "model"
            else:
                gemini_role = "user"
            contents.append({
                "role": gemini_role,
                "parts": [{"text": msg.get("content", "")}],
            })

        payload: Dict[str, Any] = {"contents": contents}
        if system_instruction:
            payload["systemInstruction"] = {
                "parts": [{"text": system_instruction}]
            }
        return payload

    async def chat(
        self,
        messages: List[Dict[str, str]],
        system_instruction: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> Dict[str, Any]:
        if not self.is_configured:
            # Fallback mock response for testing when key is unconfigured
            return {
                "content": f"[Gemini Simulation] As Spider, your AI Sidekick: I received your message: '{messages[-1]['content'] if messages else ''}'. (Configure GEMINI_API_KEY for live responses)",
                "model": self.model,
                "provider": self.provider_name,
                "token_usage": {"prompt_tokens": 50, "completion_tokens": 30, "total_tokens": 80},
            }

        url = f"{self.base_url}/models/{self.model}:generateContent?key={self.api_key}"
        payload = self._convert_messages(messages, system_instruction)
        payload["generationConfig"] = {
            "temperature": temperature,
            "maxOutputTokens": max_tokens,
        }

        async with httpx.AsyncClient(timeout=45.0) as client:
            try:
                resp = await client.post(url, json=payload)
                if resp.status_code != 200:
                    logger.error("Gemini API Error (%d): %s", resp.status_code, resp.text[:200])
                    raise AIProviderException(f"Gemini API returned error {resp.status_code}", provider=self.provider_name)

                data = resp.json()
                text = ""
                candidates = data.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    text = "".join(p.get("text", "") for p in parts)

                usage_meta = data.get("usageMetadata", {})
                return {
                    "content": text or "No response generated.",
                    "model": self.model,
                    "provider": self.provider_name,
                    "token_usage": {
                        "prompt_tokens": usage_meta.get("promptTokenCount", 0),
                        "completion_tokens": usage_meta.get("candidatesTokenCount", 0),
                        "total_tokens": usage_meta.get("totalTokenCount", 0),
                    },
                }
            except httpx.RequestError as e:
                logger.error("Gemini request network failure: %s", str(e))
                raise AIProviderException(f"Gemini connection error: {str(e)}", provider=self.provider_name)

    async def stream_chat(
        self,
        messages: List[Dict[str, str]],
        system_instruction: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> AsyncIterator[str]:
        if not self.is_configured:
            # Yield simulated tokens
            simulated = f"[Gemini Simulation] Spider replying: '{messages[-1]['content'] if messages else ''}'."
            for chunk in simulated.split(" "):
                yield chunk + " "
            return

        url = f"{self.base_url}/models/{self.model}:streamGenerateContent?alt=sse&key={self.api_key}"
        payload = self._convert_messages(messages, system_instruction)
        payload["generationConfig"] = {
            "temperature": temperature,
            "maxOutputTokens": max_tokens,
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream("POST", url, json=payload) as response:
                if response.status_code != 200:
                    err_body = await response.aread()
                    logger.error("Gemini stream error %d: %s", response.status_code, err_body.decode(errors="ignore")[:200])
                    raise AIProviderException(f"Gemini stream error {response.status_code}", provider=self.provider_name)

                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:].strip()
                        if not data_str or data_str == "[DONE]":
                            continue
                        try:
                            chunk_data = json.loads(data_str)
                            candidates = chunk_data.get("candidates", [])
                            if candidates:
                                parts = candidates[0].get("content", {}).get("parts", [])
                                for p in parts:
                                    t = p.get("text", "")
                                    if t:
                                        yield t
                        except Exception:
                            continue
