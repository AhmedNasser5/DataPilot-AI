"""
Chart Recommendation Engine.

Recommends visualizations in a deliberate priority order that mirrors
how a BI analyst would structure a report: trend first, then category
rankings, then composition, then geography, then distribution/outliers,
then correlation — never generic/meaningless charts. Category rankings
are always horizontal bars (readable labels, no rotated text) and
composition uses a donut instead of a flat "record count" bar.
"""
from __future__ import annotations

import uuid

from models.analysis import ChartRecommendation
from models.profile import DatasetProfile

_GEO_HINTS = ("country", "region", "location", "city", "state", "province", "governorate")


class ChartRecommender:
    def recommend(self, profile: DatasetProfile, max_charts: int = 8) -> list[ChartRecommendation]:
        charts: list[ChartRecommendation] = []
        cols = profile.columns

        date_cols = [n for n, c in cols.items() if c.detected_type == "datetime"]
        numeric_cols = [n for n, c in cols.items() if c.detected_type == "numeric" and not c.is_possible_id]
        category_cols = [n for n, c in cols.items() if c.detected_type == "categorical" and not c.is_high_cardinality]
        amount_cols = [n for n, c in cols.items() if any(g.label == "currency" for g in c.semantic_types)]

        primary_metric = amount_cols[0] if amount_cols else (numeric_cols[0] if numeric_cols else None)
        geo_col = next((c for c in category_cols if any(h in c.lower() for h in _GEO_HINTS)), None)
        ranking_col = next((c for c in category_cols if c != geo_col), None)

        # 1) Trend — time series (highest priority: reveals seasonality/growth)
        if date_cols and primary_metric:
            charts.append(self._chart(
                f"{primary_metric} Trend Over Time", "line", [date_cols[0], primary_metric], "sum",
                "A time dimension and a numerical metric were detected.",
                "Identify growth, decline, and seasonality over time.",
            ))

        # 2) Category ranking — horizontal bar (readable at any label length)
        if ranking_col and primary_metric:
            charts.append(self._chart(
                f"Top {ranking_col} by {primary_metric}", "bar_h", [ranking_col, primary_metric], "sum",
                "A categorical dimension and a numerical metric were detected.",
                "Rank categories to spot the largest contributors at a glance.",
            ))

        # 3) Composition — donut (top segments + "Other"), more informative than a flat count bar
        if ranking_col:
            charts.append(self._chart(
                f"Share of {'Total ' + primary_metric if primary_metric else 'Records'} by {ranking_col}",
                "donut", [ranking_col, primary_metric] if primary_metric else [ranking_col],
                "sum" if primary_metric else "count",
                "A categorical column with a meaningful metric to distribute across it was detected.",
                "Show the proportional composition of the top contributors versus everything else.",
            ))

        # 4) Geography — a second, distinct categorical dimension read as location
        if geo_col and primary_metric:
            charts.append(self._chart(
                f"{primary_metric} by {geo_col}", "bar_h", [geo_col, primary_metric], "sum",
                "A location-like categorical column was detected, separate from the primary ranking dimension.",
                "Understand the geographic/regional distribution of the metric.",
            ))
        elif len(category_cols) > 1 and primary_metric:
            second_col = next((c for c in category_cols if c != ranking_col), None)
            if second_col:
                charts.append(self._chart(
                    f"{primary_metric} by {second_col}", "bar_h", [second_col, primary_metric], "sum",
                    "An additional categorical dimension was detected.",
                    "Explore a second angle of category performance.",
                ))

        # 5) Relationship — two numerics
        if len(numeric_cols) >= 2:
            charts.append(self._chart(
                f"{numeric_cols[0]} vs {numeric_cols[1]}", "scatter", [numeric_cols[0], numeric_cols[1]], None,
                "Two numerical variables were detected.",
                "Explore the relationship/correlation between two metrics.",
            ))

        # 6) Distribution / outliers
        if primary_metric or numeric_cols:
            dist_col = primary_metric or numeric_cols[0]
            charts.append(self._chart(
                f"Distribution of {dist_col}", "histogram", [dist_col], None,
                "A numerical column with sufficient spread was detected.",
                "Understand the shape, skew, and spread of the values.",
            ))
            second_numeric = next((c for c in numeric_cols if c != dist_col), None)
            if second_numeric:
                charts.append(self._chart(
                    f"Box Plot of {second_numeric}", "box", [second_numeric], None,
                    "An additional numerical column was detected.",
                    "Visualize quartiles and potential outliers at a glance.",
                ))

        # 7) Correlation heatmap once there's enough numeric structure
        if len(numeric_cols) >= 3:
            charts.append(self._chart(
                "Correlation Heatmap", "heatmap", numeric_cols[:8], None,
                "Three or more numerical columns were detected.",
                "Spot pairs of metrics that move together.",
            ))

        # Fallback so the dashboard is never empty
        if not charts:
            charts.append(self._chart(
                "Data Table (Sample)", "table", list(cols.keys())[:15], None,
                "No clear numeric/categorical/date combination was detected for a specialized chart.",
                "Provide a direct view of the underlying data.",
            ))

        return charts[:max_charts]

    @staticmethod
    def _chart(title, chart_type, columns, agg, reason, purpose) -> ChartRecommendation:
        return ChartRecommendation(
            chart_id=f"CH-{uuid.uuid4().hex[:6]}", title=title, chart_type=chart_type,
            columns=columns, aggregation=agg, reason=reason, purpose=purpose,
        )


chart_recommender = ChartRecommender()
