# 🧠 FakeScope – AI Fake News Checker Agent

## Descripción general

**FakeScope** es un **agente de verificación de noticias** impulsado por **DeepSeek API** y **modelos NLI** (XLM-Roberta o DeBERTa) que evalúa la veracidad de afirmaciones, artículos o URLs.

Dado un texto o enlace, el sistema:
1. **Extrae afirmaciones atómicas** (claims).
2. **Busca evidencia confiable** en fuentes abiertas (Wikipedia + motores de búsqueda).
3. **Evalúa la postura** de cada evidencia respecto a la afirmación.
4. **Agrega y calibra** un veredicto final (`True`, `False`, `Mixed`, `Unverifiable`).
5. **Redacta un reporte explicativo** con citas verificables.

Todo el proceso se orquesta mediante **LangGraph**, con **DeepSeek** como razonador principal.

---

## ⚙️ Stack Tecnológico

- **Backend:** FastAPI  
- **Orquestación:** LangGraph  
- **Razonamiento:** DeepSeek API (`deepseek-reasoner` o `deepseek-chat`)  
- **Embeddings:** BAAI/bge-m3 o e5  
- **Vector Store:** ChromaDB (in-memory o persistente)  
- **Clasificador NLI:** DeBERTa-v3 o XLM-Roberta para soporte/refutación  
- **Frontend:** Streamlit o Dash (modo visual)  
- **Persistencia ligera:** SQLite o JSON local  
- **Colas y jobs (opcional):** Celery + Redis (solo si se requiere batch)  
- **Lenguaje:** Python 3.10+  

> 💡 No se utiliza Docker ni contenedores. El proyecto se ejecuta 100 % localmente mediante entorno virtual o Conda.

---

## 🧩 Arquitectura de Agentes

```
┌───────────────────────────────────────────────┐
│                FakeScope Pipeline             │
├───────────────────────────────────────────────┤
│ 1️⃣ Intake Agent (URL/Text Parser)            │
│   → Limpieza HTML, detección de idioma        │
│   → Llama a Claim Extractor                   │
│                                               │
│ 2️⃣ Claim Extractor (DeepSeek)                │
│   → Divide texto en afirmaciones atómicas     │
│   → Devuelve JSON estructurado                │
│                                               │
│ 3️⃣ Evidence Retriever                        │
│   → Wikipedia API + Search API (Bing/Tavily)  │
│   → BM25 + Re-ranker denso (bge-m3)           │
│   → Filtro de dominios confiables             │
│                                               │
│ 4️⃣ Stance Analyzer                           │
│   → NLI (DeBERTa o DeepSeek few-shot)         │
│   → Clasifica cada claim-evidence pair        │
│                                               │
│ 5️⃣ Verdict Aggregator                        │
│   → Combina posturas                          │
│   → Calibra confianza (Brier/ECE)             │
│                                               │
│ 6️⃣ Report Writer (DeepSeek)                  │
│   → Resume hallazgos                          │
│   → Redacta veredicto y citas en Markdown     │
└───────────────────────────────────────────────┘
```

---

## 📚 Flujo de Ejecución

1. **Input**: texto plano o URL (extraído con `newspaper3k` o `BeautifulSoup`).
2. **Extracción de afirmaciones**: DeepSeek produce JSON con claims y entidades.
3. **Plan de búsqueda**: DeepSeek propone queries informativas.
4. **Recuperación de evidencia**: Wikipedia + buscador (API oficial).
5. **Re-ranking**: BM25 + embeddings densos (bge-m3).
6. **Análisis de postura**: NLI o LLM clasifican `supports / refutes / unknown`.
7. **Agregación**: se combinan posturas y confianza.
8. **Reporte**: DeepSeek redacta resumen con citas y veredicto global.
9. **Visualización**: Streamlit muestra resultado + gráfico + export PDF/Markdown.

---

## 🧠 Uso de DeepSeek API

DeepSeek se usa en tres etapas:

| Rol | Descripción | Output |
|-----|--------------|--------|
| Claim Extractor | Divide texto en afirmaciones verificables | JSON (claims, entidades) |
| Query Planner | Genera consultas informativas por claim | Lista de queries |
| Report Writer | Resume resultados, explica veredicto | Texto natural + citas |

### Ejemplo de llamada básica

```python
import os, httpx

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
BASE_URL = "https://api.deepseek.com/v1/chat/completions"

def call_deepseek(messages):
    headers = {"Authorization": f"Bearer {DEEPSEEK_API_KEY}"}
    payload = {
        "model": "deepseek-reasoner",
        "messages": messages,
        "temperature": 0.2
    }
    response = httpx.post(BASE_URL, json=payload, headers=headers, timeout=60)
    return response.json()
```

---

## 🧩 Estructura de Carpetas

```
FakeScope/
├── api/
│   ├── main.py                # FastAPI app
│   ├── routers/
│   │   └── verify.py          # Endpoint principal /verify
│   └── schemas.py             # Pydantic (Claim, Evidence, Verdict)
├── agents/
│   ├── claim_extractor.py     # DeepSeek prompts
│   ├── query_planner.py       # Generación de consultas
│   ├── retrieval.py           # Wikipedia + buscador
│   ├── rerank.py              # BM25 + embeddings densos
│   ├── stance.py              # NLI / DeepSeek postura
│   └── aggregate.py           # Agregación + confianza
├── rag/
│   ├── vectorstore.py         # ChromaDB helpers
│   └── embeddings.py          # BGE-M3 o E5
├── ui/
│   └── app.py                 # Streamlit/Dash UI
├── eval/
│   ├── datasets.py            # FEVER / LIAR / MultiFC loaders
│   ├── metrics.py             # F1, FEVER score, ECE
│   └── run_benchmark.py
├── config/
│   └── settings.toml          # Claves y configuración
├── tests/
│   └── test_pipeline.py
├── requirements.txt
├── README.md
└── AGENTS.md
```

---

## 🧪 Evaluación y Métricas

El sistema se evalúa en datasets públicos:

| Dataset | Uso | Métrica clave |
|----------|-----|----------------|
| FEVER | Verificación con Wikipedia | FEVER Score |
| LIAR | Frases políticas | Accuracy / F1 |
| MultiFC | Multi-fuente | Macro-F1 |
| WELFake | Noticias falsas | Precision / Recall |

**Métricas adicionales:**
- Recall@5, Recall@10 (retrieval)
- Brier Score (calibración)
- Expected Calibration Error (ECE)
- Latencia p95 del pipeline

---

## 🖥️ Interfaz (Streamlit)

**Entrada:**
- URL o texto
- Idioma automático (`spa/en`)

**Salida:**
- Veredicto global (`True`, `False`, `Mixed`, `Unverifiable`)
- Nivel de confianza
- Tabla claim → evidencia → postura
- Resumen explicativo
- Botón “Exportar a PDF / Markdown”

**Vista avanzada:**
- Grafo visual de relaciones Claim ↔ Evidence
- Métricas por etapa
- Logs de tiempo y decisiones de agentes

---

### Dependencias clave
```
fastapi
uvicorn
httpx
langgraph
chromadb
sentence-transformers
transformers
scikit-learn
pydantic
streamlit
beautifulsoup4
python-dotenv
```

---

## 🧩 API Endpoints

**`POST /verify`**
```json
{
  "input": {
    "url": "https://example.com/news/123",
    "language": "auto"
  }
}
```

**Respuesta:**
```json
{
  "verdict": "Mixed",
  "confidence": 0.72,
  "summary": "La afirmación es parcialmente correcta según fuentes oficiales.",
  "claims": [
    {
      "text": "El gobierno aprobó una ley de IA en 2025.",
      "stance": "supports",
      "evidence": [
        {
          "source": "wikipedia",
          "title": "Ley de Inteligencia Artificial 2025",
          "url": "https://es.wikipedia.org/wiki/...",
          "snippet": "El parlamento aprobó la ley..."
        }
      ]
    }
  ]
}
```

---

## 🧱 Buenas prácticas éticas

- Mostrar **todas las fuentes y fechas**.
- Si no hay evidencia sólida → `Unverifiable`.
- Respetar robots.txt (usar APIs oficiales).
- No almacenar textos de usuarios ni contenido sensible.
- Señalar claramente **limitaciones y sesgos potenciales**.

---

## 🚀 Roadmap

| Sprint | Objetivos principales |
|---------|----------------------|
| **Sprint 1** | FastAPI + DeepSeek Claim Extractor + Wikipedia retrieval + UI básica |
| **Sprint 2** | NLI + Re-ranking denso + agregación de confianza + evaluación FEVER |
| **Sprint 3** | Batch verification + Streamlit avanzado + export PDF + visualización de grafo |

---

## 🏷️ Badges recomendadas

```md
![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB)
![FastAPI](https://img.shields.io/badge/FastAPI-async-green)
![DeepSeek](https://img.shields.io/badge/LLM-DeepSeek-orange)
![LangGraph](https://img.shields.io/badge/Orchestration-LangGraph-blueviolet)
![RAG](https://img.shields.io/badge/RAG-Hybrid%20BM25%20%2B%20Dense-brightgreen)
![Eval](https://img.shields.io/badge/Eval-FEVER%20%7C%20LIAR%20%7C%20MultiFC-yellow)
```
