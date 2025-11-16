"""Layer 1: Action/Value/Unit Parser

Extracts intent type, operation, value, and unit from text.
Independent of track/device context - purely focused on action patterns.

Extracted patterns from existing mixer_parser.py, transport_parser.py, and device_parser.py.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional
import re

# Fuzzy matching for action words using Damerau-Levenshtein distance
# (same approach as device_context_parser.py - no external dependencies)
FUZZY_AVAILABLE = True


def damerau_levenshtein(a: str, b: str) -> int:
    """Calculate Damerau-Levenshtein edit distance between two strings.

    Handles:
    - Insertions: "wat" → "what" (missing 'h')
    - Deletions: "seet" → "set" (extra 'e')
    - Substitutions: "incrase" → "increase" (wrong character)
    - Transpositions: "opne" → "open" (swapped characters)
    """
    n, m = len(a), len(b)
    if n == 0:
        return m
    if m == 0:
        return n

    dp = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(n + 1):
        dp[i][0] = i
    for j in range(m + 1):
        dp[0][j] = j

    for i in range(1, n + 1):
        for j in range(1, m + 1):
            cost = 0 if a[i - 1] == b[j - 1] else 1
            dp[i][j] = min(
                dp[i - 1][j] + 1,        # deletion
                dp[i][j - 1] + 1,        # insertion
                dp[i - 1][j - 1] + cost  # substitution
            )
            if i > 1 and j > 1 and a[i - 1] == b[j - 2] and a[i - 2] == b[j - 1]:
                dp[i][j] = min(dp[i][j], dp[i - 2][j - 2] + 1)  # transposition

    return dp[n][m]


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


# Canonical action word vocabulary (known with absolute confidence)
ACTION_WORDS = {
    # SET operations
    "set", "change", "adjust", "make",
    # RELATIVE operations
    "increase", "decrease", "raise", "lower",
    # TOGGLE operations
    "mute", "unmute", "solo", "unsolo",
    # GET queries
    "what", "how", "list", "who", "which",
    "show", "tell", "get", "check",  # Enhanced vocabulary
    # TRANSPORT
    "play", "stop", "loop",
    # NAVIGATION
    "open", "close", "pin", "unpin",
    "view",  # Enhanced vocabulary
}


def fuzzy_match_action_word(word: str) -> Optional[str]:
    """Fuzzy match a word against canonical action vocabulary using edit distance.

    Args:
        word: Word to match (e.g., "wat", "incrase", "seet")

    Returns:
        Canonical action word if match found, None otherwise

    Examples:
        >>> fuzzy_match_action_word("wat")
        "what"
        >>> fuzzy_match_action_word("incrase")
        "increase"
        >>> fuzzy_match_action_word("seet")
        "set"

    Edit distance thresholds (same as device_context_parser):
        - Words <= 4 chars: allow 1 edit
        - Words 5-7 chars: allow 2 edits
        - Words 8-10 chars: allow 3 edits
        - Words >= 11 chars: allow 4 edits
    """
    if not FUZZY_AVAILABLE:
        return None

    if not word or len(word) < 2:
        return None

    # Check protected words: parameters/entities that should NOT be fuzzy matched
    # to avoid ambiguous interpretations (e.g., "pan" should not match "pin")
    try:
        from server.config.app_config import get_protected_words
        protected = get_protected_words()
        if word.lower() in protected:
            return None  # Don't fuzzy match protected words
    except Exception:
        # If config unavailable, use minimal defaults
        if word.lower() in ("pan", "mute", "solo", "volume", "send"):
            return None

    # Already canonical
    if word in ACTION_WORDS:
        return word

    # Find best match using edit distance
    best_match = None
    best_distance = float('inf')

    for candidate in ACTION_WORDS:
        dist = damerau_levenshtein(word, candidate)

        # Check if within acceptable threshold (same logic as device_context_parser)
        if len(candidate) <= 4 and dist > 1:
            continue
        if 5 <= len(candidate) <= 7 and dist > 2:
            continue
        if 8 <= len(candidate) <= 10 and dist > 3:
            continue
        if len(candidate) >= 11 and dist > 4:
            continue

        # Update best match
        if dist < best_distance:
            best_distance = dist
            best_match = candidate

    return best_match


def normalize_action_words(text: str) -> str:
    """Normalize action words in text using fuzzy matching.

    Scans first 3 words (where action words typically appear) and
    corrects typos against canonical vocabulary.

    Args:
        text: Input text (e.g., "wat is track 1 volume")

    Returns:
        Text with action words corrected (e.g., "what is track 1 volume")
    """
    if not FUZZY_AVAILABLE:
        return text

    words = text.split()
    if not words:
        return text

    # Check first 3 words for action word typos
    for i in range(min(3, len(words))):
        word_lower = words[i].lower()
        canonical = fuzzy_match_action_word(word_lower)
        if canonical and canonical != word_lower:
            words[i] = canonical

    return " ".join(words)


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
            intent_type="relative_change",
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
# GET QUERY PATTERNS (what is/how many/list)
# ============================================================================

def parse_get_query(text: str) -> Optional[ActionMatch]:
    """Parse GET query commands: what is, how many, list, show, tell, get, check

    Examples:
        "what is track 1 volume"
        "what is return A reverb decay"
        "how many audio tracks"
        "list audio tracks"
        "show me track 1 volume"
        "tell me return A pan"
        "get track 1 volume"
        "check track 2 mute"
    """
    s = text.lower().strip()

    # GET queries: "what is...", "what's..."
    if re.search(r"\b(what\s+is|what's|whats)\b", s):
        return ActionMatch(
            intent_type="get_parameter",
            operation=None,
            value=None,
            unit=None,
            confidence=0.95,
            method="regex",
            raw_text="what is"
        )

    # Count queries: "how many..."
    if re.search(r"\bhow\s+many\b", s):
        return ActionMatch(
            intent_type="get_parameter",
            operation=None,
            value=None,
            unit=None,
            confidence=0.95,
            method="regex",
            raw_text="how many"
        )

    # List command: "list..."
    # Note: Target determination (tracks vs returns vs parameters) is handled by track_parser (Layer 2)
    # This layer just detects the "list" action
    if re.search(r"\blist\b", s):
        return ActionMatch(
            intent_type="list_capabilities",
            operation=None,
            value=None,  # No longer hardcoding "tracks" or "returns"
            unit=None,
            confidence=0.95,
            method="regex",
            raw_text="list"
        )

    # Who/which queries: "who sends to...", "which tracks..."
    if re.search(r"\b(who|which)\b", s):
        return ActionMatch(
            intent_type="get_parameter",
            operation=None,
            value=None,
            unit=None,
            confidence=0.95,
            method="regex",
            raw_text="who/which"
        )

    # Show queries: "show me...", "show..."
    if re.search(r"\bshow(\s+me)?\b", s):
        return ActionMatch(
            intent_type="get_parameter",
            operation=None,
            value=None,
            unit=None,
            confidence=0.95,
            method="regex",
            raw_text="show"
        )

    # Tell queries: "tell me..."
    if re.search(r"\btell(\s+me)?\b", s):
        return ActionMatch(
            intent_type="get_parameter",
            operation=None,
            value=None,
            unit=None,
            confidence=0.95,
            method="regex",
            raw_text="tell"
        )

    # Get queries: "get..." (direct retrieval)
    if re.search(r"\bget\b", s):
        return ActionMatch(
            intent_type="get_parameter",
            operation=None,
            value=None,
            unit=None,
            confidence=0.95,
            method="regex",
            raw_text="get"
        )

    # Check queries: "check..."
    if re.search(r"\bcheck\b", s):
        return ActionMatch(
            intent_type="get_parameter",
            operation=None,
            value=None,
            unit=None,
            confidence=0.95,
            method="regex",
            raw_text="check"
        )

    # Status queries: "is ... on/enabled" (GET, not toggle)
    # Examples: "is track 3 mute on", "is return B solo enabled"
    if re.search(r"\bis\s+.+?\s+(on|enabled|off|disabled)\b", s):
        return ActionMatch(
            intent_type="get_parameter",
            operation=None,
            value=None,
            unit=None,
            confidence=0.95,
            method="regex",
            raw_text="is ... on/enabled"
        )

    return None


# ============================================================================
# NAVIGATION PATTERNS (open)
# ============================================================================

def parse_navigation_command(text: str) -> Optional[ActionMatch]:
    """Parse navigation commands: open, view

    Examples:
        "open track 1"
        "open return A reverb"
        "open controls"
        "view track 1"
        "view return A"
    """
    s = text.lower().strip()

    # Open/view command
    if re.search(r"\b(open|close|pin|unpin|view)\b", s):
        return ActionMatch(
            intent_type="open_capabilities",
            operation=None,
            value=None,
            unit=None,
            confidence=0.95,
            method="regex",
            raw_text="open"
        )

    return None


# ============================================================================
# MAIN PARSER FUNCTION
# ============================================================================

def parse_action(text: str) -> Optional[ActionMatch]:
    """Parse action from text using regex patterns.

    Tries patterns in order of specificity:
    1. GET queries (what is/how many/list) - checked first to avoid false SET matches
    2. Transport commands (most specific keywords)
    3. Navigation commands (open/list)
    4. Relative changes (increase/decrease by)
    5. Absolute changes (set/change to)
    6. Toggle operations (mute/solo)

    Args:
        text: Input text (lowercase, typo-corrected)

    Returns:
        ActionMatch if found, None otherwise
    """
    # FIRST: Normalize action words using fuzzy matching
    # This catches "wat" → "what", "incrase" → "increase", etc.
    # Independent of LLM/nlp_config - uses known vocabulary
    text_normalized = normalize_action_words(text)

    # Try GET queries first (avoid "what is" being caught by other patterns)
    result = parse_get_query(text_normalized)
    if result:
        return result

    # Try transport (most specific keywords)
    result = parse_transport_command(text_normalized)
    if result:
        return result

    # Try navigation
    result = parse_navigation_command(text_normalized)
    if result:
        return result

    # Try relative changes (more specific than absolute)
    result = parse_relative_change(text_normalized)
    if result:
        return result

    # Try absolute changes
    result = parse_absolute_change(text_normalized)
    if result:
        return result

    # Try toggles
    result = parse_toggle_operation(text_normalized)
    if result:
        return result

    # No match found
    return None
