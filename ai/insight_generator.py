"""
Insight Generator.

Takes ALREADY-COMPUTED evidence (stats, KPI values, correlations) and
asks the LLM to phrase insights from it — tagged FACT / CALCULATION /
INTERPRETATION / HYPOTHESIS. If AI is disabled, falls back to a
deterministic templated summary so the feature never fully breaks.
"""
from __future__ import annotations

import json

from ai.llm_client import LLMUnavailableError, llm_client
from ai.prompts.insights_prompt import INSIGHTS_PROMPT
from ai.prompts.system_prompt import BASE_SYSTEM_PROMPT
from models.analysis import DomainDetection, Insight, InsightKind


class InsightGenerator:
    def generate(self, domain: DomainDetection, evidence: dict) -> list[Insight]:
        if not llm_client.is_available():
            return self._fallback(evidence)

        prompt = INSIGHTS_PROMPT.format(
            domain=domain.domain,
            domain_confidence=domain.confidence,
            evidence_json=json.dumps(evidence, default=str, ensure_ascii=False),
        )
        try:
            raw = llm_client.complete_json(BASE_SYSTEM_PROMPT, prompt, max_tokens=800)
        except LLMUnavailableError:
            return self._fallback(evidence)

        items = raw if isinstance(raw, list) else raw.get("insights", [])
        insights = []
        for item in items:
            try:
                kind = InsightKind(item.get("kind", "interpretation").lower())
            except ValueError:
                kind = InsightKind.INTERPRETATION
            insights.append(Insight(text=item.get("text", ""), kind=kind, evidence=evidence))
        return insights or self._fallback(evidence)

    def _fallback(self, evidence: dict) -> list[Insight]:
        insights = [Insight(
            text="AI-generated narrative insights are unavailable (no LLM configured). "
                 "Below is a deterministic summary of the computed evidence instead.",
            kind=InsightKind.FACT, evidence=evidence,
        )]
        for key, value in list(evidence.items())[:5]:
            insights.append(Insight(text=f"{key}: {value}", kind=InsightKind.CALCULATION, evidence={key: value}))
        return insights


insight_generator = InsightGenerator()
