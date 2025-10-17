from __future__ import annotations

import argparse
import asyncio
from textwrap import indent

from agents.pipeline import FakeScopePipeline
from agents.types import StanceLabel, VerificationTask


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run FakeScope pipeline on plain text or a URL and print the fact-checking report.",
    )
    parser.add_argument("--url", type=str, help="URL of the article to verify", default=None)
    parser.add_argument("--text", type=str, help="Raw text or claim to verify", default=None)
    parser.add_argument(
        "--language",
        type=str,
        default="auto",
        help="Language code for the input (auto for detection)",
    )
    return parser


def _render(result: dict) -> str:
    verdict = result.get("verdict")
    claims = result.get("claims", [])
    report = result.get("report", "")

    lines = []
    if verdict:
        lines.append("=== Verdict ===")
        lines.append(f"Label     : {verdict.label.value.upper()}")
        lines.append(f"Confidence: {verdict.confidence:.2f}")
        lines.append("")
    if report:
        lines.append("=== Report ===")
        lines.append(report.strip())
        lines.append("")
    if claims:
        lines.append("=== Claims ===")
        for idx, claim in enumerate(claims, start=1):
            lines.append(f"Claim {idx}: {claim.text}")
            stance = claim.stance.value if isinstance(claim.stance, StanceLabel) else str(claim.stance)
            confidence = claim.confidence if claim.confidence is not None else 0.0
            lines.append(f"  Stance     : {stance}")
            lines.append(f"  Confidence : {confidence:.2f}")
            if claim.evidences:
                lines.append("  Evidence:")
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
    output = _render(result)
    print(output)


if __name__ == "__main__":
    main()
