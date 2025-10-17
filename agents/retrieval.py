from __future__ import annotations

import asyncio
from dataclasses import replace
from typing import Dict, Iterable, List

import httpx
from loguru import logger

from agents.types import Claim, Evidence, FakeScopeState
from config.settings import RetrievalConfig, get_settings

try:  # optional tavily import
    from tavily import TavilyClient
except Exception:  # pragma: no cover
    TavilyClient = None  # type: ignore

try:  # optional duckduckgo import
    from ddgs import DDGS
except Exception:  # pragma: no cover
    DDGS = None  # type: ignore


class EvidenceRetriever:
    def __init__(self, config: RetrievalConfig | None = None) -> None:
        self._config = config or get_settings().retrieval
        self._tavily = None
        if self._config.search_provider == "tavily" and TavilyClient and self._config.tavily_api_key:
            self._tavily = TavilyClient(api_key=self._config.tavily_api_key)
        self._http_timeout = httpx.Timeout(20)

    async def _search_wikipedia(self, query: str, language: str) -> List[Evidence]:
        try:
            import wikipedia  # type: ignore

            wikipedia.set_lang("es" if language == "es" else language if language not in ("auto", "unknown") else "en")
            results = wikipedia.search(query, results=5)
            evidences: List[Evidence] = []
            for title in results:
                try:
                    page = wikipedia.page(title, auto_suggest=False)
                    evidences.append(
                        Evidence(
                            source="wikipedia",
                            title=page.title,
                            url=page.url,
                            snippet=page.summary[:500],
                        )
                    )
                except Exception:
                    continue
            return evidences
        except Exception as exc:  # pragma: no cover - offline fallback
            logger.debug("Wikipedia search failed: %s", exc)
            return []

    async def _search_tavily(self, query: str) -> List[Evidence]:
        if not self._tavily:
            return []
        loop = asyncio.get_running_loop()
        data = await loop.run_in_executor(None, self._tavily.search, query, "advanced")
        evidences: List[Evidence] = []
        for result in data.get("results", []):
            evidences.append(
                Evidence(
                    source=result.get("source", "web"),
                    title=result.get("title", ""),
                    url=result.get("url", ""),
                    snippet=result.get("content", ""),
                    score=result.get("score"),
                    metadata={"published_date": result.get("published_date")},
                )
            )
        return evidences

    async def _search_duckduckgo(self, query: str) -> List[Evidence]:
        if DDGS is None:
            return []

        def _run_search() -> List[dict]:
            with DDGS() as ddgs:
                return list(ddgs.text(query, max_results=self._config.max_documents))

        loop = asyncio.get_running_loop()
        try:
            results = await loop.run_in_executor(None, _run_search)
        except Exception as exc:  # pragma: no cover - network failure
            logger.debug("DuckDuckGo search failed: %s", exc)
            return []

        evidences: List[Evidence] = []
        for item in results:
            evidences.append(
                Evidence(
                    source="duckduckgo",
                    title=item.get("title", ""),
                    url=item.get("href", ""),
                    snippet=item.get("body", ""),
                )
            )
        return evidences

    async def _retrieve_for_query(self, claim: Claim, query: str) -> List[Evidence]:
        language = claim.language or "auto"
        gathered: List[Evidence] = []
        wiki = await self._search_wikipedia(query, language)
        gathered.extend(wiki)
        provider = self._config.search_provider
        if provider == "tavily":
            gathered.extend(await self._search_tavily(query))
        elif provider == "duckduckgo":
            gathered.extend(await self._search_duckduckgo(query))
        elif provider == "bing":  # kept for backwards compatibility
            gathered.extend(await self._search_bing(query))
        return gathered[: self._config.max_documents]

    async def _search_bing(self, query: str) -> List[Evidence]:  # pragma: no cover - legacy path
        if not self._config.bing_api_key:
            return []
        endpoint = "https://api.bing.microsoft.com/v7.0/search"
        headers = {"Ocp-Apim-Subscription-Key": self._config.bing_api_key}
        params = {"q": query, "textDecorations": False, "textFormat": "Raw", "mkt": "en-US"}
        async with httpx.AsyncClient(timeout=self._http_timeout) as client:
            response = await client.get(endpoint, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
        evidences: List[Evidence] = []
        for item in data.get("webPages", {}).get("value", []):
            evidences.append(
                Evidence(
                    source="bing",
                    title=item.get("name", ""),
                    url=item.get("url", ""),
                    snippet=item.get("snippet", ""),
                )
            )
        return evidences

    def _merge(self, existing: Iterable[Evidence], new_items: Iterable[Evidence]) -> List[Evidence]:
        combined: Dict[str, Evidence] = {e.url: e for e in existing if e.url}
        for item in new_items:
            if item.url in combined:
                continue
            combined[item.url] = item
        return list(combined.values())

    async def run(self, state: FakeScopeState) -> Dict[str, Dict[str, List[Evidence]]]:
        plan = state.get("plan", {})
        claim_lookup = {claim.identifier: claim for claim in state.get("claims", [])}
        evidences: Dict[str, List[Evidence]] = {claim_id: [] for claim_id in plan.keys()}

        for claim_id, queries in plan.items():
            claim = claim_lookup.get(claim_id)
            if not claim:
                continue
            for query in queries:
                try:
                    results = await self._retrieve_for_query(claim, query)
                except Exception as exc:
                    logger.debug("Retrieval failed for query '%s': %s", query, exc)
                    results = []
                evidences[claim_id] = self._merge(evidences.get(claim_id, []), results)

        updated_claims: List[Claim] = []
        for claim in state.get("claims", []):
            updated_claims.append(replace(claim, evidences=evidences.get(claim.identifier, [])))

        return {
            "claims": updated_claims,
            "evidences": evidences,
        }


__all__ = ["EvidenceRetriever"]
