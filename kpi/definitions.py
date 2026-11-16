"""
KPI template catalog.

Templates describe WHAT a KPI needs (required semantic roles), not a
fixed hardcoded list forced onto every dataset. The recommender picks
templates whose required columns can actually be resolved against the
current dataset; unresolvable templates are skipped or reported as
"cannot be calculated".
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class KPITemplate:
    kpi_id: str
    name: str
    definition: str
    formula: str
    requires: list[str]          # semantic roles: "amount", "date", "category", "id", "quantity"
    calculation_method: str
    domains: list[str]


KPI_TEMPLATES: list[KPITemplate] = [
    KPITemplate(
        "total_revenue", "Total Revenue",
        "The sum of all monetary transaction amounts in the dataset.",
        "SUM(amount_column)", ["amount"],
        "SQL SUM aggregation over the detected amount/currency column.",
        ["Sales / E-commerce", "Finance", "HR / Workforce Analytics"],
    ),
    KPITemplate(
        "average_order_value", "Average Order Value (AOV)",
        "The average monetary value per transaction/order.",
        "AVG(amount_column)", ["amount"],
        "SQL AVG aggregation over the detected amount column.",
        ["Sales / E-commerce"],
    ),
    KPITemplate(
        "total_quantity_sold", "Total Quantity Sold",
        "The total number of units sold across all transactions.",
        "SUM(quantity_column)", ["quantity"],
        "SQL SUM aggregation over the detected quantity column.",
        ["Sales / E-commerce", "Manufacturing / Operations"],
    ),
    KPITemplate(
        "top_category_by_amount", "Top Category by Revenue",
        "The category/product that generated the highest total monetary amount.",
        "GROUP BY category ORDER BY SUM(amount) DESC LIMIT 1",
        ["amount", "category"],
        "SQL GROUP BY + SUM + ORDER BY DESC on the detected category and amount columns.",
        ["Sales / E-commerce", "Marketing", "HR / Workforce Analytics"],
    ),
    KPITemplate(
        "record_count", "Total Record Count",
        "The total number of rows/records in the dataset.",
        "COUNT(*)", [],
        "SQL COUNT(*) over the full table.",
        ["General / Unclassified", "Sales / E-commerce", "Finance", "HR / Workforce Analytics",
         "Logistics / Inventory", "Healthcare", "Education", "Real Estate",
         "SaaS / Customer Analytics", "Manufacturing / Operations", "Marketing"],
    ),
    KPITemplate(
        "unique_entity_count", "Unique Entity Count",
        "The number of distinct entities (e.g. customers, patients, students) in an ID-like column.",
        "COUNT(DISTINCT id_column)", ["id"],
        "SQL COUNT(DISTINCT ...) over the detected identifier column.",
        ["Sales / E-commerce", "Healthcare", "Education", "HR / Workforce Analytics", "SaaS / Customer Analytics"],
    ),
    KPITemplate(
        "revenue_trend", "Revenue Trend Over Time",
        "How the total monetary amount changes across time periods.",
        "SUM(amount) GROUP BY date_period", ["amount", "date"],
        "SQL DATE_TRUNC + SUM + GROUP BY on the detected date and amount columns.",
        ["Sales / E-commerce", "Finance", "Marketing"],
    ),
    KPITemplate(
        "average_metric_by_category", "Average Metric by Category",
        "The average of the primary numeric metric broken down by category.",
        "AVG(numeric_column) GROUP BY category", ["amount", "category"],
        "SQL AVG + GROUP BY on a numeric column and a categorical column.",
        ["HR / Workforce Analytics", "Manufacturing / Operations", "Healthcare", "Education"],
    ),
    KPITemplate(
        "total_capital_raised", "Total Capital Raised",
        "The sum of a funding/investment/capital-style monetary column, distinct from operational revenue.",
        "SUM(capital_column)", ["capital"],
        "SQL SUM aggregation over the detected funding/capital column.",
        ["HR / Workforce Analytics", "Finance", "Sales / E-commerce", "SaaS / Customer Analytics"],
    ),
]
