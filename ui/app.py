from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from agents.pipeline import FakeScopePipeline
from agents.types import VerificationTask

st.set_page_config(page_title="FakeScope", layout="wide")

LANGUAGE_LABELS = {"en": "English", "es": "Español"}

LANG_STRINGS = {
    "en": {
        "instructions_title": "Usage",
        "instructions_steps": [
            "Leave the language on English unless the article is in Spanish.",
            "Paste a URL or the full article text.",
            "Click Verify to run the multi-agent pipeline.",
        ],
        "outputs_title": "Possible verdicts",
        "outputs_list": ["supports", "refutes", "neutral", "unknown", "mixed"],
        "text_label": "Article or claim",
        "text_placeholder": "Paste the article or claim here...",
        "submit": "Verify",
        "warning": "Provide a URL or text to verify.",
        "processing": "Processing...",
        "process": "Agent process",
        "planner": "Search plan per claim",
        "no_plan": "No plan recorded.",
        "evidence": "Retrieved evidence",
        "no_evidence": "No evidence retrieved.",
        "stance_results": "Stance assessment",
        "no_stance": "No stance results.",
        "stance_entry": "- {label} (confidence={confidence:.2f}) — {title}",
        "verdict": "Verdict",
        "metric_label": "Result",
        "metric_delta": "confidence {value:.2f}",
        "report": "Report",
        "claims": "Claims",
        "stance_line": "Stance: {label} | Confidence: {confidence:.2f}",
        "footer": "Created by Ricardo Urdaneta",
    },
    "es": {
        "instructions_title": "Instrucciones",
        "instructions_steps": [
            "Cambia el idioma a Español solo si la noticia está en Español.",
            "Pega una URL o el texto completo del artículo.",
            "Presiona Verificar para ejecutar el pipeline.",
        ],
        "outputs_title": "Veredictos posibles",
        "outputs_list": ["supports", "refutes", "neutral", "unknown", "mixed"],
        "text_label": "Artículo o afirmación",
        "text_placeholder": "Pega el artículo o afirmación aquí...",
        "submit": "Verificar",
        "warning": "Proporciona una URL o un texto para verificar.",
        "processing": "Procesando...",
        "process": "Proceso del agente",
        "planner": "Plan de búsqueda por claim",
        "no_plan": "Sin plan registrado.",
        "evidence": "Evidencias recuperadas",
        "no_evidence": "Sin evidencias recuperadas.",
        "stance_results": "Resultados de postura",
        "no_stance": "Sin resultados de postura.",
        "stance_entry": "- {label} (confianza={confidence:.2f}) — {title}",
        "verdict": "Veredicto",
        "metric_label": "Resultado",
        "metric_delta": "confianza {value:.2f}",
        "report": "Reporte",
        "claims": "Afirmaciones",
        "stance_line": "Postura: {label} | Confianza: {confidence:.2f}",
        "footer": "Realizado por: Ricardo Urdaneta",
    },
}

DEFAULT_LANGUAGE = "en"

def get_strings(lang: str) -> dict[str, str]:
    return LANG_STRINGS.get(lang, LANG_STRINGS[DEFAULT_LANGUAGE])

language = st.selectbox(
    "Language",
    options=["en", "es"],
    index=0,
    format_func=lambda value: LANGUAGE_LABELS.get(value, value),
)
strings = get_strings(language)

st.title("FakeScope")
st.caption("AI-powered fact checking with LangGraph + DeepSeek")

with st.expander(strings["instructions_title"], expanded=False):
    for step in strings["instructions_steps"]:
        st.markdown(f"- {step}")
    st.markdown(f"**{strings['outputs_title']}:** " + ", ".join(strings["outputs_list"]))

pipeline = FakeScopePipeline()

with st.form("verification-form"):
    col1, col2 = st.columns(2)
    with col1:
        url = st.text_input("URL", placeholder="https://...", key="input_url")
    with col2:
        pass
    text = st.text_area(
        strings["text_label"],
        height=220,
        placeholder=strings["text_placeholder"],
        key="input_text",
    )
    submitted = st.form_submit_button(strings["submit"])

if submitted:
    strings = get_strings(language)
    if not url and not text:
        st.warning(strings["warning"])
    else:
        with st.spinner(strings["processing"]):
            task = VerificationTask(input_text=text or None, url=url or None, language=language)
            result = pipeline.invoke(task)
        result_language = result.get("language", language)
        strings = get_strings(result_language)
        verdict = result.get("verdict")
        report = result.get("report", "")
        claims = result.get("claims", [])
        plan = result.get("plan", {})
        evidences = result.get("evidences", {})
        stance_results = result.get("stance_results", {})

        st.subheader(strings["process"])
        with st.expander(strings["planner"], expanded=False):
            if not plan:
                st.write(strings["no_plan"])
            else:
                for claim_id, queries in plan.items():
                    st.markdown(f"**{claim_id}**")
                    for query in queries:
                        st.write(f"- {query}")
        with st.expander(strings["evidence"], expanded=False):
            if not evidences:
                st.write(strings["no_evidence"])
            else:
                for claim in claims:
                    st.markdown(f"**{claim.identifier} - {claim.text}**")
                    for ev in evidences.get(claim.identifier, []):
                        st.write(f"- [{ev.title}]({ev.url})")
                        snippet = ev.snippet or ""
                        if snippet:
                            st.caption(snippet[:300] + ("..." if len(snippet) > 300 else ""))
        with st.expander(strings["stance_results"], expanded=False):
            if not stance_results:
                st.write(strings["no_stance"])
            else:
                for claim in claims:
                    assessments = stance_results.get(claim.identifier, [])
                    st.markdown(f"**{claim.identifier} - {claim.text}**")
                    for assessment in assessments:
                        st.write(
                            strings["stance_entry"].format(
                                label=assessment.label.value,
                                confidence=assessment.confidence,
                                title=assessment.evidence.title,
                            )
                        )

        st.subheader(strings["verdict"])
        if verdict:
            st.metric(
                strings["metric_label"],
                verdict.label.value.upper(),
                delta=strings["metric_delta"].format(value=verdict.confidence),
            )

        st.subheader(strings["report"])
        st.markdown(report)

        st.subheader(strings["claims"])
        for claim in claims:
            st.markdown(f"**{claim.text}**")
            st.write(
                strings["stance_line"].format(
                    label=claim.stance.value,
                    confidence=claim.confidence or 0.0,
                )
            )
            for evidence in claim.evidences:
                snippet = evidence.snippet or ""
                suffix = "..." if len(snippet) > 200 else ""
                st.write(f"- [{evidence.title}]({evidence.url}) - {snippet[:200]}{suffix}")

footer = strings["footer"]
st.markdown(
    f"""
    <div style=\"text-align: center; margin-top: 2rem; color: #94a3b8;\">
        {footer}<br/>
        <div style=\"margin-top: 0.75rem;\">
            <a class=\"fake-button\" href=\"https://github.com/Ricardouchub\" target=\"_blank\">GitHub</a>
            <a class=\"fake-button\" href=\"https://www.linkedin.com/in/ricardourdanetacastro\" target=\"_blank\">LinkedIn</a>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)
