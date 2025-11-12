"""Layer 2: Track/Return Parser

Extracts track/return/master references from text.
Independent of parameter or device context - purely focused on target location.

Extracted patterns from existing mixer_parser.py.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional
import re


@dataclass
class TrackMatch:
    """Result from track/return parsing."""
    domain: str              # "track", "return", "master"
    index: Optional[int]     # Track number (0-indexed) or Return index (0=A, 1=B, etc.), None for master
    reference: str           # Original reference string ("Track 1", "Return A", "Master")
    confidence: float        # 0.0-1.0
    method: str             # "regex", "llm_fallback"


# ============================================================================
# TRACK PATTERNS
# ============================================================================

def parse_track_reference(text: str) -> Optional[TrackMatch]:
    """Parse track references: 'track 1', 'track 12', etc.

    Examples:
        "track 1" → TrackMatch(domain="track", index=0, reference="Track 1")
        "track 5" → TrackMatch(domain="track", index=4, reference="Track 5")
    """
    pattern = r"\btrack\s+(\d+)\b"
    match = re.search(pattern, text, re.IGNORECASE)

    if match:
        track_num = int(match.group(1))

        # Convert to 0-indexed
        index = track_num - 1

        return TrackMatch(
            domain="track",
            index=index,
            reference=f"Track {track_num}",
            confidence=0.95,
            method="regex"
        )

    return None


# ============================================================================
# RETURN PATTERNS
# ============================================================================

def parse_return_reference(text: str) -> Optional[TrackMatch]:
    """Parse return references: 'return A', 'return B', etc.

    Examples:
        "return A" → TrackMatch(domain="return", index=0, reference="Return A")
        "return B" → TrackMatch(domain="return", index=1, reference="Return B")
        "return a" → TrackMatch(domain="return", index=0, reference="Return A")  # Case insensitive
    """
    pattern = r"\breturn\s+([a-d])\b"
    match = re.search(pattern, text, re.IGNORECASE)

    if match:
        return_letter = match.group(1).upper()

        # Convert letter to 0-indexed number (A=0, B=1, C=2, D=3)
        index = ord(return_letter) - ord('A')

        return TrackMatch(
            domain="return",
            index=index,
            reference=f"Return {return_letter}",
            confidence=0.95,
            method="regex"
        )

    return None


# ============================================================================
# MASTER PATTERNS
# ============================================================================

def parse_master_reference(text: str) -> Optional[TrackMatch]:
    """Parse master references: 'master'

    Examples:
        "master" → TrackMatch(domain="master", index=None, reference="Master")
        "set master volume to -3" → TrackMatch(domain="master", index=None, reference="Master")
    """
    pattern = r"\bmaster\b"
    match = re.search(pattern, text, re.IGNORECASE)

    if match:
        return TrackMatch(
            domain="master",
            index=None,
            reference="Master",
            confidence=0.95,
            method="regex"
        )

    return None


# ============================================================================
# MAIN PARSER FUNCTION
# ============================================================================

def parse_track(text: str) -> Optional[TrackMatch]:
    """Parse track/return/master reference from text.

    Tries patterns in order:
    1. Track references (track 1, track 2, ...)
    2. Return references (return A, return B, ...)
    3. Master reference (master)

    Args:
        text: Input text (lowercase recommended but not required - patterns are case-insensitive)

    Returns:
        TrackMatch if found, None otherwise
    """
    # Try track first (most specific)
    result = parse_track_reference(text)
    if result:
        return result

    # Try return
    result = parse_return_reference(text)
    if result:
        return result

    # Try master
    result = parse_master_reference(text)
    if result:
        return result

    # No match found
    return None
