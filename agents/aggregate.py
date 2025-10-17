from __future__ import annotations

from collections import Counter
from statistics import mean
from typing import Dict, List

from agents.types import FakeScopeState, StanceAssessment, StanceLabel, Verdict


class VerdictAggregator:
    def _aggregate_claims(self, stance_results: Dict[str, List[StanceAssessment]]) -> Verdict:
        labels: List[StanceLabel] = []
        confidences: List[float] = []
        for assessments in stance_results.values():
            for assessment in assessments:
                if assessment.label == StanceLabel.UNKNOWN:
                    continue
                labels.append(assessment.label)
                confidences.append(assessment.confidence)
        if not labels:
            return Verdict(label=StanceLabel.UNKNOWN, confidence=0.0, details={"rationale": "Insufficient evidence"})

        label_counts = Counter(labels)
        dominant_label, dominant_count = label_counts.most_common(1)[0]
        distinct_labels = len(label_counts)
        avg_confidence = mean(confidences) if confidences else 0.0

        verdict_label = dominant_label if distinct_labels == 1 else StanceLabel.MIXED
        details = {
            "label_distribution": {label.value: count for label, count in label_counts.items()},
            "avg_confidence": avg_confidence,
        }
        return Verdict(label=verdict_label, confidence=float(avg_confidence), details=details)

    async def run(self, state: FakeScopeState) -> Dict[str, Verdict]:
        stance_results = state.get("stance_results", {})
        verdict = self._aggregate_claims(stance_results)
        return {"verdict": verdict}


__all__ = ["VerdictAggregator"]
