"""Typo learning module - learns corrections from LLM fallback successes.

When regex_first mode falls back to LLM and succeeds, this module detects
typo corrections and adds them to the dictionary for future fast lookups.

Example flow:
1. Query: "set track 1 volme to -20"
2. Regex: No match (unknown word "volme")
3. LLM: Corrects to "volume", returns intent
4. Learner: Detects "volme" → "volume", adds to dictionary
5. Next time: Typo corrector fixes "volme" → "volume" → Regex matches → Fast!
"""

from __future__ import annotations

import os
import re
from typing import Dict, Set, Tuple, List
from difflib import SequenceMatcher

from models.intent_types import Intent


def _levenshtein_distance(s1: str, s2: str) -> int:
    """Calculate Levenshtein distance between two strings."""
    if len(s1) < len(s2):
        return _levenshtein_distance(s2, s1)

    if len(s2) == 0:
        return len(s1)

    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            # Cost of insertions, deletions, or substitutions
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row

    return previous_row[-1]


def _extract_known_terms() -> Set[str]:
    """Extract known parameter/device terms from config for reference.

    Returns set of canonical terms that should NOT be treated as typos.
    """
    known_terms = set()

    # Import here to avoid circular dependency
    try:
        import sys
        import os
        # Add server path to import app_config
        server_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'server'))
        if server_path not in sys.path:
            sys.path.insert(0, server_path)

        from config.app_config import (
            get_mixer_param_aliases,
            get_device_param_aliases,
            get_device_type_aliases,
            get_device_qualifier_aliases,
        )

        # Add mixer params
        mixer_aliases = get_mixer_param_aliases()
        known_terms.update(mixer_aliases.keys())  # Aliases
        known_terms.update(mixer_aliases.values())  # Canonical names

        # Add device params
        device_aliases = get_device_param_aliases()
        known_terms.update(device_aliases.keys())
        known_terms.update(device_aliases.values())

        # Add device types
        device_types = get_device_type_aliases()
        for device_type, aliases in device_types.items():
            known_terms.add(device_type)
            known_terms.update(aliases)

        # Add device qualifiers
        device_qualifiers = get_device_qualifier_aliases()
        for device_type, qualifiers in device_qualifiers.items():
            for qualifier, aliases in qualifiers.items():
                known_terms.add(qualifier)
                known_terms.update(aliases)

    except Exception:
        # Fallback to common terms if import fails
        known_terms = {
            'volume', 'pan', 'mute', 'solo', 'send', 'return',
            'reverb', 'delay', 'eq', 'compressor', 'amp',
            'decay', 'feedback', 'rate', 'depth', 'mix', 'wet', 'dry',
            'frequency', 'gain', 'threshold', 'ratio', 'attack', 'release',
        }

    return known_terms


def _tokenize_query(query: str) -> List[str]:
    """Extract meaningful words from query, excluding common stop words.

    Args:
        query: Original user query

    Returns:
        List of lowercase tokens (excluding stop words and numbers)
    """
    # Stop words that don't need learning
    stop_words = {
        'set', 'make', 'change', 'adjust', 'get', 'what', 'is', 'the',
        'to', 'at', 'by', 'of', 'on', 'in', 'for', 'a', 'an',
        'track', 'return', 'device', 'plugin',
    }

    # Tokenize on whitespace and common delimiters
    tokens = re.findall(r'\b[a-z]+\b', query.lower())

    # Filter out stop words and very short tokens
    return [t for t in tokens if t not in stop_words and len(t) >= 3]


def _extract_intent_terms(intent: Intent) -> Set[str]:
    """Extract terms from intent that could be corrections of typos.

    Args:
        intent: LLM-generated intent dictionary

    Returns:
        Set of lowercase terms that appear in the intent
    """
    terms = set()

    # Extract parameter names from targets
    targets = intent.get('targets', [])
    for target in targets:
        if 'parameter' in target:
            param = target['parameter']
            # Check for None before calling .lower()
            if param is not None and isinstance(param, str):
                terms.update(param.lower().split())

        if 'plugin' in target:
            plugin = target['plugin']
            # Check for None before calling .lower()
            if plugin is not None and isinstance(plugin, str):
                terms.update(plugin.lower().split())

    return terms


def detect_typos(query: str, intent: Intent) -> Dict[str, str]:
    """Detect typos by comparing query tokens with intent terms.

    Finds query tokens that are:
    1. Not in known terms dictionary
    2. Similar to an intent term (edit distance ≤ 2)
    3. Different from that intent term

    Args:
        query: Original user query with potential typos
        intent: LLM-corrected intent result

    Returns:
        Dictionary mapping typo → correction (e.g., {"volme": "volume"})
    """
    # Disable learning if explicitly configured
    if os.getenv("DISABLE_TYPO_LEARNING", "").lower() in ("1", "true", "yes"):
        return {}

    typos = {}

    # Get tokens from query and intent
    query_tokens = _tokenize_query(query)
    intent_terms = _extract_intent_terms(intent)
    known_terms = _extract_known_terms()

    # Find potential typos
    for token in query_tokens:
        # Skip if this is already a known term
        if token in known_terms:
            continue

        # Check if similar to any intent term
        for term in intent_terms:
            if token == term:
                continue

            # Calculate similarity
            distance = _levenshtein_distance(token, term)

            # If close enough (distance ≤ 2) and not already known, it's likely a typo
            if distance <= 2 and len(token) >= 3:
                # Prefer correction with smaller distance
                if token not in typos or distance < _levenshtein_distance(token, typos[token]):
                    typos[token] = term

    return typos


def learn_from_llm_success(query: str, intent: Intent, persist: bool = True) -> Dict[str, str]:
    """Main entry point - detect and optionally persist typo corrections.

    This function is called when LLM fallback succeeds in regex_first mode.
    It detects typos and returns them for potential addition to the config.

    Args:
        query: Original user query
        intent: LLM-corrected intent result
        persist: If True (default), save corrections to app_config.json

    Returns:
        Dictionary of detected typo corrections
    """
    detected_typos = detect_typos(query, intent)

    if detected_typos:
        # Log for monitoring (optional)
        log_enabled = os.getenv("LOG_TYPO_LEARNING", "true").lower() in ("1", "true", "yes")
        if log_enabled:
            print(f"[TYPO LEARNING] Detected corrections: {detected_typos}")

        # Optionally persist to config (non-blocking, best-effort)
        if persist:
            try:
                # Import here to avoid any circular dependencies at module load time
                from learning.typo_persister import persist_typos
                # Run persistence in a try-except to never block
                persist_typos(detected_typos)
            except ImportError:
                # Persistence module not available - skip silently
                if log_enabled:
                    print(f"[TYPO LEARNING] Persistence not available (import error)")
            except Exception as e:
                # Non-fatal - learning still works, just not persisted
                if log_enabled:
                    print(f"[TYPO LEARNING] Failed to persist (non-blocking): {e}")

    return detected_typos
