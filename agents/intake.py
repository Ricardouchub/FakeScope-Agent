from __future__ import annotations

import asyncio
import re
from typing import Any, Dict

import httpx
from bs4 import BeautifulSoup
from loguru import logger

from agents.types import FakeScopeState, VerificationTask


class IntakeAgent:
    def __init__(self, timeout: int = 30) -> None:
        self._timeout = httpx.Timeout(timeout)

    async def _fetch_url(self, url: str) -> str:
        async with httpx.AsyncClient(timeout=self._timeout, follow_redirects=True) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.text

    def _clean_html(self, html: str) -> str:
        soup = BeautifulSoup(html, "html.parser")
        for tag in soup(["script", "style", "noscript", "header", "footer", "form", "svg"]):
            tag.decompose()
        text = soup.get_text(" ", strip=True)
        return re.sub(r"\s+", " ", text).strip()

    async def _load_text(self, task: VerificationTask) -> str:
        if task.input_text:
            return task.input_text
        if task.url:
            html = await self._fetch_url(task.url)
            return self._clean_html(html)
        return ""

    async def run(self, state: FakeScopeState) -> Dict[str, Any]:
        task = state.get("task")
        if not task:
            raise ValueError("Verification task missing from state")

        load_task = task if isinstance(task, VerificationTask) else VerificationTask(**task)  # type: ignore[arg-type]

        try:
            text = await self._load_text(load_task)
        except Exception as exc:
            logger.exception("Failed to load input text: %s", exc)
            text = load_task.input_text or ""

        language = load_task.language or "es"
        return {
            "normalized_text": text,
            "language": language,
        }

    def run_blocking(self, state: FakeScopeState) -> Dict[str, Any]:
        return asyncio.run(self.run(state))


__all__ = ["IntakeAgent"]
