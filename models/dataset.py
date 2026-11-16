"""
Unified Dataset representation.

Every loader (CSV, Excel, JSON, Parquet, ...) must normalize its
output into this structure so the rest of the system never needs
to know where the data came from.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

import pandas as pd


@dataclass
class SheetInfo:
    """Metadata about one sheet in a multi-sheet Excel workbook."""
    name: str
    n_rows: int
    n_cols: int
    columns: list[str] = field(default_factory=list)


@dataclass
class DatasetMetadata:
    dataset_id: str
    original_filename: str
    file_format: str
    file_size_bytes: int
    row_count: int
    column_count: int
    estimated_memory_bytes: int
    created_at: str
    sheet_name: Optional[str] = None
    available_sheets: list[SheetInfo] = field(default_factory=list)


@dataclass
class Dataset:
    """
    A single in-memory dataset version.

    `version` follows the convention: v1 (original), v2 (cleaned), ...
    The DataFrame itself is the source of truth; `metadata` is derived
    from it at construction/refresh time.
    """
    dataframe: pd.DataFrame
    metadata: DatasetMetadata
    version: str = "v1"
    version_label: str = "Original"
    parent_version: Optional[str] = None

    @staticmethod
    def new(
        df: pd.DataFrame,
        original_filename: str,
        file_format: str,
        file_size_bytes: int,
        sheet_name: Optional[str] = None,
        available_sheets: Optional[list[SheetInfo]] = None,
        dataset_id: Optional[str] = None,
    ) -> "Dataset":
        meta = DatasetMetadata(
            dataset_id=dataset_id or str(uuid.uuid4())[:8],
            original_filename=original_filename,
            file_format=file_format,
            file_size_bytes=file_size_bytes,
            row_count=len(df),
            column_count=len(df.columns),
            estimated_memory_bytes=int(df.memory_usage(deep=True).sum()),
            created_at=datetime.now(timezone.utc).isoformat(),
            sheet_name=sheet_name,
            available_sheets=available_sheets or [],
        )
        return Dataset(dataframe=df, metadata=meta, version="v1", version_label="Original")

    def derive(self, new_df: pd.DataFrame, version: str, version_label: str) -> "Dataset":
        """Create a new Dataset version from a transformed dataframe, without
        mutating self. The original object is never overwritten."""
        new_meta = DatasetMetadata(
            dataset_id=self.metadata.dataset_id,
            original_filename=self.metadata.original_filename,
            file_format=self.metadata.file_format,
            file_size_bytes=self.metadata.file_size_bytes,
            row_count=len(new_df),
            column_count=len(new_df.columns),
            estimated_memory_bytes=int(new_df.memory_usage(deep=True).sum()),
            created_at=datetime.now(timezone.utc).isoformat(),
            sheet_name=self.metadata.sheet_name,
            available_sheets=self.metadata.available_sheets,
        )
        return Dataset(
            dataframe=new_df,
            metadata=new_meta,
            version=version,
            version_label=version_label,
            parent_version=self.version,
        )
