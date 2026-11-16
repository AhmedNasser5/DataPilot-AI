"""
Dataset Service.

Application-layer facade the Streamlit UI (or any future frontend)
calls to upload/load datasets. Wraps the ingestion + profiling + SQL
registration engines behind a simple interface.
"""
from __future__ import annotations

from core.ingestion.loader_registry import loader_registry
from core.profiling.profiler import DatasetProfiler
from core.sql.table_manager import table_manager
from models.dataset import Dataset, SheetInfo


class DatasetService:
    def __init__(self):
        self._profiler = DatasetProfiler()

    def detect_format(self, filename: str, content: bytes):
        return loader_registry.detect(filename, content)

    def list_excel_sheets(self, content: bytes) -> list[SheetInfo]:
        return loader_registry.list_excel_sheets(content)

    def load_dataset(self, filename: str, content: bytes, sheet_name: str | None = None) -> Dataset:
        dataset = loader_registry.load(filename, content, sheet_name=sheet_name)
        table_manager.register(dataset)
        return dataset

    def profile(self, dataset: Dataset):
        return self._profiler.profile(dataset)

    def register_version(self, dataset: Dataset) -> str:
        return table_manager.register(dataset)


dataset_service = DatasetService()
