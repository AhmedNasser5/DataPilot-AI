"""
Anomaly detection for analytical exploration (as opposed to the
quality engine's outlier flagging, which drives cleaning suggestions).
Same underlying techniques, exposed for ad-hoc "what's anomalous here"
analysis in the AI Analyst / KPI Explorer.
"""
from __future__ import annotations

import pandas as pd

from core.quality.outliers import OutlierDetector


class AnomalyDetectionEngine:
    def __init__(self):
        self._detector = OutlierDetector()

    def analyze_column(self, df: pd.DataFrame, column: str) -> dict:
        series = pd.to_numeric(df[column], errors="coerce").dropna()
        if len(series) < 8 or series.std() == 0:
            return {"error": "Not enough numeric variation to run anomaly detection."}

        method, mask = self._detector._select_and_run(series)
        anomalous = series[mask]
        return {
            "method": method,
            "reason_for_method": self._reason(method),
            "total_values": len(series),
            "anomaly_count": int(mask.sum()),
            "anomaly_pct": round(100 * mask.sum() / len(series), 2),
            "anomalous_values_sample": anomalous.head(20).tolist(),
            "limitations": (
                "Statistical anomaly detection flags unusual values; it does not confirm "
                "whether they are data errors or genuine rare events. Domain review is recommended."
            ),
        }

    @staticmethod
    def _reason(method: str) -> str:
        if "IQR" in method:
            return "Small sample size: IQR is a simple, robust choice for limited data."
        if "Modified Z-score" in method:
            return "Distribution is notably skewed: median/MAD-based scoring resists distortion by extreme values."
        if "Isolation Forest" in method:
            return "Larger sample size allows a model-based method to capture more complex anomaly patterns."
        return "Z-score was used as the general-purpose default for roughly-symmetric, moderate-size data."


anomaly_detection_engine = AnomalyDetectionEngine()
