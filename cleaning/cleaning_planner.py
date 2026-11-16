"""
Cleaning Planner.

Turns detected QualityIssues into concrete, explainable Transformation
proposals across the three cleaning levels. Deterministic rules decide
WHICH transformation fits WHICH issue; the AI (ai/cleaning_advisor.py)
may only add reasoning/explanation on top for ambiguous Level-3 cases —
it never invents the transformation itself.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pandas as pd

from models.profile import DatasetProfile
from models.quality import QualityIssue
from models.transformation import CleaningLevel, Transformation, TransformationStatus


class CleaningPlanner:
    def build_plan(self, df: pd.DataFrame, profile: DatasetProfile, issues: list[QualityIssue]) -> list[Transformation]:
        plan: list[Transformation] = []
        now = datetime.now(timezone.utc).isoformat()

        # Level 1: exact duplicate rows -> safe automatic
        dup_issue = next((i for i in issues if i.category == "duplicate" and i.column is None), None)
        if dup_issue:
            plan.append(Transformation(
                transformation_id=self._tid(), column=None,
                issue=dup_issue.description, severity=dup_issue.severity.value,
                detection_method=dup_issue.detection_method,
                action="remove_exact_duplicate_rows", action_label="Remove exact duplicate rows",
                reason="Exact duplicate rows add no information and can bias aggregations and counts.",
                confidence=1.0, reversibility="irreversible (rows removed)",
                expected_impact=f"Removes {dup_issue.affected_rows} row(s); improves Uniqueness score.",
                level=CleaningLevel.SAFE_AUTOMATIC, timestamp=now,
                python_logic="df.drop_duplicates(keep='first')",
                sql_logic="SELECT DISTINCT * FROM dataset",
                affected_rows=dup_issue.affected_rows,
            ))

        for issue in issues:
            col = issue.column
            if col is None or col not in df.columns:
                continue
            cprofile = profile.columns.get(col)
            if cprofile is None:
                continue

            if issue.category == "type" and "numeric_stored_as_text" in cprofile.flags:
                plan.append(self._make(col, issue, "convert_numeric_text_to_numeric",
                    "Convert numeric-looking text to numeric type",
                    "Values look numeric (with currency symbols/commas removed) but are stored as text, "
                    "blocking correct sorting, aggregation, and statistics.",
                    0.85, CleaningLevel.AI_ASSISTED, now,
                    python_logic=f"pd.to_numeric(df['{col}'].str.replace(r'[,$%\\s]', '', regex=True))"))

            elif issue.category == "type" and "date_stored_as_text" in cprofile.flags:
                plan.append(self._make(col, issue, "convert_text_to_datetime",
                    "Parse text values into proper datetime type",
                    "Values are date-like text; converting enables correct sorting, filtering, and time-series analysis.",
                    0.8, CleaningLevel.AI_ASSISTED, now,
                    python_logic=f"pd.to_datetime(df['{col}'], errors='coerce')"))

            elif issue.category == "missing" and cprofile.detected_type == "numeric":
                skewed = cprofile.skewness is not None and abs(cprofile.skewness) > 1
                group_col = self._find_grouping_column(df, profile, target_col=col)

                if group_col:
                    # Prefer group-aware imputation: a single global median/mean can be
                    # very misleading for metrics that vary hugely by segment (e.g. layoff
                    # size differs enormously between a 10-person startup and a 10,000-
                    # person enterprise). Imputing within each group of `group_col`
                    # keeps the fill value representative of similar records.
                    plan.append(self._make(
                        col, issue, "group_median_imputation",
                        f"Group-aware median imputation (grouped by '{group_col}')",
                        (
                            f"This metric likely varies a lot across different '{group_col}' segments, "
                            f"so a single global median/mean could be misleading (e.g. it would understate "
                            f"large organizations and overstate small ones). Filling missing values with the "
                            f"median WITHIN each '{group_col}' group keeps the imputed value representative "
                            f"of similar records. Groups with no data at all fall back to the overall median."
                        ),
                        0.7, CleaningLevel.ADVANCED_CONTEXTUAL, now,
                        python_logic=f"df.groupby('{group_col}')['{col}'].transform(lambda s: s.fillna(s.median()))",
                        params={"group_column": group_col},
                    ))
                else:
                    action = "median_imputation" if skewed else "mean_imputation"
                    label = "Median imputation" if skewed else "Mean imputation"
                    reason = (
                        ("The distribution is skewed, so the median is more robust to extreme values. "
                         if skewed else
                         "The distribution is roughly symmetric, so the mean is a reasonable central estimate. ")
                        + "Note: this uses one global value for the whole dataset — if this metric actually "
                          "varies a lot across a category you care about (e.g. industry, region, segment), "
                          "review the imputed values before trusting downstream aggregations built on them."
                    )
                    plan.append(self._make(col, issue, action, label, reason, 0.75,
                                            CleaningLevel.AI_ASSISTED, now,
                                            python_logic=f"df['{col}'].fillna(df['{col}'].{'median' if skewed else 'mean'}())"))

            elif issue.category == "missing" and cprofile.detected_type == "categorical":
                plan.append(self._make(col, issue, "mode_imputation", "Mode (most frequent value) imputation",
                    "For categorical data, filling missing values with the most frequent category "
                    "preserves the existing distribution better than dropping rows.",
                    0.6, CleaningLevel.AI_ASSISTED, now,
                    python_logic=f"df['{col}'].fillna(df['{col}'].mode().iloc[0])"))

            elif issue.category == "consistency" and "leading/trailing whitespace" in issue.description:
                plan.append(self._make(col, issue, "trim_whitespace", "Trim leading/trailing whitespace",
                    "Whitespace differences make identical categories look distinct, inflating cardinality.",
                    1.0, CleaningLevel.SAFE_AUTOMATIC, now,
                    python_logic=f"df['{col}'].str.strip()"))

            elif issue.category == "consistency" and "capitalization" in issue.description:
                plan.append(self._make(col, issue, "normalize_categories", "Normalize category casing (lower-case)",
                    "Case differences (e.g. 'Cairo' vs 'cairo') represent the same category and should be unified.",
                    0.8, CleaningLevel.AI_ASSISTED, now,
                    python_logic=f"df['{col}'].str.strip().str.lower()"))

            elif issue.category == "outlier":
                plan.append(self._make(col, issue, "flag_outliers_column", "Flag potential outliers (no value change)",
                    "Per policy, statistically unusual values are flagged for review rather than "
                    "automatically altered or removed, since they may be valid extreme observations.",
                    0.7, CleaningLevel.ADVANCED_CONTEXTUAL, now,
                    python_logic=f"df['{col}_is_outlier'] = <outlier boolean mask>",
                    reversibility="reversible (adds a new column, original values untouched)"))

        return self._order_by_dependency(plan)

    # Execution order matters: type conversions must run before imputation
    # (otherwise valid "$70.08"-style values would look missing and get
    # overwritten by mean/median), and outlier flagging must run last
    # (it needs already-cleaned numeric values).
    _ACTION_PRIORITY = {
        "remove_exact_duplicate_rows": 0,
        "convert_numeric_text_to_numeric": 1,
        "convert_text_to_datetime": 1,
        "trim_whitespace": 2,
        "normalize_categories": 2,
        "standardize_missing_markers": 2,
        "standardize_boolean": 2,
        "mean_imputation": 3,
        "median_imputation": 3,
        "mode_imputation": 3,
        "flag_outliers_column": 4,
    }

    def _order_by_dependency(self, plan: list[Transformation]) -> list[Transformation]:
        return sorted(plan, key=lambda t: self._ACTION_PRIORITY.get(t.action, 99))

    def _make(self, col, issue: QualityIssue, action, label, reason, confidence, level, ts,
              python_logic="", sql_logic="", reversibility="reversible (creates a new dataset version)",
              params: dict | None = None) -> Transformation:
        return Transformation(
            transformation_id=self._tid(), column=col, issue=issue.description,
            severity=issue.severity.value, detection_method=issue.detection_method,
            action=action, action_label=label, reason=reason, confidence=confidence,
            reversibility=reversibility,
            expected_impact=f"Affects up to {issue.affected_rows} row(s) in column '{col}'.",
            level=level, timestamp=ts, python_logic=python_logic, sql_logic=sql_logic,
            affected_rows=issue.affected_rows, params=params or {},
        )

    @staticmethod
    def _find_grouping_column(df: pd.DataFrame, profile: DatasetProfile, target_col: str) -> str | None:
        """
        Finds a reasonable categorical column to group by for imputation:
        low-to-moderate cardinality (2-30 distinct values), not the target
        column itself, with at least 2 non-null members per group on
        average so the group median is meaningfully different from the
        global one. Returns None if nothing suitable is found.
        """
        candidates = []
        for name, cprofile in profile.columns.items():
            if name == target_col or name not in df.columns:
                continue
            if cprofile.detected_type != "categorical":
                continue
            if not (2 <= cprofile.cardinality <= 30):
                continue
            avg_group_size = profile.row_count / cprofile.cardinality if cprofile.cardinality else 0
            if avg_group_size < 2:
                continue
            candidates.append((name, cprofile.cardinality))

        if not candidates:
            return None
        # Prefer a column name that reads like a natural grouping dimension
        preferred_hints = ("industry", "category", "segment", "department", "region",
                           "stage", "type", "sector", "location", "country")
        for hint in preferred_hints:
            for name, _ in candidates:
                if hint in name.lower():
                    return name
        # Otherwise, pick the lowest-cardinality candidate (broadest, most stable groups)
        candidates.sort(key=lambda c: c[1])
        return candidates[0][0]

    @staticmethod
    def _tid() -> str:
        return f"TR-{uuid.uuid4().hex[:8].upper()}"


cleaning_planner = CleaningPlanner()
