from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field, HttpUrl, model_validator

from agents.types import StanceLabel


class VerificationInput(BaseModel):
    text: Optional[str] = Field(default=None, description="Plain text content to verify")
    url: Optional[HttpUrl] = Field(default=None, description="URL pointing to an article")
    language: str = Field(default="auto", description="Input language (auto for detection)")

    @model_validator(mode="after")
    def validate_payload(self) -> "VerificationInput":
        if not self.text and not self.url:
            raise ValueError("Either text or url must be provided")
        return self


class EvidenceSchema(BaseModel):
    source: str
    title: str
    url: HttpUrl | str
    snippet: str
    stance: StanceLabel | None = None
    confidence: float | None = None


class ClaimSchema(BaseModel):
    id: str = Field(alias="identifier")
    text: str
    stance: StanceLabel = StanceLabel.UNKNOWN
    confidence: float | None = None
    evidences: List[EvidenceSchema] = Field(default_factory=list)

    model_config = {
        "populate_by_name": True
    }


class VerificationRequest(BaseModel):
    input: VerificationInput


class VerdictSchema(BaseModel):
    label: StanceLabel
    confidence: float


class VerificationResponse(BaseModel):
    verdict: VerdictSchema
    summary: str
    claims: List[ClaimSchema]


__all__ = [
    "VerificationInput",
    "EvidenceSchema",
    "ClaimSchema",
    "VerificationRequest",
    "VerificationResponse",
    "VerdictSchema",
]
