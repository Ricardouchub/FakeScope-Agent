from __future__ import annotations

import asyncio
import re
from typing import Any, Dict

import httpx
from bs4 import BeautifulSoup
from langdetect import DetectorFactory, detect
from loguru import logger

from agents.types import FakeScopeState, VerificationTask

DetectorFactory.seed = 42


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
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    def _detect_language(self, text: str, fallback: str = "auto") -> str:
        try:
            return detect(text)
        except Exception:
            return fallback

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

        if isinstance(task, VerificationTask):
            load_task = task
        else:
            load_task = VerificationTask(**task)  # type: ignore[arg-type]

        try:
            text = await self._load_text(load_task)
        except Exception as exc:
            logger.exception("Failed to load input text: %s", exc)
            text = load_task.input_text or ""

        language = load_task.language if load_task.language != "auto" else self._detect_language(text)
        return {
            "normalized_text": text,
            "language": language,
        }

    def run_blocking(self, state: FakeScopeState) -> Dict[str, Any]:
        return asyncio.run(self.run(state))


__all__ = ["IntakeAgent"]
