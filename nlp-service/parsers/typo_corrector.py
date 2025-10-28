"""Typo correction and ordinal word expansion for fallback parser."""

from __future__ import annotations

import re
from typing import Dict


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
    """Get typo correction map from config.

    Single source of truth: configs/app_config.json

    Returns:
        Dictionary mapping common typos to correct spellings.
        Returns empty dict if config unavailable (fail gracefully).
    """
    try:
        from server.config.app_config import get_typo_corrections as get_config_typos
        return get_config_typos() or {}
    except Exception:
        # Config unavailable - return empty dict
        # This should rarely happen in production
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
    for typo, correct in typo_map.items():
        q = re.sub(rf"\b{typo}\b", correct, q)

    return q
