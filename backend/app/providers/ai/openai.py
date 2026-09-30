"""SpiderGPT OpenAI AI Provider Implementation."""
import json
from typing import AsyncIterator, Dict, Any, List, Optional
import httpx

from backend.app.core.config import settings
from backend.app.core.exceptions import AIProviderException
from backend.app.core.logging import logger
from backend.app.providers.ai.base import AIProvider


class OpenAIProvider(AIProvider):
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        base_url: str = "https://api.openai.com/v1",
        custom_provider_name: str = "openai",
    ):
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.model = model or settings.OPENAI_MODEL or "gpt-4o-mini"
        self.base_url = base_url
        self._name = custom_provider_name

    @property
    def provider_name(self) -> str:
        return self._name

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key)

    def _prepare_payload(
        self,
        messages: List[Dict[str, str]],
        system_instruction: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        stream: bool = False,
    ) -> Dict[str, Any]:
        formatted_msgs = []
        if system_instruction:
            formatted_msgs.append({"role": "system", "content": system_instruction})
        for m in messages:
            formatted_msgs.append({"role": m.get("role", "user"), "content": m.get("content", "")})

        return {
            "model": self.model,
            "messages": formatted_msgs,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": stream,
        }

    async def chat(
        self,
        messages: List[Dict[str, str]],
        system_instruction: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> Dict[str, Any]:
        if not self.is_configured:
            return {
                "content": f"[{self._name.title()} Simulation] Spider Sidekick: Processed your query: '{messages[-1]['content'] if messages else ''}'. (Configure API key for live calls)",
                "model": self.model,
                "provider": self.provider_name,
                "token_usage": {"prompt_tokens": 40, "completion_tokens": 25, "total_tokens": 65},
            }

        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = self._prepare_payload(messages, system_instruction, temperature, max_tokens, stream=False)

        async with httpx.AsyncClient(timeout=45.0) as client:
            try:
                resp = await client.post(url, headers=headers, json=payload)
                if resp.status_code != 200:
                    logger.error("%s API error (%d): %s", self._name, resp.status_code, resp.text[:200])
                    raise AIProviderException(f"{self._name} returned status {resp.status_code}", provider=self.provider_name)

                data = resp.json()
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                usage = data.get("usage", {})
                return {
                    "content": content or "No response generated.",
                    "model": data.get("model", self.model),
                    "provider": self.provider_name,
                    "token_usage": {
                        "prompt_tokens": usage.get("prompt_tokens", 0),
                        "completion_tokens": usage.get("completion_tokens", 0),
                        "total_tokens": usage.get("total_tokens", 0),
                    },
                }
            except httpx.RequestError as e:
                logger.error("%s network request failure: %s", self._name, str(e))
                raise AIProviderException(f"{self._name} connection error: {str(e)}", provider=self.provider_name)

    async def stream_chat(
        self,
        messages: List[Dict[str, str]],
        system_instruction: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> AsyncIterator[str]:
        if not self.is_configured:
            simulated = f"[{self._name.title()} Simulation] Spider streaming response for: {messages[-1]['content'] if messages else ''}."
            for chunk in simulated.split(" "):
                yield chunk + " "
            return

        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = self._prepare_payload(messages, system_instruction, temperature, max_tokens, stream=True)

        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream("POST", url, headers=headers, json=payload) as response:
                if response.status_code != 200:
                    err_body = await response.aread()
                    logger.error("%s stream error (%d): %s", self._name, response.status_code, err_body.decode(errors="ignore")[:200])
                    raise AIProviderException(f"{self._name} stream error {response.status_code}", provider=self.provider_name)

                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        raw_data = line[6:].strip()
                        if raw_data == "[DONE]":
                            break
                        try:
                            parsed = json.loads(raw_data)
                            delta = parsed.get("choices", [{}])[0].get("delta", {}).get("content", "")
                            if delta:
                                yield delta
                        except Exception:
                            continue
