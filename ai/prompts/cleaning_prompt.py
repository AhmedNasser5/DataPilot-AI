"""Prompt template for AI-assisted cleaning explanations (Level 3 ambiguous cases)."""

CLEANING_EXPLAIN_PROMPT = """A deterministic engine detected the following data-quality issue and proposed
a transformation. Explain the reasoning in plain, professional language for a
non-technical business user, in 2-4 sentences. Do not change or invent the numbers
given below — only explain and contextualize them.

Column: {column}
Issue: {issue}
Proposed action: {action_label}
Detection method: {detection_method}
Confidence: {confidence}
Sample before values: {before_sample}
Sample after values: {after_sample}

Respond with plain text only (no JSON, no markdown headers).
"""
