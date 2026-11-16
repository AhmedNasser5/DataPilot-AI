"""
Excel loader (.xlsx / .xls) with intelligent multi-sheet handling.

Sheets are never blindly merged. The loader exposes sheet metadata so
the service/UI layer can let the user pick a sheet.
"""
from __future__ import annotations

import io

import pandas as pd

from core.ingestion.base_loader import BaseLoader, LoadRequest, LoaderError
from models.dataset import Dataset, SheetInfo


class ExcelLoader(BaseLoader):
    format_names = ("xlsx", "xls")

    def list_sheets(self, content: bytes) -> list[SheetInfo]:
        try:
            xls = pd.ExcelFile(io.BytesIO(content))
        except Exception as e:
            raise LoaderError(f"Could not open Excel workbook: {e}")

        sheets = []
        for name in xls.sheet_names:
            try:
                preview = xls.parse(name, nrows=0)
                # read a small sample to estimate row count cheaply isn't exact;
                # do a full but lightweight parse of just the index to get shape.
                full = xls.parse(name)
                sheets.append(SheetInfo(
                    name=name,
                    n_rows=len(full),
                    n_cols=len(full.columns),
                    columns=[str(c) for c in full.columns],
                ))
            except Exception:
                sheets.append(SheetInfo(name=name, n_rows=0, n_cols=0, columns=[]))
        return sheets

    def load(self, request: LoadRequest) -> Dataset:
        try:
            xls = pd.ExcelFile(io.BytesIO(request.content))
        except Exception as e:
            raise LoaderError(f"Could not open Excel workbook '{request.filename}': {e}")

        available_sheets = self.list_sheets(request.content)
        sheet_name = request.sheet_name or xls.sheet_names[0]
        if sheet_name not in xls.sheet_names:
            raise LoaderError(f"Sheet '{sheet_name}' not found in workbook.")

        try:
            df = xls.parse(sheet_name)
        except Exception as e:
            raise LoaderError(f"Failed to parse sheet '{sheet_name}': {e}")

        df = self.normalize_dataframe(df)

        return Dataset.new(
            df=df,
            original_filename=request.filename,
            file_format="xlsx/xls",
            file_size_bytes=len(request.content),
            sheet_name=sheet_name,
            available_sheets=available_sheets,
        )
