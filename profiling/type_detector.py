"""
Detects the effective data type of each column, going beyond the raw
pandas dtype: numeric-as-text, dates-as-text, booleans, etc.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

import numpy as np
import pandas as pd
from dateutil import parser as dateutil_parser

def is_text_like_dtype(series: pd.Series) -> bool:
    """True for classic object-dtype columns AND pandas' newer dedicated
    string dtype (default in pandas >= 3.0). Centralizing this check avoids
    scattering pandas-version-sensitive dtype comparisons across the codebase."""
    return bool(pd.api.types.is_object_dtype(series) or pd.api.types.is_string_dtype(series))


_BOOL_TRUE = {"true", "yes", "y", "1", "t"}
_BOOL_FALSE = {"false", "no", "n", "0", "f"}
_NUMERIC_CLEAN_RE = re.compile(r"^[\s\$€£¥،,\.\-\+%\d]+$")


@dataclass
class TypeDetectionResult:
    detected_type: str          # numeric | categorical | boolean | datetime | text | id | empty
    confidence: float
    evidence: str
    numeric_as_text: bool = False
    date_as_text: bool = False


class TypeDetector:
    """Column-level effective-type inference."""

    def detect(self, series: pd.Series) -> TypeDetectionResult:
        non_null = series.dropna()
        if non_null.empty:
            return TypeDetectionResult("empty", 1.0, "Column has no non-null values.")

        if pd.api.types.is_bool_dtype(series):
            return TypeDetectionResult("boolean", 1.0, "Native pandas boolean dtype.")

        if pd.api.types.is_numeric_dtype(series):
            return self._classify_numeric(series, non_null)

        if pd.api.types.is_datetime64_any_dtype(series):
            return TypeDetectionResult("datetime", 1.0, "Native pandas datetime dtype.")

        # Object/string columns need heuristic sniffing
        sample = non_null.astype(str).str.strip()
        sample_lower = sample.str.lower()

        bool_hits = sample_lower.isin(_BOOL_TRUE | _BOOL_FALSE).mean()
        if bool_hits > 0.95 and sample_lower.nunique() <= 2:
            return TypeDetectionResult("boolean", float(bool_hits), "Values map to boolean-like tokens.", )

        numeric_like = self._numeric_like_ratio(sample)
        if numeric_like > 0.9:
            return TypeDetectionResult(
                "numeric", numeric_like,
                "Text values are almost entirely numeric-looking (numbers stored as text).",
                numeric_as_text=True,
            )

        date_like = self._date_like_ratio(sample)
        if date_like > 0.85:
            return TypeDetectionResult(
                "datetime", date_like,
                "Text values are almost entirely parseable as dates (dates stored as text).",
                date_as_text=True,
            )

        unique_ratio = sample.nunique() / max(len(sample), 1)
        avg_len = sample.str.len().mean()
        if unique_ratio > 0.5 and avg_len > 20:
            return TypeDetectionResult("text", 0.7, "High cardinality and long average length suggest free text.")

        return TypeDetectionResult("categorical", 0.75, "Discrete set of repeated text values.")

    def _classify_numeric(self, series: pd.Series, non_null: pd.Series) -> TypeDetectionResult:
        unique_ratio = non_null.nunique() / max(len(non_null), 1)
        all_int_like = np.all(np.equal(np.mod(non_null, 1), 0)) if len(non_null) else False
        if all_int_like and non_null.nunique() <= 2 and set(non_null.unique()).issubset({0, 1}):
            return TypeDetectionResult("boolean", 0.9, "Numeric column restricted to {0,1}.")
        return TypeDetectionResult("numeric", 1.0, "Native numeric dtype.")

    @staticmethod
    def _numeric_like_ratio(sample: pd.Series) -> float:
        cleaned = sample.str.replace(r"[,\s\$€£¥%]", "", regex=True)
        def _is_num(v: str) -> bool:
            try:
                float(v)
                return True
            except ValueError:
                return False
        return cleaned.map(_is_num).mean() if len(cleaned) else 0.0

    @staticmethod
    def _date_like_ratio(sample: pd.Series) -> float:
        subset = sample.head(200)  # cap cost
        hits = 0
        for v in subset:
            if len(v) < 6 or len(v) > 35:
                continue
            try:
                dateutil_parser.parse(v, fuzzy=False)
                hits += 1
            except (ValueError, OverflowError, TypeError):
                continue
        return hits / max(len(subset), 1)
