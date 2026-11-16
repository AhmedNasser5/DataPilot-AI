"""Loader for CSV, TSV, and generic delimited text files."""
from __future__ import annotations

import io

import pandas as pd

from core.ingestion.base_loader import BaseLoader, LoadRequest, LoaderError
from models.dataset import Dataset


class CSVLoader(BaseLoader):
    format_names = ("csv", "tsv", "txt_delimited")

    def __init__(self, delimiter: str | None = None):
        self.delimiter = delimiter

    def load(self, request: LoadRequest) -> Dataset:
        delimiter = self.delimiter or ","
        encoding_used = None
        last_error: Exception | None = None

        for encoding in ("utf-8", "utf-8-sig", "latin-1", "cp1256"):
            try:
                text = request.content.decode(encoding)
                encoding_used = encoding
                break
            except (UnicodeDecodeError, LookupError) as e:
                last_error = e
                text = None
        if text is None:
            raise LoaderError(
                f"Could not decode file '{request.filename}' with common encodings. "
                f"Original error: {last_error}"
            )

        try:
            df = pd.read_csv(
                io.StringIO(text),
                sep=delimiter,
                engine="python",
                on_bad_lines="warn",
                skip_blank_lines=True,
            )
        except Exception as e:
            raise LoaderError(f"Failed to parse '{request.filename}' as delimited text: {e}")

        if df.empty and len(df.columns) == 0:
            raise LoaderError(f"'{request.filename}' appears to be empty or has no detectable columns.")

        df = self.normalize_dataframe(df)

        return Dataset.new(
            df=df,
            original_filename=request.filename,
            file_format=f"delimited(sep='{delimiter}', encoding={encoding_used})",
            file_size_bytes=len(request.content),
        )
