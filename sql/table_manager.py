"""Maps dataset versions to DuckDB table names and keeps them in sync."""
from __future__ import annotations

import re

import pandas as pd

from core.sql.duckdb_engine import duckdb_engine
from models.dataset import Dataset


def sanitize_table_name(name: str) -> str:
    n = re.sub(r"[^\w]", "_", name.strip().lower())
    n = re.sub(r"_+", "_", n).strip("_")
    if not n or n[0].isdigit():
        n = f"t_{n}"
    return n


class TableManager:
    def __init__(self):
        self._dataset_to_table: dict[str, str] = {}  # f"{dataset_id}:{version}" -> table_name

    def register(self, dataset: Dataset) -> str:
        base = sanitize_table_name(dataset.metadata.original_filename.rsplit(".", 1)[0])
        table_name = f"{base}_{dataset.version}"
        key = f"{dataset.metadata.dataset_id}:{dataset.version}"
        duckdb_engine.register_table(table_name, dataset.dataframe, key)
        self._dataset_to_table[key] = table_name
        return table_name

    def table_for(self, dataset: Dataset) -> str | None:
        key = f"{dataset.metadata.dataset_id}:{dataset.version}"
        return self._dataset_to_table.get(key)

    def get_schema_info(self, table_name: str) -> pd.DataFrame:
        return duckdb_engine.get_schema(table_name)


table_manager = TableManager()
