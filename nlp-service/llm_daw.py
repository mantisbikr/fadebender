"""
Lightweight LLM-backed DAW command interpreter.

Supports multiple execution modes:
- REGEX_FIRST: Try fast regex patterns first, fallback to LLM (RECOMMENDED - 1-10ms typical)
- LLM_FIRST: Try LLM first, fallback to regex (LEGACY - 2-5s typical)
- REGEX_ONLY: Only use regex (for testing coverage)
- LLM_ONLY: Only use LLM (for testing accuracy)
- PARALLEL: Run both, return faster (for A/B testing)

Set mode via: export NLP_MODE=regex_first
"""
from __future__ import annotations

from models.intent_types import Intent
from execution import dispatch


def interpret_daw_command(
    query: str,
    model_preference: str | None = None,
    strict: bool | None = None,
) -> Intent:
    """Interpret user query into DAW commands.

    Execution mode is determined by NLP_MODE environment variable:
    - regex_first: Fast patterns → LLM fallback (performance)
    - llm_first: LLM → Regex fallback (legacy, default)
    - regex_only: Only regex patterns (testing)
    - llm_only: Only LLM (testing)
    - parallel: Both (A/B testing)

    Args:
        query: User command text
        model_preference: LLM model to use (e.g., "gemini-2.5-flash")
        strict: If True, don't fallback on LLM errors

    Returns:
        Intent dictionary with meta.latency_ms for performance tracking
    """
    return dispatch(query, model_preference, strict)


if __name__ == "__main__":
    import argparse
    import json
    import os
    import sys
    try:
        from dotenv import load_dotenv  # optional
        load_dotenv()
    except Exception:
        pass

    parser = argparse.ArgumentParser(description="Parse a DAW command and print JSON.")
    parser.add_argument("text", help="Command text in quotes")
    parser.add_argument("--model", dest="model", default=None, help="Model preference (e.g., gemini-2.5-flash or llama)")
    parser.add_argument("--mode", dest="mode", default=None, help="Pipeline mode (regex_first, llm_first, regex_only, llm_only, parallel)")
    args = parser.parse_args()

    # Override mode if specified
    if args.mode:
        os.environ["NLP_MODE"] = args.mode

    result = interpret_daw_command(args.text, model_preference=args.model)
    print(json.dumps(result, ensure_ascii=False))
    sys.exit(0)
