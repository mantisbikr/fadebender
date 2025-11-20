#!/usr/bin/env python3
"""Audit typo corrections for bad mappings.

This script checks both app_config.json and Firestore for suspicious
typo corrections that are too different from each other.

Usage:
    python scripts/audit_typo_corrections.py
"""

import sys
import os
from pathlib import Path

# Add server path for imports
server_path = Path(__file__).parent.parent / "server"
sys.path.insert(0, str(server_path))

# Add nlp-service path
nlp_path = Path(__file__).parent.parent / "nlp-service"
sys.path.insert(0, str(nlp_path))


def levenshtein_distance(s1: str, s2: str) -> int:
    """Calculate Levenshtein distance between two strings."""
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)

    if len(s2) == 0:
        return len(s1)

    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row

    return previous_row[-1]


def is_valid_correction(typo: str, correction: str, max_distance: int = 3) -> tuple[bool, str]:
    """Check if a typo correction is valid.

    Returns:
        (is_valid, reason) - True if valid, False with reason if invalid
    """
    # Check Levenshtein distance
    distance = levenshtein_distance(typo, correction)
    if distance > max_distance:
        return False, f"Distance too large: {distance} > {max_distance}"

    # Reject single-letter corrections
    if len(correction) == 1:
        return False, "Single letter correction"

    # Reject digit-only corrections
    if correction.isdigit():
        return False, "Digit-only correction"

    # Check length ratio
    max_len = max(len(typo), len(correction))
    min_len = min(len(typo), len(correction))

    # Allow if one is a substring of the other
    is_substring = (correction in typo) or (typo in correction)

    if not is_substring and min_len < max_len * 0.7:
        return False, f"Length ratio too different: {min_len}/{max_len} = {min_len/max_len:.1%}"

    # Check character overlap
    typo_chars = set(typo.lower())
    correction_chars = set(correction.lower())
    shared = typo_chars & correction_chars

    min_char_len = min(len(typo_chars), len(correction_chars))
    if min_char_len > 0 and len(shared) / min_char_len < 0.3:
        return False, f"Too few shared characters: {len(shared)}/{min_char_len} = {len(shared)/min_char_len:.1%}"

    return True, "OK"


def audit_corrections(corrections: dict[str, str], source: str):
    """Audit typo corrections and print suspicious ones."""
    print(f"\n{'='*80}")
    print(f"Auditing {len(corrections)} corrections from {source}")
    print(f"{'='*80}\n")

    suspicious = []

    for typo, correction in sorted(corrections.items()):
        is_valid, reason = is_valid_correction(typo, correction)
        distance = levenshtein_distance(typo, correction)

        if not is_valid:
            suspicious.append((typo, correction, distance, reason))
            print(f"❌ SUSPICIOUS: '{typo}' → '{correction}' (distance={distance})")
            print(f"   Reason: {reason}\n")
        elif distance > 2:
            print(f"⚠️  BORDERLINE: '{typo}' → '{correction}' (distance={distance})")
            print(f"   Status: {reason}\n")

    if not suspicious:
        print("✅ All corrections look reasonable!\n")
    else:
        print(f"\n{'='*80}")
        print(f"Found {len(suspicious)} suspicious corrections that should be removed:")
        print(f"{'='*80}\n")
        for typo, correction, distance, reason in suspicious:
            print(f"  '{typo}' → '{correction}' ({reason})")


def main():
    print("Typo Correction Audit Tool")
    print("="*80)

    # Load from app_config.json
    try:
        from config.app_config import get_typo_corrections
        config_typos = get_typo_corrections() or {}
        print(f"\n✓ Loaded {len(config_typos)} corrections from app_config.json")
        audit_corrections(config_typos, "app_config.json")
    except Exception as e:
        print(f"\n✗ Failed to load app_config.json: {e}")

    # Load from Firestore
    try:
        from learning.typo_cache_store import get_typo_corrections as get_firestore_typos
        firestore_typos = get_firestore_typos() or {}
        print(f"\n✓ Loaded {len(firestore_typos)} corrections from Firestore")
        audit_corrections(firestore_typos, "Firestore")
    except Exception as e:
        print(f"\n✗ Failed to load Firestore corrections: {e}")


if __name__ == "__main__":
    main()
