"""LLM-first strategy: Try LLM first, fallback to regex.

LEGACY mode - preserves original behavior (2-5s typical).
"""

from __future__ import annotations

import os
import time

from models.intent_types import Intent
from execution.llm_executor import call_llm
from execution.regex_executor import try_regex_parse
from execution.response_builder import build_clarification_response


def execute(query: str, model_preference: str | None, strict: bool | None) -> Intent:
    """Try LLM first (2-5s), fallback to regex.

    Args:
        query: User query text
        model_preference: LLM model preference
        strict: If True, don't fallback on LLM errors

    Returns:
        Intent dictionary with meta.pipeline and meta.latency_ms
    """
    start = time.perf_counter()

    try:
        result = call_llm(query, model_preference)
        result['meta']['pipeline'] = 'llm_primary'
        result['meta']['latency_ms'] = (time.perf_counter() - start) * 1000
        return result
    except Exception as e:
        if strict is None:
            strict = os.getenv("LLM_STRICT", "").lower() in ("1", "true", "yes", "on")
        if strict:
            raise

        # LLM failed - try regex fallback
        result = try_regex_parse(query, str(e), model_preference)
        if result:
            result['meta']['pipeline'] = 'regex_fallback'
            result['meta']['latency_ms'] = (time.perf_counter() - start) * 1000
            return result

        # Both failed
        return build_clarification_response(query, str(e), model_preference, start)
