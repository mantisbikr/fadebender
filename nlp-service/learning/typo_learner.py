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
    # Stop words that don't need learning (including action words!)
    stop_words = {
        # Query structure words
        'set', 'make', 'change', 'adjust', 'get', 'what', 'is', 'the',
        'to', 'at', 'by', 'of', 'on', 'in', 'for', 'a', 'an', 'and',
        # Target types (should never be learned as typos)
        'track', 'return', 'device', 'plugin', 'master',
        # Action words (critical: never learn these!)
        'mute', 'unmute', 'solo', 'unsolo', 'enable', 'disable',
        'bypass', 'unbypass', 'arm', 'unarm',
        # Relative change verbs (CRITICAL: must never be mapped to parameters!)
        'increase', 'decrease', 'reduce', 'add', 'subtract',
        'up', 'down', 'raise', 'lower', 'boost', 'cut',
        'louder', 'quieter', 'more', 'less',
        # Toggle verbs
        'toggle', 'flip', 'switch',
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
        # Extract parameter name (e.g., "volume", "pan", "mute")
        if 'parameter' in target:
            param = target['parameter']
            # Check for None before calling .lower()
            if param is not None and isinstance(param, str):
                terms.update(param.lower().split())

        # Extract plugin name (e.g., "reverb", "delay")
        if 'plugin' in target:
            plugin = target['plugin']
            # Check for None before calling .lower()
            if plugin is not None and isinstance(plugin, str):
                terms.update(plugin.lower().split())

        # Extract target names (e.g., "Track 1" → "track", "Return A" → "return")
        # This helps learn "rack" → "track", not "rack" → "mute"
        for key in ['track', 'return', 'device']:
            if key in target:
                target_name = target[key]
                if target_name is not None and isinstance(target_name, str):
                    # Extract just the type word (e.g., "Track 1" → "track")
                    words = target_name.lower().split()
                    terms.update(words)

    return terms


def _is_valid_correction(typo: str, correction: str) -> bool:
    """Validate that a typo correction is sensible, not garbage.

    Rejects corrections that are likely LLM hallucinations or parsing errors.

    Args:
        typo: The original word (potential typo)
        correction: The proposed correction

    Returns:
        True if the correction is valid, False if it's garbage

    Examples of INVALID corrections:
        - "freq" → "a" (single letter correction)
        - "from" → "1" (single digit correction)
        - "filter" → "freq" (unrelated short word)
        - "in filter freq" → "in freq a" (corrupted multi-word)

    Examples of VALID corrections:
        - "volme" → "volume" (legitimate typo)
        - "paning" → "pan" (legitimate typo)
        - "reverbb" → "reverb" (legitimate typo)
    """
    # Reject single-letter corrections (almost never legitimate)
    if len(correction) == 1:
        return False

    # Reject single-digit corrections (numbers are not corrections)
    if correction.isdigit() and len(correction) == 1:
        return False

    # Reject if correction contains only digits
    if correction.isdigit():
        return False

    # Reject if typo contains spaces (multi-word) but correction doesn't (or vice versa)
    # This catches "in filter freq" → "in freq a" type corruptions
    typo_words = typo.split()
    correction_words = correction.split()

    if len(typo_words) > 1 or len(correction_words) > 1:
        # For multi-word phrases, reject if word count changes significantly
        # This prevents "in filter freq" → "a" type corruption
        if len(correction_words) < len(typo_words) - 1:  # Lost more than 1 word
            return False

    # Reject corrections that are much shorter than the typo (likely truncation errors)
    # Example: "filter" → "a" (6 chars → 1 char)
    if len(typo) >= 5 and len(correction) <= 2:
        return False

    # Reject if length ratio is too different UNLESS one is a substring of the other
    # Example: "filter" (6) → "freq" (4) = 67% which should be rejected
    # Example: "paning" (6) → "pan" (3) = 50% but "pan" is substring, so ACCEPT
    # Example: "volme" (5) → "volume" (6) = 83% which should be accepted
    # Example: "parameter" (9) → "x" (1) = 11% which is clearly wrong
    max_len = max(len(typo), len(correction))
    min_len = min(len(typo), len(correction))

    # Allow if one is a substring of the other (suffix/prefix removal)
    is_substring = (correction in typo) or (typo in correction)

    if not is_substring and min_len < max_len * 0.7:  # Less than 70% and not substring
        return False

    # Reject if the correction is completely different (no shared characters)
    # This catches completely unrelated "corrections"
    typo_chars = set(typo.lower())
    correction_chars = set(correction.lower())
    shared = typo_chars & correction_chars

    # If less than 30% character overlap, likely not a typo
    min_len = min(len(typo_chars), len(correction_chars))
    if min_len > 0 and len(shared) / min_len < 0.3:
        return False

    return True


def detect_typos(query: str, intent: Intent, suspected_typos: List[str] | None = None) -> Dict[str, str]:
    """Detect typos by comparing query tokens with intent terms.

    Prioritizes suspected typos (words that failed regex matching) for precise detection,
    then falls back to fuzzy matching for any remaining unknown words.

    Args:
        query: Original user query with potential typos
        intent: LLM-corrected intent result
        suspected_typos: Optional list of words that failed regex matching (e.g., ["paning"])

    Returns:
        Dictionary mapping typo → correction (e.g., {"paning": "pan", "volme": "volume"})

    Examples:
        With suspected typos (precise):
        >>> detect_typos("set track 2 paning to left", intent, ["paning"])
        {"paning": "pan"}

        Without suspected typos (fuzzy fallback):
        >>> detect_typos("set track 1 volme to -20", intent)
        {"volme": "volume"}
    """
    # Disable learning if explicitly configured
    if os.getenv("DISABLE_TYPO_LEARNING", "").lower() in ("1", "true", "yes"):
        return {}

    typos = {}
    intent_terms = _extract_intent_terms(intent)
    known_terms = _extract_known_terms()

    # PRIORITY 1: Check suspected typos directly (precise detection)
    if suspected_typos:
        for suspected in suspected_typos:
            suspected_lower = suspected.lower()

            # Skip if already a known term
            if suspected_lower in known_terms:
                continue

            # Find best match in intent terms (no distance threshold for suspected words!)
            best_match = None
            best_distance = float('inf')

            for term in intent_terms:
                if suspected_lower == term:
                    continue

                distance = _levenshtein_distance(suspected_lower, term)

                # For suspected typos, be more lenient (distance ≤ 4 instead of 2)
                # This catches "paning" → "pan" (distance 3)
                if distance <= 4 and distance < best_distance:
                    best_match = term
                    best_distance = distance

            if best_match:
                typos[suspected_lower] = best_match

    # PRIORITY 2: Fuzzy matching for any remaining unknown words (fallback)
    query_tokens = _tokenize_query(query)

    for token in query_tokens:
        # Skip if already detected as suspected typo
        if token in typos:
            continue

        # Skip if this is already a known term
        if token in known_terms:
            continue

        # Check if similar to any intent term (strict threshold)
        for term in intent_terms:
            if token == term:
                continue

            distance = _levenshtein_distance(token, term)

            # If close enough (distance ≤ 2) and not already known, it's likely a typo
            if distance <= 2 and len(token) >= 3:
                # Prefer correction with smaller distance
                if token not in typos or distance < _levenshtein_distance(token, typos[token]):
                    typos[token] = term

    # VALIDATION: Filter out garbage corrections before returning
    validated_typos = {
        typo: correction
        for typo, correction in typos.items()
        if _is_valid_correction(typo, correction)
    }

    # Log rejected corrections for debugging
    rejected = set(typos.keys()) - set(validated_typos.keys())
    if rejected and os.getenv("LOG_TYPO_LEARNING", "true").lower() in ("1", "true", "yes"):
        for typo in rejected:
            print(f"[TYPO LEARNING] REJECTED garbage correction: '{typo}' → '{typos[typo]}'")

    return validated_typos


def learn_from_llm_success(
    query: str,
    intent: Intent,
    suspected_typos: List[str] | None = None,
    persist: bool = True
) -> Dict[str, str]:
    """Main entry point - detect and optionally persist typo corrections.

    This function is called when LLM fallback succeeds in regex_first mode.
    It detects typos and returns them for potential addition to the config.

    Args:
        query: Original user query
        intent: LLM-corrected intent result
        suspected_typos: Optional list of words that failed regex matching
        persist: If True (default), save corrections to app_config.json

    Returns:
        Dictionary of detected typo corrections
    """
    detected_typos = detect_typos(query, intent, suspected_typos)

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
