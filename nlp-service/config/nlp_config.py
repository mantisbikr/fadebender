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
    """Get NLP mode from config or environment variable.

    Priority order:
    1. NLP_MODE environment variable (allows runtime override)
    2. app_config.py nlp.mode setting (configurable default)
    3. Fallback to regex_first (recommended for performance)

    Set via config: Edit configs/app_config.json nlp.mode
    Set via env: export NLP_MODE=regex_first

    Returns:
        NLPMode enum value (defaults to REGEX_FIRST for performance)
    """
    # Check env var first (highest priority)
    env_mode = os.getenv("NLP_MODE")
    if env_mode:
        try:
            return NLPMode(env_mode.lower())
        except ValueError:
            pass  # Fall through to config

    # Check app_config (middle priority)
    try:
        from server.config.app_config import get_nlp_mode_config
        config_mode = get_nlp_mode_config()
        try:
            return NLPMode(config_mode.lower())
        except ValueError:
            pass  # Fall through to default
    except Exception:
        pass  # Config not available (e.g., running from nlp-service standalone)

    # Default to regex_first for performance
    return NLPMode.REGEX_FIRST


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
