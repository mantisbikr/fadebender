"""
Lightweight LLM-backed DAW command interpreter.

- Primary: Use Vertex AI via SDK when available.
- Fallback: Simple pattern-based parsing when SDK or network is unavailable.
"""
from __future__ import annotations

import json
from typing import Dict, List, Any
import os

from config.llm_config import get_llm_project_id, get_llm_api_key, get_default_model_name


def _build_daw_prompt(query: str) -> str:
    return (
        "You are an expert DAW (Digital Audio Workstation) command interpreter. "
        "Parse natural language commands into structured JSON for controlling music production software.\n\n"
        "Return strictly valid JSON with this structure:\n"
        "{\n"
        "  \"intent\": \"set_parameter\" | \"relative_change\" | \"question_response\" | \"clarification_needed\",\n"
        "  \"targets\": [{\"track\": \"Track 1\", \"plugin\": null, \"parameter\": \"volume\"}],\n"
        "  \"operation\": {\"type\": \"absolute|relative\", \"value\": 2, \"unit\": \"dB\"},\n"
        "  \"meta\": {\"utterance\": \"original command\", \"confidence\": 0.95}\n"
        "}\n\n"
        "For questions/problems, use:\n"
        "{\n"
        "  \"intent\": \"question_response\",\n"
        "  \"answer\": \"helpful response with actionable suggestions\",\n"
        "  \"suggested_intents\": [\"set track 1 volume to -12 dB\", \"increase track 2 volume by 3 dB\"],\n"
        "  \"meta\": {\"utterance\": \"original command\", \"confidence\": 0.95}\n"
        "}\n\n"
        "For unclear commands, use:\n"
        "{\n"
        "  \"intent\": \"clarification_needed\",\n"
        "  \"question\": \"What clarification is needed?\",\n"
        "  \"context\": {\"action\": \"increase\", \"parameter\": \"volume\"},\n"
        "  \"meta\": {\"utterance\": \"original command\", \"confidence\": 0.9}\n"
        "}\n\n"
        "Examples:\n"
        "- \"increase track 2 volume by 3 dB\" → set_parameter with relative change\n"
        "- \"the vocals are too soft\" → question_response with helpful suggestions and suggested_intents like [\"set track 1 volume to -6 dB\", \"increase track 1 volume by 6 dB\"]\n"
        "- \"boost vocals\" → clarification_needed asking which track\n"
        "- \"how do I make my drums punchier?\" → question_response with EQ/compression advice and suggested_intents for specific adjustments\n\n"
        "Important: For question_response, always include 2-4 specific, actionable suggested_intents that users can click to execute.\n\n"
        f"Command: {query}\n"
        "JSON:"
    )


def interpret_daw_command(query: str, model_preference: str | None = None, strict: bool | None = None) -> Dict[str, Any]:
    """Interpret user query into DAW commands using Vertex AI if available."""
    # Try Vertex AI SDK path first
    try:
        import vertexai  # type: ignore
        from vertexai.generative_models import GenerativeModel  # type: ignore
        from vertexai.language_models import TextGenerationModel  # type: ignore

        project = get_llm_project_id()
        location = os.getenv("GCP_REGION", "us-central1")
        model_name = get_default_model_name(model_preference)

        # Initialize Vertex AI (uses service account if GOOGLE_APPLICATION_CREDENTIALS is set)
        vertexai.init(project=project, location=location)

        prompt = _build_daw_prompt(query)
        response_text = None

        if model_name.startswith("gemini"):
            model = GenerativeModel(model_name)
            resp = model.generate_content(prompt, generation_config={
                "temperature": 0.1,
                "max_output_tokens": 512,
                "top_p": 0.8,
                "top_k": 20,
            })
            response_text = getattr(resp, "text", None)
        else:
            # Use legacy TextGenerationModel for non-Gemini (e.g., Model Garden)
            model = TextGenerationModel.from_pretrained(model_name)
            resp = model.predict(prompt=prompt, temperature=0.1, max_output_tokens=512, top_p=0.8, top_k=20)
            response_text = getattr(resp, "text", None)

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
    q = query.lower().strip()

    # Absolute volume set: "set track 1 volume to -6 dB"
    # Also accept variants like "set the volume of track 1 to -6db"
    try:
        import re
        abs_match = re.search(r"(?:set|make|adjust|change)\s+(?:the\s+)?(?:volume\s+of\s+)?track\s+(\d+)\s+(?:volume\s+)?(?:to|at)\s+(-?\d+(?:\.\d+)?)\s*d\s*b\b", q)
        if not abs_match:
            # Variant: "track 1 volume to -6 dB" (missing leading verb)
            abs_match = re.search(r"track\s+(\d+)\s+volume\s+(?:to|at)\s+(-?\d+(?:\.\d+)?)\s*d\s*b\b", q)
        if abs_match:
            track_num = int(abs_match.group(1))
            value = float(abs_match.group(2))
            return {
                "intent": "set_parameter",
                "targets": [{"track": f"Track {track_num}", "plugin": None, "parameter": "volume"}],
                "operation": {"type": "absolute", "value": value, "unit": "dB"},
                "meta": {"utterance": query, "fallback": True, "error": error_msg, "model_selected": get_default_model_name(model_preference)}
            }
    except Exception:
        pass

    # Basic volume commands
    if "volume" in q and any(word in q for word in ["increase", "decrease", "up", "down", "louder", "quieter"]):
        # Try to extract track number
        import re
        track_match = re.search(r"track\s+(\d+)", q)
        if track_match:
            track_num = int(track_match.group(1))
            # Determine direction and amount
            value = 3  # default 3dB
            if "decrease" in q or "down" in q or "quieter" in q:
                value = -3

            return {
                "intent": "relative_change",
                "targets": [{"track": f"Track {track_num}", "plugin": None, "parameter": "volume"}],
                "operation": {"type": "relative", "value": value, "unit": "dB"},
                "meta": {"utterance": query, "fallback": True, "error": error_msg, "model_selected": get_default_model_name(model_preference)}
            }

    # Questions about problems
    if any(phrase in q for phrase in ["too soft", "too quiet", "can't hear", "how to", "what does"]):
        return {
            "intent": "question_response",
            "answer": "I'm having trouble connecting to the AI service. For audio issues, try: 1) Check track levels, 2) Adjust mixer settings, 3) Verify routing. Please try your command again.",
            "suggested_intents": ["set track 1 volume to -6 dB", "increase track 1 volume by 6 dB", "set track 2 volume to -12 dB"],
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
