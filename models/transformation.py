"""Data models for cleaning transformations and the audit trail."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class TransformationStatus(str, Enum):
    PROPOSED = "proposed"
    APPROVED = "approved"
    REJECTED = "rejected"
    APPLIED = "applied"
    FAILED = "failed"


class CleaningLevel(str, Enum):
    SAFE_AUTOMATIC = "level_1_safe_automatic"
    AI_ASSISTED = "level_2_ai_assisted"
    ADVANCED_CONTEXTUAL = "level_3_advanced_contextual"


@dataclass
class Transformation:
    transformation_id: str
    column: Optional[str]
    issue: str
    severity: str
    detection_method: str
    action: str                      # e.g. "median_imputation"
    action_label: str                # human readable
    reason: str
    confidence: float
    reversibility: str               # "reversible" | "irreversible"
    expected_impact: str
    level: CleaningLevel
    params: dict[str, Any] = field(default_factory=dict)
    before_sample: list[Any] = field(default_factory=list)
    after_sample: list[Any] = field(default_factory=list)
    status: TransformationStatus = TransformationStatus.PROPOSED
    affected_rows: int = 0
    python_logic: str = ""
    sql_logic: str = ""
    timestamp: str = ""
    error: Optional[str] = None
