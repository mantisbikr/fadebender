#!/usr/bin/env python3
"""Test script for typo learning system.

This script tests the phase 2 learning system that detects and persists typos
when LLM fallback succeeds in regex_first mode.
"""

import os
import sys

# Add nlp-service to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'nlp-service'))

# Disable persistence for testing (we'll verify detection only)
os.environ['DISABLE_TYPO_PERSISTENCE'] = '1'
os.environ['LOG_TYPO_LEARNING'] = '1'

from learning.typo_learner import detect_typos
from models.intent_types import Intent


def test_typo_detection():
    """Test typo detection with various examples."""

    test_cases = [
        {
            'name': 'Volume typo (volme)',
            'query': 'set track 1 volme to -20',
            'intent': {
                'intent': 'set_parameter',
                'targets': [{'track': 'Track 1', 'parameter': 'volume'}],
                'operation': {'value': -20},
            },
            'expected': {'volme': 'volume'}
        },
        {
            'name': 'Decay typo (dcay)',
            'query': 'set return A reverb dcay to 2 s',
            'intent': {
                'intent': 'set_parameter',
                'targets': [{'track': 'Return A', 'plugin': 'reverb', 'parameter': 'decay'}],
                'operation': {'value': 2, 'unit': 's'},
            },
            'expected': {'dcay': 'decay'}
        },
        {
            'name': 'Panning typo (paning) - distance too far',
            'query': 'set track 2 paning to 50% right',
            'intent': {
                'intent': 'set_parameter',
                'targets': [{'track': 'Track 2', 'parameter': 'pan'}],
                'operation': {'value': 0.5},
            },
            'expected': {}  # Distance=3, exceeds threshold of 2 (correct behavior - avoid false positives)
        },
        {
            'name': 'Multiple typos (vilme, tack)',
            'query': 'set tack 1 vilme to -20 dB',
            'intent': {
                'intent': 'set_parameter',
                'targets': [{'track': 'Track 1', 'parameter': 'volume'}],
                'operation': {'value': -20, 'unit': 'dB'},
            },
            'expected': {'vilme': 'volume'}  # Note: 'tack' won't be detected as it's a stop word
        },
        {
            'name': 'No typos (correct query)',
            'query': 'set track 1 volume to -20',
            'intent': {
                'intent': 'set_parameter',
                'targets': [{'track': 'Track 1', 'parameter': 'volume'}],
                'operation': {'value': -20},
            },
            'expected': {}
        },
        {
            'name': 'Reverb typo (revreb)',
            'query': 'set return A revreb decay to 2 s',
            'intent': {
                'intent': 'set_parameter',
                'targets': [{'track': 'Return A', 'plugin': 'reverb', 'parameter': 'decay'}],
                'operation': {'value': 2, 'unit': 's'},
            },
            'expected': {'revreb': 'reverb'}
        },
    ]

    print("=" * 80)
    print("TYPO LEARNING SYSTEM TEST")
    print("=" * 80)
    print()

    passed = 0
    failed = 0

    for i, test in enumerate(test_cases, 1):
        print(f"Test {i}: {test['name']}")
        print(f"  Query: {test['query']}")
        print(f"  Expected: {test['expected']}")

        detected = detect_typos(test['query'], test['intent'])
        print(f"  Detected: {detected}")

        # Check if detected matches expected
        if detected == test['expected']:
            print("  Result: ✓ PASS")
            passed += 1
        else:
            print("  Result: ✗ FAIL")
            failed += 1

        print()

    print("=" * 80)
    print(f"SUMMARY: {passed} passed, {failed} failed out of {passed + failed} tests")
    print("=" * 80)

    return failed == 0


def test_levenshtein():
    """Test Levenshtein distance calculation."""
    from learning.typo_learner import _levenshtein_distance

    test_cases = [
        ('volme', 'volume', 1),  # One insertion
        ('dcay', 'decay', 1),     # One insertion
        ('paning', 'pan', 3),     # Three deletions
        ('vilme', 'volume', 2),   # One substitution + one insertion
        ('reverb', 'reverb', 0),  # Exact match
        ('revreb', 'reverb', 2),  # Two transpositions
    ]

    print("\n" + "=" * 80)
    print("LEVENSHTEIN DISTANCE TEST")
    print("=" * 80)
    print()

    passed = 0
    failed = 0

    for s1, s2, expected in test_cases:
        distance = _levenshtein_distance(s1, s2)
        result = "✓ PASS" if distance == expected else "✗ FAIL"
        print(f"{s1} → {s2}: distance={distance}, expected={expected} {result}")

        if distance == expected:
            passed += 1
        else:
            failed += 1

    print()
    print("=" * 80)
    print(f"SUMMARY: {passed} passed, {failed} failed out of {passed + failed} tests")
    print("=" * 80)

    return failed == 0


if __name__ == '__main__':
    success = True

    # Test Levenshtein distance
    if not test_levenshtein():
        success = False

    # Test typo detection
    if not test_typo_detection():
        success = False

    sys.exit(0 if success else 1)
