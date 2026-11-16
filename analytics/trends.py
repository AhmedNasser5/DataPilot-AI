"""Simple, honest trend detection over a date + numeric metric pair."""
from __future__ import annotations

import numpy as np
import pandas as pd


class TrendEngine:
    def detect_trend(self, df: pd.DataFrame, date_col: str, value_col: str, freq: str = "M") -> dict:
        work = df[[date_col, value_col]].copy()
        work[date_col] = pd.to_datetime(work[date_col], errors="coerce")
        work[value_col] = pd.to_numeric(work[value_col], errors="coerce")
        work = work.dropna()
        if len(work) < 3:
            return {"error": "Not enough valid (date, value) pairs to compute a trend."}

        resampled = work.set_index(date_col)[value_col].resample(freq).sum(min_count=1).dropna()
        if len(resampled) < 2:
            return {"error": "Not enough periods after resampling to compute a trend."}

        x = np.arange(len(resampled))
        y = resampled.values.astype(float)
        slope, intercept = np.polyfit(x, y, 1)

        pct_change_total = ((y[-1] - y[0]) / y[0] * 100) if y[0] != 0 else None
        direction = "increasing" if slope > 0 else ("decreasing" if slope < 0 else "flat")

        return {
            "periods": [str(p.date()) for p in resampled.index],
            "values": [float(v) for v in y],
            "slope_per_period": float(slope),
            "direction": direction,
            "total_pct_change": round(pct_change_total, 2) if pct_change_total is not None else None,
            "first_period_value": float(y[0]),
            "last_period_value": float(y[-1]),
        }


trend_engine = TrendEngine()
