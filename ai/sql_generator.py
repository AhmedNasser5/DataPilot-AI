"""
Natural-Language-to-SQL generator.

The LLM only proposes SQL text. It is ALWAYS validated by
core.sql.query_validator and executed by core.sql.query_executor before
any result is shown — the generator itself never returns fabricated data.
"""
from __future__ import annotations

import pandas as pd

from ai.llm_client import LLMUnavailableError, llm_client
from ai.prompts.sql_prompt import NL_TO_SQL_PROMPT
from ai.prompts.system_prompt import BASE_SYSTEM_PROMPT
from core.sql.query_validator import query_validator


class SQLGenerationResult:
    def __init__(self, sql: str | None, reason: str = "", ai_used: bool = True):
        self.sql = sql
        self.reason = reason
        self.ai_used = ai_used


class SQLGenerator:
    def generate(self, table_name: str, schema_df: pd.DataFrame, question: str) -> SQLGenerationResult:
        if not llm_client.is_available():
            return SQLGenerationResult(
                None,
                "AI SQL generation is disabled (no LLM_API_KEY configured). "
                "You can still write SQL manually in the SQL Lab.",
                ai_used=False,
            )

        schema_text = "\n".join(f"- {row['column_name']} ({row['column_type']})" for _, row in schema_df.iterrows())
        prompt = NL_TO_SQL_PROMPT.format(table_name=table_name, schema=schema_text, question=question)

        try:
            result = llm_client.complete_json(BASE_SYSTEM_PROMPT, prompt, max_tokens=500)
        except LLMUnavailableError as e:
            return SQLGenerationResult(None, str(e), ai_used=False)

        sql = result.get("sql")
        reason = result.get("reason", "")
        if not sql:
            return SQLGenerationResult(None, reason or "The AI could not map this question to the available schema.")

        validation = query_validator.validate(sql)
        if not validation.is_valid:
            return SQLGenerationResult(None, f"Generated SQL was rejected by the safety validator: {validation.reason}")

        return SQLGenerationResult(validation.sanitized_sql, "")


sql_generator = SQLGenerator()
