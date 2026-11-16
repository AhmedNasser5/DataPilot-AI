"""
KPI Calculator.

Generates and EXECUTES real SQL (via DuckDB) for each KPI. The value
shown to the user is always the actual query result — never an LLM
estimate. If a required column is missing, the KPI is marked
non-calculable with an explicit reason instead of being guessed.
"""
from __future__ import annotations

from core.sql.query_executor import query_executor
from models.analysis import KPIDefinition


class KPICalculator:
    def calculate(self, table_name: str, kpi: KPIDefinition) -> KPIDefinition:
        try:
            sql = self._build_sql(table_name, kpi)
        except ValueError as e:
            kpi.calculable = False
            kpi.reason_not_calculable = str(e)
            return kpi

        kpi.sql = sql
        result = query_executor.run(sql)
        if result.error:
            kpi.calculable = False
            kpi.reason_not_calculable = f"SQL execution failed: {result.error}"
            return kpi

        if not result.rows:
            kpi.calculable = False
            kpi.reason_not_calculable = "Query returned no rows."
            return kpi

        if len(result.rows) == 1 and len(result.columns) == 1:
            # Single scalar aggregate (e.g. SUM, AVG, COUNT)
            kpi.value = result.rows[0][0]
        elif len(result.rows) == 1:
            # Single row, multiple columns (e.g. "top category" -> name + total)
            kpi.value = dict(zip(result.columns, result.rows[0]))
        else:
            # Multi-row series result (e.g. a trend broken down by period/category) —
            # preserve every row rather than silently dropping all but the first.
            kpi.value = [dict(zip(result.columns, r)) for r in result.rows]
        kpi.calculable = True
        return kpi

    def _build_sql(self, table: str, kpi: KPIDefinition) -> str:
        cols = kpi.required_columns
        t = f'"{table}"'

        if kpi.kpi_id == "total_revenue":
            return f'SELECT SUM(TRY_CAST("{cols[0]}" AS DOUBLE)) AS total_revenue FROM {t}'
        if kpi.kpi_id == "total_capital_raised":
            return f'SELECT SUM(TRY_CAST("{cols[0]}" AS DOUBLE)) AS total_capital_raised FROM {t}'
        if kpi.kpi_id == "average_order_value":
            return f'SELECT AVG(TRY_CAST("{cols[0]}" AS DOUBLE)) AS avg_order_value FROM {t}'
        if kpi.kpi_id == "total_quantity_sold":
            return f'SELECT SUM(TRY_CAST("{cols[0]}" AS DOUBLE)) AS total_quantity FROM {t}'
        if kpi.kpi_id == "top_category_by_amount":
            amount_col, cat_col = cols[0], cols[1]
            return (
                f'SELECT "{cat_col}" AS category, SUM(TRY_CAST("{amount_col}" AS DOUBLE)) AS total '
                f'FROM {t} GROUP BY "{cat_col}" ORDER BY total DESC LIMIT 1'
            )
        if kpi.kpi_id == "record_count":
            return f'SELECT COUNT(*) AS record_count FROM {t}'
        if kpi.kpi_id == "unique_entity_count":
            return f'SELECT COUNT(DISTINCT "{cols[0]}") AS unique_count FROM {t}'
        if kpi.kpi_id == "revenue_trend":
            amount_col, date_col = cols[0], cols[1]
            return (
                f'SELECT DATE_TRUNC(\'month\', TRY_CAST("{date_col}" AS TIMESTAMP)) AS period, '
                f'SUM(TRY_CAST("{amount_col}" AS DOUBLE)) AS total '
                f'FROM {t} GROUP BY period ORDER BY period'
            )
        if kpi.kpi_id == "average_metric_by_category":
            amount_col, cat_col = cols[0], cols[1]
            return (
                f'SELECT "{cat_col}" AS category, AVG(TRY_CAST("{amount_col}" AS DOUBLE)) AS avg_value '
                f'FROM {t} GROUP BY "{cat_col}" ORDER BY avg_value DESC'
            )

        raise ValueError(f"No SQL builder implemented for KPI '{kpi.kpi_id}'.")


kpi_calculator = KPICalculator()
