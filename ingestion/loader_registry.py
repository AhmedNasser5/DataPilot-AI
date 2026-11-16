"""
Extensible loader registry.

New data sources are added by implementing BaseLoader and registering
an instance here — no other code needs to change (open/closed principle).
Database and API connectors are designed as future extensions that will
register themselves the same way.
"""
from __future__ import annotations

from config.settings import settings
from core.ingestion.base_loader import BaseLoader, LoadRequest, LoaderError
from core.ingestion.csv_loader import CSVLoader
from core.ingestion.excel_loader import ExcelLoader
from core.ingestion.format_detector import FormatDetector
from core.ingestion.json_loader import JSONLoader
from core.ingestion.parquet_loader import ParquetLoader
from models.dataset import Dataset, SheetInfo


class UnsupportedFormatError(LoaderError):
    pass


class FileTooLargeError(LoaderError):
    pass


class LoaderRegistry:
    """Central entry point for turning raw uploaded bytes into a Dataset."""

    def __init__(self):
        self._detector = FormatDetector()
        self._excel_loader = ExcelLoader()
        self._json_loader = JSONLoader()
        self._parquet_loader = ParquetLoader()

    def detect(self, filename: str, content: bytes):
        return self._detector.detect(filename, content)

    def list_excel_sheets(self, content: bytes) -> list[SheetInfo]:
        return self._excel_loader.list_sheets(content)

    def load(self, filename: str, content: bytes, sheet_name: str | None = None) -> Dataset:
        size_mb = len(content) / (1024 * 1024)
        if size_mb > settings.max_file_size_mb:
            raise FileTooLargeError(
                f"File is {size_mb:.1f} MB which exceeds the configured limit of "
                f"{settings.max_file_size_mb} MB (MAX_FILE_SIZE_MB)."
            )

        detected = self._detector.detect(filename, content)
        request = LoadRequest(filename=filename, content=content, sheet_name=sheet_name)

        if detected.format in ("csv", "tsv", "txt_delimited"):
            loader: BaseLoader = CSVLoader(delimiter=detected.delimiter)
        elif detected.format in ("xlsx", "xls"):
            loader = self._excel_loader
        elif detected.format in ("json", "ndjson"):
            loader = self._json_loader
        elif detected.format in ("parquet", "feather"):
            loader = self._parquet_loader
        else:
            raise UnsupportedFormatError(
                f"Format '{detected.format}' is not supported yet. "
                f"Supported formats: CSV, TSV, delimited TXT, XLSX, XLS, JSON, NDJSON, Parquet, Feather. "
                f"New loaders can be added via the loader registry."
            )

        dataset = loader.load(request)
        return dataset


loader_registry = LoaderRegistry()
