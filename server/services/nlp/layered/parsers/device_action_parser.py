"""Parse device action commands (load, etc.)."""

import re
from typing import Optional, Dict, Any


def parse_load_device(text: str) -> Optional[Dict[str, Any]]:
    """Parse device loading commands.

    Examples:
        "load reverb on track 2"
        "add compressor to track 1"
        "load analog preset lush pad on track 3"
        "put reverb cathedral on return A"
        "load limiter on the master"
        "add arpeggiator to return B"
    """
    # Pattern: (load|add|put|insert) <device> [preset <preset_name>|<preset_name>] (on|to) [the] (track|return|master) <index>

    # Try with explicit "preset" keyword first
    # e.g., "load analog preset lush pad on track 3"
    m = re.match(
        r"^(?:load|add|put|insert)\s+"
        r"(\w+(?:\s+\w+)?)\s+"  # device name (1-2 words)
        r"preset\s+"
        r"(.+?)\s+"  # preset name (greedy until target)
        r"(?:on|to)\s+(?:the\s+)?"
        r"(track|return|master)\s*"
        r"(\w+)?$",  # optional index
        text,
        re.IGNORECASE
    )
    if m:
        device_name = m.group(1).strip()
        preset_name = m.group(2).strip()
        domain = m.group(3).lower()
        index_str = m.group(4)

        return _build_load_intent(domain, index_str, device_name, preset_name)

    # Try without "preset" keyword but with preset name
    # e.g., "load reverb cathedral on track 2"
    # This is harder - we need to distinguish device name from preset name
    # Strategy: capture everything between verb and target, then split
    m = re.match(
        r"^(?:load|add|put|insert)\s+"
        r"(.+?)\s+"  # device + optional preset (greedy)
        r"(?:on|to)\s+(?:the\s+)?"
        r"(track|return|master)\s*"
        r"(\w+)?$",  # optional index
        text,
        re.IGNORECASE
    )
    if m:
        device_and_preset = m.group(1).strip()
        domain = m.group(2).lower()
        index_str = m.group(3)

        # Split device_and_preset into device and optional preset
        # Common devices are 1-2 words, presets can be multiple words
        # Strategy: Check if device_map knows the first 1-2 words as a device
        device_name, preset_name = _split_device_preset(device_and_preset)

        return _build_load_intent(domain, index_str, device_name, preset_name)

    return None


def _split_device_preset(text: str) -> tuple[str, Optional[str]]:
    """Split text into device name and optional preset name.

    Strategy:
    - First word is always device name
    - If second word exists and first word is a known single-word device, include second word in preset
    - Otherwise second word is part of device name (for multi-word devices like "Auto Filter")

    For now, use simple heuristic: first 1-2 words are device, rest is preset.
    """
    words = text.split()

    if len(words) == 1:
        # Just device name
        return words[0], None

    if len(words) == 2:
        # Could be "Reverb Cathedral" or "Auto Filter"
        # Check if first word is a complete device name
        # For simplicity: assume it's device + preset
        return words[0], words[1]

    # 3+ words: try device as 1 word first, then 2 words
    # Common multi-word devices: Auto Filter, Auto Pan, Channel EQ, Drum Buss, etc.
    # Strategy: if second word is "Filter", "Pan", "EQ", "Buss", "Rack", etc., it's part of device
    second_word_lower = words[1].lower()
    if second_word_lower in ["filter", "pan", "eq", "buss", "rack", "delay", "reverb"]:
        # Multi-word device
        device_name = f"{words[0]} {words[1]}"
        preset_name = " ".join(words[2:]) if len(words) > 2 else None
    else:
        # Single-word device
        device_name = words[0]
        preset_name = " ".join(words[1:])

    return device_name, preset_name


def _build_load_intent(
    domain: str,
    index_str: Optional[str],
    device_name: str,
    preset_name: Optional[str]
) -> Dict[str, Any]:
    """Build device load intent from parsed components."""
    intent = {
        "domain": "device",
        "action": "load",
        "device_name": device_name,
    }

    if preset_name:
        intent["preset_name"] = preset_name

    # Parse target
    if domain == "master":
        intent["target_domain"] = "master"
    elif domain == "track":
        if not index_str:
            return None  # Track requires index
        try:
            intent["target_domain"] = "track"
            intent["track_index"] = int(index_str)
        except ValueError:
            return None
    elif domain == "return":
        if not index_str:
            return None  # Return requires index
        # Return can be number or letter
        if index_str.isdigit():
            intent["target_domain"] = "return"
            intent["return_index"] = int(index_str)
        else:
            # Letter reference (A, B, C, etc.)
            intent["target_domain"] = "return"
            intent["return_ref"] = index_str.upper()

    return intent


def parse_device_action(text: str) -> Optional[Dict[str, Any]]:
    """Try all device action parsers in order.

    Returns parsed intent or None.
    """
    parsers = [
        parse_load_device,
    ]

    for parser in parsers:
        result = parser(text)
        if result:
            return result

    return None
