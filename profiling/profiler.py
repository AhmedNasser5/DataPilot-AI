"""
Dataset Profiling Engine.

Produces a DatasetProfile containing per-column statistics, detected
types, semantic guesses, and structural flags (constant, high
cardinality, possible ID/PK, etc). All numbers here come from actual
pandas/numpy/scipy computation — nothing is estimated by an LLM.
"""
from __future__ import annotations

import re
from datetime import datetime, timezone

import numpy as np
import pandas as pd
from scipy import stats as scipy_stats

from config.settings import settings
from core.profiling.semantic_detector import SemanticDetector
from core.profiling.type_detector import TypeDetector
from models.dataset import Dataset
from models.profile import ColumnProfile, DatasetProfile


def normalize_column_name(name: str) -> str:
    n = str(name).strip().lower()
    n = re.sub(r"[^\w]+", "_", n, flags=re.UNICODE)
    n = re.sub(r"_+", "_", n).strip("_")
    return n or "column"


class DatasetProfiler:
    def __init__(self):
        self._type_detector = TypeDetector()
        self._semantic_detector = SemanticDetector()

    def profile(self, dataset: Dataset) -> DatasetProfile:
        df = dataset.dataframe
        n_rows = len(df)

        columns: dict[str, ColumnProfile] = {}
        normalized_seen: dict[str, int] = {}

        for col in df.columns:
            series = df[col]
            columns[col] = self._profile_column(col, series, n_rows, normalized_seen)

        self._flag_possible_primary_keys(columns, n_rows)

        return DatasetProfile(
            dataset_id=dataset.metadata.dataset_id,
            version=dataset.version,
            row_count=n_rows,
            column_count=len(df.columns),
            estimated_memory_mb=round(dataset.metadata.estimated_memory_bytes / (1024 * 1024), 3),
            columns=columns,
            generated_at=datetime.now(timezone.utc).isoformat(),
        )

    def _profile_column(self, col_name: str, series: pd.Series, n_rows: int,
                         normalized_seen: dict[str, int]) -> ColumnProfile:
        norm = normalize_column_name(col_name)
        if norm in normalized_seen:
            normalized_seen[norm] += 1
            norm = f"{norm}_{normalized_seen[norm]}"
        else:
            normalized_seen[norm] = 0

        null_count = int(series.isna().sum())
        # also count "empty-looking" strings for object columns as informational
        non_null = series.dropna()
        unique_count = int(non_null.nunique())

        type_result = self._type_detector.detect(series)
        is_numeric = type_result.detected_type == "numeric" and not type_result.numeric_as_text

        semantic = self._semantic_detector.detect(col_name, series, is_numeric)

        profile = ColumnProfile(
            original_name=col_name,
            normalized_name=norm,
            pandas_dtype=str(series.dtype),
            detected_type=type_result.detected_type,
            semantic_types=semantic,
            null_count=null_count,
            null_percentage=round(100 * null_count / n_rows, 2) if n_rows else 0.0,
            unique_count=unique_count,
            unique_percentage=round(100 * unique_count / n_rows, 2) if n_rows else 0.0,
            cardinality=unique_count,
        )

        if type_result.numeric_as_text:
            profile.flags.append("numeric_stored_as_text")
        if type_result.date_as_text:
            profile.flags.append("date_stored_as_text")

        if is_numeric and not non_null.empty:
            self._fill_numeric_stats(profile, non_null.astype(float))
        elif not non_null.empty:
            self._fill_categorical_stats(profile, non_null)

        # structural flags
        if n_rows > 0:
            if unique_count <= 1:
                profile.is_constant = True
                profile.flags.append("constant_column")
            elif (unique_count / n_rows) >= settings.near_constant_threshold and unique_count > 1:
                # near constant defined as: dominated by a single value, not high unique ratio
                top_freq_ratio = non_null.value_counts(normalize=True).iloc[0] if not non_null.empty else 0
                if top_freq_ratio >= settings.near_constant_threshold:
                    profile.is_near_constant = True
                    profile.flags.append("near_constant_column")

            if (unique_count / n_rows) >= settings.high_cardinality_ratio:
                profile.is_high_cardinality = True
                profile.flags.append("high_cardinality")

            name_l = col_name.lower()
            name_hints_id = any(h in name_l for h in ("id", "_id", "uuid", "code", "key"))
            # A datetime column being high-cardinality is normal (many distinct timestamps)
            # and is NOT identifier-like on its own; only count high-cardinality as an ID
            # signal for non-datetime columns.
            cardinality_hints_id = profile.is_high_cardinality and profile.detected_type != "datetime"
            if (name_hints_id or cardinality_hints_id) and unique_count / n_rows > 0.9:
                profile.is_possible_id = True
                profile.flags.append("possible_id_column")

        if null_count == n_rows and n_rows > 0:
            profile.detected_type = "empty"
            profile.flags.append("empty_column")

        return profile

    def _fill_numeric_stats(self, profile: ColumnProfile, series: pd.Series) -> None:
        profile.zero_count = int((series == 0).sum())
        profile.negative_count = int((series < 0).sum())
        profile.minimum = float(series.min())
        profile.maximum = float(series.max())
        profile.mean = float(series.mean())
        profile.median = float(series.median())
        try:
            profile.mode = float(series.mode().iloc[0]) if not series.mode().empty else None
        except Exception:
            profile.mode = None
        profile.std = float(series.std()) if len(series) > 1 else 0.0
        profile.variance = float(series.var()) if len(series) > 1 else 0.0
        try:
            q = series.quantile([0.05, 0.25, 0.5, 0.75, 0.95])
            profile.quantiles = {f"p{int(k*100)}": float(v) for k, v in q.items()}
        except Exception:
            profile.quantiles = {}
        if len(series) >= 3 and series.std() > 0:
            try:
                profile.skewness = float(scipy_stats.skew(series))
                profile.kurtosis = float(scipy_stats.kurtosis(series))
            except Exception:
                pass
        vc = series.value_counts().head(5)
        profile.most_frequent_values = [(float(k), int(v)) for k, v in vc.items()]
        profile.sample_values = [float(v) for v in series.head(5).tolist()]

    def _fill_categorical_stats(self, profile: ColumnProfile, series: pd.Series) -> None:
        vc = series.value_counts().head(5)
        profile.most_frequent_values = [(str(k), int(v)) for k, v in vc.items()]
        try:
            profile.mode = str(series.mode().iloc[0]) if not series.mode().empty else None
        except Exception:
            profile.mode = None
        profile.sample_values = [str(v) for v in series.head(5).tolist()]

    def _flag_possible_primary_keys(self, columns: dict[str, ColumnProfile], n_rows: int) -> None:
        if n_rows == 0:
            return
        candidates = [
            c for c in columns.values()
            if c.unique_count == n_rows and c.null_count == 0 and n_rows > 0
        ]
        if not candidates:
            return
        # Prefer the one whose name looks like an id column, else the first
        candidates.sort(key=lambda c: (0 if "id" in c.original_name.lower() else 1))
        candidates[0].is_possible_primary_key = True
        candidates[0].flags.append("possible_primary_key")
