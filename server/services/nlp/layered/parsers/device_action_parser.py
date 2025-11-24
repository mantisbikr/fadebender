"""Parse device action commands (load, etc.)."""

import os
import json
import re
from typing import Optional, Dict, Any, Set


# Cache for device_map.json
_DEVICE_MAP_CACHE: Optional[Dict[str, Any]] = None


def _load_device_map() -> Dict[str, Any]:
    """Load device mapping from ~/.fadebender/device_map.json (cached).

    Returns device map dict, or empty dict if not found.
    """
    global _DEVICE_MAP_CACHE
    if _DEVICE_MAP_CACHE is not None:
        return _DEVICE_MAP_CACHE

    try:
        config_path = os.path.expanduser("~/.fadebender/device_map.json")
        if os.path.exists(config_path):
            with open(config_path, "r") as f:
                _DEVICE_MAP_CACHE = json.load(f) or {}
                return _DEVICE_MAP_CACHE
    except Exception:
        pass

    _DEVICE_MAP_CACHE = {}
    return _DEVICE_MAP_CACHE


def _get_device_names() -> Set[str]:
    """Get all device names from device_map (case-insensitive set)."""
    device_map = _load_device_map()
    return {name.lower() for name in device_map.keys()}


def _fuzzy_match_device(text: str, device_names: Set[str], max_distance: int = 2) -> Optional[str]:
    """Fuzzy match text against device names (case-insensitive).

    Args:
        text: Text to match (e.g., "reverb", "auto filter")
        device_names: Set of lowercase device names from device_map
        max_distance: Maximum edit distance for fuzzy matching

    Returns:
        Matched device name (lowercase) or None
    """
    text_lower = text.lower()

    # Exact match first
    if text_lower in device_names:
        return text_lower

    # Fuzzy match using simple edit distance
    # For now, just check for single-character typos
    if max_distance > 0:
        for device_name in device_names:
            if _simple_edit_distance(text_lower, device_name) <= max_distance:
                return device_name

    return None


def _simple_edit_distance(a: str, b: str) -> int:
    """Calculate simple Levenshtein distance between two strings."""
    if len(a) < len(b):
        return _simple_edit_distance(b, a)

    if len(b) == 0:
        return len(a)

    previous_row = range(len(b) + 1)
    for i, ca in enumerate(a):
        current_row = [i + 1]
        for j, cb in enumerate(b):
            # j+1 instead of j since previous_row and current_row are one character longer
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (ca != cb)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row

    return previous_row[-1]


def _split_device_preset(text: str) -> tuple[str, Optional[str]]:
    """Split text into device name and optional preset name using device_map vocabulary.

    Strategy:
    1. Load device_map.json to get available device names
    2. Try progressively longer word combinations (1 word, 2 words, 3 words, etc.)
    3. Check if any combination matches a device in device_map (with fuzzy matching)
    4. Use the longest matching device name, rest is preset

    Examples:
        "reverb cathedral" → ("reverb", "cathedral")
        "auto filter" → ("auto filter", None)
        "auto filter band pass" → ("auto filter", "band pass")
        "compressor gentle" → ("compressor", "gentle")
        "eq eight" → ("eq eight", None)

    Args:
        text: Device + preset text (e.g., "auto filter band pass")

    Returns:
        (device_name, preset_name) tuple
    """
    device_names = _get_device_names()
    words = text.split()

    if len(words) == 0:
        return "", None

    if len(words) == 1:
        # Single word - must be device name
        return words[0], None

    # Try progressively longer combinations, starting from longest
    # This ensures we match "Auto Filter" before just "Auto"
    best_device = None
    best_device_word_count = 0

    for num_words in range(min(len(words), 4), 0, -1):  # Try up to 4 words
        candidate = " ".join(words[:num_words])
        matched_device = _fuzzy_match_device(candidate, device_names, max_distance=1)

        if matched_device:
            best_device = candidate
            best_device_word_count = num_words
            break

    if best_device:
        # Found a matching device
        if best_device_word_count < len(words):
            # Remaining words are the preset
            preset = " ".join(words[best_device_word_count:])
            return best_device, preset
        else:
            # All words are the device name
            return best_device, None
    else:
        # No device match found - default to first word as device
        # This allows fallback for devices not in device_map
        return words[0], " ".join(words[1:]) if len(words) > 1 else None


def parse_load_device(text: str) -> Optional[Dict[str, Any]]:
    """Parse device loading commands.

    Examples:
        "load reverb on track 2"
        "add compressor to track 1"
        "load analog preset lush pad on track 3"
        "put reverb cathedral on return A"
        "load limiter on the master"
        "add arpeggiator to return B"
        "load auto filter on track 3"
        "load eq eight on track 1"
    """
    # Pattern: (load|add|put|insert) <device> [preset <preset_name>|<preset_name>] (on|to) [the] (track|return|master) <index>

    # Try with explicit "preset" keyword first
    # e.g., "load analog preset lush pad on track 3"
    m = re.match(
        r"^(?:load|add|put|insert)\s+"
        r"(.+?)\s+"  # device name (variable length, non-greedy)
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
    # e.g., "load auto filter on track 3"
    m = re.match(
        r"^(?:load|add|put|insert)\s+"
        r"(.+?)\s+"  # device + optional preset (non-greedy)
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

        # Split device_and_preset using device_map vocabulary
        device_name, preset_name = _split_device_preset(device_and_preset)

        return _build_load_intent(domain, index_str, device_name, preset_name)

    return None


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


def parse_delete_device(text: str) -> Optional[Dict[str, Any]]:
    """Parse device deletion commands.

    Examples:
        "delete reverb from track 2"
        "remove compressor from track 1"
        "delete device 0 from track 2" (by index)
        "remove first reverb from track 2" (by ordinal)
        "delete second compressor from return A" (by ordinal)
        "remove the reverb from return B"
    """
    # Pattern: (delete|remove) [the] [first|second|1st|2nd] <device name|"device N"> (from|on) [the] (track|return) <index>

    # Try with ordinal first (e.g., "delete first reverb from track 2")
    m = re.match(
        r"^(?:delete|remove)\s+(?:the\s+)?"
        r"(first|second|third|1st|2nd|3rd|\d+(?:st|nd|rd|th))\s+"
        r"(.+?)\s+"
        r"(?:from|on)\s+(?:the\s+)?"
        r"(track|return)\s+"
        r"(\w+)$",
        text,
        re.IGNORECASE
    )
    if m:
        ordinal_str = m.group(1).lower()
        device_name = m.group(2).strip()
        domain = m.group(3).lower()
        index_str = m.group(4)

        # Parse ordinal to number
        ordinal_map = {
            "first": 1, "1st": 1,
            "second": 2, "2nd": 2,
            "third": 3, "3rd": 3,
        }
        ordinal = ordinal_map.get(ordinal_str)
        if ordinal is None:
            # Try to parse numeric ordinal like "4th"
            match = re.match(r"(\d+)(?:st|nd|rd|th)", ordinal_str)
            if match:
                ordinal = int(match.group(1))
            else:
                return None

        return _build_delete_intent(domain, index_str, device_name=device_name, device_ordinal=ordinal)

    # Try by device name (e.g., "delete reverb from track 2")
    m = re.match(
        r"^(?:delete|remove)\s+(?:the\s+)?"
        r"(.+?)\s+"
        r"(?:from|on)\s+(?:the\s+)?"
        r"(track|return)\s+"
        r"(\w+)$",
        text,
        re.IGNORECASE
    )
    if m:
        device_name = m.group(1).strip()
        domain = m.group(2).lower()
        index_str = m.group(3)

        # Check if it's "device N" format (by index)
        device_match = re.match(r"^device\s+(\d+)$", device_name, re.IGNORECASE)
        if device_match:
            device_index = int(device_match.group(1))
            return _build_delete_intent(domain, index_str, device_index=device_index)
        else:
            # By name
            return _build_delete_intent(domain, index_str, device_name=device_name)

    return None


def _build_delete_intent(
    domain: str,
    index_str: Optional[str],
    device_name: Optional[str] = None,
    device_index: Optional[int] = None,
    device_ordinal: Optional[int] = None
) -> Optional[Dict[str, Any]]:
    """Build device delete intent from parsed components."""
    intent = {
        "domain": "device",
        "action": "delete",
    }

    if device_name:
        intent["device_name"] = device_name
    if device_index is not None:
        intent["device_index"] = device_index
    if device_ordinal is not None:
        intent["device_ordinal"] = device_ordinal

    # Parse target
    if domain == "track":
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
        parse_delete_device,
    ]

    for parser in parsers:
        result = parser(text)
        if result:
            return result

    return None
