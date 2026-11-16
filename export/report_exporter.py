"""Builds downloadable JSON/Markdown reports from quality/profile/KPI data."""
from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass


def _serialize(obj):
    if is_dataclass(obj):
        return {k: _serialize(v) for k, v in asdict(obj).items()}
    if isinstance(obj, dict):
        return {str(k): _serialize(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_serialize(v) for v in obj]
    return obj


class ReportExporter:
    def quality_report_json(self, quality_report) -> bytes:
        return json.dumps(_serialize(quality_report), indent=2, ensure_ascii=False, default=str).encode("utf-8")

    def profile_report_json(self, profile) -> bytes:
        return json.dumps(_serialize(profile), indent=2, ensure_ascii=False, default=str).encode("utf-8")

    def markdown_summary(self, dataset_name: str, quality_report, profile, kpis) -> bytes:
        lines = [
            f"# DataPilot AI — Analysis Report", "",
            f"**Dataset:** {dataset_name}", "",
            f"## Overview", "",
            f"- Rows: {profile.row_count}",
            f"- Columns: {profile.column_count}",
            f"- Overall Data Quality Score: **{quality_report.overall_score}/100**", "",
            f"## Quality Dimensions", "",
        ]
        for dim in quality_report.dimensions.values():
            lines.append(f"- **{dim.name}**: {dim.score}/100 — `{dim.explanation}`")
        lines += ["", f"## Issues Detected: {len(quality_report.issues)}", ""]
        severity_counts = quality_report.issues_by_severity()
        for sev, count in severity_counts.items():
            lines.append(f"- {sev.title()}: {count}")
        lines += ["", "## Key Performance Indicators", ""]
        for kpi in kpis:
            if kpi.calculable:
                lines.append(f"- **{kpi.name}**: {kpi.value}  \n  _{kpi.definition}_")
            else:
                lines.append(f"- **{kpi.name}**: not calculated — {kpi.reason_not_calculable}")
        return "\n".join(lines).encode("utf-8")


report_exporter = ReportExporter()
