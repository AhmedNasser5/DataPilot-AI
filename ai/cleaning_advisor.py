"""
Cleaning Advisor.

Adds a plain-language explanation on top of a deterministically-built
Transformation (see core/cleaning/cleaning_planner.py). The AI never
decides WHICH transformation to run or WHAT number to impute — it only
explains a decision the deterministic planner already made.
"""
from __future__ import annotations

from ai.llm_client import LLMUnavailableError, llm_client
from ai.prompts.cleaning_prompt import CLEANING_EXPLAIN_PROMPT
from ai.prompts.system_prompt import BASE_SYSTEM_PROMPT
from models.transformation import Transformation


class CleaningAdvisor:
    def explain(self, transformation: Transformation) -> str:
        if not llm_client.is_available():
            return transformation.reason  # deterministic reason already exists; AI just enriches it

        prompt = CLEANING_EXPLAIN_PROMPT.format(
            column=transformation.column,
            issue=transformation.issue,
            action_label=transformation.action_label,
            detection_method=transformation.detection_method,
            confidence=transformation.confidence,
            before_sample=transformation.before_sample,
            after_sample=transformation.after_sample,
        )
        try:
            return llm_client.complete(BASE_SYSTEM_PROMPT, prompt, max_tokens=300)
        except LLMUnavailableError:
            return transformation.reason


cleaning_advisor = CleaningAdvisor()
