"""
Detects the format of an uploaded file using extension + content sniffing.

Extension alone is not trusted: a `.txt` file might be delimited data,
and a mislabeled file should still be caught where feasible.
"""
from __future__ import annotations

import io
import zipfile
from dataclasses import dataclass


@dataclass
class DetectedFormat:
    format: str            # csv | tsv | txt_delimited | xlsx | xls | json | ndjson | parquet | feather | zip | unknown
    delimiter: str | None = None
    confidence: float = 1.0
    reason: str = ""


_EXCEL_XLSX_MAGIC = b"PK\x03\x04"
_XLS_MAGIC = b"\xd0\xcf\x11\xe0"
_PARQUET_MAGIC = b"PAR1"


class FormatDetector:
    """Stateless format detection service."""

    SUPPORTED_EXTENSIONS = {
        "csv", "tsv", "txt", "xlsx", "xls", "json", "ndjson", "jsonl",
        "parquet", "feather", "zip",
    }

    def detect(self, filename: str, content: bytes) -> DetectedFormat:
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        head = content[:8]

        if head.startswith(_PARQUET_MAGIC) or content[-4:] == _PARQUET_MAGIC:
            return DetectedFormat("parquet", confidence=1.0, reason="Parquet magic bytes found")

        if head.startswith(_XLS_MAGIC):
            return DetectedFormat("xls", confidence=1.0, reason="Legacy OLE2 (.xls) magic bytes found")

        if head.startswith(_EXCEL_XLSX_MAGIC):
            # PK zip container: could be xlsx or a plain zip archive
            try:
                with zipfile.ZipFile(io.BytesIO(content)) as zf:
                    names = zf.namelist()
                    if any(n.startswith("xl/") for n in names):
                        return DetectedFormat("xlsx", confidence=1.0, reason="OOXML xl/ entries found")
                    return DetectedFormat("zip", confidence=0.95, reason="Generic ZIP archive")
            except zipfile.BadZipFile:
                pass

        text_sample = self._safe_decode(content[:4096])

        if ext in ("json", "ndjson", "jsonl"):
            if ext == "json":
                return DetectedFormat("json", confidence=0.9, reason="Extension is .json")
            return DetectedFormat("ndjson", confidence=0.9, reason=f"Extension is .{ext}")

        if text_sample:
            stripped = text_sample.strip()
            if stripped.startswith("{") or stripped.startswith("["):
                # Could be JSON or NDJSON
                lines = [l for l in stripped.splitlines() if l.strip()]
                if len(lines) > 1 and all(l.strip().startswith("{") for l in lines[:3]):
                    return DetectedFormat("ndjson", confidence=0.75, reason="Multiple JSON-object lines detected")
                return DetectedFormat("json", confidence=0.7, reason="Content starts with { or [")

            delimiter, conf = self._sniff_delimiter(text_sample)
            if delimiter == "\t":
                return DetectedFormat("tsv", delimiter="\t", confidence=conf, reason="Tab-separated structure detected")
            if delimiter is not None:
                fmt = "csv" if delimiter == "," else "txt_delimited"
                return DetectedFormat(fmt, delimiter=delimiter, confidence=conf, reason=f"Delimiter '{delimiter}' detected")

        if ext in self.SUPPORTED_EXTENSIONS:
            return DetectedFormat(ext, confidence=0.4, reason="Fell back to file extension only")

        return DetectedFormat("unknown", confidence=0.0, reason="Could not determine format")

    @staticmethod
    def _safe_decode(content: bytes) -> str | None:
        for enc in ("utf-8", "utf-8-sig", "latin-1"):
            try:
                return content.decode(enc)
            except (UnicodeDecodeError, LookupError):
                continue
        return None

    @staticmethod
    def _sniff_delimiter(sample: str) -> tuple[str | None, float]:
        import csv as _csv
        try:
            dialect = _csv.Sniffer().sniff(sample, delimiters=",;\t|")
            return dialect.delimiter, 0.85
        except Exception:
            # Heuristic fallback: count candidate delimiters on first lines
            lines = [l for l in sample.splitlines() if l.strip()][:5]
            if not lines:
                return None, 0.0
            best, best_count = None, 0
            for cand in (",", ";", "\t", "|"):
                counts = [l.count(cand) for l in lines]
                if counts and min(counts) > 0 and len(set(counts)) == 1:
                    if counts[0] > best_count:
                        best, best_count = cand, counts[0]
            return (best, 0.6) if best else (None, 0.0)
