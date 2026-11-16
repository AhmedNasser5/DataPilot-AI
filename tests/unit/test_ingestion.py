import pandas as pd
import pytest

from core.ingestion.loader_registry import loader_registry, UnsupportedFormatError, FileTooLargeError
from core.ingestion.format_detector import FormatDetector


def test_csv_load_basic():
    content = b"a,b,c\n1,2,3\n4,5,6\n"
    ds = loader_registry.load("test.csv", content)
    assert ds.metadata.row_count == 2
    assert list(ds.dataframe.columns) == ["a", "b", "c"]


def test_semicolon_delimited_detection():
    content = "a;b;c\n1;2;3\n4;5;6\n".encode("utf-8")
    detector = FormatDetector()
    detected = detector.detect("test.txt", content)
    assert detected.delimiter == ";"


def test_json_records_load():
    content = b'[{"a": 1, "b": "x"}, {"a": 2, "b": "y"}]'
    ds = loader_registry.load("test.json", content)
    assert ds.metadata.row_count == 2
    assert "a" in ds.dataframe.columns


def test_ndjson_load():
    content = b'{"a": 1}\n{"a": 2}\n{"a": 3}\n'
    ds = loader_registry.load("test.ndjson", content)
    assert ds.metadata.row_count == 3


def test_empty_dataset_raises():
    from core.ingestion.base_loader import LoaderError
    with pytest.raises(LoaderError):
        loader_registry.load("empty.csv", b"")


def test_duplicate_column_names_deduped():
    content = b"a,a,b\n1,2,3\n"
    ds = loader_registry.load("dup.csv", content)
    assert len(set(ds.dataframe.columns)) == 3


def test_unsupported_format_raises():
    with pytest.raises((UnsupportedFormatError, Exception)):
        loader_registry.load("weird.xyz123", b"\x00\x01\x02not a real format")
