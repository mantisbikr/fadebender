"""
Volume command parsing utilities.
Handles various volume command formats and converts them to Live API calls.
"""

import re
from typing import Optional, Dict, Any
try:
    from .volume_utils import db_to_live_float
except ImportError:
    from volume_utils import db_to_live_float


def parse_volume_command(text: str) -> Optional[Dict[str, Any]]:
    """
    Parse volume command from text input.

    Supports formats like:
    - "set track 1 volume to -15"
    - "set track 1 volume to -15.0"
    - "set track 1 volume to -15 dB"
    - "set track 1 volume to -15.0 dB"
    - "set track 1 vol to -5.5"
    - "set track 1 vol to -5.5db"

    Args:
        text: Input text to parse

    Returns:
        Dict with parsed command or None if no match
        Format: {
            "track_index": int,
            "db_value": float,
            "live_float": float,
            "raw_value": str,
            "matched_text": str
        }
    """
    text_lower = text.strip().lower()

    # Pattern to match volume commands with optional dB suffix
    # Supports: integers, decimals, with/without spaces before dB suffix
    pattern = r'\bset\s+track\s+(\d+)\s+vol(?:ume)?\s+to\s+(-?\d+(?:\.\d+)?)\s*(?:db|dB|DB)?\b'

    match = re.search(pattern, text_lower)
    if not match:
        return None

    track_index = int(match.group(1))
    raw_value = match.group(2)
    db_value = float(raw_value)

    # Clamp to valid dB range
    db_clamped = max(-60.0, min(6.0, db_value))

    # Convert to Live API float value
    live_float = db_to_live_float(db_clamped)

    return {
        "track_index": track_index,
        "db_value": db_clamped,
        "live_float": live_float,
        "raw_value": raw_value,
        "matched_text": match.group(0),
        "warning": db_value > 0.0
    }


if __name__ == "__main__":
    # Test the volume parser
    test_cases = [
        "set track 1 volume to -15",
        "set track 1 volume to -15.0",
        "set track 1 volume to -15 dB",
        "set track 1 volume to -15.0 dB",
        "set track 1 vol to -5.5",
        "set track 1 vol to -5.5db",
        "set track 1 volume to -7.0",
        "set track 1 volume to -10.0 dB",
        "set track 2 vol to -3.5 DB",
        "increase track 1 volume",  # Should not match
        "set track 1 volume to loud",  # Should not match
    ]

    print("Testing volume command parser:")
    print("=" * 60)

    for test in test_cases:
        result = parse_volume_command(test)
        if result:
            print(f"✓ '{test}'")
            print(f"  → Track: {result['track_index']}")
            print(f"  → dB: {result['db_value']}")
            print(f"  → Live Float: {result['live_float']:.4f}")
            print(f"  → Raw: '{result['raw_value']}'")
            print(f"  → Matched: '{result['matched_text']}'")
            if result['warning']:
                print(f"  → ⚠️  Warning: >0 dB may clip")
            print()
        else:
            print(f"✗ '{test}' → NO MATCH")
            print()