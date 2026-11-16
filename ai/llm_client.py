"""
Unified LLM client.

CRITICAL PRINCIPLE: the LLM is used ONLY for reasoning, planning,
explanation, and text/SQL generation. It NEVER performs the actual
numeric calculation — all numbers the user sees come from
core engines (pandas/numpy/scipy/DuckDB).

If no provider/key is configured, `is_available()` returns False and
every AI-dependent feature in the app must degrade gracefully
(explain that AI is disabled, but keep deterministic features working).
"""
from __future__ import annotations

import json
import logging
from typing import Optional

from config.settings import settings

logger = logging.getLogger("datapilot.ai")


class LLMUnavailableError(Exception):
    pass


class LLMClient:
    def __init__(self):
        self._client = None
        if settings.ai_enabled():
            try:
                import anthropic
                self._client = anthropic.Anthropic(api_key=settings.llm_api_key)
            except Exception as e:
                logger.warning("Failed to initialize Anthropic client: %s", e)
                self._client = None

    def is_available(self) -> bool:
        return self._client is not None

    def complete(self, system: str, user: str, max_tokens: int = 1000, temperature: float = 0.2) -> str:
        if not self.is_available():
            raise LLMUnavailableError(
                "AI features are disabled. Set LLM_PROVIDER=anthropic and LLM_API_KEY in your .env to enable them."
            )
        try:
            response = self._client.messages.create(
                model=settings.model_name,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system,
                messages=[{"role": "user", "content": user}],
            )
            parts = [block.text for block in response.content if getattr(block, "type", "") == "text"]
            return "\n".join(parts).strip()
        except Exception as e:
            logger.error("LLM completion failed: %s", e)
            raise LLMUnavailableError(f"AI request failed: {e}")

    def complete_json(self, system: str, user: str, max_tokens: int = 1000) -> dict:
        """Ask the model to reply with ONLY JSON, and parse it defensively."""
        strict_system = system + "\n\nRespond with ONLY valid JSON. No markdown fences, no preamble, no commentary."
        raw = self.complete(strict_system, user, max_tokens=max_tokens, temperature=0.0)
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.strip("`")
            cleaned = cleaned.split("\n", 1)[-1] if "\n" in cleaned else cleaned
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as e:
            logger.error("Failed to parse LLM JSON response: %s | raw=%s", e, raw[:500])
            raise LLMUnavailableError(f"AI returned invalid JSON: {e}")


llm_client = LLMClient()
