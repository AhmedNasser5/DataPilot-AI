"""Prompt template for evidence-based insight generation."""

INSIGHTS_PROMPT = """You are given ACTUAL computed statistics/results about a dataset below. Write
3-5 concise, evidence-based analytical insights a business user would find useful.

For EACH insight, tag it as one of: FACT, CALCULATION, INTERPRETATION, or HYPOTHESIS,
and make sure every number you mention appears in the evidence below (never invent
or round in a way that changes the meaning).

Detected domain: {domain} (confidence: {domain_confidence})

Evidence (JSON):
{evidence_json}

Respond with ONLY JSON: a list of objects like
[{{"kind": "FACT|CALCULATION|INTERPRETATION|HYPOTHESIS", "text": "<insight>"}}]
"""
