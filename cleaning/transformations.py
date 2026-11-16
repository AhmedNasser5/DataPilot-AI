"""
Deterministic transformation functions.

Each function takes a DataFrame + params and returns a NEW dataframe
(never mutates in place) plus a short description of what changed.
These are the actual operations the cleaning executor calls — the
LLM never performs the calculation itself, it only proposes which of
these to run and with what parameters.
"""
from __future__ import annotations

import re

import numpy as np
import pandas as pd
from dateutil import parser as dateutil_parser

from config.settings import settings


def trim_whitespace(df: pd.DataFrame, column: str) -> pd.DataFrame:
    out = df.copy()
    out[column] = out[column].map(lambda v: v.strip() if isinstance(v, str) else v)
    return out


def standardize_missing_markers(df: pd.DataFrame, column: str) -> pd.DataFrame:
    out = df.copy()
    markers = set(settings.missing_value_markers)

    def _fix(v):
        if isinstance(v, str) and v.strip().lower() in markers:
            return np.nan
        return v
    out[column] = out[column].map(_fix)
    return out


def standardize_boolean(df: pd.DataFrame, column: str) -> pd.DataFrame:
    out = df.copy()
    true_set = {"true", "yes", "y", "1", "t"}
    false_set = {"false", "no", "n", "0", "f"}

    def _fix(v):
        if pd.isna(v):
            return v
        s = str(v).strip().lower()
        if s in true_set:
            return True
        if s in false_set:
            return False
        return v
    out[column] = out[column].map(_fix)
    return out


def remove_exact_duplicate_rows(df: pd.DataFrame) -> pd.DataFrame:
    return df.drop_duplicates(keep="first").reset_index(drop=True)


def convert_numeric_text_to_numeric(df: pd.DataFrame, column: str) -> pd.DataFrame:
    out = df.copy()

    def _clean(v):
        if pd.isna(v):
            return np.nan
        s = str(v).strip()
        s = re.sub(r"[\$€£¥,،%\s]", "", s)
        try:
            return float(s)
        except ValueError:
            return np.nan
    out[column] = out[column].map(_clean)
    return out


def convert_text_to_datetime(df: pd.DataFrame, column: str) -> pd.DataFrame:
    out = df.copy()

    def _parse(v):
        if pd.isna(v):
            return pd.NaT
        try:
            return dateutil_parser.parse(str(v), fuzzy=False)
        except (ValueError, OverflowError, TypeError):
            return pd.NaT
    out[column] = out[column].map(_parse)
    return out


def median_imputation(df: pd.DataFrame, column: str) -> pd.DataFrame:
    out = df.copy()
    median = pd.to_numeric(out[column], errors="coerce").median()
    out[column] = pd.to_numeric(out[column], errors="coerce").fillna(median)
    return out


def mean_imputation(df: pd.DataFrame, column: str) -> pd.DataFrame:
    out = df.copy()
    mean = pd.to_numeric(out[column], errors="coerce").mean()
    out[column] = pd.to_numeric(out[column], errors="coerce").fillna(mean)
    return out


def group_median_imputation(df: pd.DataFrame, column: str, group_column: str) -> pd.DataFrame:
    """
    Imputes missing numeric values using the median WITHIN each group of
    `group_column`, falling back to the overall median only for groups
    that have no non-null values at all. This avoids the classic mistake
    of filling highly group-dependent metrics (e.g. layoff size, which
    varies hugely by company/industry) with one global number.
    """
    out = df.copy()
    numeric = pd.to_numeric(out[column], errors="coerce")
    overall_median = numeric.median()
    group_medians = numeric.groupby(out[group_column]).transform("median")
    filled = numeric.fillna(group_medians).fillna(overall_median)
    out[column] = filled
    return out


def mode_imputation(df: pd.DataFrame, column: str) -> pd.DataFrame:
    out = df.copy()
    mode_series = out[column].mode()
    if not mode_series.empty:
        out[column] = out[column].fillna(mode_series.iloc[0])
    return out


def normalize_categories(df: pd.DataFrame, column: str) -> pd.DataFrame:
    """Lower-case + strip to collapse case/whitespace variants of the same category."""
    out = df.copy()

    def _norm(v):
        if isinstance(v, str):
            return v.strip().lower()
        return v
    out[column] = out[column].map(_norm)
    return out


def winsorize_column(df: pd.DataFrame, column: str, lower_pct: float = 0.05, upper_pct: float = 0.95) -> pd.DataFrame:
    out = df.copy()
    series = pd.to_numeric(out[column], errors="coerce")
    lo, hi = series.quantile(lower_pct), series.quantile(upper_pct)
    out[column] = series.clip(lower=lo, upper=hi)
    return out


def flag_outliers_column(df: pd.DataFrame, column: str, mask: pd.Series) -> pd.DataFrame:
    """Adds a boolean `<column>_is_outlier` flag column instead of altering values."""
    out = df.copy()
    flag_col = f"{column}_is_outlier"
    full_mask = pd.Series(False, index=out.index)
    full_mask.loc[mask.index] = mask.values
    out[flag_col] = full_mask
    return out


def drop_column(df: pd.DataFrame, column: str) -> pd.DataFrame:
    return df.drop(columns=[column])


TRANSFORMATION_REGISTRY = {
    "trim_whitespace": trim_whitespace,
    "standardize_missing_markers": standardize_missing_markers,
    "standardize_boolean": standardize_boolean,
    "remove_exact_duplicate_rows": remove_exact_duplicate_rows,
    "convert_numeric_text_to_numeric": convert_numeric_text_to_numeric,
    "convert_text_to_datetime": convert_text_to_datetime,
    "median_imputation": median_imputation,
    "group_median_imputation": group_median_imputation,
    "mean_imputation": mean_imputation,
    "mode_imputation": mode_imputation,
    "normalize_categories": normalize_categories,
    "winsorize_column": winsorize_column,
    "drop_column": drop_column,
}
