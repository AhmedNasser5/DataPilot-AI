"""Distribution helpers: histogram bucketing and category frequency shares."""
from __future__ import annotations

import numpy as np
import pandas as pd


class DistributionEngine:
    def histogram(self, series: pd.Series, bins: int = 20) -> dict:
        s = pd.to_numeric(series, errors="coerce").dropna()
        if s.empty:
            return {"error": "No numeric data to build a histogram."}
        counts, edges = np.histogram(s, bins=bins)
        return {
            "counts": counts.tolist(),
            "bin_edges": [round(float(e), 4) for e in edges],
        }

    def category_shares(self, series: pd.Series, top_n: int = 15) -> dict:
        s = series.dropna().astype(str)
        if s.empty:
            return {"error": "No categorical data to summarize."}
        vc = s.value_counts(normalize=True).head(top_n)
        return {"categories": vc.index.tolist(), "shares": [round(float(v) * 100, 2) for v in vc.values]}


distribution_engine = DistributionEngine()
