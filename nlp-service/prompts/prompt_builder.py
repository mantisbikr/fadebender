from __future__ import annotations

import json
from typing import Any, Dict, List

from .hint_extractor import extract_llm_hints
from .prompt_templates import PROMPT_TEMPLATE

__all__ = ["build_daw_prompt"]


def _hints_text(query: str) -> str:
    try:
        hints = extract_llm_hints(query)
    except Exception:
        hints = {}
    if not hints:
        return ""
    try:
        hints_json = json.dumps(hints, ensure_ascii=False)
    except Exception:
        hints_json = "{}"
    return (
        "HINTS (use to disambiguate — include in output if consistent):\n"
        + hints_json
        + "\n"
        + "- If device_name_hint is present, use it as the plugin name EXACTLY as provided (e.g., '4th bandpass' is a device name, not an ordinal).\n"
        + "- If device_ordinal_hint is present, set targets[0].device_ordinal to that number.\n"
        + "- If track_hint is present, align targets[0].track with it.\n\n"
    )


def _mixer_context(mixer_params: List[str] | None) -> str:
    if not mixer_params:
        return ""
    joined = ", ".join(mixer_params)
    return (
        "KNOWN MIXER PARAMETERS (from DAW):\n"
        + f"{joined}\n\n"
        + "**CRITICAL RULE**: If the user mentions a parameter from this list AND does NOT mention a device/plugin name, "
        + "it is a MIXER operation (set plugin=null). Device operations ALWAYS have an explicit device name.\n\n"
    )


def _device_context(known_devices: List[Dict[str, str]] | None) -> str:
    if not known_devices:
        return ""
    by_type: Dict[str, List[str]] = {}
    for device in known_devices:
        dtype = device.get("type", "unknown")
        name = device.get("name", "")
        if name:
            by_type.setdefault(dtype, []).append(name)
    device_lines: List[str] = []
    for dtype in sorted(by_type.keys()):
        names = ", ".join(sorted(set(by_type[dtype]))[:10])
        device_lines.append(f"  {dtype}: {names}")
    return (
        "KNOWN DEVICES (from session presets):\n"
        + "\n".join(device_lines)
        + "\n\n"
        + "**IMPORTANT**: These device names are ONLY for typo correction when the user EXPLICITLY mentions a device/plugin. "
        + "DO NOT infer device operations from parameter names alone. "
        + "For example: 'screamr gain' → 'Screamer' (user mentioned device), but 'set track 1 volume' → NO device (pure mixer op).\n\n"
    )


def build_daw_prompt(
    query: str,
    mixer_params: List[str] | None = None,
    known_devices: List[Dict[str, str]] | None = None,
) -> str:
    return (
        _hints_text(query)
        + _device_context(known_devices)
        + _mixer_context(mixer_params)
        + PROMPT_TEMPLATE
        + query
        + "\nJSON:"
    )
