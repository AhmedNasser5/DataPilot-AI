"""
Outlier / anomaly detection.

CRITICAL POLICY: outliers are FLAGGED, never silently removed.
Method is selected based on dataset characteristics rather than
blindly running every algorithm on every column.
"""
from __future__ import annotations

import uuid

import numpy as np
import pandas as pd

from config.settings import settings
from models.profile import ColumnProfile
from models.quality import QualityIssue, Severity


class OutlierDetector:
    def detect(self, df: pd.DataFrame, column_profiles: dict[str, ColumnProfile]) -> list[QualityIssue]:
        issues: list[QualityIssue] = []
        numeric_cols = [
            c for c, p in column_profiles.items()
            if p.detected_type == "numeric" and c in df.columns
            and not p.is_possible_id and not p.is_possible_primary_key
        ]

        for col in numeric_cols:
            series = pd.to_numeric(df[col], errors="coerce").dropna()
            n = len(series)
            if n < 8 or series.std() == 0:
                continue

            method, mask = self._select_and_run(series)
            count = int(mask.sum())
            if count == 0:
                continue
            pct = 100 * count / n
            issues.append(QualityIssue(
                issue_id=f"OUT-{uuid.uuid4().hex[:8]}",
                column=col,
                category="outlier",
                description=(
                    f"{count} potential outlier(s) detected in '{col}' using {method} "
                    f"({pct:.1f}% of non-null values). Flagged only — not removed."
                ),
                severity=Severity.MEDIUM if pct < 5 else Severity.LOW,
                affected_rows=count,
                detection_method=method,
                confidence=0.75,
                details={"pct": round(pct, 2), "policy": "flag_not_remove"},
            ))
        return issues

    def _select_and_run(self, series: pd.Series) -> tuple[str, pd.Series]:
        n = len(series)
        skew = abs(series.skew()) if n > 2 else 0
        unique_ratio = series.nunique() / max(n, 1)

        # Low-cardinality discrete numeric data (e.g. ratings 1-5, quantity 1-10) is not
        # well suited to distribution-shape methods like Isolation Forest or Z-score,
        # which can flag the majority of common values as anomalous. IQR's quartile-based
        # range check degrades more gracefully on discrete/bounded data.
        if series.nunique() <= 20 or unique_ratio < 0.05:
            return self._iqr(series)

        if n < 30:
            return self._iqr(series)
        if skew > 1:
            # heavy skew: Modified Z-score (median/MAD based) is more robust than mean-based Z-score
            return self._modified_zscore(series)
        if n >= 200:
            try:
                return self._isolation_forest(series)
            except Exception:
                return self._zscore(series)
        return self._zscore(series)

    def _iqr(self, series: pd.Series) -> tuple[str, pd.Series]:
        q1, q3 = series.quantile(0.25), series.quantile(0.75)
        iqr = q3 - q1
        k = settings.outlier_iqr_multiplier
        lower, upper = q1 - k * iqr, q3 + k * iqr
        mask = (series < lower) | (series > upper)
        return f"IQR (k={k})", mask

    def _zscore(self, series: pd.Series) -> tuple[str, pd.Series]:
        z = (series - series.mean()) / series.std(ddof=0)
        threshold = settings.outlier_zscore_threshold
        mask = z.abs() > threshold
        return f"Z-score (threshold={threshold})", mask

    def _modified_zscore(self, series: pd.Series) -> tuple[str, pd.Series]:
        median = series.median()
        mad = (series - median).abs().median()
        if mad == 0:
            return self._iqr(series)
        mz = 0.6745 * (series - median) / mad
        mask = mz.abs() > 3.5
        return "Modified Z-score (MAD-based, threshold=3.5)", mask

    def _isolation_forest(self, series: pd.Series) -> tuple[str, pd.Series]:
        from sklearn.ensemble import IsolationForest
        X = series.values.reshape(-1, 1)
        model = IsolationForest(contamination="auto", random_state=42, n_estimators=100)
        pred = model.fit_predict(X)
        mask = pd.Series(pred == -1, index=series.index)
        return "Isolation Forest (n_estimators=100)", mask
