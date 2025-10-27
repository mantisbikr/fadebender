"""Dispatcher that routes to appropriate execution strategy based on NLP mode."""

from __future__ import annotations

from config.nlp_config import get_nlp_mode, NLPMode
from models.intent_types import Intent
from execution.strategies import regex_first, llm_first, regex_only, llm_only, parallel


def dispatch(query: str, model_preference: str | None = None, strict: bool | None = None) -> Intent:
    """Dispatch query to appropriate execution strategy based on configured mode.

    Execution mode is determined by NLP_MODE environment variable:
    - regex_first: Fast patterns → LLM fallback (default for performance)
    - llm_first: LLM → Regex fallback (legacy, preserves original behavior)
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
        # Default to llm-first (preserves original behavior)
        return llm_first.execute(query, model_preference, strict)
