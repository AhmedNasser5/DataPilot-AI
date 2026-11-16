"""Loader for JSON and NDJSON, including nested-structure flattening."""
from __future__ import annotations

import json

import pandas as pd

from core.ingestion.base_loader import BaseLoader, LoadRequest, LoaderError
from models.dataset import Dataset


class JSONLoader(BaseLoader):
    format_names = ("json", "ndjson")

    def load(self, request: LoadRequest) -> Dataset:
        try:
            text = request.content.decode("utf-8-sig")
        except UnicodeDecodeError:
            text = request.content.decode("latin-1")

        fmt_used = "json"
        try:
            if self._looks_like_ndjson(text):
                fmt_used = "ndjson"
                records = [json.loads(line) for line in text.splitlines() if line.strip()]
                df = pd.json_normalize(records)
            else:
                data = json.loads(text)
                if isinstance(data, dict):
                    # try to find the first list-of-records value; else wrap as one row
                    list_field = next((v for v in data.values() if isinstance(v, list)), None)
                    df = pd.json_normalize(list_field) if list_field is not None else pd.json_normalize([data])
                elif isinstance(data, list):
                    df = pd.json_normalize(data)
                else:
                    raise LoaderError("Top-level JSON must be an object or an array.")
        except json.JSONDecodeError as e:
            raise LoaderError(f"Invalid JSON in '{request.filename}': {e}")

        if df.empty:
            raise LoaderError(f"'{request.filename}' produced an empty table after parsing.")

        df = self.normalize_dataframe(df)

        return Dataset.new(
            df=df,
            original_filename=request.filename,
            file_format=fmt_used,
            file_size_bytes=len(request.content),
        )

    @staticmethod
    def _looks_like_ndjson(text: str) -> bool:
        lines = [l for l in text.strip().splitlines() if l.strip()]
        if len(lines) < 2:
            return False
        sample = lines[:5]
        return all(l.strip().startswith("{") and l.strip().endswith("}") for l in sample)
