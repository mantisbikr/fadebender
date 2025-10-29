"""LLM-only strategy: Only use LLM (for testing accuracy).

TESTING mode - helps test LLM accuracy without regex.
"""

from __future__ import annotations

import time

from models.intent_types import Intent
from execution.llm_executor import call_llm


def execute(query: str, model_preference: str | None, strict: bool | None) -> Intent:
    """Only use LLM (for accuracy testing).

    Args:
        query: User query text
        model_preference: LLM model preference
        strict: If True, raise on errors

    Returns:
        Intent dictionary or error response
    """
    start = time.perf_counter()

    try:
        result = call_llm(query, model_preference)
        result['meta']['pipeline'] = 'llm_only'
        result['meta']['latency_ms'] = (time.perf_counter() - start) * 1000
        return result
    except Exception as e:
        if strict:
            raise
        return {
            "intent": "clarification_needed",
            "question": f"LLM error: {str(e)}",
            "meta": {
                "utterance": query,
                "pipeline": "llm_only",
                "error": str(e),
                "latency_ms": (time.perf_counter() - start) * 1000
            }
        }
