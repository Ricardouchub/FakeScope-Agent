# FakeScope Agent

![Status](https://img.shields.io/badge/Status-Completed-2ECC71?logo=checkmarx&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)
![LangGraph](https://img.shields.io/badge/LangGraph-Orchestration-7E57C2?logo=chainlink&logoColor=white)
![DeepSeek](https://img.shields.io/badge/DeepSeek-LLM-8A2BE2?logo=deepnote&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-UI-FF4B4B?logo=streamlit&logoColor=white)
![LangSmith](https://img.shields.io/badge/LangSmith-Telemetry-7E57C2?logo=langchain&logoColor=white)
![ChromaDB](https://img.shields.io/badge/ChromaDB-Vector_Store-00E676?logo=sqlite&logoColor=white)
![DuckDuckGo](https://img.shields.io/badge/DuckDuckGo-Search-FF6600?logo=duckduckgo&logoColor=white)
![BGE_Embedding](https://img.shields.io/badge/BGE_Embedding-SentenceTransformers-1F6FEB?logo=huggingface&logoColor=white)

FakeScope is an AI Agent for automated news verification powered by **LangGraph** and **DeepSeek**. It extracts factual claims, retrieves supporting evidence, analyzes stance, and produces an explainable verdict. The repository includes the full pipeline, a **Streamlit interface**, and a **CLI utility** to run local verifications with optional telemetry via **LangSmith**.

<img width="800" src="img/FakeScope - App UI.png" alt="Main"/>

---

## Key Features
- End-to-end pipeline orchestration with **LangGraph**.
- Claim extraction, query planning, and hybrid evidence retrieval (Wikipedia + external search APIs).
- Stance classification using **NLI models (DeBERTa)** with heuristic fallbacks.
- Aggregated multilingual reports (English/Spanish) with optional **LangSmith telemetry**.
- **Streamlit UI** and **CLI tool** for running local verifications.

---

## Requirements
- Python 3.10+
- Optional API Keys:
  - `DEEPSEEK_API_KEY` → for DeepSeek reasoning.
  - `TAVILY_API_KEY` → for Tavily search; defaults to DuckDuckGo if missing.
  - `[langsmith]` section in `config/settings.toml` for telemetry (see below).
- Dependencies listed in `requirements.txt`.

---

## Heuristic vs NLI Mode
- **Heuristic Mode (default)** – lightweight, CPU-friendly, no large model downloads.  
  Produces faster results with moderate confidence.
- **NLI Mode** (`FAKESCOPE_LOAD_STANCE_MODEL=1`) – loads  
  `MoritzLaurer/mDeBERTa-v3-base-mnli-xnli`.  
  Offers much higher precision and calibrated confidence but is slower and resource-intensive.

---

## Verdicts and Confidence

FakeScope outputs both **global** and **per-claim** verdicts:

| Verdict | Meaning |
|----------|----------|
| `supports` | Evidence supports the claim. |
| `refutes` | Evidence contradicts the claim. |
| `neutral` | Evidence is unrelated or inconclusive. |
| `unknown` | Insufficient evidence found. |
| `mixed` | Conflicting evidence found (support + refute). |

The **confidence score (0.0–1.0)** reflects verdict strength:
- In **NLI mode**, derived from model probabilities (averaged across evidence).
- In **heuristic mode**, uses conservative fixed weights (e.g., 0.35 for support, 0.20 for unknown).

The Streamlit UI and LangSmith telemetry visualize both verdict and confidence, for example:  
**Result:** `SUPPORTS` | **Confidence:** `0.72`

---

## Quick Usage

### Streamlit UI
```bash
streamlit run ui/app.py
```
Select the interface language (`English` or `Español`), input text or a URL, and click **Verify**.  
The pipeline and report will be generated in the selected language.

### CLI
```bash
python app.py --text "The Eiffel Tower is located in Paris" --language en
python app.py --url https://example.com/news --language es
```
The `--language` argument controls both article interpretation and report output.

---

## Telemetry (LangSmith)
To enable LangSmith tracing, configure your `config/settings.toml`:

```toml
[langsmith]
enabled = true
api_key = "<your_api_key>"
api_url = "https://api.smith.langchain.com"
project = "FakeScope"
```

This automatically sets:
```
LANGSMITH_TRACING=true
LANGSMITH_ENDPOINT
LANGSMITH_API_KEY
LANGSMITH_PROJECT
```

LangGraph will automatically create trace runs visible on your **LangSmith dashboard**.  
You can disable automatic setup (`enabled=false`) and export environment variables manually if you prefer.

---

## Workflow
<img width="700" src="img/agent workflow.png" alt="Main"/>

```
- Intake Agent: Receives URLs or raw text, cleans tags, deduplicates paragraphs, and detects language. Normalizes content so the extractor works with plain text and saves basic metadata such as title, date, and author if found.
- Claim Extractor: Uses LLM to split text into atomic claims and structure them in JSON. Identifies key entities, dates, and relationships so each claim is independently verifiable and can be linked to search queries.
- Query Planner: Takes each claim and uses DeepSeek to generate informative queries in natural language. Proposes combinations of terms, synonyms, and geographic or temporal filters. Queries are ranked by expected coverage and logged for traceability.
- Evidence Retriever: Executes each query on Wikipedia and the approved external search engine. Applies initial BM25 filtering, discards untrusted domains, and keeps fragments with higher semantic matching. Raw content is saved with source reference and date.
- Dense Reranker: Uses BGE-M3 embeddings to reorder candidate evidence. Combines BM25 score and cosine similarity to prioritize fragments that directly answer the claim. Limits the final collection to the most relevant passages by diversity.
- Stance Analyzer: Evaluates each claim-evidence pair using an NLI classifier (DeBERTa or XLM-Roberta) or a few-shot prompt in DeepSeek. Labels the stance as supports, refutes, or unknown and calculates calibrated confidence with validation history.
- Verdict Aggregator: Groups results by claim and consolidates evidence by weighting stance analyzer confidence and source quality. Calculates a global verdict by adjusting probabilities with Brier Score and ECE to improve calibration.
- Report Writer: Uses LLM to summarize findings in a Markdown report. Explains the reasoning, highlights key evidence with citations, and communicates confidence level.
```

---

## Examples

### Mixed Verdict Example from cnn.com
<img width="700" src="img/FakeScope  - Mixed Veredict Example from CNN.png" alt="Main"/>

### Supporting Evidence
<img width="700" src="img/FakeScope - Supporting Evidence Example.png" alt="Main"/>

### Claims Extraction
<img width="700" src="img/FakeScope  - Claims Example.png" alt="Main"/>

### LangSmith Trace
<img width="700" src="img/FakeScope  - LangSmith Tracing Example.png" alt="Main"/>

### Refuted Verdict Example from theonion.com
<img width="700" src="img/FakeScope - Refute example from theonion.png" alt="Main"/>

---

## Repos Structure
```
FakeScope-Agent/
|-- app.py                        # CLI entrypoint for local verification
|-- requirements.txt              # Core dependencies
|-- config/
|   |-- settings.py               # Pydantic Settings loader
|   `-- settings.toml             # Default editable config values
|-- services/
|   |-- deepseek.py               # DeepSeek API client
|   `-- telemetry.py              # Telemetry client (LangGraph manages actual runs)
|-- agents/
|   |-- intake.py                 # Handles input normalization (URL/text)
|   |-- claim_extractor.py        # Extracts atomic claims using DeepSeek or heuristics
|   |-- query_planner.py          # Generates search queries per claim
|   |-- retrieval.py              # Retrieves evidence from Wikipedia and web engines
|   |-- rerank.py                 # Re-ranks evidence with lexical + dense signals
|   |-- stance.py                 # Stance classification (heuristic or NLI)
|   |-- aggregate.py              # Aggregates stances into a global verdict
|   |-- report_writer.py          # Writes final report in the selected language
|   |-- pipeline.py               # LangGraph node orchestration
|   `-- types.py                  # Shared dataclasses for claims, evidence, etc.
|-- ui/
|   `-- app.py                    # Streamlit interface
|-- rag/
|   |-- embeddings.py             # BGE/E5 embeddings utilities
|   `-- vectorstore.py            # ChromaDB helpers
|-- tests/
|   `-- test_pipeline.py          # Smoke test validating LangGraph pipeline
`-- README.md                     # Documentation and usage guide
```

---

## Ethics and Best Practices
- Always display sources and publication dates.  
- Use `Unverifiable` when evidence is insufficient.  
- Respect **robots.txt** and use official APIs only.  
- Never store or log user-sensitive data.  
- Be transparent about biases and limitations of the models.

---

## Author

**Ricardo Urdaneta**

[GitHub](https://github.com/Ricardouchub) | [LinkedIn](https://www.linkedin.com/in/ricardourdanetacastro)

