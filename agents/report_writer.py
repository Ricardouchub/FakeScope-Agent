from __future__ import annotations

import json
from typing import Dict, List

from agents.types import Claim, FakeScopeState, StanceLabel, Verdict
from services.deepseek import DeepSeekClient, DeepSeekMessage

REPORT_PROMPT = {
    "en": (
        "You are an analytical fact-checking assistant. Summarize the verification results in English, "
        "citing evidence URLs. Structure the response in Markdown with sections for Summary, Verdict, and Supporting Evidence."
    ),
    "es": (
        "Eres un asistente de verificaci?n anal?tica. Resume los resultados en espa?ol citando las URL de la evidencia. "
        "Estructura la respuesta en Markdown con secciones de Resumen, Veredicto y Evidencia de apoyo."
    ),
}

HEADINGS = {
    "en": {"report": "# FakeScope Report", "claims": "## Claims", "verdict": "## Verdict", "evidence": "  - Evidence:"},
    "es": {"report": "# Informe FakeScope", "claims": "## Afirmaciones", "verdict": "## Veredicto", "evidence": "  - Evidencia:"},
}

RESULT_LABEL = {
    "en": "Overall",
    "es": "Resultado",
}

MESSAGE_TEMPLATE = {
    "en": "- Verdict: {stance} ({confidence})",
    "es": "  - Veredicto: {stance} ({confidence})",
}


def _format_confidence(value: float | None) -> str:
    return f"{value:.2f}" if value is not None else "0.00"


class ReportWriter:
    def __init__(self, client: DeepSeekClient | None = None) -> None:
        self._client = client or DeepSeekClient()

    async def _llm_report(self, claims: List[Claim], verdict: Verdict, language: str) -> str:
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
        prompt = REPORT_PROMPT.get(language, REPORT_PROMPT["es"])
        messages = [
            DeepSeekMessage(role="system", content="You are a meticulous fact-checking report generator."),
            DeepSeekMessage(
                role="user",
                content=prompt
                + "\n\nDATA:\n"
                + json.dumps({"verdict": verdict.label.value, "confidence": verdict.confidence, "claims": claims_payload}),
            ),
        ]
        response = await self._client.chat(messages)
        return response.content

    def _fallback(self, claims: List[Claim], verdict: Verdict, language: str) -> str:
        headings = HEADINGS.get(language, HEADINGS["es"])
        result_label = RESULT_LABEL.get(language, RESULT_LABEL["es"])
        lines = [
            headings["report"],
            headings["verdict"],
            f"- {result_label}: **{verdict.label.value.upper()}** ({_format_confidence(verdict.confidence)})",
        ]
        lines.append(headings["claims"])
        template = MESSAGE_TEMPLATE.get(language, MESSAGE_TEMPLATE["es"])
        for claim in claims:
            lines.append(f"- **{claim.text}**")
            lines.append(template.format(stance=claim.stance.value, confidence=_format_confidence(claim.confidence)))
            if claim.evidences:
                lines.append(headings["evidence"])
                for evidence in claim.evidences[:3]:
                    lines.append(f"    - [{evidence.title}]({evidence.url})")
        return "\n".join(lines)

    async def run(self, state: FakeScopeState) -> Dict[str, str]:
        claims = state.get("claims", [])
        verdict = state.get("verdict") or Verdict(label=StanceLabel.UNKNOWN, confidence=0.0)
        language = state.get("language", "es")
        if self._client.enabled:
            try:
                report = await self._llm_report(claims, verdict, language)
            except Exception:
                report = self._fallback(claims, verdict, language)
        else:
            report = self._fallback(claims, verdict, language)
        return {"report": report}


__all__ = ["ReportWriter"]
