# FakeScope Agent

FakeScope es un agente de verificación de noticias impulsado por LangGraph y DeepSeek que extrae afirmaciones, recupera evidencia y produce un veredicto razonado. El repositorio incluye el pipeline principal, una interfaz en Streamlit y un script CLI que permiten ejecutar verificaciones locales con telemetría opcional mediante LangSmith.

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

## Roadmap
Consulta `AGENTS.md` para la visión completa del producto y próximos sprints.
