"""Data models for the profiling engine output."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class SemanticGuess:
    """A probabilistic semantic-type classification for a column."""
    label: str          # e.g. "email", "currency", "id", "geography"
    confidence: float   # 0.0 - 1.0
    evidence: str = ""


@dataclass
class ColumnProfile:
    original_name: str
    normalized_name: str
    pandas_dtype: str
    detected_type: str            # numeric | categorical | boolean | datetime | text | id
    semantic_types: list[SemanticGuess] = field(default_factory=list)

    null_count: int = 0
    null_percentage: float = 0.0
    unique_count: int = 0
    unique_percentage: float = 0.0
    cardinality: int = 0
    zero_count: int = 0
    negative_count: int = 0

    minimum: Optional[float] = None
    maximum: Optional[float] = None
    mean: Optional[float] = None
    median: Optional[float] = None
    mode: Optional[Any] = None
    std: Optional[float] = None
    variance: Optional[float] = None
    quantiles: dict[str, float] = field(default_factory=dict)
    skewness: Optional[float] = None
    kurtosis: Optional[float] = None

    most_frequent_values: list[tuple[Any, int]] = field(default_factory=list)
    sample_values: list[Any] = field(default_factory=list)

    is_constant: bool = False
    is_near_constant: bool = False
    is_high_cardinality: bool = False
    is_possible_id: bool = False
    is_possible_primary_key: bool = False
    has_mixed_types: bool = False
    flags: list[str] = field(default_factory=list)


@dataclass
class DatasetProfile:
    dataset_id: str
    version: str
    row_count: int
    column_count: int
    estimated_memory_mb: float
    columns: dict[str, ColumnProfile] = field(default_factory=dict)
    generated_at: str = ""
