"""
AI Data Analyst Agent.

Orchestrates: understand question -> inspect real schema -> generate SQL
(ai.sql_generator) -> validate + execute (core.sql) -> explain using the
REAL result. Never fabricates a result; if SQL generation or execution
fails, it says so plainly.
"""
from __future__ import annotations

import pandas as pd

from ai.llm_client import LLMUnavailableError, llm_client
from ai.prompts.system_prompt import BASE_SYSTEM_PROMPT
from ai.sql_generator import sql_generator
from core.sql.query_executor import query_executor
from core.sql.query_explainer import query_explainer
from core.sql.table_manager import table_manager


class AnalystAnswer:
    def __init__(self, question: str, sql: str | None, result_df: pd.DataFrame | None,
                 explanation: str, error: str | None = None, sql_breakdown: dict | None = None):
        self.question = question
        self.sql = sql
        self.result_df = result_df
        self.explanation = explanation
        self.error = error
        self.sql_breakdown = sql_breakdown or {}


class AnalystAgent:
    def ask(self, dataset, question: str) -> AnalystAnswer:
        table_name = table_manager.table_for(dataset)
        if not table_name:
            table_name = table_manager.register(dataset)

        schema_df = table_manager.get_schema_info(table_name)

        gen = sql_generator.generate(table_name, schema_df, question)
        if not gen.sql:
            return AnalystAnswer(question, None, None,
                                  f"I could not generate a safe SQL query for this question. {gen.reason}",
                                  error=gen.reason)

        result = query_executor.run(gen.sql)
        if result.error:
            return AnalystAnswer(question, gen.sql, None,
                                  f"The generated SQL failed to execute: {result.error}", error=result.error)

        df = pd.DataFrame(result.rows, columns=result.columns)
        breakdown = query_explainer.explain(gen.sql)
        explanation = self._explain_result(question, gen.sql, df, breakdown)

        return AnalystAnswer(question, gen.sql, df, explanation, sql_breakdown=breakdown)

    def _explain_result(self, question: str, sql: str, df: pd.DataFrame, breakdown: dict) -> str:
        preview = df.head(10).to_dict(orient="records")
        if not llm_client.is_available():
            if df.empty:
                return "The query executed successfully but returned no rows."
            return f"Query executed successfully. Top result(s): {preview}"

        prompt = (
            f"Question: {question}\n\n"
            f"Executed SQL:\n{sql}\n\n"
            f"SQL breakdown: {breakdown}\n\n"
            f"Actual result rows (already computed, do not recompute or alter): {preview}\n\n"
            "Write a concise (2-4 sentence) evidence-based answer to the question using ONLY "
            "the numbers/rows shown above. If the result is empty, say so plainly."
        )
        try:
            return llm_client.complete(BASE_SYSTEM_PROMPT, prompt, max_tokens=300)
        except LLMUnavailableError:
            if df.empty:
                return "The query executed successfully but returned no rows."
            return f"Query executed successfully. Top result(s): {preview}"


analyst_agent = AnalystAgent()
