from __future__ import annotations

import asyncio
from typing import Any, Dict, Iterable, List, Optional

import httpx
from pydantic import BaseModel, Field

from config.settings import DeepSeekConfig, get_settings


class DeepSeekMessage(BaseModel):
    role: str
    content: str


class DeepSeekResponse(BaseModel):
    id: str
    model: str
    content: str
    usage: Dict[str, Any] | None = Field(default=None)


class DeepSeekClient:
    """Lightweight HTTP client to interact with DeepSeek chat/completions API."""

    def __init__(self, config: DeepSeekConfig | None = None) -> None:
        self._config = config or get_settings().deepseek
        self._timeout = httpx.Timeout(self._config.timeout_seconds)

    @property
    def enabled(self) -> bool:
        return bool(self._config.api_key)

    def _build_headers(self) -> Dict[str, str]:
        if not self._config.api_key:
            raise RuntimeError("DeepSeek API key is not configured")
        return {
            "Authorization": f"Bearer {self._config.api_key}",
            "Content-Type": "application/json",
        }

    async def chat(
        self,
        messages: Iterable[DeepSeekMessage],
        model: Optional[str] = None,
        temperature: float = 0.2,
        response_format: Optional[Dict[str, Any]] = None,
    ) -> DeepSeekResponse:
        if not self.enabled:
            raise RuntimeError("DeepSeek client is disabled because no API key is set")

        payload: Dict[str, Any] = {
            "model": model or self._config.model,
            "messages": [message.model_dump() for message in messages],
            "temperature": temperature,
        }
        if response_format:
            payload["response_format"] = response_format

        async with httpx.AsyncClient(base_url=self._config.api_base, timeout=self._timeout) as client:
            response = await client.post("/chat/completions", json=payload, headers=self._build_headers())
            response.raise_for_status()
            data = response.json()

        content = data["choices"][0]["message"]["content"].strip()
        return DeepSeekResponse(id=data.get("id", ""), model=data.get("model", ""), content=content, usage=data.get("usage"))

    def chat_blocking(
        self,
        messages: Iterable[DeepSeekMessage],
        model: Optional[str] = None,
        temperature: float = 0.2,
        response_format: Optional[Dict[str, Any]] = None,
    ) -> DeepSeekResponse:
        """Run an async chat request from sync context."""

        return asyncio.run(self.chat(messages, model=model, temperature=temperature, response_format=response_format))


__all__ = ["DeepSeekClient", "DeepSeekMessage", "DeepSeekResponse"]
