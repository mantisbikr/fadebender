"""Regex-first strategy: Try regex patterns first, fallback to LLM.

RECOMMENDED for production use (1-10ms typical for common commands).
"""

from __future__ import annotations

import os
import time

from models.intent_types import Intent
from execution.regex_executor import try_regex_parse
from execution.llm_executor import call_llm
from execution.response_builder import build_clarification_response


def execute(query: str, model_preference: str | None, strict: bool | None) -> Intent:
    """Try regex first (1-10ms), fallback to LLM if no match.

    Args:
        query: User query text
        model_preference: LLM model preference
        strict: If True, don't fallback on LLM errors

    Returns:
        Intent dictionary with meta.pipeline and meta.latency_ms
    """
    start = time.perf_counter()

    # Try regex patterns first (fast!)
    result = try_regex_parse(query, "", model_preference)
    if result:
        result['meta']['pipeline'] = 'regex'
        result['meta']['latency_ms'] = (time.perf_counter() - start) * 1000
        result['meta']['cache_hit'] = True  # Always true for regex (no fetching needed)
        return result

    # No regex match - try LLM
    try:
        result = call_llm(query, model_preference)
        result['meta']['pipeline'] = 'llm_fallback'
        result['meta']['latency_ms'] = (time.perf_counter() - start) * 1000
        return result
    except Exception as e:
        if strict is None:
            strict = os.getenv("LLM_STRICT", "").lower() in ("1", "true", "yes", "on")
        if strict:
            raise

        # LLM also failed - return clarification
        return build_clarification_response(query, str(e), model_preference, start)
