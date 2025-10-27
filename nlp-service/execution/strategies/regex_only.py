"""Regex-only strategy: Only use regex patterns (for testing coverage).

TESTING mode - helps test regex pattern coverage.
"""

from __future__ import annotations

import time

from models.intent_types import Intent
from execution.regex_executor import try_regex_parse


def execute(query: str, model_preference: str | None, strict: bool | None) -> Intent:
    """Only use regex patterns (for coverage testing).

    Args:
        query: User query text
        model_preference: Not used (kept for interface compatibility)
        strict: Not used

    Returns:
        Intent dictionary if matched, clarification if no match
    """
    start = time.perf_counter()

    result = try_regex_parse(query, "", model_preference)
    if result:
        result['meta']['pipeline'] = 'regex_only'
        result['meta']['latency_ms'] = (time.perf_counter() - start) * 1000
        return result

    # No match
    return {
        "intent": "clarification_needed",
        "question": "Regex parser couldn't understand this command.",
        "meta": {
            "utterance": query,
            "pipeline": "regex_only",
            "latency_ms": (time.perf_counter() - start) * 1000
        }
    }
