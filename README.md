# FakeScope Agent

FakeScope es un AI Agent de verificación de noticias impulsado por **LangGraph** y **DeepSeek** que extrae afirmaciones, recupera evidencia y produce un veredicto razonado. El repositorio incluye el pipeline principal, una interfaz en Streamlit y un script CLI que permiten ejecutar verificaciones locales con telemetría mediante **LangSmith**.

<img width="800" src="img/FakeScope - App UI.png" alt="Main"/>

## Características principales
- Orquestación completa del pipeline con **LangGraph**.
- Extracción de afirmaciones, planificación de consultas y recuperación híbrida (Wikipedia + buscadores externos).
- Clasificación de postura mediante modelos NLI (DeBERTa) con heurísticas de respaldo.
- Agregación de veredictos, reporte bilingüe (es/en) y telemetría opcional hacia LangSmith.
- UI en Streamlit y script CLI para ejecutar verificaciones locales.

## Requisitos
- Python 3.10+
- Claves de API opcionales:
  - `DEEPSEEK_API_KEY` para DeepSeek.
  - `TAVILY_API_KEY` si deseas habilitar Tavily; sin clave se usa DuckDuckGo por defecto.
  - `langsmith` configurado en `config/settings.toml` (ver más abajo) para habilitar trazas automáticas.
- Dependencias listadas en `requirements.txt`.

## Modo heurístico vs. NLI
- **Modo heurístico (por defecto)**: no descarga modelos pesados y funciona en CPU. Produce veredictos rápidos pero con confianza moderada.
- **Modo NLI (activar `FAKESCOPE_LOAD_STANCE_MODEL=1`)**: descarga y usa `MoritzLaurer/mDeBERTa-v3-base-mnli-xnli`. Requiere recursos adicionales y puede tardar varios segundos por claim, pero ofrece etiquetas y confidencias mucho más precisas.

## Veredictos y confianza
FakeScope devuelve uno de los siguientes veredictos globales (y también por afirmación):
- **supports**: la evidencia respalda la afirmación.
- **refutes**: la evidencia contradice la afirmación.
- **neutral**: la evidencia encontrada es irrelevante o no concluyente (sin mezcla con otras posturas).
- **unknown**: no se recuperó evidencia suficiente para evaluar la afirmación.
- **mixed**: se halló evidencia con conclusiones opuestas (por ejemplo soporte y refutación simultáneos).

El grado de confianza (0.0-1.0) representa la fortaleza del veredicto:
- En modo NLI, procede de la probabilidad del modelo DeBERTa y se promedia entre evidencias.
- En modo heurístico (sin NLI), se asignan valores conservadores (p. ej. 0.35 para soporte, 0.20 para desconocido), lo que refleja menor fiabilidad.

La UI y la telemetría muestran esta confianza junto al veredicto (por ejemplo, “Resultado: SUPPORTS, confianza 0.72”).

## Uso rápido
### Streamlit UI
```bash
streamlit run ui/app.py
```
Selecciona idioma (`Español` o `English`), ingresa texto o URL y presiona **Verificar**. El pipeline y el reporte se generan en el mismo idioma seleccionado.

### CLI
```bash
python app.py --text "La Torre Eiffel está en París" --language es
python app.py --url https://example.com/news --language en
```
El argumento `--language` controla tanto la interpretación del artículo como el idioma de salida (`es` o `en`).

## Telemetría (LangSmith)
Si habilitas LangSmith en `config/settings.toml` (sección `[langsmith]`), el loader aplicará automáticamente las variables necesarias:
```toml
[langsmith]
enabled = true
api_key = "<tu_api_key>"
api_url = "https://api.smith.langchain.com"
project = "FakeScope"
```
Esto establece `LANGSMITH_TRACING=true`, `LANGSMITH_ENDPOINT`, `LANGSMITH_API_KEY` y `LANGSMITH_PROJECT` antes de iniciar el pipeline. LangGraph se encargará de crear los runs, y podrás verlos junto con tu feedback booleano en el dashboard de LangSmith.

Si prefieres configurarlas manualmente, desactiva `enabled` y exporta dichas variables en la consola antes de `streamlit run ...`.

## Pruebas
```bash
pytest
```

## Ejemplos
### Mixed Veredict Example
<img width="700" src="img/FakeScope  - Mixed Veredict Example from CNN.png" alt="Main"/>

### Supporting Evidence

<img width="700" src="img/FakeScope - Supporting Evidence Example.png" alt="Main"/>

### Claims

<img width="700" src="img/FakeScope  - Claims Example.png" alt="Main"/>

### LangSmith Trace

<img width="700" src="img/FakeScope  - LangSmith Tracing Example.png" alt="Main"/>

### Refutes Veredict Example

<img width="700" src="img/FakeScope - Refute example from theonion.png" alt="Main"/>

## Estructura del repositorio
```
FakeScope-Agent/
|-- app.py                        # Script CLI para ejecutar el pipeline con URL o texto
|-- requirements.txt              # Dependencias principales del proyecto
|-- config/
|   |-- settings.py               # Carga y gestión de configuración (Pydantic Settings)
|   `-- settings.toml             # Valores por defecto editables para claves y opciones
|-- services/
|   |-- deepseek.py               # Cliente HTTP para la API de DeepSeek
|   `-- telemetry.py              # Cliente de telemetría (no-op; LangGraph gestiona los runs)
|-- agents/
|   |-- intake.py                 # Normaliza la entrada (URL/texto) respetando el idioma seleccionado
|   |-- claim_extractor.py        # Obtiene afirmaciones atómicas con DeepSeek o heurísticas
|   |-- query_planner.py          # Genera consultas de verificación por claim
|   |-- retrieval.py              # Recupera evidencia desde Wikipedia y motores web
|   |-- rerank.py                 # Reordena evidencias combinando señales léxicas
|   |-- stance.py                 # Clasifica postura (heurística o NLI)
|   |-- aggregate.py              # Agrega resultados de postura en un veredicto global
|   |-- report_writer.py          # Redacta el reporte final en el idioma seleccionado
|   |-- pipeline.py               # Define el grafo LangGraph y coordina los nodos
|   `-- types.py                  # Modelos de datos compartidos (claims, evidencias, etc.)
|-- ui/
|   `-- app.py                    # Interfaz Streamlit con panel de resultados y depuración
|-- rag/
|   |-- embeddings.py             # Utilidades para embeddings (BGE/E5)
|   `-- vectorstore.py            # Helper para gestionar ChromaDB
|-- tests/
|   `-- test_pipeline.py          # Prueba básica que valida la ejecución del grafo
`-- README.md                     # Documentación y guía de uso
```


## Ética y mejores prácticas
- Mostrar siempre las fuentes citadas y las fechas disponibles.
- Responder `Unverifiable` cuando la evidencia sea insuficiente.
- Respetar robots.txt utilizando APIs oficiales.
- Evitar guardar datos sensibles de usuarios.
- Informar sobre posibles sesgos o limitaciones del sistema.


## Autor

**Ricardo Urdaneta**

[GitHub](https://github.com/Ricardouchub) | [LinkedIn](https://www.linkedin.com/in/ricardourdanetacastro)

---

# FakeScope Agent

<p align="center">
  <img src="https://img.shields.io/badge/Status-Active-2ECC71?style=flat-square&logo=checkmarx&logoColor=white" alt="Active"/>
  <img src="https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python"/>
  <img src="https://img.shields.io/badge/FastAPI-Backend-009688?style=flat-square&logo=fastapi&logoColor=white" alt="FastAPI"/>
  <img src="https://img.shields.io/badge/LangGraph-Orchestration-7E57C2?style=flat-square&logo=chainlink&logoColor=white" alt="LangGraph"/>
  <img src="https://img.shields.io/badge/DeepSeek-Reasoning-orange?style=flat-square&logo=deepmind&logoColor=white" alt="DeepSeek"/>
  <img src="https://img.shields.io/badge/Streamlit-UI-FF4B4B?style=flat-square&logo=streamlit&logoColor=white" alt="Streamlit"/>
  <img src="https://img.shields.io/badge/LangSmith-Telemetry-blueviolet?style=flat-square&logo=langchain&logoColor=white" alt="LangSmith"/>
</p>

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

## Testing
```bash
pytest
```

---

## Examples

### Mixed Verdict Example
<img width="700" src="img/FakeScope  - Mixed Veredict Example from CNN.png" alt="Main"/>

### Supporting Evidence
<img width="700" src="img/FakeScope - Supporting Evidence Example.png" alt="Main"/>

### Claims Extraction
<img width="700" src="img/FakeScope  - Claims Example.png" alt="Main"/>

### LangSmith Trace
<img width="700" src="img/FakeScope  - LangSmith Tracing Example.png" alt="Main"/>

### Refuted Verdict Example
<img width="700" src="img/FakeScope - Refute example from theonion.png" alt="Main"/>

---

## Repository Structure
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

