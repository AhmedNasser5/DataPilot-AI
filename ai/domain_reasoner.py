"""
Domain Reasoner.

The deterministic domain_detector already assigns a domain + confidence
from column-name keyword matching. This module only asks the LLM to
phrase a short human-readable justification — it cannot change the
domain or confidence value itself.
"""
from __future__ import annotations

from ai.llm_client import LLMUnavailableError, llm_client
from ai.prompts.system_prompt import BASE_SYSTEM_PROMPT
from models.analysis import DomainDetection


class DomainReasoner:
    def explain(self, domain: DomainDetection, column_names: list[str]) -> str:
        if not llm_client.is_available():
            return "; ".join(domain.evidence) or "No strong evidence found."

        prompt = (
            f"A deterministic system detected the business domain '{domain.domain}' "
            f"with confidence {domain.confidence} for a dataset with these columns: "
            f"{', '.join(column_names[:40])}.\n\n"
            f"Supporting evidence: {domain.evidence}\n\n"
            "Write ONE short sentence (max 30 words) justifying this domain classification "
            "for a business user. Do not change the domain name or confidence."
        )
        try:
            return llm_client.complete(BASE_SYSTEM_PROMPT, prompt, max_tokens=100)
        except LLMUnavailableError:
            return "; ".join(domain.evidence) or "No strong evidence found."


domain_reasoner = DomainReasoner()
