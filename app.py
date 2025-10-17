from __future__ import annotations

import argparse
import asyncio
from textwrap import indent

from agents.pipeline import FakeScopePipeline
from agents.types import StanceLabel, VerificationTask

LANGUAGE_LABELS = {"es": "Espa?ol", "en": "English"}

LANG_STRINGS = {
    "es": {
        "verdict": "=== Veredicto ===",
        "label": "Etiqueta",
        "confidence": "Confianza",
        "report": "=== Reporte ===",
        "claims": "=== Afirmaciones ===",
        "stance": "Postura",
        "evidence": "  Evidencia:",
    },
    "en": {
        "verdict": "=== Verdict ===",
        "label": "Label",
        "confidence": "Confidence",
        "report": "=== Report ===",
        "claims": "=== Claims ===",
        "stance": "Stance",
        "evidence": "  Evidence:",
    },
}


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run FakeScope pipeline on plain text or a URL and print the fact-checking report.",
    )
    parser.add_argument("--url", type=str, help="URL of the article to verify", default=None)
    parser.add_argument("--text", type=str, help="Raw text or claim to verify", default=None)
    parser.add_argument(
        "--language",
        type=str,
        choices=["es", "en"],
        default="en",
        help="Language code for the input and the generated output (es or en)",
    )
    return parser


def _render(result: dict, language: str) -> str:
    strings = LANG_STRINGS.get(language, LANG_STRINGS["en"])
    verdict = result.get("verdict")
    claims = result.get("claims", [])
    report = result.get("report", "")

    lines = []
    if verdict:
        lines.append(strings["verdict"])
        lines.append(f"{strings['label']:<10}: {verdict.label.value.upper()}")
        lines.append(f"{strings['confidence']:<10}: {verdict.confidence:.2f}")
        lines.append("")
    if report:
        lines.append(strings["report"])
        lines.append(report.strip())
        lines.append("")
    if claims:
        lines.append(strings["claims"])
        for idx, claim in enumerate(claims, start=1):
            lines.append(f"Claim {idx}: {claim.text}")
            stance = claim.stance.value if isinstance(claim.stance, StanceLabel) else str(claim.stance)
            confidence = claim.confidence if claim.confidence is not None else 0.0
            lines.append(f"  {strings['stance']:<10}: {stance}")
            lines.append(f"  {strings['confidence']:<10}: {confidence:.2f}")
            if claim.evidences:
                lines.append(strings["evidence"])
                for evidence in claim.evidences:
                    lines.append(indent(f"- {evidence.title} ({evidence.url})", "    "))
                    snippet = evidence.snippet.strip()
                    if snippet:
                        lines.append(indent(snippet[:240] + ("..." if len(snippet) > 240 else ""), "      "))
            lines.append("")
    return "\n".join(lines)


async def _ainvoke(task: VerificationTask) -> dict:
    pipeline = FakeScopePipeline()
    return await pipeline.ainvoke(task)


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    if not args.url and not args.text:
        parser.error("Provide either --url or --text")

    task = VerificationTask(input_text=args.text, url=args.url, language=args.language)
    result = asyncio.run(_ainvoke(task))
    language = result.get("language", args.language)
    output = _render(result, language)
    print(output)


if __name__ == "__main__":
    main()
