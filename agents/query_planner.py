from __future__ import annotations

import json
from dataclasses import replace
from typing import Dict, List

from agents.types import Claim, FakeScopeState
from services.deepseek import DeepSeekClient, DeepSeekMessage

QUERY_PLANNER_PROMPT = """
Given a factual claim, propose up to five concise web search queries that would help verify it.
Return JSON with a `queries` list containing strings ordered by usefulness.
"""


class QueryPlanner:
    def __init__(self, client: DeepSeekClient | None = None) -> None:
        self._client = client or DeepSeekClient()

    async def _plan(self, claim: Claim) -> List[str]:
        messages = [
            DeepSeekMessage(role="system", content="You create fact-checking search queries."),
            DeepSeekMessage(
                role="user",
                content=f"{QUERY_PLANNER_PROMPT}\n\nCLAIM: {claim.text}\nENTITIES: {', '.join(claim.entities) if claim.entities else 'N/A'}",
            ),
        ]
        response = await self._client.chat(messages, response_format={"type": "json_object"})
        data = json.loads(response.content)
        queries = data.get("queries", [])
        return [str(q).strip() for q in queries if str(q).strip()]

    def _fallback(self, claim: Claim) -> List[str]:
        base = claim.text[:180]
        queries = [base]
        if claim.entities:
            queries.append(" ".join(claim.entities))
        if len(base.split()) > 6:
            queries.append("verify " + base.split(" ")[0] + " facts")
        return list(dict.fromkeys(q for q in queries if q))

    async def run(self, state: FakeScopeState) -> Dict[str, List[str] | List[Claim]]:
        claims = state.get("claims", [])
        plan: Dict[str, List[str]] = {}
        updated_claims: List[Claim] = []
        for claim in claims:
            if self._client.enabled:
                try:
                    queries = await self._plan(claim)
                except Exception:
                    queries = self._fallback(claim)
            else:
                queries = self._fallback(claim)
            plan[claim.identifier] = queries
            updated_claims.append(replace(claim, queries=queries))
        return {"plan": plan, "claims": updated_claims}


__all__ = ["QueryPlanner"]
