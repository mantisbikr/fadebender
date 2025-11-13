"""Layer 1: Action/Value/Unit Parser

Extracts intent type, operation, value, and unit from text.
Independent of track/device context - purely focused on action patterns.

Extracted patterns from existing mixer_parser.py, transport_parser.py, and device_parser.py.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional
import re


@dataclass
class ActionMatch:
    """Result from action parsing."""
    intent_type: str          # "set_parameter", "transport", "open_capabilities", "list_capabilities"
    operation: Optional[str]  # "absolute", "relative", None (for transport/navigation)
    value: Optional[float | str | bool]  # Numeric, label string, or boolean
    unit: Optional[str]       # "dB", "%", "s", "ms", "hz", "degrees", "display", None
    confidence: float         # 0.0-1.0
    method: str              # "regex", "llm_fallback"
    raw_text: str            # Original matched text for debugging


# ============================================================================
# UNIT NORMALIZATION (from existing device_parser.py)
# ============================================================================

def normalize_unit(unit_raw: Optional[str]) -> Optional[str]:
    """Normalize unit strings to canonical form."""
    if not unit_raw:
        return None

    u = unit_raw.lower().strip()

    # Map to canonical units
    unit_map = {
        'db': 'dB',
        '%': '%',
        'percent': '%',
        'ms': 'ms',
        'millisecond': 'ms',
        'milliseconds': 'ms',
        's': 's',
        'sec': 's',
        'second': 's',
        'seconds': 's',
        'hz': 'hz',
        'khz': 'khz',
        'degree': 'degrees',
        'degrees': 'degrees',
        'deg': 'degrees',
        '°': 'degrees',
    }

    return unit_map.get(u, None)


# ============================================================================
# PARAMETER CHANGE PATTERNS (set/increase/decrease)
# ============================================================================

def parse_absolute_change(text: str) -> Optional[ActionMatch]:
    """Parse absolute parameter changes: 'set ... to X UNIT'

    Examples:
        "set track 1 volume to -10 dB"
        "set return A reverb decay to 5 seconds"
        "change track 2 pan to 50%"
    """
    # Pattern: (set|change|adjust|make) ... to VALUE [UNIT]
    # Note: No trailing \b because % is not a word character
    pattern = r"\b(set|change|adjust|make)\s+.+?\s+(?:to|at)\s+(-?\d+(?:\.\d+)?)(?:\s*(db|dB|%|percent|ms|milliseconds?|s|sec|seconds?|hz|khz|degrees?|deg|°))?"

    match = re.search(pattern, text, re.IGNORECASE)
    if match:
        verb = match.group(1)
        value = float(match.group(2))
        unit_raw = match.group(3)
        unit = normalize_unit(unit_raw)

        return ActionMatch(
            intent_type="set_parameter",
            operation="absolute",
            value=value,
            unit=unit or "display",  # Default to display if no unit
            confidence=0.95,
            method="regex",
            raw_text=match.group(0)
        )

    return None


def parse_relative_change(text: str) -> Optional[ActionMatch]:
    """Parse relative parameter changes: 'increase/decrease ... by X UNIT'

    Examples:
        "increase track 1 volume by 3 dB"
        "decrease return A reverb decay by 1 second"
        "raise track 2 send A by 5 dB"
    """
    # Pattern: (increase|decrease|raise|lower) ... by VALUE [UNIT]
    # Note: No trailing \b because % is not a word character
    pattern = r"\b(increase|decrease|raise|lower)\s+.+?\s+by\s+(-?\d+(?:\.\d+)?)(?:\s*(db|dB|%|percent|ms|milliseconds?|s|sec|seconds?|hz|khz|degrees?|deg|°))?"

    match = re.search(pattern, text, re.IGNORECASE)
    if match:
        verb = match.group(1).lower()
        value = float(match.group(2))
        unit_raw = match.group(3)
        unit = normalize_unit(unit_raw)

        # Apply direction based on verb
        if verb in ('decrease', 'lower'):
            value = -abs(value)
        else:
            value = abs(value)

        return ActionMatch(
            intent_type="set_parameter",
            operation="relative",
            value=value,
            unit=unit or "display",
            confidence=0.95,
            method="regex",
            raw_text=match.group(0)
        )

    return None


def parse_toggle_operation(text: str) -> Optional[ActionMatch]:
    """Parse toggle operations: 'mute/solo/unmute/unsolo'

    Examples:
        "mute track 1"
        "solo return A"
        "unmute track 2"
    """
    # Pattern: (mute|unmute|solo|unsolo)
    pattern = r"\b(mute|unmute|solo|unsolo)\b"

    match = re.search(pattern, text, re.IGNORECASE)
    if match:
        action = match.group(1).lower()

        # Determine value (1.0 = on, 0.0 = off)
        value = 0.0 if action in ('unmute', 'unsolo') else 1.0

        return ActionMatch(
            intent_type="set_parameter",
            operation="absolute",
            value=value,
            unit=None,
            confidence=0.95,
            method="regex",
            raw_text=match.group(0)
        )

    return None


# ============================================================================
# TRANSPORT PATTERNS (from transport_parser.py)
# ============================================================================

def parse_transport_command(text: str) -> Optional[ActionMatch]:
    """Parse transport commands: play, stop, loop, tempo, etc.

    Examples:
        "loop on"
        "set tempo to 130"
        "play"
        "stop"
    """
    s = text.lower().strip()

    # Play/Stop
    if re.search(r"\bplay\b", s) and not re.search(r"\bstop\b", s):
        return ActionMatch(
            intent_type="transport",
            operation=None,
            value="play",
            unit=None,
            confidence=0.95,
            method="regex",
            raw_text="play"
        )

    if re.search(r"\bstop\b", s):
        return ActionMatch(
            intent_type="transport",
            operation=None,
            value="stop",
            unit=None,
            confidence=0.95,
            method="regex",
            raw_text="stop"
        )

    # Loop on/off/toggle
    m = re.search(r"\b(loop)\s*(on|off|toggle)\b", s)
    if m:
        mode = m.group(2).lower()
        value = 1.0 if mode == 'on' else 0.0 if mode == 'off' else "toggle"

        return ActionMatch(
            intent_type="transport",
            operation=None,
            value=value,
            unit=None,
            confidence=0.95,
            method="regex",
            raw_text=m.group(0)
        )

    # Tempo
    m = re.search(r"\b(set|change)\s+(tempo|bpm)\s*(to)?\s*(\d+(?:\.\d+)?)\b", s)
    if m:
        bpm = float(m.group(4))
        return ActionMatch(
            intent_type="transport",
            operation=None,
            value=bpm,
            unit="bpm",
            confidence=0.95,
            method="regex",
            raw_text=m.group(0)
        )

    # Loop start/length
    m = re.search(r"\b(set|change)\s+loop\s+start\s*(to\s*)?(\d+(?:\.\d+)?)\b", s)
    if m:
        val = float(m.group(3))
        return ActionMatch(
            intent_type="transport",
            operation=None,
            value=val,
            unit="loop_start",
            confidence=0.95,
            method="regex",
            raw_text=m.group(0)
        )

    m = re.search(r"\b(set|change)\s+loop\s+length\s*(to\s*)?(\d+(?:\.\d+)?)\b", s)
    if m:
        val = float(m.group(3))
        return ActionMatch(
            intent_type="transport",
            operation=None,
            value=val,
            unit="loop_length",
            confidence=0.95,
            method="regex",
            raw_text=m.group(0)
        )

    # Time signature
    m = re.search(r"\bset\s+(time\s*signature|time\s*sig|timesig|meter)\s+numerator\s*(to\s*)?(\d+)\b", s)
    if m:
        num = int(m.group(3))
        return ActionMatch(
            intent_type="transport",
            operation=None,
            value=num,
            unit="time_sig_num",
            confidence=0.95,
            method="regex",
            raw_text=m.group(0)
        )

    m = re.search(r"\bset\s+(time\s*signature|time\s*sig|timesig|meter)\s+denominator\s*(to\s*)?(\d+)\b", s)
    if m:
        den = int(m.group(3))
        return ActionMatch(
            intent_type="transport",
            operation=None,
            value=den,
            unit="time_sig_den",
            confidence=0.95,
            method="regex",
            raw_text=m.group(0)
        )

    # Playhead position
    m = re.search(r"\b(set|move|go\s*to|locate)\s*(the\s*)?(playhead|position)\s*(to\s*)?(\d+(?:\.\d+)?)\s*(beats?)?\b", s)
    if m:
        pos = float(m.group(5))
        return ActionMatch(
            intent_type="transport",
            operation=None,
            value=pos,
            unit="position",
            confidence=0.95,
            method="regex",
            raw_text=m.group(0)
        )

    return None


# ============================================================================
# NAVIGATION PATTERNS (open/list)
# ============================================================================

def parse_navigation_command(text: str) -> Optional[ActionMatch]:
    """Parse navigation commands: open, list

    Examples:
        "open track 1"
        "list tracks"
        "open return A reverb"
    """
    s = text.lower().strip()

    # Open command
    if re.search(r"\bopen\b", s):
        return ActionMatch(
            intent_type="open_capabilities",
            operation=None,
            value=None,
            unit=None,
            confidence=0.95,
            method="regex",
            raw_text="open"
        )

    # List command
    if re.search(r"\blist\b", s):
        return ActionMatch(
            intent_type="list_capabilities",
            operation=None,
            value=None,
            unit=None,
            confidence=0.95,
            method="regex",
            raw_text="list"
        )

    return None


# ============================================================================
# MAIN PARSER FUNCTION
# ============================================================================

def parse_action(text: str) -> Optional[ActionMatch]:
    """Parse action from text using regex patterns.

    Tries patterns in order of specificity:
    1. Transport commands (most specific keywords)
    2. Navigation commands (open/list)
    3. Relative changes (increase/decrease by)
    4. Absolute changes (set/change to)
    5. Toggle operations (mute/solo)

    Args:
        text: Input text (lowercase, typo-corrected)

    Returns:
        ActionMatch if found, None otherwise
    """
    # Try transport first (most specific keywords)
    result = parse_transport_command(text)
    if result:
        return result

    # Try navigation
    result = parse_navigation_command(text)
    if result:
        return result

    # Try relative changes (more specific than absolute)
    result = parse_relative_change(text)
    if result:
        return result

    # Try absolute changes
    result = parse_absolute_change(text)
    if result:
        return result

    # Try toggles
    result = parse_toggle_operation(text)
    if result:
        return result

    # No match found
    return None
