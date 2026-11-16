"""
Relationship / correlation analysis.

Chooses a statistically appropriate method:
- numeric vs numeric  -> Pearson (linear) and Spearman (monotonic)
- categorical vs categorical -> Cramer's V
Never computes correlation between incompatible types.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats as scipy_stats


class CorrelationEngine:
    def numeric_correlation_matrix(self, df: pd.DataFrame, columns: list[str], method: str = "pearson") -> pd.DataFrame:
        if method not in ("pearson", "spearman"):
            raise ValueError("method must be 'pearson' or 'spearman'")
        numeric_df = df[columns].apply(pd.to_numeric, errors="coerce")
        return numeric_df.corr(method=method)

    def cramers_v(self, series_a: pd.Series, series_b: pd.Series) -> float | None:
        contingency = pd.crosstab(series_a.dropna(), series_b.dropna())
        if contingency.size == 0 or contingency.shape[0] < 2 or contingency.shape[1] < 2:
            return None
        chi2 = scipy_stats.chi2_contingency(contingency, correction=False)[0]
        n = contingency.sum().sum()
        phi2 = chi2 / n
        r, k = contingency.shape
        phi2corr = max(0, phi2 - ((k - 1) * (r - 1)) / (n - 1))
        rcorr = r - ((r - 1) ** 2) / (n - 1)
        kcorr = k - ((k - 1) ** 2) / (n - 1)
        denom = min((kcorr - 1), (rcorr - 1))
        if denom <= 0:
            return None
        return float(np.sqrt(phi2corr / denom))

    def top_correlated_pairs(self, corr_matrix: pd.DataFrame, top_n: int = 10, min_abs: float = 0.3) -> list[tuple[str, str, float]]:
        pairs = []
        cols = corr_matrix.columns
        for i, c1 in enumerate(cols):
            for c2 in cols[i + 1:]:
                val = corr_matrix.loc[c1, c2]
                if pd.notna(val) and abs(val) >= min_abs:
                    pairs.append((c1, c2, round(float(val), 3)))
        pairs.sort(key=lambda p: abs(p[2]), reverse=True)
        return pairs[:top_n]


correlation_engine = CorrelationEngine()
