"""Regex-based parsing executor."""

from __future__ import annotations

import re
from typing import Dict, Any, List, Set

from parsers import apply_typo_corrections, parse_mixer_command, parse_device_command
from execution.response_builder import build_question_response


def _extract_known_terms_fast() -> Set[str]:
    """Extract known terms from config for typo detection.

    Returns set of canonical terms that should NOT be treated as typos.
    Optimized version that caches result.
    """
    # Use the same extraction as typo_learner but cache it
    try:
        from learning.typo_learner import _extract_known_terms
        return _extract_known_terms()
    except Exception:
        # Fallback to common terms
        return {
            'volume', 'pan', 'mute', 'solo', 'send', 'return', 'track',
            'reverb', 'delay', 'eq', 'compressor', 'amp', 'chorus', 'flanger', 'phaser',
            'decay', 'feedback', 'rate', 'depth', 'mix', 'wet', 'dry',
            'frequency', 'gain', 'threshold', 'ratio', 'attack', 'release',
            'set', 'get', 'what', 'is', 'the', 'to', 'at', 'by', 'of', 'on',
        }


def _extract_suspected_typos(query: str) -> List[str]:
    """Extract words from query that are not in known terms (suspected typos).

    Args:
        query: Original user query

    Returns:
        List of words that don't match known terms (potential typos)

    Examples:
        >>> _extract_suspected_typos("set track 2 paning to left")
        ['paning']
        >>> _extract_suspected_typos("set track 1 volme to -20")
        ['volme']
    """
    # Stop words that should never be treated as typos
    stop_words = {
        # Query structure words
        'set', 'make', 'change', 'adjust', 'get', 'what', 'is', 'the',
        'to', 'at', 'by', 'of', 'on', 'in', 'for', 'a', 'an', 'and',
        # Target types
        'track', 'return', 'device', 'plugin',
        # Action words (critical: never treat these as typos!)
        'mute', 'unmute', 'solo', 'unsolo', 'enable', 'disable',
        'bypass', 'unbypass', 'arm', 'unarm',
        # Directional words
        'left', 'right', 'center',
        # Ordinals (though converted to numbers)
        'first', 'second', 'third', 'fourth', 'fifth',
    }

    known_terms = _extract_known_terms_fast()

    # Tokenize query (extract alphabetic words)
    tokens = re.findall(r'\b[a-z]+\b', query.lower())

    # Find words not in known terms or stop words
    suspected = []
    for token in tokens:
        if token not in known_terms and token not in stop_words and len(token) >= 3:
            suspected.append(token)

    return suspected


def try_regex_parse(
    query: str,
    error_msg: str,
    model_preference: str | None
) -> tuple[Dict[str, Any] | None, List[str]]:
    """Try regex-based parsing.

    Args:
        query: User query text
        error_msg: Error message from previous attempts
        model_preference: User's model preference

    Returns:
        Tuple of (Intent dict if matched or None, list of suspected typo words)
        - If parsing succeeds: (intent_dict, [])
        - If parsing fails: (None, ['suspected', 'typo', 'words'])
    """
    # Apply typo corrections and expand ordinal words
    q = apply_typo_corrections(query)

    # Try mixer commands first (most common: volume, pan, solo, mute, sends)
    result = parse_mixer_command(q, query, error_msg, model_preference)
    if result:
        return result, []

    # Try device commands (reverb, delay, compressor, etc.)
    result = parse_device_command(q, query, error_msg, model_preference)
    if result:
        return result, []

    # Questions about problems (treat as help-style queries)
    if any(phrase in q for phrase in [
        "too soft", "too quiet", "can't hear", "how to", "what does",
        "weak", "thin", "muddy", "boomy", "harsh", "dull"
    ]):
        return build_question_response(query, error_msg, model_preference), []

    # No match - extract suspected typos for learning
    suspected_typos = _extract_suspected_typos(query)
    return None, suspected_typos
