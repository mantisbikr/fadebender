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


def _extract_llm_hints(query: str) -> Dict[str, Any]:
    """Extract lightweight hints from the user utterance to guide the LLM.

    Returns a dict that may include:
      - track_hint: "Return A" | "Track N" | "Master"
      - device_name_hint: device name (known generic or arbitrary name before param keywords)
      - device_ordinal_hint: 1-based ordinal (from "reverb 2" or "device 2" or word ordinals)
    """
    import re
    h: Dict[str, Any] = {}
    q = query or ""
    ql = q.lower()

    # Track/Return/Master
    m_ret = re.search(r"\breturn\s+([a-d])\b", ql)
    if m_ret:
        h["track_hint"] = f"Return {m_ret.group(1).upper()}"
    else:
        m_trk = re.search(r"\btrack\s+(\d+)\b", ql)
        if m_trk:
            h["track_hint"] = f"Track {int(m_trk.group(1))}"
        elif re.search(r"\bmaster\b", ql):
            h["track_hint"] = "Master"

    # Known generic device names
    generic = ["align delay", "reverb", "delay", "compressor", "eq", "equalizer"]
    found = None
    for name in generic:
        pat = name.replace(" ", r"\s+")
        if re.search(rf"\b{pat}\b", ql):
            found = name
            break
    if found:
        if found == "equalizer":
            found = "eq"
        h["device_name_hint"] = found

    # Arbitrary device names before known param keywords (e.g., "4th bandpass" before "mode")
    if "device_name_hint" not in h:
        m_arbitrary = re.search(r"\breturn\s+[a-d]\b\s+(?:the\s+)?(.+?)\s+(mode|quality|type|algorithm|alg|distunit|units?)\b", ql)
        if m_arbitrary:
            dn = m_arbitrary.group(1).strip()
            if dn:
                h["device_name_hint"] = dn

    # Ordinals (numeric and word)
    ord_map = {"first":1,"second":2,"third":3,"fourth":4,"fifth":5,"sixth":6,"seventh":7,"eighth":8,"ninth":9,"tenth":10}
    ord_val = None
    # Generic: device N
    m_devn = re.search(r"\bdevice\s+(\d+)\b", ql)
    if m_devn:
        ord_val = int(m_devn.group(1))
    # Named: <device> N
    if ord_val is None and ("device_name_hint" in h):
        pat = str(h["device_name_hint"]).replace(" ", r"\s+")
        m_named = re.search(rf"\b{pat}\s+(\d+)\b", ql)
        if m_named:
            ord_val = int(m_named.group(1))
    # Word ordinals
    if ord_val is None:
        m_word = re.search(r"\b(first|second|third|fourth|fifth|sixth|seventh|eighth|ninth|tenth)\s+(?:device|" + (str(h.get("device_name_hint",""))).replace(" ", r"\s+") + r")\b", ql)
        if m_word:
            ord_val = ord_map.get(m_word.group(1).lower())
    if isinstance(ord_val, int) and ord_val > 0:
        h["device_ordinal_hint"] = ord_val

    return h


def _build_daw_prompt(query: str, mixer_params: List[str] | None = None, known_devices: List[Dict[str, str]] | None = None) -> str:
    # Inject lightweight HINTS to help the LLM include device ordinals and track scope
    def _hints_text(q: str) -> str:
        try:
            hints = _extract_llm_hints(q)
        except Exception:
            hints = {}
        if not hints:
            return ""
        try:
            hjson = json.dumps(hints, ensure_ascii=False)
        except Exception:
            hjson = "{}"
        # Nudge model to honor hints explicitly
        return (
            "HINTS (use to disambiguate — include in output if consistent):\n"
            + hjson + "\n"
            + "- If device_name_hint is present, use it as the plugin name EXACTLY as provided (e.g., '4th bandpass' is a device name, not an ordinal).\n"
            + "- If device_ordinal_hint is present, set targets[0].device_ordinal to that number.\n"
            + "- If track_hint is present, align targets[0].track with it.\n\n"
        )

    # Build mixer params context if available
    mixer_context = ""
    if mixer_params:
        mixer_context = (
            "KNOWN MIXER PARAMETERS (from DAW):\n"
            f"{', '.join(mixer_params)}\n\n"
            "**CRITICAL RULE**: If the user mentions a parameter from this list AND does NOT mention a device/plugin name, "
            "it is a MIXER operation (set plugin=null). Device operations ALWAYS have an explicit device name.\n\n"
        )

    # Build known devices context if available
    device_context = ""
    if known_devices:
        # Group by type for better readability
        by_type: Dict[str, List[str]] = {}
        for d in known_devices:
            dtype = d.get("type", "unknown")
            name = d.get("name", "")
            if name:
                by_type.setdefault(dtype, []).append(name)

        device_lines = []
        for dtype in sorted(by_type.keys()):
            names = ", ".join(sorted(set(by_type[dtype]))[:10])  # Limit to 10 per type to save tokens
            device_lines.append(f"  {dtype}: {names}")

        device_context = (
            "KNOWN DEVICES (from session presets):\n"
            + "\n".join(device_lines) + "\n\n"
            + "**IMPORTANT**: These device names are ONLY for typo correction when the user EXPLICITLY mentions a device/plugin. "
            + "DO NOT infer device operations from parameter names alone. "
            + "For example: 'screamr gain' → 'Screamer' (user mentioned device), but 'set track 1 volume' → NO device (pure mixer op).\n\n"
        )

    return (
        f"{_hints_text(query)}"
        f"{device_context}"
        f"{mixer_context}"
        "You are an expert audio engineer and Ableton Live power user. Your job is to interpret natural language "
        "commands for controlling a DAW session - tracks, returns (send effects), master channel, and audio devices/plugins.\n\n"
        "**CONTEXT: You understand audio engineering terminology**\n"
        "- Mixer controls: volume (gain/level/loudness), pan (balance/stereo position), mute, solo, sends (aux sends)\n"
        "- Effect parameters: decay (reverb tail), feedback (delay repeats), threshold (compressor), attack/release, "
        "dry/wet (effect mix), cutoff (filter frequency), resonance (filter Q), predelay (early reflections)\n"
        "- Common typos and abbreviations: vol→volume, fbk→feedback, res→resonance, lo cut→low cut, "
        "tack→track, retun→return, vilme→volume, etc.\n"
        "- Units: dB (decibels), ms (milliseconds), s (seconds), Hz/kHz (frequency), % (percentage)\n\n"
        "**CRITICAL: Be forgiving with typos, abbreviations, and variations.** Audio engineers type fast and use "
        "shorthand. Interpret intent from context. If \"vilme\" appears with a track number and dB value, it's clearly \"volume\".\n\n"
        "Parse commands into structured JSON for controlling tracks, returns, master, devices, and effects.\n\n"
        "Return strictly valid JSON with this structure (fields are required unless marked optional):\n"
        "{\n"
        "  \"intent\": \"set_parameter\" | \"relative_change\" | \"question_response\" | \"clarification_needed\",\n"
        "  \"targets\": [{\n"
        "      \"track\": \"Track 1|Return A|Master\",\n"
        "      \"plugin\": \"reverb|compressor|delay|eq|align delay\" | null,\n"
        "      \"parameter\": \"decay|predelay|volume|pan|send A|mode|quality|...\",\n"
        "      \"device_ordinal\": 2  /* optional: when user says 'reverb 2' or 'device 2' */\n"
        "  }],\n"
        "  \"operation\": {\"type\": \"absolute|relative\", \"value\": 2, \"unit\": \"dB|ms|s|Hz|kHz|%|display|null\"},\n"
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
        "- Always set \"plugin\" to device name (e.g., reverb, delay, eq, compressor, align delay).\n"
        "- If user says an ordinal (e.g., 'reverb 2' or 'device 2'), include \"device_ordinal\" with that 1-based number.\n"
        "- For label selections (e.g., Mode 'Distance', Quality 'High', On/Off), set operation.value to that string and unit='display'.\n"
        "- \"set return A reverb decay to 2 seconds\" → {\"track\": \"Return A\", \"plugin\": \"reverb\", \"parameter\": \"decay\"}\n"
        "- \"set track 1 compressor threshold to -12 dB\" → {\"track\": \"Track 1\", \"plugin\": \"compressor\", \"parameter\": \"threshold\"}\n"
        "- \"increase return B delay time by 50 ms\" → relative change for delay device\n"
        "- \"set return A reverb predelay to 20 ms\", \"set track 2 eq gain to 3 dB\"\n"
        "- \"set Return B reverb 2 decay to 2 s\" → include \"device_ordinal\": 2 in the target.\n"
        "- \"set Return B device 2 decay to 2 s\" → include \"device_ordinal\": 2 (plugin may be omitted).\n"
        "- \"set Return B Align Delay Mode to Distance\" → operation.value=\"Distance\", unit=\"display\".\n\n"
        "## Help/Questions:\n"
        "- \"how do I control sends?\" → question_response with explanation and examples\n"
        "- \"what does reverb decay do?\" → question_response explaining the parameter\n"
        "- \"the vocals are too soft\" → question_response with suggested_intents for volume adjustments\n\n"
        "IMPORTANT RULES:\n\n"
        "**Track Naming:**\n"
        "1. Return tracks ALWAYS use letters: \"Return A\", \"Return B\", \"Return C\" (never \"Return 1\")\n"
        "2. Sends ALWAYS use letters: \"send A\", \"send B\" (never \"send 1\")\n"
        "3. Regular tracks use numbers: \"Track 1\", \"Track 2\"\n\n"
        "**Mixer vs Device Operations (CRITICAL):**\n"
        "4. **MIXER operations** (plugin=null): volume, pan, mute, solo, send - when NO device name mentioned\n"
        "   - \"set track 1 volume to -6\" → plugin=null, parameter=\"volume\" (MIXER)\n"
        "   - \"set tack 1 vilme to -20\" → plugin=null, parameter=\"volume\" (MIXER with typos)\n"
        "   - \"pan return A 10% left\" → plugin=null, parameter=\"pan\" (MIXER)\n"
        "5. **DEVICE operations** (plugin=device name): ALL other parameters when device name IS mentioned\n"
        "   - \"set return A reverb decay to 2s\" → plugin=\"reverb\", parameter=\"decay\" (DEVICE)\n"
        "   - \"set track 2 compressor threshold to -12\" → plugin=\"compressor\", parameter=\"threshold\" (DEVICE)\n\n"
        "**Parameter Handling:**\n"
        "6. Solo/mute/unmute/unsolo: set_parameter with value 1 (on) or 0 (off)\n"
        "7. Pan values: -50 to +50 (negative=left, positive=right, 0=center)\n"
        "8. Label selections (Mode, Quality, Type, On/Off): set operation.value to label string, unit='display'\n"
        "9. Be forgiving with units: \"s\"/\"sec\"/\"seconds\", \"ms\"/\"milliseconds\", \"dB\"/\"db\"/\"decibels\" are all valid\n\n"
        "**Device Ordinals:**\n"
        "10. Device names before params are literal: \"4th bandpass mode\" → plugin='4th bandpass' (NOT ordinal=4)\n"
        "11. Only set device_ordinal when ordinal FOLLOWS name: \"reverb 2 decay\" → plugin=\"reverb\", device_ordinal=2\n\n"
        "**Response Quality:**\n"
        "12. For question_response, ALWAYS include 2-4 specific suggested_intents\n"
        "13. Only use clarification_needed when truly ambiguous (e.g., \"boost vocals\" without specifying track)\n"
        "14. Interpret typos intelligently - context matters more than exact spelling\n\n"
        "**🚨 CRITICAL: NEVER use known devices for mixer parameters! 🚨**\n"
        "If the command mentions ONLY track/return + parameter (volume/pan/mute/send), set plugin=null.\n"
        "Device names from known devices list are ONLY for when user EXPLICITLY says the device name.\n"
        "Examples of MIXER ops (plugin=null): 'set track 1 volume', 'pan return A', 'mute track 2'\n"
        "Examples of DEVICE ops (plugin=name): 'set return A reverb decay', 'set track 2 compressor threshold'\n\n"
        "EXAMPLES (including typos/variations):\n\n"
        "**Mixer Operations (no device name):**\n"
        "- \"solo track 1\" → {\"intent\": \"set_parameter\", \"targets\": [{\"track\": \"Track 1\", \"plugin\": null, \"parameter\": \"solo\"}], \"operation\": {\"type\": \"absolute\", \"value\": 1, \"unit\": null}}\n"
        "- \"mute track 2\" → {\"intent\": \"set_parameter\", \"targets\": [{\"track\": \"Track 2\", \"plugin\": null, \"parameter\": \"mute\"}], \"operation\": {\"type\": \"absolute\", \"value\": 1, \"unit\": null}}\n"
        "- \"set return A volume to -3 dB\" → {\"intent\": \"set_parameter\", \"targets\": [{\"track\": \"Return A\", \"plugin\": null, \"parameter\": \"volume\"}], \"operation\": {\"type\": \"absolute\", \"value\": -3, \"unit\": \"dB\"}}\n"
        "- \"set tack 1 vilme to -20\" → {\"intent\": \"set_parameter\", \"targets\": [{\"track\": \"Track 1\", \"plugin\": null, \"parameter\": \"volume\"}], \"operation\": {\"type\": \"absolute\", \"value\": -20, \"unit\": null}} (TYPOS CORRECTED)\n"
        "- \"set track 1 send A to -12 dB\" → {\"intent\": \"set_parameter\", \"targets\": [{\"track\": \"Track 1\", \"plugin\": null, \"parameter\": \"send A\"}], \"operation\": {\"type\": \"absolute\", \"value\": -12, \"unit\": \"dB\"}}\n"
        "- \"pan retun b 25% left\" → {\"intent\": \"set_parameter\", \"targets\": [{\"track\": \"Return B\", \"plugin\": null, \"parameter\": \"pan\"}], \"operation\": {\"type\": \"absolute\", \"value\": -25, \"unit\": null}} (TYPO: retun→return)\n\n"
        "**Device Operations (device name present):**\n"
        "- \"set return A reverb decay to 2 seconds\" → {\"intent\": \"set_parameter\", \"targets\": [{\"track\": \"Return A\", \"plugin\": \"reverb\", \"parameter\": \"decay\"}], \"operation\": {\"type\": \"absolute\", \"value\": 2, \"unit\": \"seconds\"}}\n"
        "- \"set return B reverb 2 decay to 2 s\" → {\"intent\": \"set_parameter\", \"targets\": [{\"track\": \"Return B\", \"plugin\": \"reverb\", \"parameter\": \"decay\", \"device_ordinal\": 2}], \"operation\": {\"type\": \"absolute\", \"value\": 2, \"unit\": \"s\"}}\n"
        "- \"set return A revreb feedbak to 40%\" → {\"intent\": \"set_parameter\", \"targets\": [{\"track\": \"Return A\", \"plugin\": \"reverb\", \"parameter\": \"feedback\"}], \"operation\": {\"type\": \"absolute\", \"value\": 40, \"unit\": \"%\"}} (TYPOS: revreb→reverb, feedbak→feedback)\n"
        "- \"set return B align delay mode to distance\" → {\"intent\": \"set_parameter\", \"targets\": [{\"track\": \"Return B\", \"plugin\": \"align delay\", \"parameter\": \"mode\"}], \"operation\": {\"type\": \"absolute\", \"value\": \"distance\", \"unit\": \"display\"}}\n"
        "- \"set return A 4th bandpass mode to fade\" → {\"intent\": \"set_parameter\", \"targets\": [{\"track\": \"Return A\", \"plugin\": \"4th bandpass\", \"parameter\": \"mode\"}], \"operation\": {\"type\": \"absolute\", \"value\": \"fade\", \"unit\": \"display\"}}\n"
        "- \"set track 2 comprssor threshhold to -12 db\" → {\"intent\": \"set_parameter\", \"targets\": [{\"track\": \"Track 2\", \"plugin\": \"compressor\", \"parameter\": \"threshold\"}], \"operation\": {\"type\": \"absolute\", \"value\": -12, \"unit\": \"dB\"}} (TYPOS: comprssor→compressor, threshhold→threshold, db→dB)\n\n"
        "- \"how do I control sends?\" → {\"intent\": \"question_response\", \"answer\": \"You can control sends by specifying the track and send letter...\", \"suggested_intents\": [\"set track 1 send A to -12 dB\", \"increase track 2 send B by 3 dB\"]}\n"
        "- \"boost vocals\" → {\"intent\": \"clarification_needed\", \"question\": \"Which track contains the vocals?\", \"context\": {\"action\": \"increase\", \"parameter\": \"volume\"}}\n\n"
        f"Command: {query}\n"
        "JSON:"
    )


def _fetch_session_devices() -> List[Dict[str, str]] | None:
    """Fetch all devices from current Live session snapshot."""
    try:
        import requests
        resp = requests.get("http://127.0.0.1:8722/snapshot", timeout=2.0)
        if not resp.ok:
            return None

        snapshot = resp.json()
        if not snapshot or not snapshot.get("ok"):
            return None

        devices = []
        seen = set()

        # Extract from data.devices structure (more detailed)
        data = snapshot.get("data", {})
        device_data = data.get("devices", {})

        # Process track devices
        for track_idx, track_info in device_data.get("tracks", {}).items():
            for dev in track_info.get("devices", []):
                name = dev.get("name", "").strip()
                if name and name not in seen:
                    devices.append({"name": name, "type": "unknown"})
                    seen.add(name)

        # Process return devices
        for return_idx, return_info in device_data.get("returns", {}).items():
            for dev in return_info.get("devices", []):
                name = dev.get("name", "").strip()
                if name and name not in seen:
                    devices.append({"name": name, "type": "unknown"})
                    seen.add(name)

        return devices if devices else None
    except Exception:
        return None


def interpret_daw_command(query: str, model_preference: str | None = None, strict: bool | None = None) -> Dict[str, Any]:
    """Interpret user query into DAW commands using Vertex AI if available."""
    mixer_params = None
    known_devices = None

    # PRIORITY 1: Fetch devices from current Live session (most accurate)
    try:
        known_devices = _fetch_session_devices()
    except Exception:
        pass

    # PRIORITY 2: Fall back to Firestore presets only if session fetch failed
    if not known_devices:
        try:
            import sys
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'server'))
            from services.mapping_store import MappingStore
            store = MappingStore()

            presets = store.list_presets()
            if presets:
                known_devices = []
                seen = set()
                for p in presets:
                    name = p.get("device_name") or p.get("name")
                    dtype = p.get("device_type") or "unknown"
                    if name and name not in seen:
                        known_devices.append({"name": name, "type": dtype})
                        seen.add(name)
        except Exception:
            pass

    # Fetch mixer params from Firestore
    try:
        import sys
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'server'))
        from services.mapping_store import MappingStore
        store = MappingStore()
        mixer_params = store.get_mixer_param_names()
    except Exception:
        pass

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

        prompt = _build_daw_prompt(query, mixer_params, known_devices)

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
    q = query.lower().strip()
    # Ordinal word mapping for device selection (first..tenth)
    ordinal_words = {
        'first': '1', 'second': '2', 'third': '3', 'fourth': '4', 'fifth': '5',
        'sixth': '6', 'seventh': '7', 'eighth': '8', 'ninth': '9', 'tenth': '10'
    }
    for w, d in ordinal_words.items():
        q = __import__('re').sub(rf"\b{w}\b", d, q)
    # Light typo corrections to improve robustness when LLM is unavailable
    # Config-driven typo corrections (falls back to defaults if config unavailable)
    try:
        from server.config.app_config import get_typo_corrections  # type: ignore
        typo_map = get_typo_corrections() or {}
    except Exception:
        typo_map = {
            'retrun': 'return', 'retun': 'return',
            'revreb': 'reverb', 'reverbb': 'reverb', 'revebr': 'reverb', 'reverv': 'reverb',
            'strereo': 'stereo', 'streo': 'stereo', 'stere': 'stereo',
            'tack': 'track', 'trck': 'track', 'trac': 'track',
            'sennd': 'send', 'snd': 'send',
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

    # Track device parameter with unit, allowing device capture and optional ordinal
    try:
        import re
        dev_pat = r"reverb|align\s+delay|delay|compressor|eq|equalizer"
        units_pat = r"db|dB|%|percent|ms|millisecond|milliseconds|s|sec|second|seconds|hz|khz|degree|degrees|deg|°"
        m = re.search(rf"\bset\s+track\s+(\d+)\s+(?:(?:the\s+)?({dev_pat})(?:\s+(\d+))?\s+)?(?!device\s+\d+\b)(.+?)\s+(?:to|at)\s+(-?\d+(?:\.\d+)?)(?:\s*({units_pat}))?\b", q)
        if m:
            track_num = int(m.group(1))
            device_raw = m.group(2) or ''
            device_ord = m.group(3)
            pname = m.group(4).strip()
            value = float(m.group(5))
            unit_raw = m.group(6)
            dev_norm = None
            if device_raw:
                dr = device_raw.lower().strip()
                if dr in ("eq", "equalizer"): dev_norm = "eq"
                elif dr == "compressor": dev_norm = "compressor"
                elif dr == "delay": dev_norm = "delay"
                elif dr.replace(" ", "") == "aligndelay": dev_norm = "align delay"
                else: dev_norm = dr
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
            out = {
                'intent': 'set_parameter',
                'targets': [{ 'track': f'Track {track_num}', 'plugin': (dev_norm or 'reverb'), 'parameter': pname }],
                'operation': { 'type': 'absolute', 'value': value, 'unit': unit_out },
                'meta': { 'utterance': query, 'fallback': True, 'error': error_msg, 'model_selected': get_default_model_name(model_preference) }
            }
            if device_ord:
                try:
                    out['targets'][0]['device_ordinal'] = int(device_ord)
                except Exception:
                    pass
            return out
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

    # Return device parameter: capture device name and optional ordinal (reverb 2|align delay 2|...)
    try:
        import re
        dev_pat = r"reverb|align\s+delay|delay|compressor|eq|equalizer"
        units_pat = r"db|dB|%|percent|ms|millisecond|milliseconds|s|sec|second|seconds|hz|khz|degree|degrees|deg|°"
        m = re.search(rf"\bset\s+return\s+([a-d])\s+(?:(?:the\s+)?({dev_pat})(?:\s+(\d+))?\s+)?(?!device\s+\d+\b)(.+?)\s+(?:to|at)\s+(-?\d+(?:\.\d+)?)(?:\s*({units_pat}))?\b", q)
        if m:
            return_ref = m.group(1).upper()
            device_raw = m.group(2) or ''
            device_ord = m.group(3)
            pname = m.group(4).strip()
            value = float(m.group(5))
            unit_raw = m.group(6)
            dev_norm = None
            if device_raw:
                dr = device_raw.lower().strip()
                if dr in ("eq", "equalizer"): dev_norm = "eq"
                elif dr == "compressor": dev_norm = "compressor"
                elif dr == "delay": dev_norm = "delay"
                elif dr.replace(" ", "") == "aligndelay": dev_norm = "align delay"
                else: dev_norm = dr
            # Normalize some common param names
            pname_norm_map = {
                'stereo image': 'Stereo Image',
                'decay': 'Decay',
                'predelay': 'Predelay',
                'dry / wet': 'Dry/Wet',
                'dry wet': 'Dry/Wet',
            }
            pn = ' '.join(pname.split()).lower()
            pn = pn.replace('dry / wet', 'dry / wet').replace('dry wet', 'dry / wet')
            param_ref = pname_norm_map.get(pn, pname)
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
            out = {
                'intent': 'set_parameter',
                'targets': [{ 'track': f'Return {return_ref}', 'plugin': (dev_norm or 'reverb'), 'parameter': param_ref }],
                'operation': { 'type': 'absolute', 'value': value, 'unit': unit_out },
                'meta': { 'utterance': query, 'fallback': True, 'error': error_msg, 'model_selected': get_default_model_name(model_preference) }
            }
            if device_ord:
                try:
                    out['targets'][0]['device_ordinal'] = int(device_ord)
                except Exception:
                    pass
            return out
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

    # Sends control (track) variants: allow missing 'to' or 'on' phrasing
    try:
        import re
        # Variant without 'to'
        m = re.search(r"\bset\s+track\s+(\d+)\s+(?:send\s+)?([a-d])\s+(-?\d+(?:\.\d+)?)(?:\s*(db|dB|%|percent))?\b", q)
        if not m:
            # Variant: set send A on track 1 to -12 dB
            m = re.search(r"\bset\s+send\s+([a-d])\s+on\s+track\s+(\d+)\s*(?:to|at)?\s*(-?\d+(?:\.\d+)?)(?:\s*(db|dB|%|percent))?\b", q)
            if m:
                # Rearrange capture groups to unify handling
                track_num = int(m.group(2))
                send_ref = m.group(1).upper()
                value = float(m.group(3))
                unit = m.group(4)
            else:
                track_num = None
        if m and track_num is None:
            track_num = int(m.group(1))
            send_ref = m.group(2).upper()
            value = float(m.group(3))
            unit = m.group(4)
        if m:
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

    # Return device param: label selection (e.g., Mode to Distance)
    try:
        import re
        dev_pat = r"reverb|align\s+delay|delay|compressor|eq|equalizer"
        # Capture a word/label value (no number required)
        m = re.search(rf"\bset\s+return\s+([a-d])\s+(?:(?:the\s+)?({dev_pat})(?:\s+(\d+))?\s+)?(mode|quality|type|algorithm|alg|distunit|units?)\s+(?:to|at|=)\s*([a-zA-Z]+)\b", q)
        if m:
            return_ref = m.group(1).upper()
            device_raw = m.group(2) or ''
            device_ord = m.group(3)
            pname = m.group(4).strip()
            label = m.group(5).strip()
            dr = device_raw.lower().strip() if device_raw else ''
            if dr in ("eq", "equalizer"): plugin = "eq"
            elif dr == "compressor": plugin = "compressor"
            elif dr == "delay": plugin = "delay"
            elif dr.replace(" ", "") == "aligndelay": plugin = "align delay"
            else: plugin = (dr or 'reverb')
            # Normalize common param names
            pname_map = { 'mode': 'Mode', 'algorithm': 'Algorithm', 'alg': 'Algorithm', 'type': 'Type', 'quality': 'Quality', 'distunit': 'DistUnit', 'units': 'Units' }
            param_ref = pname_map.get(pname.lower(), pname.title())
            out = {
                'intent': 'set_parameter',
                'targets': [{ 'track': f'Return {return_ref}', 'plugin': plugin, 'parameter': param_ref }],
                'operation': { 'type': 'absolute', 'value': label, 'unit': 'display' },
                'meta': { 'utterance': query, 'fallback': True, 'error': error_msg, 'model_selected': get_default_model_name(model_preference) }
            }
            if device_ord:
                try:
                    out['targets'][0]['device_ordinal'] = int(device_ord)
                except Exception:
                    pass
            return out
    except Exception:
        pass

    # Return device param: label selection with arbitrary device name (fallback)
    try:
        import re
        m = re.search(r"\bset\s+return\s+([a-d])\s+(?:the\s+)?(.+?)\s+(mode|quality|type|algorithm|alg|distunit|units?)\s+(?:to|at|=)\s*([a-zA-Z]+)\b", q)
        if m:
            return_ref = m.group(1).upper()
            device_name = m.group(2).strip()
            pname = m.group(3).strip()
            label = m.group(4).strip()
            pname_map = { 'mode': 'Mode', 'algorithm': 'Algorithm', 'alg': 'Algorithm', 'type': 'Type', 'quality': 'Quality', 'distunit': 'DistUnit', 'units': 'Units' }
            param_ref = pname_map.get(pname.lower(), pname.title())
            return {
                'intent': 'set_parameter',
                'targets': [{ 'track': f'Return {return_ref}', 'plugin': device_name, 'parameter': param_ref }],
                'operation': { 'type': 'absolute', 'value': label, 'unit': 'display' },
                'meta': { 'utterance': query, 'fallback': True, 'error': error_msg, 'model_selected': get_default_model_name(model_preference) }
            }
    except Exception:
        pass

    # Return device param: numeric with arbitrary device name (e.g., "set Return A 4th bandpass feedback to 20 %")
    try:
        import re
        units_pat = r"db|dB|%|percent|ms|millisecond|milliseconds|s|sec|second|seconds|hz|khz|degree|degrees|deg|°"
        m = re.search(rf"\bset\s+return\s+([a-d])\s+(?:the\s+)?(.+?)\s+(.+?)\s+(?:to|at)\s+(-?\d+(?:\.\d+)?)(?:\s*({units_pat}))?\b", q)
        if m:
            return_ref = m.group(1).upper()
            device_name = m.group(2).strip()
            pname = m.group(3).strip()
            value = float(m.group(4))
            unit_raw = m.group(5)
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
            return {
                'intent': 'set_parameter',
                'targets': [{ 'track': f'Return {return_ref}', 'plugin': device_name, 'parameter': pname }],
                'operation': { 'type': 'absolute', 'value': value, 'unit': unit_out },
                'meta': { 'utterance': query, 'fallback': True, 'error': error_msg, 'model_selected': get_default_model_name(model_preference) }
            }
    except Exception:
        pass

    # Track device param: numeric with arbitrary device name (e.g., "set track 2 4th bandpass feedback to 20 %")
    try:
        import re
        units_pat = r"db|dB|%|percent|ms|millisecond|milliseconds|s|sec|second|seconds|hz|khz|degree|degrees|deg|°"
        m = re.search(rf"\bset\s+track\s+(\d+)\s+(?:the\s+)?(.+?)\s+(.+?)\s+(?:to|at)\s+(-?\d+(?:\.\d+)?)(?:\s*({units_pat}))?\b", q)
        if m:
            track_num = int(m.group(1))
            device_name = m.group(2).strip()
            pname = m.group(3).strip()
            value = float(m.group(4))
            unit_raw = m.group(5)
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
            return {
                'intent': 'set_parameter',
                'targets': [{ 'track': f'Track {track_num}', 'plugin': device_name, 'parameter': pname }],
                'operation': { 'type': 'absolute', 'value': value, 'unit': unit_out },
                'meta': { 'utterance': query, 'fallback': True, 'error': error_msg, 'model_selected': get_default_model_name(model_preference) }
            }
    except Exception:
        pass

    # Track device param: label selection (e.g., Mode to Distance)
    try:
        import re
        dev_pat = r"reverb|align\s+delay|delay|compressor|eq|equalizer"
        m = re.search(rf"\bset\s+track\s+(\d+)\s+(?:(?:the\s+)?({dev_pat})(?:\s+(\d+))?\s+)?(mode|quality|type|algorithm|alg|distunit|units?)\s+(?:to|at|=)\s*([a-zA-Z]+)\b", q)
        if m:
            track_num = int(m.group(1))
            device_raw = m.group(2) or ''
            device_ord = m.group(3)
            pname = m.group(4).strip()
            label = m.group(5).strip()
            dr = device_raw.lower().strip() if device_raw else ''
            if dr in ("eq", "equalizer"): plugin = "eq"
            elif dr == "compressor": plugin = "compressor"
            elif dr == "delay": plugin = "delay"
            elif dr.replace(" ", "") == "aligndelay": plugin = "align delay"
            else: plugin = (dr or 'reverb')
            pname_map = { 'mode': 'Mode', 'algorithm': 'Algorithm', 'alg': 'Algorithm', 'type': 'Type', 'quality': 'Quality', 'distunit': 'DistUnit', 'units': 'Units' }
            param_ref = pname_map.get(pname.lower(), pname.title())
            out = {
                'intent': 'set_parameter',
                'targets': [{ 'track': f'Track {track_num}', 'plugin': plugin, 'parameter': param_ref }],
                'operation': { 'type': 'absolute', 'value': label, 'unit': 'display' },
                'meta': { 'utterance': query, 'fallback': True, 'error': error_msg, 'model_selected': get_default_model_name(model_preference) }
            }
            if device_ord:
                try:
                    out['targets'][0]['device_ordinal'] = int(device_ord)
                except Exception:
                    pass
            return out

    except Exception:
        pass

    # Return generic ordinal device without name: "set return A device 2 <param> to <val> [unit]"
    try:
        import re
        units_pat = r"db|dB|%|percent|ms|millisecond|milliseconds|s|sec|second|seconds|hz|khz|degree|degrees|deg|°"
        m = re.search(rf"\bset\s+return\s+([a-d])\s+device\s+(\d+)\s+(.+?)\s+(?:to|at)\s+(-?\d+(?:\.\d+)?)(?:\s*({units_pat}))?\b", q)
        if m:
            return_ref = m.group(1).upper()
            device_ord = m.group(2)
            pname = m.group(3).strip()
            value = float(m.group(4))
            unit_raw = m.group(5)
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
            out = {
                'intent': 'set_parameter',
                'targets': [{ 'track': f'Return {return_ref}', 'plugin': 'device', 'parameter': pname, 'device_ordinal': int(device_ord) }],
                'operation': { 'type': 'absolute', 'value': value, 'unit': unit_out },
                'meta': { 'utterance': query, 'fallback': True, 'error': error_msg, 'model_selected': get_default_model_name(model_preference) }
            }
            return out
    except Exception:
        pass

    # Track generic ordinal device without name: "set track N device 2 <param> to <val> [unit]"
    try:
        import re
        units_pat = r"db|dB|%|percent|ms|millisecond|milliseconds|s|sec|second|seconds|hz|khz|degree|degrees|deg|°"
        m = re.search(rf"\bset\s+track\s+(\d+)\s+device\s+(\d+)\s+(.+?)\s+(?:to|at)\s+(-?\d+(?:\.\d+)?)(?:\s*({units_pat}))?\b", q)
        if m:
            track_num = int(m.group(1))
            device_ord = m.group(2)
            pname = m.group(3).strip()
            value = float(m.group(4))
            unit_raw = m.group(5)
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
            out = {
                'intent': 'set_parameter',
                'targets': [{ 'track': f'Track {track_num}', 'plugin': 'device', 'parameter': pname, 'device_ordinal': int(device_ord) }],
                'operation': { 'type': 'absolute', 'value': value, 'unit': unit_out },
                'meta': { 'utterance': query, 'fallback': True, 'error': error_msg, 'model_selected': get_default_model_name(model_preference) }
            }
            return out
    except Exception:
        pass
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

    # Sends control (return) variants: allow missing 'to' or 'on' phrasing
    try:
        import re
        # Variant without 'to'
        m = re.search(r"\bset\s+return\s+([a-d])\s+(?:send\s+)?([a-d])\s+(-?\d+(?:\.\d+)?)(?:\s*(db|dB|%|percent))?\b", q)
        if not m:
            # Variant: set send B on return A to -10 dB
            m = re.search(r"\bset\s+send\s+([a-d])\s+on\s+return\s+([a-d])\s*(?:to|at)?\s*(-?\d+(?:\.\d+)?)(?:\s*(db|dB|%|percent))?\b", q)
            if m:
                return_ref = m.group(2).upper()
                send_ref = m.group(1).upper()
                value = float(m.group(3))
                unit = m.group(4)
            else:
                return_ref = None
        if m and return_ref is None:
            return_ref = m.group(1).upper()
            send_ref = m.group(2).upper()
            value = float(m.group(3))
            unit = m.group(4)
        if m:
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

    # Generic return device parameter with unit, allowing device capture and optional ordinal
    try:
        import re
        dev_pat = r"reverb|align\s+delay|delay|compressor|eq|equalizer"
        units_pat = r"db|dB|%|percent|ms|millisecond|milliseconds|s|sec|second|seconds|hz|khz|degree|degrees|deg|°"
        m = re.search(rf"\bset\s+return\s+([a-d])\s+(?:(?:the\s+)?({dev_pat})(?:\s+(\d+))?\s+)?(.+?)\s+(?:to|at)\s+(-?\d+(?:\.\d+)?)(?:\s*({units_pat}))?\b", q)
        if m:
            return_ref = m.group(1).upper()
            device_raw = m.group(2) or ''
            device_ord = m.group(3)
            pname = m.group(4).strip()
            value = float(m.group(5))
            unit_raw = m.group(6)
            dev_norm = None
            if device_raw:
                dr = device_raw.lower().strip()
                if dr in ("eq", "equalizer"): dev_norm = "eq"
                elif dr == "compressor": dev_norm = "compressor"
                elif dr == "delay": dev_norm = "delay"
                elif dr.replace(" ", "") == "aligndelay": dev_norm = "align delay"
                else: dev_norm = dr
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
            out = {
                'intent': 'set_parameter',
                'targets': [{ 'track': f'Return {return_ref}', 'plugin': (dev_norm or 'reverb'), 'parameter': pname }],
                'operation': { 'type': 'absolute', 'value': value, 'unit': unit_out },
                'meta': { 'utterance': query, 'fallback': True, 'error': error_msg, 'model_selected': get_default_model_name(model_preference) }
            }
            if device_ord:
                try:
                    out['targets'][0]['device_ordinal'] = int(device_ord)
                except Exception:
                    pass
            return out
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
