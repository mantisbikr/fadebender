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
        "You are an expert DAW (Digital Audio Workstation) command interpreter for Ableton Live. "
        "Parse natural language commands into structured JSON for controlling tracks, returns, master, devices, and effects.\n\n"
        "Return strictly valid JSON with this structure:\n"
        "{\n"
        "  \"intent\": \"set_parameter\" | \"relative_change\" | \"question_response\" | \"clarification_needed\",\n"
        "  \"targets\": [{\"track\": \"Track 1\", \"plugin\": null, \"parameter\": \"volume\"}],\n"
        "  \"operation\": {\"type\": \"absolute|relative\", \"value\": 2, \"unit\": \"dB\"},\n"
        "  \"meta\": {\"utterance\": \"original command\", \"confidence\": 0.95}\n"
        "}\n\n"
        "For questions/help, use:\n"
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
        "SUPPORTED COMMANDS:\n\n"
        "## Track Controls (use \"Track N\" format):\n"
        "- Volume: \"set track 1 volume to -6 dB\", \"increase track 2 volume by 3 dB\"\n"
        "- Pan: \"pan track 2 50% left\", \"pan track 1 25% right\", \"center track 3\"\n"
        "- Mute: \"mute track 1\", \"unmute track 2\"\n"
        "- Solo: \"solo track 1\", \"unsolo track 2\"\n"
        "- Sends: \"set track 1 send A to -12 dB\", \"set track 2 send B to -6 dB\" (use letter A, B, C, etc.)\n\n"
        "## Return Track Controls (use \"Return A/B/C\" format with letters):\n"
        "- Volume: \"set return A volume to -3 dB\", \"increase return B volume by 2 dB\"\n"
        "- Pan: \"pan return A 30% left\"\n"
        "- Mute: \"mute return B\", \"unmute return A\"\n"
        "- Solo: \"solo return A\"\n"
        "- Sends: \"set return A send B to -10 dB\"\n\n"
        "## Master Track Controls:\n"
        "- Volume: \"set master volume to -3 dB\", \"increase master volume by 1 dB\"\n"
        "- Pan: \"pan master 10% right\"\n\n"
        "## Device Parameters (plugin is device name, parameter is knob/control):\n"
        "- \"set return A reverb decay to 2 seconds\" → {\"track\": \"Return A\", \"plugin\": \"reverb\", \"parameter\": \"decay\"}\n"
        "- \"set track 1 compressor threshold to -12 dB\" → {\"track\": \"Track 1\", \"plugin\": \"compressor\", \"parameter\": \"threshold\"}\n"
        "- \"increase return B delay time by 50 ms\" → relative change for delay device\n"
        "- \"set return A reverb predelay to 20 ms\", \"set track 2 eq gain to 3 dB\"\n\n"
        "## Help/Questions:\n"
        "- \"how do I control sends?\" → question_response with explanation and examples\n"
        "- \"what does reverb decay do?\" → question_response explaining the parameter\n"
        "- \"the vocals are too soft\" → question_response with suggested_intents for volume adjustments\n\n"
        "IMPORTANT RULES:\n"
        "1. Return tracks ALWAYS use letters: \"Return A\", \"Return B\", \"Return C\" (never \"Return 1\")\n"
        "2. Sends ALWAYS use letters: \"send A\", \"send B\" (never \"send 1\")\n"
        "3. Regular tracks use numbers: \"Track 1\", \"Track 2\"\n"
        "4. For device parameters, set \"plugin\" to the device name (reverb, compressor, eq, delay, etc.)\n"
        "5. Solo/mute/unmute/unsolo are set_parameter commands with value 1 (on) or 0 (off)\n"
        "6. Pan values: -50 to +50 (negative = left, positive = right, 0 = center)\n"
        "7. For question_response, ALWAYS include 2-4 specific suggested_intents\n"
        "8. Only use clarification_needed when the command is truly ambiguous (e.g., \"boost vocals\" without specifying track)\n\n"
        "EXAMPLES:\n"
        "- \"solo track 1\" → {\"intent\": \"set_parameter\", \"targets\": [{\"track\": \"Track 1\", \"plugin\": null, \"parameter\": \"solo\"}], \"operation\": {\"type\": \"absolute\", \"value\": 1, \"unit\": null}}\n"
        "- \"mute track 2\" → {\"intent\": \"set_parameter\", \"targets\": [{\"track\": \"Track 2\", \"plugin\": null, \"parameter\": \"mute\"}], \"operation\": {\"type\": \"absolute\", \"value\": 1, \"unit\": null}}\n"
        "- \"set return A volume to -3 dB\" → {\"intent\": \"set_parameter\", \"targets\": [{\"track\": \"Return A\", \"plugin\": null, \"parameter\": \"volume\"}], \"operation\": {\"type\": \"absolute\", \"value\": -3, \"unit\": \"dB\"}}\n"
        "- \"set track 1 send A to -12 dB\" → {\"intent\": \"set_parameter\", \"targets\": [{\"track\": \"Track 1\", \"plugin\": null, \"parameter\": \"send A\"}], \"operation\": {\"type\": \"absolute\", \"value\": -12, \"unit\": \"dB\"}}\n"
        "- \"set return A reverb decay to 2 seconds\" → {\"intent\": \"set_parameter\", \"targets\": [{\"track\": \"Return A\", \"plugin\": \"reverb\", \"parameter\": \"decay\"}], \"operation\": {\"type\": \"absolute\", \"value\": 2, \"unit\": \"seconds\"}}\n"
        "- \"how do I control sends?\" → {\"intent\": \"question_response\", \"answer\": \"You can control sends by specifying the track and send letter...\", \"suggested_intents\": [\"set track 1 send A to -12 dB\", \"increase track 2 send B by 3 dB\"]}\n"
        "- \"boost vocals\" → {\"intent\": \"clarification_needed\", \"question\": \"Which track contains the vocals?\", \"context\": {\"action\": \"increase\", \"parameter\": \"volume\"}}\n\n"
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
    # Light typo corrections to improve robustness when LLM is unavailable
    typo_map = {
        'retrun': 'return', 'retun': 'return',
        'revreb': 'reverb', 'reverbb': 'reverb', 'revebr': 'reverb', 'reverv': 'reverb',
        'strereo': 'stereo', 'streo': 'stereo', 'stere': 'stereo',
    }
    for k, v in typo_map.items():
        q = __import__('re').sub(rf"\b{k}\b", v, q)

    # Absolute volume set: "set track 1 volume to -6 dB" (unit optional: dB, %, or normalized)
    # Also accept variants like "set the volume of track 1 to -6db", or without unit: "set track 1 volume to 0.5"
    try:
        import re
        # Generalized pattern with optional unit (db|%); if absent, leave unit None (treated as normalized)
        abs_match = re.search(r"(?:set|make|adjust|change)\s+(?:the\s+)?(?:volume\s+of\s+)?track\s+(\d+)\s+(?:volume\s+)?(?:to|at)\s+(-?\d+(?:\.\d+)?)(?:\s*(db|dB|%|percent))?\b", q)
        if not abs_match:
            # Variant: "track 1 volume to -6 dB" (missing leading verb)
            abs_match = re.search(r"track\s+(\d+)\s+volume\s+(?:to|at)\s+(-?\d+(?:\.\d+)?)(?:\s*(db|dB|%|percent))?\b", q)
        if abs_match:
            track_num = int(abs_match.group(1))
            value = float(abs_match.group(2))
            unit = abs_match.group(3)
            unit_out = None
            if unit:
                unit_l = unit.lower()
                if unit_l in ("db",):
                    unit_out = "dB"
                elif unit_l in ("%", "percent"):
                    unit_out = "%"
            return {
                "intent": "set_parameter",
                "targets": [{"track": f"Track {track_num}", "plugin": None, "parameter": "volume"}],
                "operation": {"type": "absolute", "value": value, "unit": unit_out},
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

    # Pan absolute using Live-style input like '25L' or '25R'
    try:
        import re
        m = re.search(r"\b(\d{1,2}|50)\s*([lr])\b", q)
        if m:
            amt = int(m.group(1))
            side = m.group(2)
            # map 25L => -25, 25R => +25
            pan_val = -amt if side == 'l' else amt
            trk = re.search(r"track\s+(\d+)", q)
            track_num = int(trk.group(1)) if trk else 1
            return {
                "intent": "set_parameter",
                "targets": [{"track": f"Track {track_num}", "plugin": None, "parameter": "pan"}],
                "operation": {"type": "absolute", "value": pan_val, "unit": "%"},
                "meta": {"utterance": query, "fallback": True, "error": error_msg, "model_selected": get_default_model_name(model_preference)}
            }
    except Exception:
        pass

    # Return device parameter by name (common ones): e.g., "set return A reverb stereo image to 50 [degrees|%]"
    try:
        import re
        m = re.search(r"\bset\s+return\s+([a-d])\b.*?(stereo\s+image|decay|predelay|dry\s*/\s*wet|dry\s*wet|dry|wet)\s+(?:to|at)\s+(-?\d+(?:\.\d+)?)(?:\s*(db|dB|%|percent|ms|millisecond|milliseconds|s|sec|second|seconds|hz|khz|degree|degrees|deg|°))?\b", q)
        if m:
            return_ref = m.group(1).upper()
            pname = m.group(2)
            value = float(m.group(3))
            unit_raw = m.group(4)
            # Normalize param name
            pname_norm_map = {
                'stereo image': 'Stereo Image',
                'decay': 'Decay',
                'predelay': 'Predelay',
                'dry / wet': 'Dry/Wet',
                'dry wet': 'Dry/Wet',
                'dry': 'Dry/Wet',
                'wet': 'Dry/Wet',
            }
            pn = ' '.join(pname.split()).lower()
            pn = pn.replace('dry / wet', 'dry / wet').replace('dry wet', 'dry / wet')
            param_ref = pname_norm_map.get(pn, pname.title())
            # Normalize unit
            unit_out = None
            if unit_raw:
                u = unit_raw.lower()
                if u in ('db',): unit_out = 'dB'
                elif u in ('%','percent'): unit_out = '%'
                elif u in ('ms', 'millisecond', 'milliseconds'): unit_out = 'ms'
                elif u in ('s','sec','second','seconds'): unit_out = 's'
                elif u in ('hz',): unit_out = 'hz'
                elif u in ('khz',): unit_out = 'khz'
                elif u in ('degree','degrees','deg','°'): unit_out = 'degrees'
            return {
                'intent': 'set_parameter',
                'targets': [{ 'track': f'Return {return_ref}', 'plugin': 'reverb', 'parameter': param_ref }],
                'operation': { 'type': 'absolute', 'value': value, 'unit': unit_out },
                'meta': { 'utterance': query, 'fallback': True, 'error': error_msg, 'model_selected': get_default_model_name(model_preference) }
            }
    except Exception:
        pass

    # Solo/Mute toggles
    try:
        import re
        m = re.search(r"\b(solo|unsolo|mute|unmute)\s+track\s+(\d+)\b", q)
        if m:
            action = m.group(1).lower()
            track_num = int(m.group(2))
            param = 'solo' if 'solo' in action else 'mute'
            value = 0.0 if action in ('unsolo', 'unmute') else 1.0
            return {
                "intent": "set_parameter",
                "targets": [{"track": f"Track {track_num}", "plugin": None, "parameter": param}],
                "operation": {"type": "absolute", "value": value, "unit": None},
                "meta": {"utterance": query, "fallback": True, "error": error_msg, "model_selected": get_default_model_name(model_preference)}
            }
    except Exception:
        pass

    # Sends control (track): set track N send A to X [dB|%]
    try:
        import re
        m = re.search(r"\bset\s+track\s+(\d+)\s+(?:send\s+)?([a-d])\b.*?\bto\s+(-?\d+(?:\.\d+)?)(?:\s*(db|dB|%|percent))?\b", q)
        if m:
            track_num = int(m.group(1))
            send_ref = m.group(2).upper()
            value = float(m.group(3))
            unit = m.group(4)
            unit_out = None
            if unit:
                unit_l = unit.lower()
                if unit_l in ("db",): unit_out = "dB"
                elif unit_l in ("%", "percent"): unit_out = "%"
            return {
                "intent": "set_parameter",
                "targets": [{"track": f"Track {track_num}", "plugin": None, "parameter": f"send {send_ref}"}],
                "operation": {"type": "absolute", "value": value, "unit": unit_out},
                "meta": {"utterance": query, "fallback": True, "error": error_msg, "model_selected": get_default_model_name(model_preference)}
            }
    except Exception:
        pass

    # Sends control (return): set return A send B to X [dB|%]
    try:
        import re
        m = re.search(r"\bset\s+return\s+([a-d])\s+(?:send\s+)?([a-d])\b.*?\bto\s+(-?\d+(?:\.\d+)?)(?:\s*(db|dB|%|percent))?\b", q)
        if m:
            return_ref = m.group(1).upper()
            send_ref = m.group(2).upper()
            value = float(m.group(3))
            unit = m.group(4)
            unit_out = None
            if unit:
                unit_l = unit.lower()
                if unit_l in ("db",): unit_out = "dB"
                elif unit_l in ("%", "percent"): unit_out = "%"
            return {
                "intent": "set_parameter",
                "targets": [{"track": f"Return {return_ref}", "plugin": None, "parameter": f"send {send_ref}"}],
                "operation": {"type": "absolute", "value": value, "unit": unit_out},
                "meta": {"utterance": query, "fallback": True, "error": error_msg, "model_selected": get_default_model_name(model_preference)}
            }
    except Exception:
        pass

    # Return volume absolute: set return A volume to -3 dB
    try:
        import re
        m = re.search(r"\bset\s+return\s+([a-d])\s+volume\s+(?:to|at)\s+(-?\d+(?:\.\d+)?)(?:\s*(db|dB|%|percent))?\b", q)
        if m:
            return_ref = m.group(1).upper()
            value = float(m.group(2))
            unit = m.group(3)
            unit_out = None
            if unit:
                unit_l = unit.lower()
                if unit_l in ("db",): unit_out = "dB"
                elif unit_l in ("%", "percent"): unit_out = "%"
            return {
                "intent": "set_parameter",
                "targets": [{"track": f"Return {return_ref}", "plugin": None, "parameter": "volume"}],
                "operation": {"type": "absolute", "value": value, "unit": unit_out},
                "meta": {"utterance": query, "fallback": True, "error": error_msg, "model_selected": get_default_model_name(model_preference)}
            }
    except Exception:
        pass

    # Generic return device parameter with unit: set return A reverb <param> to <val> [unit]
    try:
        import re
        m = re.search(r"\bset\s+return\s+([a-d])\s+(?:reverb\s+)?(.+?)\s+(?:to|at)\s+(-?\d+(?:\.\d+)?)(?:\s*(db|dB|%|percent|ms|millisecond|milliseconds|s|sec|second|seconds|hz|khz|degree|degrees|deg|°))?\b", q)
        if m:
            return_ref = m.group(1).upper()
            pname = m.group(2).strip()
            value = float(m.group(3))
            unit_raw = m.group(4)
            unit_out = None
            if unit_raw:
                u = unit_raw.lower()
                if u in ('db',): unit_out = 'dB'
                elif u in ('%','percent'): unit_out = '%'
                elif u in ('ms','millisecond','milliseconds'): unit_out = 'ms'
                elif u in ('s','sec','second','seconds'): unit_out = 's'
                elif u in ('hz',): unit_out = 'hz'
                elif u in ('khz',): unit_out = 'khz'
                elif u in ('degree','degrees','deg','°'): unit_out = 'degrees'
            # Use device_index=0 and plugin hint 'reverb' to help mapping, but execution will use param_ref
            return {
                'intent': 'set_parameter',
                'targets': [{ 'track': f'Return {return_ref}', 'plugin': 'reverb', 'parameter': pname }],
                'operation': { 'type': 'absolute', 'value': value, 'unit': unit_out },
                'meta': { 'utterance': query, 'fallback': True, 'error': error_msg, 'model_selected': get_default_model_name(model_preference) }
            }
    except Exception:
        pass

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
