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
    """Get typo correction map (config-driven with fallback).

    Returns:
        Dictionary mapping common typos to correct spellings.
    """
    try:
        from server.config.app_config import get_typo_corrections as get_config_typos
        return get_config_typos() or _get_default_typo_map()
    except Exception:
        return _get_default_typo_map()


def _get_default_typo_map() -> Dict[str, str]:
    """Default typo corrections when config is unavailable.

    Returns:
        Dictionary of common typos and their corrections.
    """
    return {
        'retrun': 'return',
        'retun': 'return',
        'revreb': 'reverb',
        'reverbb': 'reverb',
        'revebr': 'reverb',
        'reverv': 'reverb',
        'strereo': 'stereo',
        'streo': 'stereo',
        'stere': 'stereo',
        'tack': 'track',
        'trck': 'track',
        'trac': 'track',
        'sennd': 'send',
        'snd': 'send',
    }


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
