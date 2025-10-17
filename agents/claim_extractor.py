from __future__ import annotations

import json
import re
import uuid
from typing import Dict, List

from services.deepseek import DeepSeekClient, DeepSeekMessage
from agents.types import Claim, FakeScopeState


CLAIM_EXTRACTION_PROMPT = """
You are an expert fact-checking assistant. Extract atomic, checkable claims from the provided article.
Respond with JSON containing a list named "claims" where each item has:
- text: the verbatim claim text (concise)
- language: detected language code (ISO-639-1)
- entities: key entities mentioned
Provide ONLY valid JSON.
"""


class ClaimExtractor:
    def __init__(self, client: DeepSeekClient | None = None) -> None:
        self._client = client or DeepSeekClient()

    async def _call_deepseek(self, article: str) -> List[Claim]:
        messages = [
            DeepSeekMessage(role="system", content="You extract factual claims."),
            DeepSeekMessage(role="user", content=CLAIM_EXTRACTION_PROMPT + f"\n\nARTICLE:\n{article}"),
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
                    language=entry.get("language", "auto"),
                    entities=[entity.strip() for entity in entry.get("entities", []) if entity],
                )
            )
        return claims

    def _fallback_split(self, article: str) -> List[Claim]:
        sentences = re.split(r"(?<=[.!?])\s+", article)
        claims: List[Claim] = []
        for idx, sentence in enumerate(sentences):
            snippet = sentence.strip()
            if len(snippet.split()) < 6:
                continue
            identifier = f"claim-{idx+1}"
            claims.append(Claim(identifier=identifier, text=snippet, entities=[]))
        return claims

    async def run(self, state: FakeScopeState) -> Dict[str, List[Claim]]:
        article = state.get("normalized_text", "")
        if not article:
            return {"claims": []}

        if self._client.enabled:
            try:
                claims = await self._call_deepseek(article)
            except Exception:
                claims = self._fallback_split(article)
        else:
            claims = self._fallback_split(article)

        language = state.get("language", "auto")
        for claim in claims:
            if claim.language == "auto" and language:
                claim.language = language
        return {"claims": claims}


__all__ = ["ClaimExtractor"]
