# FakeScope Agent

FakeScope es un agente de verificacion de noticias impulsado por LangGraph y DeepSeek que extrae afirmaciones, recupera evidencia y produce un veredicto razonado. Este repositorio contiene la API (FastAPI), el pipeline de agentes y una interfaz basica en Streamlit.

## Caracteristicas principales
- Orquestacion completa del pipeline con **LangGraph**.
- Extraccion de afirmaciones, planificacion de consultas y recuperacion hibrida (Wikipedia + buscadores externos).
- Clasificacion de postura mediante modelos NLI (DeBERTa / XLM-R) con heuristicas de respaldo.
- Agregacion de veredictos con calibracion simple y reporte final asistido por LLM.
- API REST (`POST /verify`) y UI en Streamlit.

## Requisitos
- Python 3.10+
- Claves de API opcionales:
  - `DEEPSEEK_API_KEY` para DeepSeek.
  - `TAVILY_API_KEY` si deseas habilitar Tavily; sin clave se usa DuckDuckGo por defecto.
- Dependencias listadas en `requirements.txt`.

> Nota: El analizador de postura usa heuristicas por defecto. Si quieres habilitar el modelo NLI completo (carga pesada), exporta `FAKESCOPE_LOAD_STANCE_MODEL=1` antes de ejecutar la aplicacion.

## Estructura del repositorio
```
FakeScope-Agent/
|-- app.py                        # Script CLI para ejecutar el pipeline con URL o texto
|-- requirements.txt              # Dependencias principales del proyecto
|-- AGENTS.md                     # Documento con la vision y la arquitectura del agente
|-- config/
|   |-- settings.py               # Carga y gestion de configuracion (Pydantic Settings)
|   `-- settings.toml             # Valores por defecto editables para claves y opciones
|-- services/
|   `-- deepseek.py               # Cliente HTTP ligero para interactuar con la API de DeepSeek
|-- agents/
|   |-- intake.py                 # Normaliza la entrada (URL/texto) y detecta idioma
|   |-- claim_extractor.py        # Obtiene afirmaciones atomicas con DeepSeek o heuristicas
|   |-- query_planner.py          # Genera consultas de verificacion por cada claim
|   |-- retrieval.py              # Recupera evidencia desde Wikipedia y motores web
|   |-- rerank.py                 # Reordena evidencias combinando senales lexicas y densas
|   |-- stance.py                 # Clasifica postura (heuristica o NLI)
|   |-- aggregate.py              # Agrega resultados de postura en un veredicto global
|   |-- report_writer.py          # Redacta el reporte final con DeepSeek o plantilla
|   |-- pipeline.py               # Define el grafo LangGraph y coordina los nodos
|   `-- types.py                  # Modelos de datos compartidos (claims, evidencias, etc.)
|-- api/
|   |-- main.py                   # App FastAPI y registro de rutas
|   |-- schemas.py                # Esquemas Pydantic para peticiones y respuestas
|   `-- routers/
|       `-- verify.py             # Endpoint POST /verify que usa el pipeline
|-- ui/
|   `-- app.py                    # Interfaz Streamlit con panel de resultados y depuracion
|-- rag/
|   |-- embeddings.py             # Utilidades para embeddings (BGE/E5)
|   `-- vectorstore.py            # Helper para gestionar ChromaDB
|-- eval/
|   |-- datasets.py               # Cargadores de datasets (FEVER, etc.)
|   |-- metrics.py                # Metricas de evaluacion y calibracion
|   `-- run_benchmark.py          # Script para ejecutar benchmarks sobre el pipeline
|-- tests/
|   `-- test_pipeline.py          # Prueba basica que valida la ejecucion del grafo
`-- README.md                     # Documentacion general y guia de uso
```
## Evaluacion rapida
Coloca datasets en `eval/data/` y ejecuta:
```bash
python -m eval.run_benchmark --limit 50
```

### Ejemplo con WELFake
```bash
python -m eval.run_benchmark --dataset welfake --text-column text --label-column label --limit 10
```

## Pruebas
```bash
pytest
```

## Telemetria (Langfuse)
- Define credenciales en `config/settings.toml` o via variables de entorno:
  - `FAKESCOPE_LANGFUSE__ENABLED=true`
  - `FAKESCOPE_LANGFUSE__PUBLIC_KEY=<tu_public_key>`
  - `FAKESCOPE_LANGFUSE__SECRET_KEY=<tu_secret_key>`
  - Opcional: `FAKESCOPE_LANGFUSE__HOST`, `FAKESCOPE_LANGFUSE__ENVIRONMENT`, `FAKESCOPE_LANGFUSE__RELEASE`.
- Cada ejecucion del pipeline genera un trace `fakescope_pipeline` con input y veredicto.
- Los eventos se capturan automaticamente al usar la API, CLI o UI cuando `langfuse` esta instalado.

## Etica y mejores practicas
- Mostrar siempre las fuentes citadas y las fechas disponibles.
- Responder `Unverifiable` cuando la evidencia sea insuficiente.
- Respetar robots.txt utilizando APIs oficiales.
- Evitar guardar datos sensibles de usuarios.
- Informar sobre posibles sesgos o limitaciones del sistema.

## Roadmap
Consulta `AGENTS.md` para la vision completa del producto y proximos sprints.











