"""
Semantic/domain inference engine.

Combines column names + detected semantic types to guess the probable
business domain of the dataset. Never forces a domain when evidence
is weak — returns low confidence instead.
"""
from __future__ import annotations

from models.analysis import DomainDetection
from models.profile import DatasetProfile

_DOMAIN_KEYWORDS = {
    "Sales / E-commerce": (
        "order", "product", "sku", "price", "revenue", "customer", "cart",
        "quantity", "discount", "invoice", "طلب", "منتج", "عميل", "سعر",
    ),
    "Finance": (
        "transaction", "account", "balance", "payment", "loan", "interest",
        "credit", "debit", "budget", "expense", "حساب", "دفع", "فاتورة",
    ),
    "Marketing": (
        "campaign", "impression", "click", "ctr", "conversion", "lead",
        "channel", "ad_spend", "engagement", "حملة",
    ),
    "HR / Workforce Analytics": (
        "employee", "salary", "hire_date", "department", "position",
        "attendance", "performance_review", "موظف", "راتب", "قسم",
        "laid_off", "layoff", "layoffs", "total_laid_off", "percentage_laid_off",
        "headcount", "workforce_reduction", "workforce", "severance",
    ),
    "Logistics / Inventory": (
        "shipment", "warehouse", "stock", "inventory", "supplier",
        "delivery", "tracking", "shipping", "مخزون", "شحنة",
    ),
    "Healthcare": (
        "patient", "diagnosis", "treatment", "hospital", "doctor",
        "prescription", "admission", "مريض", "تشخيص",
    ),
    "Education": (
        "student", "course", "grade", "enrollment", "instructor",
        "semester", "طالب", "مقرر", "درجة",
    ),
    "Real Estate": (
        "property", "listing", "square_feet", "bedrooms", "rent",
        "mortgage", "عقار", "شقة",
    ),
    "SaaS / Customer Analytics": (
        "subscription", "churn", "mrr", "arr", "plan", "trial",
        "active_user", "session", "retention",
    ),
    "Manufacturing / Operations": (
        "machine", "batch", "defect", "downtime", "production_line",
        "yield", "maintenance",
    ),
}


class DomainDetector:
    def detect(self, profile: DatasetProfile) -> DomainDetection:
        col_names = " ".join(c.lower() for c in profile.columns.keys())
        semantic_labels = set()
        for c in profile.columns.values():
            semantic_labels.update(g.label for g in c.semantic_types)

        scores: dict[str, tuple[int, list[str]]] = {}
        for domain, keywords in _DOMAIN_KEYWORDS.items():
            hits = [kw for kw in keywords if kw in col_names]
            if hits:
                scores[domain] = (len(hits), hits)

        if "currency" in semantic_labels:
            for domain in ("Sales / E-commerce", "Finance"):
                if domain in scores:
                    count, hits = scores[domain]
                    scores[domain] = (count + 1, hits + ["currency-like column detected"])

        if not scores:
            return DomainDetection(domain="General / Unclassified", confidence=0.0,
                                    evidence=["No strong domain-specific column names detected."])

        ranked = sorted(scores.items(), key=lambda kv: kv[1][0], reverse=True)
        top_domain, (top_hits, evidence) = ranked[0]
        max_possible = max(len(kws) for kws in _DOMAIN_KEYWORDS.values())
        confidence = min(0.95, round(0.35 + 0.6 * (top_hits / max_possible), 2))

        alternatives = [(d, min(0.9, round(0.35 + 0.6 * (h / max_possible), 2))) for d, (h, _) in ranked[1:4]]

        return DomainDetection(
            domain=top_domain,
            confidence=confidence,
            evidence=[f"Matched column-name keyword: '{e}'" for e in evidence],
            alternative_domains=alternatives,
        )


domain_detector = DomainDetector()
