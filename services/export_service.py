"""Export Service — facade over all export engines (dataset, report, transformations)."""
from __future__ import annotations

import pandas as pd

from core.export.dataset_exporter import dataset_exporter
from core.export.report_exporter import report_exporter
from core.export.transformation_exporter import transformation_exporter
from models.transformation import Transformation


class ExportService:
    def export_dataset(self, df: pd.DataFrame, fmt: str) -> bytes:
        fmt = fmt.lower()
        if fmt == "csv":
            return dataset_exporter.to_csv_bytes(df)
        if fmt == "xlsx":
            return dataset_exporter.to_xlsx_bytes(df)
        if fmt == "json":
            return dataset_exporter.to_json_bytes(df)
        if fmt == "parquet":
            return dataset_exporter.to_parquet_bytes(df)
        raise ValueError(f"Unsupported export format: {fmt}")

    def export_quality_report(self, quality_report) -> bytes:
        return report_exporter.quality_report_json(quality_report)

    def export_profile_report(self, profile) -> bytes:
        return report_exporter.profile_report_json(profile)

    def export_markdown_summary(self, dataset_name: str, quality_report, profile, kpis) -> bytes:
        return report_exporter.markdown_summary(dataset_name, quality_report, profile, kpis)

    def export_transformations_python(self, transformations: list[Transformation]) -> bytes:
        return transformation_exporter.to_python_script(transformations)

    def export_transformations_sql(self, transformations: list[Transformation]) -> bytes:
        return transformation_exporter.to_sql_script(transformations)


export_service = ExportService()
