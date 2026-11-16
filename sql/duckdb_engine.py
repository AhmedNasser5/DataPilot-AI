"""
DuckDB analytical engine wrapper.

Every uploaded/cleaned dataset version is registered here as a real
queryable table so that ALL SQL shown to the user is SQL that was
actually executed against real data — never fabricated.
"""
from __future__ import annotations

import threading

import duckdb
import pandas as pd


class DuckDBEngine:
    def __init__(self):
        self._conn = duckdb.connect(database=":memory:")
        self._lock = threading.Lock()
        self._registered_tables: dict[str, str] = {}  # table_name -> dataset_id:version

    def register_table(self, table_name: str, df: pd.DataFrame, source_key: str) -> None:
        with self._lock:
            self._conn.register(table_name, df)
            self._registered_tables[table_name] = source_key

    def unregister_table(self, table_name: str) -> None:
        with self._lock:
            try:
                self._conn.unregister(table_name)
            except Exception:
                pass
            self._registered_tables.pop(table_name, None)

    def list_tables(self) -> list[str]:
        with self._lock:
            return list(self._registered_tables.keys())

    def get_schema(self, table_name: str) -> pd.DataFrame:
        with self._lock:
            return self._conn.execute(f"DESCRIBE {self._quote(table_name)}").fetchdf()

    def sample(self, table_name: str, n: int = 10) -> pd.DataFrame:
        with self._lock:
            return self._conn.execute(f"SELECT * FROM {self._quote(table_name)} LIMIT {int(n)}").fetchdf()

    def execute(self, sql: str, max_rows: int | None = None) -> pd.DataFrame:
        with self._lock:
            result = self._conn.execute(sql)
            df = result.fetchdf()
        if max_rows is not None and len(df) > max_rows:
            return df.head(max_rows)
        return df

    @staticmethod
    def _quote(name: str) -> str:
        return f'"{name}"'


duckdb_engine = DuckDBEngine()
