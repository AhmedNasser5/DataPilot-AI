"""Data models for domain detection, KPIs, charts, insights, SQL results."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


@dataclass
class DomainDetection:
    domain: str
    confidence: float
    evidence: list[str] = field(default_factory=list)
    alternative_domains: list[tuple[str, float]] = field(default_factory=list)


@dataclass
class KPIDefinition:
    kpi_id: str
    name: str
    definition: str
    formula: str
    required_columns: list[str]
    calculation_method: str
    sql: Optional[str] = None
    value: Optional[Any] = None
    unit: Optional[str] = None
    time_period: Optional[str] = None
    calculable: bool = True
    reason_not_calculable: Optional[str] = None


@dataclass
class ChartRecommendation:
    chart_id: str
    title: str
    chart_type: str          # line | bar | area | scatter | histogram | box | heatmap | table
    columns: list[str]
    aggregation: Optional[str]
    reason: str
    purpose: str


@dataclass
class SQLResult:
    sql: str
    columns: list[str]
    rows: list[tuple]
    row_count: int
    execution_time_ms: float
    truncated: bool = False
    error: Optional[str] = None


class InsightKind(str, Enum):
    FACT = "fact"
    CALCULATION = "calculation"
    INTERPRETATION = "interpretation"
    HYPOTHESIS = "hypothesis"


@dataclass
class Insight:
    text: str
    kind: InsightKind
    evidence: dict[str, Any] = field(default_factory=dict)
