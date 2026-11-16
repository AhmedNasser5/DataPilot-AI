"""
Transparent Data Quality Score formula.

Every sub-score is a simple, auditable percentage. Nothing here is an
AI-generated number — it is computed directly from profiling + issue
data so the user can see exactly why the score is what it is.

Dimensions:
    Completeness  = 100 * (1 - total_missing_cells / total_cells)
    Uniqueness    = 100 * (1 - duplicate_rows / total_rows)
    Validity      = 100 * (1 - invalid_value_rows / total_rows)
    Consistency   = 100 * (1 - consistency_affected_rows / total_rows)

Overall score = weighted average (weights are explicit and documented).
"""
from __future__ import annotations

from models.profile import DatasetProfile
from models.quality import QualityDimensionScore, QualityIssue, Severity

DIMENSION_WEIGHTS = {
    "completeness": 0.35,
    "validity": 0.25,
    "consistency": 0.20,
    "uniqueness": 0.20,
}


def _clip(x: float) -> float:
    return max(0.0, min(100.0, x))


def compute_quality_dimensions(
    profile: DatasetProfile,
    issues: list[QualityIssue],
) -> dict[str, QualityDimensionScore]:
    n_rows = max(profile.row_count, 1)
    n_cells = max(profile.row_count * max(profile.column_count, 1), 1)

    missing_cells = sum(c.null_count for c in profile.columns.values())
    completeness = _clip(100 * (1 - missing_cells / n_cells))

    dup_issue_rows = sum(i.affected_rows for i in issues if i.category == "duplicate" and i.column is None)
    uniqueness = _clip(100 * (1 - dup_issue_rows / n_rows))

    # Validity and consistency are computed PER-COLUMN then averaged across all columns,
    # rather than summed and capped at total rows. This avoids one or two badly-typed
    # columns collapsing the whole dataset's score to zero, while still penalizing
    # datasets where MANY columns have problems.
    n_cols = max(profile.column_count, 1)

    validity_per_col: dict[str, float] = {c: 0.0 for c in profile.columns.keys()}
    for i in issues:
        if i.category in ("validity", "type") and i.column:
            ratio = min(i.affected_rows / n_rows, 1.0)
            validity_per_col[i.column] = min(1.0, validity_per_col.get(i.column, 0.0) + ratio)
    validity = _clip(100 * (1 - sum(validity_per_col.values()) / n_cols)) if validity_per_col else 100.0

    consistency_per_col: dict[str, float] = {c: 0.0 for c in profile.columns.keys()}
    for i in issues:
        if i.category == "consistency" and i.column:
            ratio = min(i.affected_rows / n_rows, 1.0)
            consistency_per_col[i.column] = min(1.0, consistency_per_col.get(i.column, 0.0) + ratio)
    consistency = _clip(100 * (1 - sum(consistency_per_col.values()) / n_cols)) if consistency_per_col else 100.0

    def _contrib(cat_filter) -> list[str]:
        return [i.issue_id for i in issues if cat_filter(i)]

    return {
        "completeness": QualityDimensionScore(
            "Completeness", round(completeness, 1),
            f"100 * (1 - missing_cells / total_cells) = 100 * (1 - {missing_cells}/{n_cells})",
            _contrib(lambda i: i.category == "missing"),
        ),
        "validity": QualityDimensionScore(
            "Validity", round(validity, 1),
            "100 * (1 - average across columns of min(1, invalid_rows_in_column / total_rows))",
            _contrib(lambda i: i.category in ("validity", "type")),
        ),
        "consistency": QualityDimensionScore(
            "Consistency", round(consistency, 1),
            "100 * (1 - average across columns of min(1, inconsistent_rows_in_column / total_rows))",
            _contrib(lambda i: i.category == "consistency"),
        ),
        "uniqueness": QualityDimensionScore(
            "Uniqueness", round(uniqueness, 1),
            f"100 * (1 - duplicate_rows / total_rows) = 100 * (1 - {dup_issue_rows}/{n_rows})",
            _contrib(lambda i: i.category == "duplicate"),
        ),
    }


def compute_overall_score(dimensions: dict[str, QualityDimensionScore]) -> float:
    total_weight = sum(DIMENSION_WEIGHTS.values())
    weighted = sum(dimensions[k].score * w for k, w in DIMENSION_WEIGHTS.items() if k in dimensions)
    return round(weighted / total_weight, 1)
