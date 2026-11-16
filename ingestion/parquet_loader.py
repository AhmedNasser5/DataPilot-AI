"""Loader for columnar formats: Parquet and Feather, via PyArrow."""
from __future__ import annotations

import io

import pandas as pd

from core.ingestion.base_loader import BaseLoader, LoadRequest, LoaderError
from models.dataset import Dataset


class ParquetLoader(BaseLoader):
    format_names = ("parquet", "feather")

    def load(self, request: LoadRequest) -> Dataset:
        buf = io.BytesIO(request.content)
        fmt = self._detect_columnar_format(request.filename)
        try:
            if fmt == "feather":
                df = pd.read_feather(buf)
            else:
                df = pd.read_parquet(buf)
        except Exception as e:
            raise LoaderError(f"Failed to read {fmt} file '{request.filename}': {e}")

        df = self.normalize_dataframe(df)

        return Dataset.new(
            df=df,
            original_filename=request.filename,
            file_format=fmt,
            file_size_bytes=len(request.content),
        )

    @staticmethod
    def _detect_columnar_format(filename: str) -> str:
        return "feather" if filename.lower().endswith((".feather", ".ft")) else "parquet"
