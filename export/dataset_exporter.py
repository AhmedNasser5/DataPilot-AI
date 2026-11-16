"""Exports a dataframe to CSV/XLSX/JSON/Parquet bytes for download."""
from __future__ import annotations

import io
import json

import pandas as pd


class DatasetExporter:
    def to_csv_bytes(self, df: pd.DataFrame) -> bytes:
        return df.to_csv(index=False).encode("utf-8-sig")

    def to_xlsx_bytes(self, df: pd.DataFrame) -> bytes:
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="data")
        return buf.getvalue()

    def to_json_bytes(self, df: pd.DataFrame) -> bytes:
        return df.to_json(orient="records", force_ascii=False, indent=2).encode("utf-8")

    def to_parquet_bytes(self, df: pd.DataFrame) -> bytes:
        buf = io.BytesIO()
        df.to_parquet(buf, index=False)
        return buf.getvalue()


dataset_exporter = DatasetExporter()
