"""
Semantic-type detection layer.

Goes beyond structural type (numeric/text/date) to guess *meaning*:
email, phone, URL, currency, percentage, geography, ID, primary key.
Every result carries a confidence score — nothing here is asserted
as certain.
"""
from __future__ import annotations

import re

import pandas as pd

from models.profile import SemanticGuess

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[a-zA-Z]{2,}$")
_URL_RE = re.compile(r"^(https?://|www\.)[^\s]+$", re.IGNORECASE)
_PHONE_RE = re.compile(r"^\+?[\d\s\-\(\)]{7,20}$")
_CURRENCY_SYMBOLS = ("$", "€", "£", "¥", "ر.س", "ج.م", "USD", "EUR", "GBP", "EGP", "SAR")
_PERCENT_RE = re.compile(r"^-?\d+(\.\d+)?\s?%$")
_GEO_COLUMN_HINTS = (
    "country", "city", "state", "region", "province", "governorate",
    "address", "location", "lat", "lon", "lng", "latitude", "longitude",
    "zip", "postal", "دولة", "مدينة", "محافظة", "عنوان",
)
_ID_COLUMN_HINTS = ("id", "_id", "code", "uuid", "identifier", "رقم", "كود")


class SemanticDetector:
    """Combines column-name hints with value-pattern sniffing."""

    def detect(self, column_name: str, series: pd.Series, is_numeric: bool) -> list[SemanticGuess]:
        guesses: list[SemanticGuess] = []
        name_l = column_name.lower().strip()
        non_null = series.dropna()

        guesses.extend(self._name_based_guesses(name_l))

        if not is_numeric and not non_null.empty:
            sample = non_null.astype(str).str.strip().head(300)
            guesses.extend(self._pattern_based_guesses(sample))
        elif is_numeric:
            guesses.extend(self._numeric_semantic_guesses(name_l, non_null))

        # ID / primary key candidacy based on cardinality (added by caller using this + profile)
        merged = self._merge_guesses(guesses)
        return sorted(merged, key=lambda g: g.confidence, reverse=True)

    def _name_based_guesses(self, name_l: str) -> list[SemanticGuess]:
        out = []
        if any(h in name_l for h in _GEO_COLUMN_HINTS):
            out.append(SemanticGuess("geography", 0.6, f"Column name '{name_l}' matches geographic hints."))
        if any(h in name_l for h in _ID_COLUMN_HINTS):
            out.append(SemanticGuess("id", 0.55, f"Column name '{name_l}' matches ID-like hints."))
        if "email" in name_l or "بريد" in name_l:
            out.append(SemanticGuess("email", 0.5, "Column name suggests email."))
        if "phone" in name_l or "mobile" in name_l or "هاتف" in name_l:
            out.append(SemanticGuess("phone", 0.5, "Column name suggests phone number."))
        if "url" in name_l or "link" in name_l or "website" in name_l:
            out.append(SemanticGuess("url", 0.5, "Column name suggests URL."))
        if any(k in name_l for k in ("price", "revenue", "cost", "amount", "salary", "fee", "funds_raised", "funding", "capital", "investment", "سعر", "تكلفة")):
            out.append(SemanticGuess("currency", 0.4, "Column name suggests a monetary amount."))
        if "percent" in name_l or name_l.endswith("_pct") or "نسبة" in name_l:
            out.append(SemanticGuess("percentage", 0.5, "Column name suggests a percentage."))
        return out

    def _pattern_based_guesses(self, sample: pd.Series) -> list[SemanticGuess]:
        out = []
        n = max(len(sample), 1)
        email_ratio = sample.map(lambda v: bool(_EMAIL_RE.match(v))).mean()
        if email_ratio > 0.8:
            out.append(SemanticGuess("email", float(email_ratio), "Values match email pattern."))

        url_ratio = sample.map(lambda v: bool(_URL_RE.match(v))).mean()
        if url_ratio > 0.8:
            out.append(SemanticGuess("url", float(url_ratio), "Values match URL pattern."))

        phone_ratio = sample.map(lambda v: bool(_PHONE_RE.match(v))).mean()
        if phone_ratio > 0.8:
            out.append(SemanticGuess("phone", float(phone_ratio), "Values match phone-number pattern."))

        currency_ratio = sample.map(lambda v: any(sym in v for sym in _CURRENCY_SYMBOLS)).mean()
        if currency_ratio > 0.5:
            out.append(SemanticGuess("currency", float(currency_ratio), "Values contain currency symbols/codes."))

        percent_ratio = sample.map(lambda v: bool(_PERCENT_RE.match(v))).mean()
        if percent_ratio > 0.5:
            out.append(SemanticGuess("percentage", float(percent_ratio), "Values match percentage pattern (e.g. '12.5%')."))

        return out

    def _numeric_semantic_guesses(self, name_l: str, non_null: pd.Series) -> list[SemanticGuess]:
        out = []
        if any(k in name_l for k in ("price", "revenue", "cost", "amount", "salary", "fee", "total", "funds_raised", "funding", "capital", "investment", "سعر")):
            out.append(SemanticGuess("currency", 0.5, "Numeric column name suggests a monetary amount."))
        if "percent" in name_l or name_l.endswith("_pct") or name_l.endswith("_rate"):
            if not non_null.empty and non_null.between(-1, 1).mean() > 0.9:
                out.append(SemanticGuess("percentage", 0.6, "Column name and 0-1 range suggest a ratio/percentage."))
            elif not non_null.empty and non_null.between(0, 100).mean() > 0.9:
                out.append(SemanticGuess("percentage", 0.5, "Column name and 0-100 range suggest a percentage."))
        if any(k in name_l for k in ("lat", "latitude")):
            if not non_null.empty and non_null.between(-90, 90).mean() > 0.95:
                out.append(SemanticGuess("geography", 0.7, "Values fall within valid latitude range."))
        if any(k in name_l for k in ("lon", "lng", "longitude")):
            if not non_null.empty and non_null.between(-180, 180).mean() > 0.95:
                out.append(SemanticGuess("geography", 0.7, "Values fall within valid longitude range."))
        return out

    @staticmethod
    def _merge_guesses(guesses: list[SemanticGuess]) -> list[SemanticGuess]:
        best: dict[str, SemanticGuess] = {}
        for g in guesses:
            if g.label not in best or g.confidence > best[g.label].confidence:
                best[g.label] = g
        return list(best.values())
