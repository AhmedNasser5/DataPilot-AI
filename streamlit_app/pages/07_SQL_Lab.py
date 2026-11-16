"""SQL Lab: browse schema, write or generate SQL, execute safely against DuckDB."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pandas as pd
import streamlit as st

from ai.sql_generator import sql_generator
from config.settings import settings
from core.sql.table_manager import table_manager
from services.analytics_service import analytics_service
from streamlit_app.components.navigation import render_sidebar
from streamlit_app.components.state import get_state
from streamlit_app.components.status import ai_disabled_notice, no_dataset_notice
from streamlit_app.components.theme import apply_theme, hero, section_title

apply_theme("SQL Lab", "🗄️")
state = get_state()
render_sidebar(state)

hero("SQL Lab", "Real, sandboxed SQL over your dataset — powered by DuckDB. Every result shown was actually executed.")

if not state.has_dataset():
    no_dataset_notice()
    st.stop()

table_name = analytics_service.ensure_registered(state.working_dataset)

section_title("Table & Schema")
st.markdown(f"Your dataset is queryable as table: **`{table_name}`**")
schema_df = table_manager.get_schema_info(table_name)
st.dataframe(schema_df, use_container_width=True, height=220)

st.markdown("---")
section_title("Ask in natural language (optional)")
if not settings.ai_enabled():
    ai_disabled_notice()
else:
    nl_question = st.text_input("e.g. 'What are the top 10 rows by [numeric column]?'")
    if st.button("✨ Generate SQL from question"):
        with st.spinner("Generating SQL..."):
            gen = sql_generator.generate(table_name, schema_df, nl_question)
        if gen.sql:
            st.session_state["sql_lab_query"] = gen.sql
            st.success("SQL generated below — review it, then run it.")
        else:
            st.warning(gen.reason)

st.markdown("---")
section_title("Write / Run SQL")
st.caption("Only read-only SELECT / WITH statements are allowed. DROP, DELETE, UPDATE, INSERT, "
           f"ALTER, and TRUNCATE are blocked. Results are capped at {settings.max_result_rows:,} rows.")

default_sql = st.session_state.get("sql_lab_query", f'SELECT * FROM "{table_name}" LIMIT 20')
sql_text = st.text_area("SQL query", value=default_sql, height=140)

if st.button("▶️ Run Query", type="primary"):
    with st.spinner("Executing..."):
        result = analytics_service.run_sql(sql_text)
    if result.error:
        st.error(result.error)
    else:
        st.success(f"✅ {result.row_count} row(s) in {result.execution_time_ms} ms"
                   + (" (truncated at limit)" if result.truncated else ""))
        df_result = pd.DataFrame(result.rows, columns=result.columns)
        st.dataframe(df_result, use_container_width=True, height=400)

        with st.expander("🔍 SQL breakdown"):
            breakdown = analytics_service.explain_sql(result.sql)
            st.json(breakdown)

        state.sql_history.append({"sql": result.sql, "rows": result.row_count, "time_ms": result.execution_time_ms})

        st.download_button("⬇️ Download result as CSV", data=df_result.to_csv(index=False).encode("utf-8-sig"),
                            file_name="query_result.csv", mime="text/csv")

if state.sql_history:
    with st.expander(f"🕘 Query history ({len(state.sql_history)})"):
        for h in reversed(state.sql_history[-20:]):
            st.code(h["sql"], language="sql")
            st.caption(f"{h['rows']} rows · {h['time_ms']} ms")
