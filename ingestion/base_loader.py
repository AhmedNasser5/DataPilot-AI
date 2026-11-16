"""Abstract base class every format loader must implement."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

import pandas as pd

from models.dataset import Dataset


@dataclass
class LoadRequest:
    filename: str
    content: bytes
    sheet_name: Optional[str] = None   # for multi-sheet Excel selection


class LoaderError(Exception):
    """Raised when a file cannot be parsed by a loader, with a user-friendly message."""


class BaseLoader(ABC):
    format_names: tuple[str, ...] = ()

    @abstractmethod
    def load(self, request: LoadRequest) -> Dataset:
        """Parse raw bytes into a normalized Dataset."""

    @staticmethod
    def normalize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
        """Common normalization applied after any loader parses a dataframe:
        - strip whitespace from column names
        - deduplicate identical column names
        - reset index
        """
        df = df.copy()
        new_cols = [str(c).strip() for c in df.columns]
        seen: dict[str, int] = {}
        deduped = []
        for c in new_cols:
            if c in seen:
                seen[c] += 1
                deduped.append(f"{c}__dup{seen[c]}")
            else:
                seen[c] = 0
                deduped.append(c)
        df.columns = deduped
        df = df.reset_index(drop=True)
        return df
