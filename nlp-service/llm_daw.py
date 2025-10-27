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

import json
import os
import time
from typing import Any, Dict, List

from config.llm_config import get_llm_project_id, get_llm_api_key, get_default_model_name
from config.nlp_config import get_nlp_mode, get_llm_timeout, NLPMode
from prompts.prompt_builder import build_daw_prompt
from models.intent_types import Intent
from fetchers import fetch_devices_cached, fetch_mixer_params_cached
from parsers import apply_typo_corrections, parse_mixer_command, parse_device_command


def interpret_daw_command(
    query: str,
    model_preference: str | None = None,
    strict: bool | None = None,
) -> Intent:
    """Interpret user query into DAW commands.

    Execution mode is determined by NLP_MODE environment variable:
    - regex_first: Fast patterns → LLM fallback (default)
    - llm_first: LLM → Regex fallback (legacy)
    - regex_only: Only regex patterns
    - llm_only: Only LLM
    - parallel: Both (for testing)

    Args:
        query: User command text
        model_preference: LLM model to use (e.g., "gemini-2.5-flash")
        strict: If True, don't fallback on LLM errors

    Returns:
        Intent dictionary with meta.latency_ms for performance tracking
    """
    mode = get_nlp_mode()

    if mode == NLPMode.REGEX_FIRST:
        return _interpret_regex_first(query, model_preference, strict)
    elif mode == NLPMode.LLM_FIRST:
        return _interpret_llm_first(query, model_preference, strict)
    elif mode == NLPMode.REGEX_ONLY:
        return _interpret_regex_only(query, model_preference)
    elif mode == NLPMode.LLM_ONLY:
        return _interpret_llm_only(query, model_preference, strict)
    elif mode == NLPMode.PARALLEL:
        return _interpret_parallel(query, model_preference, strict)
    else:
        # Default to regex-first
        return _interpret_regex_first(query, model_preference, strict)


def _interpret_regex_first(query: str, model_preference: str | None, strict: bool | None) -> Intent:
    """RECOMMENDED: Try regex first (1-10ms), fallback to LLM if no match."""
    start = time.perf_counter()

    # Try regex patterns first (fast!)
    result = _try_regex_parse(query, "", model_preference)
    if result:
        result['meta']['pipeline'] = 'regex'
        result['meta']['latency_ms'] = (time.perf_counter() - start) * 1000
        result['meta']['cache_hit'] = True  # Always true for regex (no fetching needed)
        return result

    # No regex match - try LLM
    try:
        result = _call_llm(query, model_preference)
        result['meta']['pipeline'] = 'llm_fallback'
        result['meta']['latency_ms'] = (time.perf_counter() - start) * 1000
        return result
    except Exception as e:
        if strict is None:
            strict = os.getenv("LLM_STRICT", "").lower() in ("1", "true", "yes", "on")
        if strict:
            raise

        # LLM also failed - return clarification
        return _clarification_response(query, str(e), model_preference, start)


def _interpret_llm_first(query: str, model_preference: str | None, strict: bool | None) -> Intent:
    """LEGACY: Try LLM first (2-5s), fallback to regex."""
    start = time.perf_counter()

    try:
        result = _call_llm(query, model_preference)
        result['meta']['pipeline'] = 'llm_primary'
        result['meta']['latency_ms'] = (time.perf_counter() - start) * 1000
        return result
    except Exception as e:
        if strict is None:
            strict = os.getenv("LLM_STRICT", "").lower() in ("1", "true", "yes", "on")
        if strict:
            raise

        # LLM failed - try regex fallback
        result = _try_regex_parse(query, str(e), model_preference)
        if result:
            result['meta']['pipeline'] = 'regex_fallback'
            result['meta']['latency_ms'] = (time.perf_counter() - start) * 1000
            return result

        # Both failed
        return _clarification_response(query, str(e), model_preference, start)


def _interpret_regex_only(query: str, model_preference: str | None) -> Intent:
    """TESTING: Only use regex patterns (for coverage testing)."""
    start = time.perf_counter()

    result = _try_regex_parse(query, "", model_preference)
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


def _interpret_llm_only(query: str, model_preference: str | None, strict: bool | None) -> Intent:
    """TESTING: Only use LLM (for accuracy testing)."""
    start = time.perf_counter()

    try:
        result = _call_llm(query, model_preference)
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


def _interpret_parallel(query: str, model_preference: str | None, strict: bool | None) -> Intent:
    """TESTING: Run both pipelines, return faster one, log comparison."""
    from concurrent.futures import ThreadPoolExecutor
    import threading

    start = time.perf_counter()
    results = {}
    lock = threading.Lock()

    def run_regex():
        result = _try_regex_parse(query, "", model_preference)
        with lock:
            results['regex'] = result if result else None

    def run_llm():
        try:
            result = _call_llm(query, model_preference)
            with lock:
                results['llm'] = result
        except Exception as e:
            with lock:
                results['llm'] = None
                results['llm_error'] = str(e)

    # Run both in parallel
    with ThreadPoolExecutor(max_workers=2) as executor:
        regex_future = executor.submit(run_regex)
        llm_future = executor.submit(run_llm)

        # Wait for both to complete
        regex_future.result()
        llm_future.result()

    # Determine which one to return
    regex_result = results.get('regex')
    llm_result = results.get('llm')

    total_latency = (time.perf_counter() - start) * 1000

    # If regex succeeded, use it (usually faster)
    if regex_result:
        result = regex_result
        result['meta']['pipeline'] = 'parallel_regex_won'
        result['meta']['total_latency_ms'] = total_latency
        result['meta']['comparison'] = {
            'regex_succeeded': True,
            'llm_succeeded': llm_result is not None,
            'llm_error': results.get('llm_error')
        }
        return result

    # Regex failed, use LLM if available
    if llm_result:
        result = llm_result
        result['meta']['pipeline'] = 'parallel_llm_won'
        result['meta']['total_latency_ms'] = total_latency
        result['meta']['comparison'] = {
            'regex_succeeded': False,
            'llm_succeeded': True
        }
        return result

    # Both failed
    return _clarification_response(query, results.get('llm_error', 'Both parsers failed'), model_preference, start)


def _try_regex_parse(query: str, error_msg: str, model_preference: str | None) -> Dict[str, Any] | None:
    """Try regex-based parsing.

    Returns:
        Intent dict if matched, None if no match
    """
    # Apply typo corrections and expand ordinal words
    q = apply_typo_corrections(query)

    # Try mixer commands first (most common: volume, pan, solo, mute, sends)
    result = parse_mixer_command(q, query, error_msg, model_preference)
    if result:
        return result

    # Try device commands (reverb, delay, compressor, etc.)
    result = parse_device_command(q, query, error_msg, model_preference)
    if result:
        return result

    # Questions about problems (treat as help-style queries)
    if any(phrase in q for phrase in [
        "too soft", "too quiet", "can't hear", "how to", "what does",
        "weak", "thin", "muddy", "boomy", "harsh", "dull"
    ]):
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
            "meta": {"utterance": query, "fallback": True, "error": error_msg, "model_selected": model_name}
        }

    # No match
    return None


def _call_llm(query: str, model_preference: str | None) -> Intent:
    """Call LLM with cached device/param data.

    Uses caching to avoid repeated Firestore/HTTP calls.
    Typical latency: 2-4 seconds (dominated by LLM inference).

    Raises:
        Exception on LLM errors
    """
    # Fetch with caching (5 second TTL by default)
    known_devices = fetch_devices_cached()
    mixer_params = fetch_mixer_params_cached()

    from google import genai  # type: ignore
    from google.genai import types  # type: ignore

    project = get_llm_project_id()
    location = os.getenv("GCP_REGION", "us-central1")
    model_name = get_default_model_name(model_preference)

    # Initialize client with Vertex AI mode
    client = genai.Client(vertexai=True, project=project, location=location)

    prompt = build_daw_prompt(query, mixer_params, known_devices)

    # Generate content with configuration
    config = types.GenerateContentConfig(
        temperature=0.1,
        max_output_tokens=512,
        top_p=0.8,
        top_k=20,
    )

    resp = client.models.generate_content(
        model=model_name,
        contents=prompt,
        config=config
    )

    response_text = resp.text if hasattr(resp, 'text') else None
    if not response_text:
        raise RuntimeError("Empty LLM response")

    text = response_text.strip()
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end <= start:
        raise ValueError("No JSON found in response")

    result = json.loads(text[start:end + 1])
    result.setdefault("meta", {})["model_used"] = model_name
    return result


def _clarification_response(query: str, error_msg: str, model_preference: str | None, start_time: float) -> Intent:
    """Return clarification response when all parsers fail."""
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


if __name__ == "__main__":
    import argparse
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
