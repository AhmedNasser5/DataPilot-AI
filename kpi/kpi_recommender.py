"""
Matches KPI templates against the actual dataset schema.

A KPI is only recommended if its required semantic roles can be
resolved to real columns. If they cannot, the KPI is not fabricated —
it is either skipped or (if explicitly requested) reported with
`calculable=False` and a clear reason.
"""
from __future__ import annotations

from core.kpi.definitions import KPI_TEMPLATES, KPITemplate
from models.analysis import DomainDetection, KPIDefinition
from models.profile import DatasetProfile

# Domain-aware display-name overrides: same underlying calculation, but a
# label that actually matches the business language of the detected domain
# (e.g. a layoffs dataset should say "Total Impacted", not "Total Revenue").
_DOMAIN_KPI_LABELS: dict[tuple[str, str], tuple[str, str]] = {
    ("HR / Workforce Analytics", "total_revenue"): (
        "Total Impacted", "Sum of the primary workforce-impact metric (e.g. people laid off) across all records.",
    ),
    ("HR / Workforce Analytics", "unique_entity_count"): (
        "Total Entities Affected", "Count of distinct organizations/entities represented in the dataset.",
    ),
    ("HR / Workforce Analytics", "top_category_by_amount"): (
        "Top Affected Sector", "The category (e.g. industry or company) with the highest cumulative impact.",
    ),
    ("HR / Workforce Analytics", "record_count"): (
        "Total Events Recorded", "Total number of recorded events/rows in the dataset.",
    ),
}


class ColumnRoleResolver:
    """Resolves semantic roles ('amount', 'date', 'category', 'quantity', 'id') to real column names."""

    def resolve(self, profile: DatasetProfile) -> dict[str, list[str]]:
        roles: dict[str, list[str]] = {
            "amount": [], "date": [], "category": [], "quantity": [], "id": [], "capital": [],
        }
        capital_hints = ("funds_raised", "funding", "capital", "investment")
        for name, col in profile.columns.items():
            labels = {g.label for g in col.semantic_types}
            name_l = name.lower()
            is_capital_like = col.detected_type == "numeric" and any(h in name_l for h in capital_hints)
            if is_capital_like:
                roles["capital"].append(name)
            elif "currency" in labels or (col.detected_type == "numeric" and any(
                    k in name_l for k in ("amount", "revenue", "price", "total", "sales"))):
                roles["amount"].append(name)
            if col.detected_type == "datetime":
                roles["date"].append(name)
            if col.detected_type == "categorical" and not col.is_high_cardinality:
                roles["category"].append(name)
            if col.detected_type == "numeric" and any(
                    k in name_l for k in ("qty", "quantity", "units", "count")):
                roles["quantity"].append(name)
            if col.is_possible_id or col.is_possible_primary_key:
                roles["id"].append(name)
        return roles


class KPIRecommender:
    def __init__(self):
        self._resolver = ColumnRoleResolver()

    def recommend(self, profile: DatasetProfile, domain: DomainDetection) -> list[KPIDefinition]:
        roles = self._resolver.resolve(profile)
        recommendations: list[KPIDefinition] = []

        candidates = [t for t in KPI_TEMPLATES if domain.domain in t.domains or not t.requires]

        for template in candidates:
            resolved_cols, missing = self._try_resolve(template, roles)
            if missing:
                continue  # silently skip — do not fabricate; only truly available KPIs are recommended
            name, definition = template.name, template.definition
            override = _DOMAIN_KPI_LABELS.get((domain.domain, template.kpi_id))
            if override:
                name, definition = override
            recommendations.append(KPIDefinition(
                kpi_id=template.kpi_id,
                name=name,
                definition=definition,
                formula=template.formula,
                required_columns=resolved_cols,
                calculation_method=template.calculation_method,
                calculable=True,
            ))

        # Executive-style scalar/single-row KPIs surface first; multi-row
        # breakdowns (which belong in charts, not KPI cards) sort last.
        list_valued_ids = {"revenue_trend", "average_metric_by_category"}
        recommendations.sort(key=lambda k: k.kpi_id in list_valued_ids)
        return recommendations

    @staticmethod
    def _try_resolve(template: KPITemplate, roles: dict[str, list[str]]) -> tuple[list[str], list[str]]:
        resolved, missing = [], []
        for role in template.requires:
            available = roles.get(role, [])
            if available:
                resolved.append(available[0])
            else:
                missing.append(role)
        return resolved, missing


kpi_recommender = KPIRecommender()
column_role_resolver = ColumnRoleResolver()
