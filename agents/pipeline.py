from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from typing import Any, Dict, List

from langgraph.graph import END, START, StateGraph

from agents.aggregate import VerdictAggregator
from agents.claim_extractor import ClaimExtractor
from agents.intake import IntakeAgent
from agents.query_planner import QueryPlanner
from agents.report_writer import ReportWriter
from agents.retrieval import EvidenceRetriever
from agents.rerank import HybridReranker
from agents.stance import StanceAnalyzer
from agents.types import Claim, FakeScopeState, VerificationTask
from services.telemetry import get_telemetry


class FakeScopePipeline:
    def __init__(self) -> None:
        self.intake = IntakeAgent()
        self.claim_extractor = ClaimExtractor()
        self.query_planner = QueryPlanner()
        self.retriever = EvidenceRetriever()
        self.reranker = HybridReranker()
        self.stance_analyzer = StanceAnalyzer()
        self.aggregator = VerdictAggregator()
        self.report_writer = ReportWriter()
        self.telemetry = get_telemetry()

        builder = StateGraph(FakeScopeState)
        builder.add_node("intake", self.intake.run)
        builder.add_node("claims", self.claim_extractor.run)
        builder.add_node("planner", self.query_planner.run)
        builder.add_node("retriever", self.retriever.run)
        builder.add_node("rerank", self._rerank_node)
        builder.add_node("stance", self.stance_analyzer.run)
        builder.add_node("aggregate", self.aggregator.run)
        builder.add_node("report", self.report_writer.run)

        builder.add_edge(START, "intake")
        builder.add_edge("intake", "claims")
        builder.add_edge("claims", "planner")
        builder.add_edge("planner", "retriever")
        builder.add_edge("retriever", "rerank")
        builder.add_edge("rerank", "stance")
        builder.add_edge("stance", "aggregate")
        builder.add_edge("aggregate", "report")
        builder.add_edge("report", END)

        self.graph = builder.compile()

    async def _rerank_node(self, state: FakeScopeState) -> Dict[str, Any]:
        claims: List[Claim] = []
        evidences = state.get("evidences", {})
        for claim in state.get("claims", []):
            ranked = self.reranker.rerank(claim, evidences.get(claim.identifier, claim.evidences))
            claims.append(
                Claim(
                    identifier=claim.identifier,
                    text=claim.text,
                    language=claim.language,
                    entities=claim.entities,
                    queries=claim.queries,
                    evidences=ranked,
                    stance=claim.stance,
                    confidence=claim.confidence,
                    metadata=claim.metadata,
                )
            )
            evidences[claim.identifier] = ranked
        return {"claims": claims, "evidences": evidences}

    async def ainvoke(self, task: VerificationTask) -> Dict[str, Any]:
        state: FakeScopeState = {
            "task": task,
            "run_metadata": {
                "started_at": datetime.now(UTC).isoformat(),
            },
        }
        trace = self.telemetry.start_trace(
            name="fakescope_pipeline",
            input={
                "url": task.url,
                "text_preview": (task.input_text[:300] if task.input_text else None),
                "language": task.language,
            },
            metadata=state["run_metadata"],
        )
        if trace:
            state["run_metadata"]["trace_id"] = getattr(trace, "id", None)
        try:
            result = await self.graph.ainvoke(state)
            verdict = result.get("verdict")
            summary = {
                "verdict": verdict.label.value if verdict else None,
                "confidence": verdict.confidence if verdict else None,
                "claims": [claim.text for claim in result.get("claims", [])],
            }
            self.telemetry.log_event(trace, "verdict", output=summary)
            self.telemetry.finish_trace(trace, output=summary)
            return result
        except Exception as exc:  # pragma: no cover - telemetry only
            self.telemetry.finish_trace(trace, error=exc)
            raise
        finally:
            self.telemetry.flush()

    def invoke(self, task: VerificationTask) -> Dict[str, Any]:
        return asyncio.run(self.ainvoke(task))


__all__ = ["FakeScopePipeline"]
