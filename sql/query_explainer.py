"""Lightweight SQL breakdown for user-facing explanations (not a full parser)."""
from __future__ import annotations

import re


class QueryExplainer:
    def explain(self, sql: str) -> dict:
        lowered = sql.lower()

        tables = re.findall(r"from\s+([a-zA-Z0-9_\"\.]+)", lowered) + \
                 re.findall(r"join\s+([a-zA-Z0-9_\"\.]+)", lowered)
        group_by = re.search(r"group by\s+(.+?)(order by|limit|$)", lowered, re.DOTALL)
        order_by = re.search(r"order by\s+(.+?)(limit|$)", lowered, re.DOTALL)
        limit = re.search(r"limit\s+(\d+)", lowered)
        where = re.search(r"where\s+(.+?)(group by|order by|limit|$)", lowered, re.DOTALL)
        aggregations = re.findall(r"\b(sum|avg|count|min|max|median|stddev)\s*\(", lowered)

        return {
            "tables_used": sorted(set(t.strip('"') for t in tables)),
            "filters": where.group(1).strip() if where else None,
            "aggregations": sorted(set(aggregations)),
            "grouping": group_by.group(1).strip() if group_by else None,
            "sorting": order_by.group(1).strip() if order_by else None,
            "limit": int(limit.group(1)) if limit else None,
        }


query_explainer = QueryExplainer()
