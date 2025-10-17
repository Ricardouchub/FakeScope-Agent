from __future__ import annotations

import math
from typing import Iterable, List

from agents.types import Claim, Evidence


class HybridReranker:
    """Simple hybrid reranker placeholder combining lexical and score cues."""

    def __init__(self, top_k: int = 5) -> None:
        self._top_k = top_k

    def _bm25_like(self, query: str, text: str) -> float:
        query_terms = query.lower().split()
        doc_terms = text.lower().split()
        if not doc_terms:
            return 0.0
        score = 0.0
        for term in query_terms:
            tf = doc_terms.count(term)
            if tf == 0:
                continue
            score += math.log(1 + tf)
        return score

    def rerank(self, claim: Claim, evidences: Iterable[Evidence]) -> List[Evidence]:
        scored: List[tuple[float, Evidence]] = []
        query = claim.text
        for evidence in evidences:
            lexical = self._bm25_like(query, evidence.snippet)
            hybrid_score = lexical
            if evidence.score is not None:
                hybrid_score += evidence.score
            scored.append((hybrid_score, evidence))
        scored.sort(key=lambda item: item[0], reverse=True)
        return [ev for _, ev in scored[: self._top_k]]


__all__ = ["HybridReranker"]
