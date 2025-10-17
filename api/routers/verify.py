from __future__ import annotations

from typing import Dict, List

from fastapi import APIRouter, HTTPException, status

from agents.pipeline import FakeScopePipeline
from agents.types import Claim, StanceAssessment, VerificationTask
from api.schemas import (
    ClaimSchema,
    EvidenceSchema,
    VerificationRequest,
    VerificationResponse,
    VerdictSchema,
)

router = APIRouter(prefix="/verify", tags=["verify"])
_pipeline = FakeScopePipeline()


def _map_claim(claim: Claim, assessments: List[StanceAssessment] | None) -> ClaimSchema:
    stance_lookup: Dict[str, StanceAssessment] = {}
    for assessment in assessments or []:
        if assessment.evidence.url:
            stance_lookup[assessment.evidence.url] = assessment

    evidence_payload = []
    for evidence in claim.evidences:
        stance = stance_lookup.get(evidence.url)
        evidence_payload.append(
            EvidenceSchema(
                source=evidence.source,
                title=evidence.title,
                url=evidence.url,
                snippet=evidence.snippet,
                stance=stance.label if stance else None,
                confidence=stance.confidence if stance else None,
            )
        )
    return ClaimSchema(
        identifier=claim.identifier,
        text=claim.text,
        stance=claim.stance,
        confidence=claim.confidence,
        evidences=evidence_payload,
    )


@router.post("", response_model=VerificationResponse)
async def verify(request: VerificationRequest) -> VerificationResponse:
    task = VerificationTask(
        input_text=request.input.text,
        url=str(request.input.url) if request.input.url else None,
        language=request.input.language,
    )
    try:
        result = await _pipeline.ainvoke(task)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc

    claims = result.get("claims", [])
    stance_results = result.get("stance_results", {})
    verdict = result.get("verdict")
    if verdict is None:
        raise HTTPException(status_code=500, detail="Pipeline did not return a verdict")
    report = result.get("report", "")

    claim_payload = [_map_claim(claim, stance_results.get(claim.identifier)) for claim in claims]
    response = VerificationResponse(
        verdict=VerdictSchema(label=verdict.label, confidence=verdict.confidence),
        summary=report,
        claims=claim_payload,
    )
    return response


__all__ = ["router"]
