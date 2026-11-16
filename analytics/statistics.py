"""Descriptive statistical analysis, computed with pandas/numpy/scipy only."""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats as scipy_stats


class StatisticsEngine:
    def numeric_summary(self, series: pd.Series) -> dict:
        s = pd.to_numeric(series, errors="coerce").dropna()
        if s.empty:
            return {"error": "No numeric data available."}
        return {
            "count": int(s.count()),
            "mean": float(s.mean()),
            "median": float(s.median()),
            "std": float(s.std()) if len(s) > 1 else 0.0,
            "variance": float(s.var()) if len(s) > 1 else 0.0,
            "min": float(s.min()),
            "max": float(s.max()),
            "q1": float(s.quantile(0.25)),
            "q3": float(s.quantile(0.75)),
            "skewness": float(scipy_stats.skew(s)) if len(s) > 2 else None,
            "kurtosis": float(scipy_stats.kurtosis(s)) if len(s) > 2 else None,
        }

    def categorical_summary(self, series: pd.Series) -> dict:
        s = series.dropna().astype(str)
        if s.empty:
            return {"error": "No categorical data available."}
        counts = s.value_counts()
        proportions = s.value_counts(normalize=True)
        entropy = float(scipy_stats.entropy(counts)) if len(counts) > 1 else 0.0
        return {
            "cardinality": int(s.nunique()),
            "top_values": [(k, int(v)) for k, v in counts.head(10).items()],
            "top_proportions": [(k, round(float(v) * 100, 2)) for k, v in proportions.head(10).items()],
            "entropy": round(entropy, 4),
        }


statistics_engine = StatisticsEngine()
