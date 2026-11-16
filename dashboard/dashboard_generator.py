"""
Turns a ChartRecommendation into an actual Plotly figure, computed
from the real dataframe (via pandas aggregation). No chart is ever
rendered from invented data.
"""
from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from models.analysis import ChartRecommendation

_LABEL_MAX_LEN = 20


def _truncate(label: str, max_len: int = _LABEL_MAX_LEN) -> str:
    s = str(label)
    return s if len(s) <= max_len else s[: max_len - 1] + "…"


class DashboardGenerator:
    def build_figure(self, df: pd.DataFrame, chart: ChartRecommendation):
        try:
            if chart.chart_type == "line":
                return self._line(df, chart)
            if chart.chart_type == "bar":
                return self._bar(df, chart)
            if chart.chart_type == "bar_h":
                return self._bar_h(df, chart)
            if chart.chart_type == "donut":
                return self._donut(df, chart)
            if chart.chart_type == "scatter":
                return self._scatter(df, chart)
            if chart.chart_type == "histogram":
                return self._histogram(df, chart)
            if chart.chart_type == "box":
                return self._box(df, chart)
            if chart.chart_type == "heatmap":
                return self._heatmap(df, chart)
            if chart.chart_type == "table":
                return self._table(df, chart)
        except Exception as e:
            fig = go.Figure()
            fig.add_annotation(text=f"Could not render chart: {e}", showarrow=False)
            return fig
        return None

    def _line(self, df, chart: ChartRecommendation):
        date_col, value_col = chart.columns
        work = df[[date_col, value_col]].copy()
        work[date_col] = pd.to_datetime(work[date_col], errors="coerce")
        work[value_col] = pd.to_numeric(work[value_col], errors="coerce")
        work = work.dropna()

        # "ME" (Month-End) is the modern pandas offset alias. The bare
        # "M" alias is deprecated/removed on current pandas and raises
        # ValueError — always use "ME" (or "YE" for long ranges).
        freq = "YE" if work[date_col].dt.to_period("M").nunique() > 36 else "ME"
        grouped = work.set_index(date_col).resample(freq)[value_col].sum().reset_index()

        fig = px.line(grouped, x=date_col, y=value_col, markers=True, title=chart.title)
        fig.update_yaxes(tickformat=".2s")
        return fig

    def _prep_category_agg(self, df, cat_col, val_col, aggregation, top_n=12):
        work = df[[cat_col, val_col]].copy() if val_col else df[[cat_col]].copy()
        if val_col:
            work[val_col] = pd.to_numeric(work[val_col], errors="coerce")
            if aggregation == "count":
                grouped = work.groupby(cat_col).size().reset_index(name=val_col)
            else:
                grouped = work.groupby(cat_col, dropna=True)[val_col].sum().reset_index()
        else:
            grouped = work[cat_col].value_counts().reset_index()
            grouped.columns = [cat_col, "count"]
            val_col = "count"
        grouped = grouped.sort_values(val_col, ascending=False).head(top_n)
        grouped["__label"] = grouped[cat_col].astype(str).map(_truncate)
        return grouped, val_col

    def _bar(self, df, chart: ChartRecommendation):
        cat_col = chart.columns[0]
        val_col = chart.columns[1] if len(chart.columns) == 2 else None
        grouped, val_col = self._prep_category_agg(df, cat_col, val_col, chart.aggregation)
        fig = px.bar(grouped, x="__label", y=val_col, title=chart.title,
                     hover_name=cat_col, labels={"__label": cat_col})
        fig.update_yaxes(tickformat=".2s")
        return fig

    def _bar_h(self, df, chart: ChartRecommendation):
        """Horizontal ranking bar — the preferred layout for category rankings
        since it avoids rotated/overlapping x-axis labels."""
        cat_col = chart.columns[0]
        val_col = chart.columns[1] if len(chart.columns) == 2 else None
        grouped, val_col = self._prep_category_agg(df, cat_col, val_col, chart.aggregation, top_n=12)
        grouped = grouped.sort_values(val_col, ascending=True)  # so the top item renders at the top visually
        fig = px.bar(grouped, x=val_col, y="__label", orientation="h", title=chart.title,
                     hover_name=cat_col, labels={"__label": cat_col})
        fig.update_xaxes(tickformat=".2s")
        fig.update_layout(yaxis=dict(automargin=True))
        return fig

    def _donut(self, df, chart: ChartRecommendation):
        """Composition chart: top N categories by the metric, remainder grouped as 'Other'."""
        cat_col = chart.columns[0]
        val_col = chart.columns[1] if len(chart.columns) == 2 else None
        work = df[[cat_col, val_col]].copy() if val_col else df[[cat_col]].copy()
        if val_col:
            work[val_col] = pd.to_numeric(work[val_col], errors="coerce")
            grouped = work.groupby(cat_col, dropna=True)[val_col].sum().reset_index()
        else:
            grouped = work[cat_col].value_counts().reset_index()
            grouped.columns = [cat_col, "count"]
            val_col = "count"
        grouped = grouped.sort_values(val_col, ascending=False)

        top_n = 7
        if len(grouped) > top_n:
            head = grouped.head(top_n).copy()
            other_total = grouped.iloc[top_n:][val_col].sum()
            other_row = pd.DataFrame({cat_col: ["Other"], val_col: [other_total]})
            grouped = pd.concat([head, other_row], ignore_index=True)
        grouped["__label"] = grouped[cat_col].astype(str).map(_truncate)

        fig = px.pie(grouped, names="__label", values=val_col, title=chart.title, hole=0.55)
        fig.update_traces(textposition="outside", textinfo="label+percent")
        return fig

    def _scatter(self, df, chart: ChartRecommendation):
        x_col, y_col = chart.columns
        work = df[[x_col, y_col]].apply(pd.to_numeric, errors="coerce").dropna()
        fig = px.scatter(work, x=x_col, y=y_col, title=chart.title, opacity=0.65)
        fig.update_xaxes(tickformat=".2s")
        fig.update_yaxes(tickformat=".2s")
        return fig

    def _histogram(self, df, chart: ChartRecommendation):
        col = chart.columns[0]
        series = pd.to_numeric(df[col], errors="coerce").dropna()
        fig = px.histogram(series, x=col if col in series.to_frame().columns else 0, title=chart.title, nbins=30)
        fig.update_layout(showlegend=False)
        fig.update_xaxes(tickformat=".2s")
        return fig

    def _box(self, df, chart: ChartRecommendation):
        col = chart.columns[0]
        series = pd.to_numeric(df[col], errors="coerce").dropna()
        fig = px.box(series.to_frame(name=col), y=col, title=chart.title)
        fig.update_yaxes(tickformat=".2s")
        return fig

    def _heatmap(self, df, chart: ChartRecommendation):
        numeric_df = df[chart.columns].apply(pd.to_numeric, errors="coerce")
        corr = numeric_df.corr(method="pearson")
        fig = px.imshow(corr, text_auto=".2f", color_continuous_scale="RdBu_r", zmin=-1, zmax=1, title=chart.title)
        return fig

    def _table(self, df, chart: ChartRecommendation):
        cols = [c for c in chart.columns if c in df.columns]
        sample = df[cols].head(50)
        fig = go.Figure(data=[go.Table(
            header=dict(values=list(sample.columns), fill_color="#0369A1", font=dict(color="white"), align="left"),
            cells=dict(values=[sample[c].astype(str) for c in sample.columns], align="left"),
        )])
        fig.update_layout(title=chart.title)
        return fig


dashboard_generator = DashboardGenerator()
