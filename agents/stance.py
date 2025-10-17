from __future__ import annotations

import os
from typing import Dict, Iterable, List, Optional

import numpy as np
from loguru import logger

from agents.types import Claim, Evidence, FakeScopeState, StanceAssessment, StanceLabel

try:  # optional heavy import
    from transformers import AutoModelForSequenceClassification, AutoTokenizer
    import torch
except Exception:  # pragma: no cover
    AutoModelForSequenceClassification = None  # type: ignore
    AutoTokenizer = None  # type: ignore
    torch = None  # type: ignore


MODEL_NAME = "MoritzLaurer/mDeBERTa-v3-base-mnli-xnli"


def _env_flag(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.lower() in {"1", "true", "yes", "on"}


class StanceAnalyzer:
    def __init__(self, model_name: str = MODEL_NAME, threshold: float = 0.5, load_model: Optional[bool] = None) -> None:
        self._model_name = model_name
        self._threshold = threshold
        env_desired = _env_flag("FAKESCOPE_LOAD_STANCE_MODEL", default=False)
        desired = load_model if load_model is not None else env_desired
        self._use_model = bool(desired and AutoTokenizer and AutoModelForSequenceClassification)
        self._tokenizer = None
        self._model = None
        if self._use_model:
            try:
                self._tokenizer = AutoTokenizer.from_pretrained(model_name)
                self._model = AutoModelForSequenceClassification.from_pretrained(model_name)
                if torch and torch.cuda.is_available():
                    self._model.to("cuda")
            except Exception as exc:  # pragma: no cover - weight download failure
                logger.debug("Failed to load stance model: %s", exc)
                self._tokenizer = None
                self._model = None
                self._use_model = False

    def _predict_with_model(self, claim: Claim, evidence: Evidence) -> Optional[StanceAssessment]:
        if not self._use_model or not self._model or not self._tokenizer:
            return None
        if not claim.text or not evidence.snippet:
            return None
        encoded = self._tokenizer(
            claim.text,
            evidence.snippet,
            return_tensors="pt",
            truncation=True,
            padding=True,
            max_length=512,
        )
        if torch and torch.cuda.is_available():
            encoded = {k: v.to(self._model.device) for k, v in encoded.items()}
        with torch.no_grad():
            logits = self._model(**encoded).logits
        probs = torch.softmax(logits, dim=-1).cpu().numpy()[0]
        labels = self._model.config.id2label
        label_idx = int(np.argmax(probs))
        label_name = labels[label_idx].lower()
        map_label = self._map_label(label_name)
        confidence = float(probs[label_idx])
        return StanceAssessment(
            claim_id=claim.identifier,
            evidence=evidence,
            label=map_label,
            confidence=confidence,
        )

    def _map_label(self, name: str) -> StanceLabel:
        if "entail" in name or "support" in name:
            return StanceLabel.SUPPORTS
        if "contrad" in name or "refute" in name:
            return StanceLabel.REFUTES
        if "neutral" in name or "unknown" in name:
            return StanceLabel.UNKNOWN
        return StanceLabel.NEUTRAL

    def _heuristic(self, claim: Claim, evidence: Evidence) -> StanceAssessment:
        snippet = evidence.snippet.lower()
        claim_text = claim.text.lower()
        if any(term in snippet for term in claim_text.split()[:3]):
            label = StanceLabel.SUPPORTS
            confidence = 0.35
        else:
            label = StanceLabel.UNKNOWN
            confidence = 0.2
        return StanceAssessment(
            claim_id=claim.identifier,
            evidence=evidence,
            label=label,
            confidence=confidence,
        )

    def analyze(self, claim: Claim, evidences: Iterable[Evidence]) -> List[StanceAssessment]:
        results: List[StanceAssessment] = []
        for evidence in evidences:
            assessment = self._predict_with_model(claim, evidence)
            if assessment is None:
                assessment = self._heuristic(claim, evidence)
            results.append(assessment)
        return results

    async def run(self, state: FakeScopeState) -> Dict[str, Dict[str, List[StanceAssessment]]]:
        stance_results: Dict[str, List[StanceAssessment]] = {}
        updated_claims: List[Claim] = []
        for claim in state.get("claims", []):
            assessments = self.analyze(claim, claim.evidences)
            stance_results[claim.identifier] = assessments
            if assessments:
                # pick the most confident label
                best = max(assessments, key=lambda item: item.confidence)
                claim = Claim(
                    identifier=claim.identifier,
                    text=claim.text,
                    language=claim.language,
                    entities=claim.entities,
                    queries=claim.queries,
                    evidences=claim.evidences,
                    stance=best.label,
                    confidence=best.confidence,
                    metadata=claim.metadata,
                )
            updated_claims.append(claim)
        return {
            "claims": updated_claims,
            "stance_results": stance_results,
        }


__all__ = ["StanceAnalyzer"]
