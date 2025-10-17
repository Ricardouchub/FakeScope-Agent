from __future__ import annotations

import json
from typing import Dict, List

from agents.types import Claim, FakeScopeState, StanceLabel, Verdict
from services.deepseek import DeepSeekClient, DeepSeekMessage

REPORT_PROMPT = """
You are an analytical fact-checking assistant. Summarize the verification results, citing evidence URLs.
Structure the response in Markdown with sections for Summary, Verdict, and Supporting Evidence.
"""


def _format_confidence(value: float | None) -> str:
    return f"{value:.2f}" if value is not None else "0.00"


class ReportWriter:
    def __init__(self, client: DeepSeekClient | None = None) -> None:
        self._client = client or DeepSeekClient()

    async def _llm_report(self, claims: List[Claim], verdict: Verdict) -> str:
        claims_payload = [
            {
                "text": claim.text,
                "stance": claim.stance.value,
                "confidence": claim.confidence,
                "evidence": [
                    {"title": ev.title, "url": ev.url, "snippet": ev.snippet} for ev in claim.evidences
                ],
            }
            for claim in claims
        ]
        messages = [
            DeepSeekMessage(role="system", content="You are a meticulous fact-checking report generator."),
            DeepSeekMessage(
                role="user",
                content=REPORT_PROMPT
                + "\n\nDATA:\n"
                + json.dumps({"verdict": verdict.label.value, "confidence": verdict.confidence, "claims": claims_payload}),
            ),
        ]
        response = await self._client.chat(messages)
        return response.content

    def _fallback(self, claims: List[Claim], verdict: Verdict) -> str:
        lines = ["# FakeScope Report", "## Verdict", f"- Overall: **{verdict.label.value.upper()}** ({_format_confidence(verdict.confidence)})"]
        lines.append("## Claims")
        for claim in claims:
            lines.append(f"- **Claim:** {claim.text}")
            lines.append(f"  - Verdict: {claim.stance.value} ({_format_confidence(claim.confidence)})")
            if claim.evidences:
                lines.append("  - Evidence:")
                for evidence in claim.evidences[:3]:
                    lines.append(f"    - [{evidence.title}]({evidence.url})")
        return "\n".join(lines)

    async def run(self, state: FakeScopeState) -> Dict[str, str]:
        claims = state.get("claims", [])
        verdict = state.get("verdict") or Verdict(label=StanceLabel.UNKNOWN, confidence=0.0)
        if self._client.enabled:
            try:
                report = await self._llm_report(claims, verdict)
            except Exception:
                report = self._fallback(claims, verdict)
        else:
            report = self._fallback(claims, verdict)
        return {"report": report}


__all__ = ["ReportWriter"]
