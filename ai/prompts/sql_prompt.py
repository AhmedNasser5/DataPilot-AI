"""Prompt template for natural-language-to-SQL generation."""

NL_TO_SQL_PROMPT = """Given the following table schema (name, DuckDB type) and a natural-language
question, generate a single read-only DuckDB SQL query (SELECT/WITH only) that
answers it. Use exactly the table name and column names given — do not invent
columns that are not listed. If the question cannot be answered with the given
schema, respond with {{"sql": null, "reason": "<why not>"}} instead.

Table name: {table_name}

Schema:
{schema}

Question: {question}

Respond with ONLY JSON of the form:
{{"sql": "<the SQL query, or null>", "reason": "<short reason if sql is null, else empty string>"}}
"""
