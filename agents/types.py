from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, TypedDict


class StanceLabel(str, Enum):
    SUPPORTS = "supports"
    REFUTES = "refutes"
    NEUTRAL = "neutral"
    UNKNOWN = "unknown"
    MIXED = "mixed"


@dataclass
class Evidence:
    source: str
    title: str
    url: str
    snippet: str
    score: float | None = None
    published_at: str | None = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Claim:
    identifier: str
    text: str
    language: str = "es"
    entities: List[str] = field(default_factory=list)
    queries: List[str] = field(default_factory=list)
    evidences: List[Evidence] = field(default_factory=list)
    stance: StanceLabel = StanceLabel.UNKNOWN
    confidence: float | None = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class StanceAssessment:
    claim_id: str
    evidence: Evidence
    label: StanceLabel
    confidence: float
    rationale: str | None = None


@dataclass
class Verdict:
    label: StanceLabel
    confidence: float
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class VerificationTask:
    input_text: str | None = None
    url: str | None = None
    language: str = "es"

    def has_url(self) -> bool:
        return bool(self.url)

    def has_text(self) -> bool:
        return bool(self.input_text)


class FakeScopeState(TypedDict, total=False):
    task: VerificationTask
    normalized_text: str
    language: str
    claims: List[Claim]
    plan: Dict[str, List[str]]
    evidences: Dict[str, List[Evidence]]
    stance_results: Dict[str, List[StanceAssessment]]
    verdict: Verdict
    report: str
    run_metadata: Dict[str, Any]


__all__ = [
    "StanceLabel",
    "Evidence",
    "Claim",
    "StanceAssessment",
    "Verdict",
    "VerificationTask",
    "FakeScopeState",
]
