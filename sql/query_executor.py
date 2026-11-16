"""Executes validated SQL against DuckDB with timing, row-limits, and safe error handling."""
from __future__ import annotations

import time

from config.settings import settings
from core.sql.duckdb_engine import duckdb_engine
from core.sql.query_validator import query_validator
from models.analysis import SQLResult


class QueryExecutor:
    def run(self, sql: str) -> SQLResult:
        validation = query_validator.validate(sql)
        if not validation.is_valid:
            return SQLResult(sql=sql, columns=[], rows=[], row_count=0,
                              execution_time_ms=0.0, error=f"Query rejected: {validation.reason}")

        start = time.perf_counter()
        try:
            df = duckdb_engine.execute(validation.sanitized_sql, max_rows=settings.max_result_rows)
        except Exception as e:
            return SQLResult(sql=validation.sanitized_sql, columns=[], rows=[], row_count=0,
                              execution_time_ms=round((time.perf_counter() - start) * 1000, 2),
                              error=f"Execution error: {e}")
        elapsed = round((time.perf_counter() - start) * 1000, 2)

        truncated = len(df) >= settings.max_result_rows
        return SQLResult(
            sql=validation.sanitized_sql,
            columns=[str(c) for c in df.columns],
            rows=[tuple(r) for r in df.itertuples(index=False, name=None)],
            row_count=len(df),
            execution_time_ms=elapsed,
            truncated=truncated,
        )


query_executor = QueryExecutor()
