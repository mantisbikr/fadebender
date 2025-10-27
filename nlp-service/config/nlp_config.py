"""NLP pipeline configuration and mode settings."""

from __future__ import annotations

import os
from enum import Enum


class NLPMode(str, Enum):
    """NLP pipeline execution modes.

    REGEX_FIRST: Try regex patterns first, fallback to LLM (RECOMMENDED)
                 - Fast for common commands (1-10ms)
                 - Accurate fallback for complex queries

    LLM_FIRST: Try LLM first, fallback to regex (LEGACY)
               - Slower but may handle edge cases better
               - Original behavior

    REGEX_ONLY: Only use regex patterns (for testing coverage)
                - Fast but limited to known patterns

    LLM_ONLY: Only use LLM (for testing accuracy)
              - Slow but handles all cases

    PARALLEL: Run both pipelines, return faster, log comparison
              - Good for A/B testing
              - Logs discrepancies for analysis
    """
    REGEX_FIRST = "regex_first"
    LLM_FIRST = "llm_first"
    REGEX_ONLY = "regex_only"
    LLM_ONLY = "llm_only"
    PARALLEL = "parallel"


def get_nlp_mode() -> NLPMode:
    """Get NLP mode from environment variable.

    Set via: export NLP_MODE=regex_first

    Returns:
        NLPMode enum value (defaults to LLM_FIRST to match original behavior)
    """
    mode_str = os.getenv("NLP_MODE", "llm_first").lower()
    try:
        return NLPMode(mode_str)
    except ValueError:
        # Invalid mode, return default
        return NLPMode.LLM_FIRST


def get_llm_timeout() -> float:
    """Get LLM timeout in seconds.

    Set via: export LLM_TIMEOUT_MS=800

    Returns:
        Timeout in seconds (defaults to 0.8s = 800ms)
    """
    timeout_ms = int(os.getenv("LLM_TIMEOUT_MS", "800"))
    return timeout_ms / 1000.0


def get_cache_ttl() -> int:
    """Get cache TTL in seconds.

    Set via: export CACHE_TTL_SECONDS=5

    Returns:
        Cache TTL in seconds (defaults to 5)
    """
    return int(os.getenv("CACHE_TTL_SECONDS", "5"))
