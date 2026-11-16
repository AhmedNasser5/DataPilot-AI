"""Validates that a QualityReport is internally consistent."""
from __future__ import annotations

from models.quality import QualityReport


class QualityValidator:
    def validate(self, report: QualityReport) -> list[str]:
        problems = []
        if not (0 <= report.overall_score <= 100):
            problems.append(f"Overall score {report.overall_score} is out of the expected 0-100 range.")
        for name, dim in report.dimensions.items():
            if not (0 <= dim.score <= 100):
                problems.append(f"Dimension '{name}' score {dim.score} is out of range.")
        return problems


quality_validator = QualityValidator()
