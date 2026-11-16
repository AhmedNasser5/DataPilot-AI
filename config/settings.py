"""
Central application configuration.

All limits, provider settings, and paths are read from environment
variables (see .env.example). Nothing here is hardcoded as a secret.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

BASE_DIR = Path(__file__).resolve().parent.parent


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, default))
    except (TypeError, ValueError):
        return default


def _env_float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, default))
    except (TypeError, ValueError):
        return default


@dataclass(frozen=True)
class Settings:
    # --- Environment ---
    environment: str = os.getenv("ENVIRONMENT", "development")

    # --- LLM / AI provider ---
    llm_provider: str = os.getenv("LLM_PROVIDER", "none").lower()
    llm_api_key: str = os.getenv("LLM_API_KEY", "")
    model_name: str = os.getenv("MODEL_NAME", "claude-sonnet-4-5")

    # --- Resource limits ---
    max_file_size_mb: int = _env_int("MAX_FILE_SIZE_MB", 500)
    max_rows_for_preview: int = _env_int("MAX_ROWS_FOR_PREVIEW", 1000)
    max_query_time_seconds: int = _env_int("MAX_QUERY_TIME_SECONDS", 30)
    max_result_rows: int = _env_int("MAX_RESULT_ROWS", 10000)
    max_memory_usage_mb: int = _env_int("MAX_MEMORY_USAGE_MB", 2048)
    max_concurrent_jobs: int = _env_int("MAX_CONCURRENT_JOBS", 4)

    # --- Paths ---
    storage_dir: Path = BASE_DIR / "storage"
    originals_dir: Path = BASE_DIR / "storage" / "originals"
    versions_dir: Path = BASE_DIR / "storage" / "versions"
    processed_dir: Path = BASE_DIR / "storage" / "processed"
    exports_dir: Path = BASE_DIR / "storage" / "exports"
    duckdb_path: Path = BASE_DIR / "data" / "datapilot.duckdb"

    # --- Data-quality / detection thresholds (transparent & documented) ---
    near_constant_threshold: float = _env_float("NEAR_CONSTANT_THRESHOLD", 0.98)
    high_cardinality_ratio: float = _env_float("HIGH_CARDINALITY_RATIO", 0.9)
    outlier_iqr_multiplier: float = _env_float("OUTLIER_IQR_MULTIPLIER", 1.5)
    outlier_zscore_threshold: float = _env_float("OUTLIER_ZSCORE_THRESHOLD", 3.0)

    missing_value_markers: tuple = field(default_factory=lambda: (
        "", " ", "na", "n/a", "null", "none", "nan", "-", "--", "unknown",
        "unk", "missing", "?", "#n/a", "nil",
    ))

    def ai_enabled(self) -> bool:
        return self.llm_provider in ("anthropic",) and bool(self.llm_api_key)


settings = Settings()

for _p in (settings.originals_dir, settings.versions_dir,
           settings.processed_dir, settings.exports_dir,
           settings.duckdb_path.parent):
    _p.mkdir(parents=True, exist_ok=True)
