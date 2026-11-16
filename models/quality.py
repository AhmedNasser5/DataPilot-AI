"""Data models for the Data Quality Engine."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class Severity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class QualityIssue:
    issue_id: str
    column: Optional[str]
    category: str          # missing | duplicate | type | consistency | validity | outlier
    description: str
    severity: Severity
    affected_rows: int
    detection_method: str
    confidence: float = 1.0
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class QualityDimensionScore:
    name: str
    score: float           # 0-100
    explanation: str
    contributing_issues: list[str] = field(default_factory=list)


@dataclass
class QualityReport:
    dataset_id: str
    version: str
    overall_score: float
    dimensions: dict[str, QualityDimensionScore] = field(default_factory=dict)
    issues: list[QualityIssue] = field(default_factory=list)

    def issues_by_severity(self) -> dict[str, int]:
        counts = {s.value: 0 for s in Severity}
        for i in self.issues:
            counts[i.severity.value] += 1
        return counts
