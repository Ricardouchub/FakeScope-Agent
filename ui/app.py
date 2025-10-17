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

st.markdown(
    """
    <style>
    .main {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #111827 100%);
        color: #e2e8f0;
    }
    .fakescope-hero {
        padding: 2.5rem 2rem 1rem 2rem;
        background: rgba(15, 23, 42, 0.65);
        border-radius: 18px;
        border: 1px solid rgba(148, 163, 184, 0.2);
        backdrop-filter: blur(12px);
    }
    .fakescope-section {
        padding: 1.75rem 1.75rem;
        background: rgba(15, 23, 42, 0.78);
        border-radius: 18px;
        border: 1px solid rgba(148, 163, 184, 0.18);
        margin-bottom: 1.5rem;
    }
    details.stExpander > summary {
        font-weight: 600;
        color: #f1f5f9;
    }
    details.stExpander {
        background: rgba(30, 41, 59, 0.55) !important;
        border: 1px solid rgba(148, 163, 184, 0.2) !important;
        border-radius: 14px !important;
    }
    details.stExpander div[role="group"] > div {
        padding: 0.75rem 1rem 1rem 1rem;
    }
    .fake-button {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        padding: 0.45rem 0.95rem;
        border-radius: 999px;
        border: 1px solid rgba(148, 163, 184, 0.35);
        color: #e2e8f0 !important;
        background: rgba(100, 116, 139, 0.2);
        text-decoration: none;
        font-size: 0.85rem;
        font-weight: 600;
        margin-right: 0.5rem;
        transition: all 0.2s ease-in-out;
    }
    .fake-button:hover {
        background: rgba(148, 163, 184, 0.35);
        border-color: rgba(226, 232, 240, 0.6);
    }
    .stMetric > div {
        background: rgba(15, 118, 110, 0.22);
        border-radius: 14px;
        padding: 0.25rem 0.75rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

with st.container():
    st.markdown(
        """
        <div class="fakescope-hero">
            <h1 style="margin-bottom: 0.25rem; color: #f8fafc;">FakeScope</h1>
            <p style="margin-bottom: 0; color: #94a3b8;">Verificador de noticias asistido por LangGraph + DeepSeek</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

pipeline = FakeScopePipeline()

with st.form("verification-form"):
    st.markdown("<div class='fakescope-section'>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        url = st.text_input("URL", placeholder="https://...", key="input_url")
    with col2:
        language = st.selectbox("Idioma", options=["auto", "es", "en"], index=0, key="input_language")
    text = st.text_area(
        "Texto",
        height=220,
        placeholder="Pega el articulo o afirmacion aqui...",
        key="input_text",
    )
    submitted = st.form_submit_button("Verificar")
    st.markdown("</div>", unsafe_allow_html=True)

if submitted:
    if not url and not text:
        st.warning("Proporciona una URL o un texto para verificar.")
    else:
        with st.spinner("Procesando..."):
            task = VerificationTask(input_text=text or None, url=url or None, language=language)
            result = pipeline.invoke(task)
        verdict = result.get("verdict")
        report = result.get("report", "")
        claims = result.get("claims", [])
        plan = result.get("plan", {})
        evidences = result.get("evidences", {})
        stance_results = result.get("stance_results", {})

        st.markdown("<div class='fakescope-section'>", unsafe_allow_html=True)
        st.subheader("Proceso del agente")
        with st.expander("Plan de busqueda por claim", expanded=False):
            if not plan:
                st.write("Sin plan registrado.")
            else:
                for claim_id, queries in plan.items():
                    st.markdown(f"**{claim_id}**")
                    for query in queries:
                        st.write(f"- {query}")
        with st.expander("Evidencias recuperadas", expanded=False):
            if not evidences:
                st.write("Sin evidencias recuperadas.")
            else:
                for claim in claims:
                    st.markdown(f"**{claim.identifier} - {claim.text}**")
                    for ev in evidences.get(claim.identifier, []):
                        st.write(f"- [{ev.title}]({ev.url})")
                        snippet = ev.snippet or ""
                        if snippet:
                            st.caption(snippet[:300] + ("..." if len(snippet) > 300 else ""))
        with st.expander("Resultados de postura", expanded=False):
            if not stance_results:
                st.write("Sin resultados de postura.")
            else:
                for claim in claims:
                    assessments = stance_results.get(claim.identifier, [])
                    st.markdown(f"**{claim.identifier} - {claim.text}**")
                    for assessment in assessments:
                        st.write(
                            f"- {assessment.label.value} (confianza={assessment.confidence:.2f}) ? {assessment.evidence.title}"
                        )
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div class='fakescope-section'>", unsafe_allow_html=True)
        if verdict:
            st.subheader("Veredicto")
            st.metric("Resultado", verdict.label.value.upper(), delta=f"confianza {verdict.confidence:.2f}")

        st.subheader("Reporte")
        st.markdown(report)

        st.subheader("Afirmaciones")
        for claim in claims:
            st.markdown(f"**{claim.text}**")
            st.write(f"Postura: {claim.stance.value} | Confianza: {claim.confidence or 0:.2f}")
            for evidence in claim.evidences:
                snippet = evidence.snippet or ""
                st.write(f"- [{evidence.title}]({evidence.url}) - {snippet[:200]}{'...' if len(snippet) > 200 else ''}")
        st.markdown("</div>", unsafe_allow_html=True)

st.markdown(
    """
    <div style="text-align: center; margin-top: 2rem; color: #94a3b8;">
        Realizado por: Ricardo Urdaneta<br/>
        <div style="margin-top: 0.75rem;">
            <a class="fake-button" href="https://github.com/Ricardouchub" target="_blank">GitHub</a>
            <a class="fake-button" href="https://www.linkedin.com/in/ricardourdanetacastro" target="_blank">LinkedIn</a>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)
