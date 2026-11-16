"""AI Analyst: conversational Q&A, always backed by actually-executed SQL — never fabricated."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st

from config.settings import settings
from services.analytics_service import analytics_service
from streamlit_app.components.navigation import render_sidebar
from streamlit_app.components.state import get_state
from streamlit_app.components.status import ai_disabled_notice, no_dataset_notice
from streamlit_app.components.theme import apply_theme, hero, section_title

apply_theme("AI Analyst", "🤖")
state = get_state()
render_sidebar(state)

hero("AI Data Analyst", "Ask anything about your data. Every answer is grounded in SQL that was actually executed.")

if not state.has_dataset():
    no_dataset_notice()
    st.stop()

if not settings.ai_enabled():
    ai_disabled_notice()

section_title("Generate evidence-based insights")
if st.button("✨ Generate insights from current KPIs & profile", disabled=not state.kpis):
    with st.spinner("Analyzing evidence..."):
        evidence = {
            "domain": state.domain.domain if state.domain else None,
            "quality_score": state.quality_report.overall_score if state.quality_report else None,
            "kpis": {k.name: k.value for k in state.kpis if k.calculable},
            "row_count": state.profile.row_count if state.profile else None,
        }
        insights = analytics_service.generate_insights(state.domain, evidence)
    for ins in insights:
        icon = {"fact": "📌", "calculation": "🧮", "interpretation": "💡", "hypothesis": "❓"}.get(ins.kind.value, "•")
        st.markdown(f"{icon} **[{ins.kind.value.upper()}]** {ins.text}")

st.markdown("---")
section_title("Ask a question")

for msg in state.ai_chat_history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("sql"):
            with st.expander("View executed SQL & result"):
                st.code(msg["sql"], language="sql")
                if msg.get("df") is not None:
                    st.dataframe(msg["df"], use_container_width=True)

question = st.chat_input("e.g. 'Which category has the highest total revenue?'")
if question:
    state.ai_chat_history.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            answer = analytics_service.ask_ai_analyst(state.working_dataset, question)
        st.markdown(answer.explanation)
        if answer.sql:
            with st.expander("View executed SQL & result"):
                st.code(answer.sql, language="sql")
                if answer.result_df is not None:
                    st.dataframe(answer.result_df, use_container_width=True)

    state.ai_chat_history.append({
        "role": "assistant", "content": answer.explanation,
        "sql": answer.sql, "df": answer.result_df,
    })
