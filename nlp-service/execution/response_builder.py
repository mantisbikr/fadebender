"""Response builders for error handling and clarification."""

from __future__ import annotations

import time
from typing import Dict, Any

from config.llm_config import get_default_model_name
from models.intent_types import Intent


def build_clarification_response(
    query: str,
    error_msg: str,
    model_preference: str | None,
    start_time: float
) -> Intent:
    """Return clarification response when all parsers fail.

    Args:
        query: Original user query
        error_msg: Error message from failed parsing
        model_preference: User's model preference
        start_time: Time when parsing started

    Returns:
        Intent dictionary with clarification_needed
    """
    # Safely get model name without throwing exception
    try:
        model_name = get_default_model_name(model_preference)
    except Exception:
        model_name = model_preference or "unknown"

    return {
        "intent": "clarification_needed",
        "question": "I'm having trouble understanding your command. Could you be more specific about which track and what parameter you want to adjust?",
        "context": {"partial_query": query},
        "meta": {
            "utterance": query,
            "fallback": True,
            "error": error_msg,
            "model_selected": model_name,
            "latency_ms": (time.perf_counter() - start_time) * 1000
        }
    }


def build_question_response(
    query: str,
    error_msg: str,
    model_preference: str | None
) -> Intent:
    """Return helpful response for audio troubleshooting questions.

    Args:
        query: Original user query
        error_msg: Error message from LLM
        model_preference: User's model preference

    Returns:
        Intent dictionary with question_response
    """
    # Safely get model name
    try:
        model_name = get_default_model_name(model_preference)
    except Exception:
        model_name = model_preference or "unknown"

    return {
        "intent": "question_response",
        "answer": "I'm having trouble connecting to the AI service. For audio issues, try: 1) Check track levels, 2) Apply gentle compression (2–4 dB GR), 3) Use EQ to cut muddiness around 200–400 Hz.",
        "suggested_intents": [
            "set track 1 volume to -6 dB",
            "increase track 1 volume by 3 dB",
            "reduce compressor threshold on track 1 by 3 dB"
        ],
        "meta": {
            "utterance": query,
            "fallback": True,
            "error": error_msg,
            "model_selected": model_name
        }
    }
