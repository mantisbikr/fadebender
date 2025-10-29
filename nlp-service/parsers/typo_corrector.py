"""Typo correction and ordinal word expansion for fallback parser."""

from __future__ import annotations

import re
from typing import Dict

# Import typo sources at module level (avoid repeated imports)
_firestore_typos = None
_config_typos = None

try:
    from learning.typo_cache_store import get_typo_corrections as _firestore_typos
except Exception:
    pass

try:
    from server.config.app_config import get_typo_corrections as _config_typos
except Exception:
    pass


# Ordinal word mapping for device selection (first..tenth)
ORDINAL_WORD_MAP = {
    'first': '1',
    'second': '2',
    'third': '3',
    'fourth': '4',
    'fifth': '5',
    'sixth': '6',
    'seventh': '7',
    'eighth': '8',
    'ninth': '9',
    'tenth': '10'
}


def get_typo_corrections() -> Dict[str, str]:
    """Get typo correction map from Firestore with TTL caching.

    Single source of truth: Firestore (nlp_config/typo_corrections)
    Fallback: configs/app_config.json if Firestore unavailable

    Returns:
        Dictionary mapping common typos to correct spellings.
        Returns empty dict if both sources unavailable (fail gracefully).
    """
    # Primary: Firestore with TTL cache (fast in-memory reads)
    if _firestore_typos:
        try:
            return _firestore_typos() or {}
        except Exception:
            pass

    # Fallback: Local config file
    if _config_typos:
        try:
            return _config_typos() or {}
        except Exception:
            pass

    # Both sources failed
    return {}


def apply_typo_corrections(query: str) -> str:
    """Apply typo corrections and expand ordinal words.

    Args:
        query: User query string to correct

    Returns:
        Corrected query string with typos fixed and ordinals expanded

    Examples:
        >>> apply_typo_corrections("set tack 1 vilme to -6")
        'set track 1 vilme to -6'
        >>> apply_typo_corrections("set first reverb decay to 2s")
        'set 1 reverb decay to 2s'
    """
    q = query.lower().strip()

    # Expand ordinal words (first → 1, second → 2, etc.)
    for word, digit in ORDINAL_WORD_MAP.items():
        q = re.sub(rf"\b{word}\b", digit, q)

    # Apply typo corrections
    typo_map = get_typo_corrections()

    # Debug logging
    import os
    if os.getenv("DEBUG_TYPO_CORRECTION", "").lower() in ("1", "true", "yes"):
        print(f"[TYPO CORRECTOR] Loaded {len(typo_map)} corrections")
        if "pain" in query.lower():
            print(f"[TYPO CORRECTOR] Query contains 'pain', checking corrections...")
            print(f"[TYPO CORRECTOR] 'pain' in typo_map: {'pain' in typo_map}")
            if 'pain' in typo_map:
                print(f"[TYPO CORRECTOR] Will correct 'pain' → '{typo_map['pain']}'")

    for typo, correct in typo_map.items():
        old_q = q
        q = re.sub(rf"\b{typo}\b", correct, q)
        if old_q != q and os.getenv("DEBUG_TYPO_CORRECTION", "").lower() in ("1", "true", "yes"):
            print(f"[TYPO CORRECTOR] Applied: '{typo}' → '{correct}'")

    return q
