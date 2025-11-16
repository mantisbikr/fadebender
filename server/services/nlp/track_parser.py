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
    index: Optional[int]     # Track number (0-indexed) or Return index (0=A, 1=B, etc.), None for master or collections
    reference: str           # Original reference string ("Track 1", "Return A", "Master", "tracks", "returns")
    confidence: float        # 0.0-1.0
    method: str             # "regex", "llm_fallback"
    filter: Optional[str] = None  # Optional filter: "audio", "midi" for collection queries


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
# COLLECTION/PLURAL PATTERNS (for list commands)
# ============================================================================

def parse_track_collection(text: str) -> Optional[TrackMatch]:
    """Parse plural track references: 'tracks', 'audio tracks', 'midi tracks', 'all tracks'.

    Used for list commands like "list tracks", "list audio tracks", etc.

    Examples:
        "list tracks" → TrackMatch(domain="track", index=None, reference="tracks", filter=None)
        "list audio tracks" → TrackMatch(domain="track", index=None, reference="tracks", filter="audio")
        "list midi tracks" → TrackMatch(domain="track", index=None, reference="tracks", filter="midi")
        "list all tracks" → TrackMatch(domain="track", index=None, reference="tracks", filter=None)
    """
    # Pattern: (all)? (audio|midi)? tracks - but NOT "return tracks"
    # Negative lookbehind to exclude "return" before "tracks"
    pattern = r"\b(?:all\s+)?(?:(audio|midi)\s+)?(?<!return\s)tracks\b"
    match = re.search(pattern, text, re.IGNORECASE)

    if match:
        filter_type = match.group(1).lower() if match.group(1) else None
        return TrackMatch(
            domain="track",
            index=None,
            reference="tracks",
            confidence=0.95,
            method="regex",
            filter=filter_type
        )

    return None


def parse_return_collection(text: str) -> Optional[TrackMatch]:
    """Parse plural return references: 'returns', 'return tracks', 'all returns', 'all return tracks'.

    Used for list commands like "list returns", "list return tracks", etc.

    Examples:
        "list returns" → TrackMatch(domain="return", index=None, reference="returns")
        "list return tracks" → TrackMatch(domain="return", index=None, reference="returns")
        "list all returns" → TrackMatch(domain="return", index=None, reference="returns")
        "list all return tracks" → TrackMatch(domain="return", index=None, reference="returns")
    """
    # Pattern 1: (all)? return tracks - requires "return" before "tracks"
    pattern1 = r"\b(?:all\s+)?return\s+tracks\b"
    # Pattern 2: (all)? returns - matches "returns" (with or without "all")
    pattern2 = r"\b(?:all\s+)?returns\b"

    match = re.search(pattern1, text, re.IGNORECASE) or re.search(pattern2, text, re.IGNORECASE)

    if match:
        return TrackMatch(
            domain="return",
            index=None,
            reference="returns",
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
    1. Specific track references (track 1, track 2, ...) - most specific
    2. Specific return references (return A, return B, ...)
    3. Master reference (master)
    4. Track collections (tracks, audio tracks, midi tracks) - for list commands
    5. Return collections (returns, return tracks) - for list commands

    Args:
        text: Input text (lowercase recommended but not required - patterns are case-insensitive)

    Returns:
        TrackMatch if found, None otherwise
    """
    # Try specific track first (track 1, track 2) - most specific
    result = parse_track_reference(text)
    if result:
        return result

    # Try specific return (return A, return B)
    result = parse_return_reference(text)
    if result:
        return result

    # Try master
    result = parse_master_reference(text)
    if result:
        return result

    # Try track collections (tracks, audio tracks, midi tracks)
    result = parse_track_collection(text)
    if result:
        return result

    # Try return collections (returns, return tracks)
    result = parse_return_collection(text)
    if result:
        return result

    # No match found
    return None
