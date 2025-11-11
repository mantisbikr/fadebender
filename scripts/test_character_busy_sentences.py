#!/usr/bin/env python3
"""
Character Typo Correction in Busy Sentences

Tests that character-level typo correction (missing, transposed, wrong characters)
works in typical intent sentences, not just simple "device param" patterns.

This validates that the fuzzy matching and device type resolution work correctly
in realistic usage scenarios.
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

# Set database before any imports
os.environ['FIRESTORE_DATABASE_ID'] = 'dev-display-value'

from server.services.parse_index import (
    build_index_from_mock_liveset,
    DeviceContextParser
)

# Test devices
TEST_DEVICES = [
    "Reverb",          # reverb
    "4th Bandpass",    # delay
    "Screamer",        # amp
    "8DotBall",        # echo
    "Mix Gel",         # compressor
]


def run_test(parser, text, expected_device, expected_param, test_name):
    """Run a single test and return (passed, result, issues)."""
    result = parser.parse_device_param(text)

    passed = True
    issues = []

    if result.device != expected_device:
        passed = False
        issues.append(f"device: got '{result.device}', expected '{expected_device}'")

    if result.param != expected_param:
        passed = False
        issues.append(f"param: got '{result.param}', expected '{expected_param}'")

    if result.confidence < 0.5:
        passed = False
        issues.append(f"low confidence: {result.confidence:.2f}")

    status = "✓ PASS" if passed else "✗ FAIL"
    print(f"  {status} {test_name}")
    if not passed or True:  # Always show details
        print(f"      Input: \"{text}\"")
        print(f"      Result: device={result.device}, param={result.param}, conf={result.confidence:.2f}, method={result.method}")

    if not passed and issues:
        for issue in issues:
            print(f"      Issue: {issue}")

    print()
    return passed


def main():
    print("=" * 80)
    print("Character Typo Correction in Busy Sentences")
    print("=" * 80)
    print()

    # Build parse index
    print("Building parse index...")
    parse_index = build_index_from_mock_liveset(TEST_DEVICES)
    parser = DeviceContextParser(parse_index)
    print(f"Loaded {len(parse_index['devices_in_set'])} devices")
    print()

    total = 0
    passed = 0

    # ========================================================================
    # Category 1: Missing Character (Busy Sentences)
    # ========================================================================
    print("=" * 80)
    print("Category 1: Missing Character in Busy Sentences")
    print("=" * 80)
    print()

    tests = [
        # Device names with missing characters
        ("set track 1 dela feedback to 50%", "4th Bandpass", "Feedback", "dela → delay (missing 'y')"),
        ("increase return A revrb decay time by 2s", "Reverb", "Decay Time", "revrb → reverb (missing 'e')"),
        ("adjust track 2 screamr gain to -6db", "Screamer", "Gain", "screamr → screamer (missing 'e')"),

        # Parameters with missing characters
        ("set reverb stero image to 100% on return A", "Reverb", "Stereo Image", "stero → stereo (missing 'e')"),
        ("increase delay feedbak by 20% on track 3", "4th Bandpass", "Feedback", "feedbak → feedback (missing 'c')"),
        ("set compressor threshol to -12db", "Mix Gel", "Threshold", "threshol → threshold (missing 'd')"),
    ]

    for text, exp_dev, exp_param, test_name in tests:
        total += 1
        if run_test(parser, text, exp_dev, exp_param, test_name):
            passed += 1

    # ========================================================================
    # Category 2: Transposed Characters (Busy Sentences)
    # ========================================================================
    print("=" * 80)
    print("Category 2: Transposed Characters in Busy Sentences")
    print("=" * 80)
    print()

    tests = [
        # Device names with transposed characters
        ("set track 1 rverb decay time to 3 seconds", "Reverb", "Decay Time", "rverb → reverb (e↔v)"),
        ("increase return A dela feedback by 10%", "4th Bandpass", "Feedback", "dela → delay (a↔y)"),

        # Parameters with transposed characters
        ("set reverb dacay time to 4s on return B", "Reverb", "Decay Time", "dacay → decay (e↔c)"),
        ("adjust compressor ataack on track 2 to 5ms", "Mix Gel", "Attack", "ataack → attack (t↔a)"),
    ]

    for text, exp_dev, exp_param, test_name in tests:
        total += 1
        if run_test(parser, text, exp_dev, exp_param, test_name):
            passed += 1

    # ========================================================================
    # Category 3: Wrong Character (Busy Sentences)
    # ========================================================================
    print("=" * 80)
    print("Category 3: Wrong Character in Busy Sentences")
    print("=" * 80)
    print()

    tests = [
        # Device names with wrong characters
        ("set track 1 deday feedback to 40%", "4th Bandpass", "Feedback", "deday → delay (l→d)"),
        ("increase return A reverv decay time by 1s", "Reverb", "Decay Time", "reverv → reverb (b→v)"),

        # Parameters with wrong characters
        ("set reverb decai time to 5 seconds on return A", "Reverb", "Decay Time", "decai → decay (y→i)"),
        ("adjust compressor threzhold on track 2 to -10db", "Mix Gel", "Threshold", "threzhold → threshold (s→z)"),
    ]

    for text, exp_dev, exp_param, test_name in tests:
        total += 1
        if run_test(parser, text, exp_dev, exp_param, test_name):
            passed += 1

    # ========================================================================
    # Summary
    # ========================================================================
    print("=" * 80)
    print("Test Summary")
    print("=" * 80)
    print(f"Total tests: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}")
    print(f"Success rate: {100 * passed / total:.1f}%")
    print()

    if passed == total:
        print("✓ SUCCESS: All character typo corrections work in busy sentences!")
        print("  Fuzzy matching + device type resolution is working correctly")
        return 0
    else:
        print(f"✗ FAILING: {total - passed} test(s) failed")
        print("  Character corrections need more work for busy sentences")
        return 1


if __name__ == "__main__":
    sys.exit(main())
