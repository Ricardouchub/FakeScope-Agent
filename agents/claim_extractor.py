from __future__ import annotations

import json
import re
import uuid
from typing import Dict, List

from services.deepseek import DeepSeekClient, DeepSeekMessage
from agents.types import Claim, FakeScopeState

LANGUAGE_NAME = {"es": "Spanish", "en": "English"}

CLAIM_EXTRACTION_PROMPT = """
You are an expert fact-checking assistant. The article is written in {language_name}.
Extract atomic, checkable claims from the provided article and respond with JSON containing a list named "claims".
Each claim must include:
- text: concise verbatim wording in {language_name}
- language: the ISO-639-1 code "{language_code}"
- entities: key entities mentioned
Provide ONLY valid JSON.
"""


class ClaimExtractor:
    def __init__(self, client: DeepSeekClient | None = None) -> None:
        self._client = client or DeepSeekClient()

    async def _call_deepseek(self, article: str, language: str) -> List[Claim]:
        language_name = LANGUAGE_NAME.get(language, "Spanish")
        prompt = CLAIM_EXTRACTION_PROMPT.format(language_name=language_name, language_code=language)
        messages = [
            DeepSeekMessage(role="system", content="You extract factual claims."),
            DeepSeekMessage(role="user", content=prompt + f"\n\nARTICLE:\n{article}"),
        ]
        response = await self._client.chat(messages, response_format={"type": "json_object"})
        data = json.loads(response.content)
        claims_payload = data.get("claims", [])
        claims: List[Claim] = []
        for entry in claims_payload:
            identifier = entry.get("id") or str(uuid.uuid4())
            claims.append(
                Claim(
                    identifier=identifier,
                    text=entry.get("text", "").strip(),
                    language=entry.get("language", language),
                    entities=[entity.strip() for entity in entry.get("entities", []) if entity],
                )
            )
        return claims

    def _fallback_split(self, article: str, language: str) -> List[Claim]:
        sentences = re.split(r"(?<=[.!?])\s+", article)
        claims: List[Claim] = []
        for idx, sentence in enumerate(sentences):
            snippet = sentence.strip()
            if len(snippet.split()) < 6:
                continue
            identifier = f"claim-{idx+1}"
            claims.append(Claim(identifier=identifier, text=snippet, language=language, entities=[]))
        return claims

    async def run(self, state: FakeScopeState) -> Dict[str, List[Claim]]:
        article = state.get("normalized_text", "")
        language = state.get("language", "es")
        if not article:
            return {"claims": []}

        if self._client.enabled:
            try:
                claims = await self._call_deepseek(article, language)
            except Exception:
                claims = self._fallback_split(article, language)
        else:
            claims = self._fallback_split(article, language)

        for claim in claims:
            claim.language = language
        return {"claims": claims}


__all__ = ["ClaimExtractor"]
