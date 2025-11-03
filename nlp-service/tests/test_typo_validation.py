#!/usr/bin/env python3
"""Test typo correction validation to prevent garbage corrections."""

import sys
import os

# Add nlp-service to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from learning.typo_learner import _is_valid_correction


def test_validation():
    """Test that validation rejects garbage corrections and accepts legitimate ones."""

    print("Testing Typo Correction Validation")
    print("=" * 60)
    print()

    # Test cases: (typo, correction, should_accept, description)
    test_cases = [
        # GARBAGE corrections (should REJECT)
        ("freq", "a", False, "Single letter correction"),
        ("from", "1", False, "Single digit correction"),
        ("filter", "freq", False, "Unrelated short words (< 30% overlap)"),
        ("hello", "123", False, "Correction is all digits"),
        ("parameter", "x", False, "Long word → single letter"),
        ("reverb", "xyz", False, "Completely different words"),

        # VALID corrections (should ACCEPT)
        ("volme", "volume", True, "Legitimate typo (1 char diff)"),
        ("paning", "pan", True, "Legitimate typo (suffix removed)"),
        ("reverbb", "reverb", True, "Double letter typo"),
        ("dela", "delay", True, "Missing letter typo"),
        ("compres", "compress", True, "Truncated word"),
        ("revreb", "reverb", True, "Transposed letters"),
        ("feedbak", "feedback", True, "Missing letter"),
        ("distorion", "distortion", True, "Missing letter"),
    ]

    passed = 0
    failed = 0

    for typo, correction, should_accept, description in test_cases:
        result = _is_valid_correction(typo, correction)
        status = "✓ PASS" if result == should_accept else "✗ FAIL"

        if result == should_accept:
            passed += 1
            print(f"{status}: '{typo}' → '{correction}'")
            print(f"         {description}")
        else:
            failed += 1
            expected = "ACCEPT" if should_accept else "REJECT"
            actual = "ACCEPTED" if result else "REJECTED"
            print(f"{status}: '{typo}' → '{correction}'")
            print(f"         {description}")
            print(f"         Expected: {expected}, Got: {actual}")

        print()

    print("=" * 60)
    print(f"SUMMARY: {passed} passed, {failed} failed")
    print("=" * 60)

    return failed == 0


if __name__ == "__main__":
    success = test_validation()
    sys.exit(0 if success else 1)
