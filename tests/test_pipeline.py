import asyncio

import pytest

from agents.pipeline import FakeScopePipeline
from agents.types import VerificationTask


@pytest.mark.asyncio
async def test_pipeline_executes_with_minimal_input(monkeypatch):
    pipeline = FakeScopePipeline()

    async def fake_retrieve_for_query(self, claim, query):
        return []

    async def fake_search_wikipedia(self, query, language):
        return []

    monkeypatch.setattr(pipeline.retriever, "_retrieve_for_query", fake_retrieve_for_query.__get__(pipeline.retriever))
    monkeypatch.setattr(pipeline.retriever, "_search_wikipedia", fake_search_wikipedia.__get__(pipeline.retriever))

    task = VerificationTask(input_text="The Eiffel Tower is located in Paris.", language="en")
    result = await pipeline.ainvoke(task)

    assert "verdict" in result
    assert result["verdict"].label.value in {"unknown", "supports", "refutes", "neutral", "mixed"}
    assert isinstance(result.get("report"), str)
