"""Layer 3: Device/Param Parser

Wraps parse_index to provide clean device + parameter extraction.
Fixes mixer parameter recognition bug.

Key fix: Check for mixer parameters FIRST before trying device parsing.
This prevents mixer params from being misidentified as device params or returning device=None.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Dict
import re


@dataclass
class DeviceParamMatch:
    """Result from device + parameter parsing (standardized for layered architecture)."""
    device: Optional[str]        # Device name ("reverb", "delay") or "mixer" for mixer params
    device_type: Optional[str]   # Device type (e.g., "reverb") or "mixer"
    device_ordinal: Optional[int]  # Device instance number (e.g., 2 for "reverb 2")
    param: Optional[str]         # Canonical parameter name (e.g., "Decay", "volume")
    confidence: float            # 0.0-1.0 confidence score
    method: str                  # "mixer_param", "exact", "fuzzy_device", etc.


# Mixer parameter patterns (from existing mixer_parser.py)
_SEND_LETTERS = [f"send {chr(ord('a') + i)}" for i in range(12)]  # send a–l
_SEND_NUMBERS = [f"send {i}" for i in range(1, 13)]  # send 1–12

MIXER_PARAMS = [
    "volume",
    "pan",
    "mute",
    "solo",
    *(_SEND_LETTERS + _SEND_NUMBERS),
    "arm",
    "monitor",
]


def is_mixer_param(text: str) -> Optional[str]:
    """Check if text contains a mixer parameter.

    Returns canonical mixer parameter name if found, None otherwise.

    Examples:
        "set track 1 volume to -10" → "volume"
        "increase return A pan by 10" → "pan"
        "mute track 2" → "mute"
    """
    text_lower = text.lower()

    # Build regex pattern for mixer params (longest first to avoid prefix issues)
    params_sorted = sorted(MIXER_PARAMS, key=len, reverse=True)
    pattern = r"\b(" + "|".join(re.escape(p) for p in params_sorted) + r")\b"

    m = re.search(pattern, text_lower)
    if m:
        # Return canonical form (capitalize first letter)
        param_raw = m.group(1)

        # Special cases
        if param_raw.startswith("send "):
            return param_raw.title()  # "Send A", "Send 1"
        else:
            return param_raw.capitalize()  # "Volume", "Pan", etc.

    return None


def parse_device_param(text: str, parse_index: Dict) -> DeviceParamMatch:
    """Parse device and parameter from text using parse_index.

    Strategy (matches current architecture):
    1. Try to match DEVICE context first (device name/type in text)
    2. If device found, use device parameter
    3. If NO device found, check if it's a mixer parameter
    4. This avoids ambiguity with params like "volume" that exist in both

    Args:
        text: Input text (e.g., "set track 1 volume to -10 dB")
        parse_index: Parse index dict with device/param vocabulary

    Returns:
        DeviceParamMatch with device, param, and confidence
    """

    # STEP 1: Try device parameter parsing first (looks for device context)
    # Import here to avoid circular dependency
    from server.services.parse_index.device_context_parser import DeviceContextParser

    parser = DeviceContextParser(parse_index)
    result = parser.parse_device_param(text)

    # STEP 2: If device found, return device parameter result
    if result.device and result.device != "mixer":
        return result

    # STEP 3: If device="mixer" was returned, use it (parse_index already handled this)
    if result.device == "mixer":
        return result

    # STEP 4: No device found - check if parameter is a mixer parameter
    # This fixes the bug where mixer params return device=None
    if result.param:
        mixer_param = is_mixer_param(text)
        if mixer_param:
            return DeviceParamMatch(
                device="mixer",
                device_type="mixer",
                device_ordinal=None,
                param=mixer_param,
                confidence=0.95,
                method="mixer_param"
            )

    # STEP 5: Return result as-is (might be param-only or no match)
    return result
