"""Dispatcher that routes to appropriate execution strategy based on NLP mode."""

from __future__ import annotations

from config.nlp_config import get_nlp_mode, NLPMode
from models.intent_types import Intent
from execution.strategies import regex_first, llm_first, regex_only, llm_only, parallel


def dispatch(query: str, model_preference: str | None = None, strict: bool | None = None) -> Intent:
    """Dispatch query to appropriate execution strategy based on configured mode.

    Execution mode priority:
    1. NLP_MODE environment variable (runtime override)
    2. app_config.py nlp.mode setting (default: regex_first)
    3. Fallback to regex_first

    Available modes:
    - regex_first: Fast patterns → LLM fallback (RECOMMENDED - 1651x faster)
    - llm_first: LLM → Regex fallback (LEGACY - 400ms overhead)
    - regex_only: Only regex patterns (testing)
    - llm_only: Only LLM (testing)
    - parallel: Both (A/B testing)

    Args:
        query: User command text
        model_preference: LLM model to use (e.g., "gemini-2.5-flash")
        strict: If True, don't fallback on LLM errors

    Returns:
        Intent dictionary with meta.latency_ms and meta.pipeline for tracking
    """
    mode = get_nlp_mode()

    if mode == NLPMode.REGEX_FIRST:
        return regex_first.execute(query, model_preference, strict)
    elif mode == NLPMode.LLM_FIRST:
        return llm_first.execute(query, model_preference, strict)
    elif mode == NLPMode.REGEX_ONLY:
        return regex_only.execute(query, model_preference, strict)
    elif mode == NLPMode.LLM_ONLY:
        return llm_only.execute(query, model_preference, strict)
    elif mode == NLPMode.PARALLEL:
        return parallel.execute(query, model_preference, strict)
    else:
        # Should never reach here, but default to regex_first for performance
        return regex_first.execute(query, model_preference, strict)
