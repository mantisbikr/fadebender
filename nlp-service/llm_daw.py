"""
Lightweight LLM-backed DAW command interpreter.

- Primary: Use Vertex AI via SDK when available.
- Fallback: Simple pattern-based parsing when SDK or network is unavailable.
"""
from __future__ import annotations

import json
import os
from typing import Any, Dict, List

from config.llm_config import get_llm_project_id, get_llm_api_key, get_default_model_name
from prompts.prompt_builder import build_daw_prompt
from models.intent_types import Intent
from fetchers import fetch_session_devices, fetch_preset_devices, fetch_mixer_params
from parsers import apply_typo_corrections, parse_mixer_command, parse_device_command


def interpret_daw_command(
    query: str,
    model_preference: str | None = None,
    strict: bool | None = None,
) -> Intent:
    """Interpret user query into DAW commands using Vertex AI if available."""
    # PRIORITY 1: Fetch devices from current Live session (most accurate)
    known_devices = fetch_session_devices()

    # PRIORITY 2: Fall back to Firestore presets only if session fetch failed
    if not known_devices:
        known_devices = fetch_preset_devices()

    # Fetch mixer params from Firestore
    mixer_params = fetch_mixer_params()

    # Fallback to hardcoded lists if Firestore unavailable
    if not mixer_params:
        mixer_params = ["volume", "pan", "mute", "solo", "send"]

    # Try Google Gen AI SDK (Vertex AI mode)
    try:
        from google import genai  # type: ignore
        from google.genai import types  # type: ignore

        project = get_llm_project_id()
        location = os.getenv("GCP_REGION", "us-central1")
        model_name = get_default_model_name(model_preference)

        # Initialize client with Vertex AI mode (uses Application Default Credentials)
        # Respects GOOGLE_APPLICATION_CREDENTIALS environment variable for service account auth
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

    except Exception as e:
        # If strict mode is enabled, do not fallback
        if strict is None:
            strict = os.getenv("LLM_STRICT", "").lower() in ("1", "true", "yes", "on")
        if strict:
            raise
        # Otherwise fallback to rule-based parsing
        return _fallback_daw_parse(query, str(e), model_preference)


def _fallback_daw_parse(query: str, error_msg: str, model_preference: str | None) -> Dict[str, Any]:
    """Simple rule-based fallback parser for basic DAW commands."""
    # Apply typo corrections and expand ordinal words
    q = apply_typo_corrections(query)

    # Try mixer commands first (most common)
    result = parse_mixer_command(q, query, error_msg, model_preference)
    if result:
        return result

    # Try device commands
    result = parse_device_command(q, query, error_msg, model_preference)
    if result:
        return result

    # Questions about problems (treat as help-style queries)
    if any(phrase in q for phrase in [
        "too soft", "too quiet", "can't hear", "how to", "what does",
        "weak", "thin", "muddy", "boomy", "harsh", "dull"
    ]):
        return {
            "intent": "question_response",
            "answer": "I'm having trouble connecting to the AI service. For audio issues, try: 1) Check track levels, 2) Apply gentle compression (2–4 dB GR), 3) Use EQ to cut muddiness around 200–400 Hz.",
            "suggested_intents": [
                "set track 1 volume to -6 dB",
                "increase track 1 volume by 3 dB",
                "reduce compressor threshold on track 1 by 3 dB"
            ],
            "meta": {"utterance": query, "fallback": True, "error": error_msg, "model_selected": get_default_model_name(model_preference)}
        }

    # Default: ask for clarification
    return {
        "intent": "clarification_needed",
        "question": "I'm having trouble understanding your command. Could you be more specific about which track and what parameter you want to adjust?",
        "context": {"partial_query": query},
        "meta": {"utterance": query, "fallback": True, "error": error_msg, "model_selected": get_default_model_name(model_preference)}
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
    args = parser.parse_args()

    result = interpret_daw_command(args.text, model_preference=args.model)
    print(json.dumps(result, ensure_ascii=False))
    sys.exit(0)
