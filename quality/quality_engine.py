"""Orchestrates all quality detectors and produces the final QualityReport."""
from __future__ import annotations

import pandas as pd

from core.profiling.quality_score import compute_overall_score, compute_quality_dimensions
from core.quality.consistency import ConsistencyDetector
from core.quality.duplicates import DuplicateDetector
from core.quality.invalid_values import InvalidValueDetector
from core.quality.missing_values import MissingValueDetector
from core.quality.outliers import OutlierDetector
from core.quality.type_issues import TypeIssueDetector
from models.profile import DatasetProfile
from models.quality import QualityReport


class QualityEngine:
    def __init__(self):
        self._missing = MissingValueDetector()
        self._duplicates = DuplicateDetector()
        self._types = TypeIssueDetector()
        self._consistency = ConsistencyDetector()
        self._invalid = InvalidValueDetector()
        self._outliers = OutlierDetector()

    def evaluate(self, df: pd.DataFrame, profile: DatasetProfile) -> QualityReport:
        issues = []
        issues += self._missing.detect(df)
        issues += self._duplicates.detect(df, profile.columns)
        issues += self._types.detect(df, profile.columns)
        issues += self._consistency.detect(df, profile.columns)
        issues += self._invalid.detect(df, profile.columns)
        issues += self._outliers.detect(df, profile.columns)

        dimensions = compute_quality_dimensions(profile, issues)
        overall = compute_overall_score(dimensions)

        return QualityReport(
            dataset_id=profile.dataset_id,
            version=profile.version,
            overall_score=overall,
            dimensions=dimensions,
            issues=issues,
        )


quality_engine = QualityEngine()
