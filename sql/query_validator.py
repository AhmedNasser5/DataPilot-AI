"""
SQL Safety Layer.

The environment is strictly analytical/read-only. Destructive
statements, multi-statement injection, and unbounded queries are
rejected before ever reaching DuckDB.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

_FORBIDDEN_KEYWORDS = (
    "drop", "delete", "update", "insert", "alter", "truncate", "create",
    "attach", "detach", "copy", "export", "import", "pragma", "call",
    "grant", "revoke", "vacuum", "install", "load",
)

_MULTI_STATEMENT_RE = re.compile(r";\s*\S")


@dataclass
class ValidationResult:
    is_valid: bool
    reason: str = ""
    sanitized_sql: str = ""


class QueryValidator:
    def __init__(self, max_result_rows: int = 10000):
        self.max_result_rows = max_result_rows

    def validate(self, sql: str) -> ValidationResult:
        if not sql or not sql.strip():
            return ValidationResult(False, "Empty query.")

        cleaned = sql.strip().rstrip(";")

        if _MULTI_STATEMENT_RE.search(sql):
            return ValidationResult(False, "Multiple SQL statements are not allowed.")

        lowered = cleaned.lower()
        if not (lowered.startswith("select") or lowered.startswith("with")):
            return ValidationResult(False, "Only SELECT / WITH (read-only) queries are allowed.")

        for kw in _FORBIDDEN_KEYWORDS:
            if re.search(rf"\b{kw}\b", lowered):
                return ValidationResult(False, f"Statement contains forbidden keyword: '{kw.upper()}'.")

        sanitized = self._enforce_limit(cleaned)
        return ValidationResult(True, "", sanitized)

    def _enforce_limit(self, sql: str) -> str:
        if re.search(r"\blimit\s+\d+\b", sql, re.IGNORECASE):
            return sql
        return f"{sql}\nLIMIT {self.max_result_rows}"


query_validator = QueryValidator()
