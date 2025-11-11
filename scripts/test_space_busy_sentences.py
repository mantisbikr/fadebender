#!/usr/bin/env python3
"""
Busy Sentence Space Typo Test

Tests that space normalization works in typical intent sentences (busy sentences),
not just simple "device param" patterns.

This test validates the token-level space normalization refactoring.
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
    print("Busy Sentence Space Typo Test")
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
    # Category 1: Space Typos in Busy Sentences (Device Names)
    # ========================================================================
    print("=" * 80)
    print("Category 1: Missing Space in Device Names (Busy Sentences)")
    print("=" * 80)
    print()

    tests = [
        # Device name without spaces in busy sentences
        ("set track 1 mixgel threshold to -10db", "Mix Gel", "Threshold", "mixgel → Mix Gel (busy sentence)"),
        ("increase return A 8dotball feedback by 20%", "8DotBall", "Feedback", "8dotball → 8DotBall (busy sentence)"),
        ("adjust mixgel ratio on track 2 to 4:1", "Mix Gel", "Ratio", "mixgel in middle of sentence"),
        ("on return B set 8dotball l time to 250ms", "8DotBall", "L Time", "8dotball with param after"),
    ]

    for text, exp_dev, exp_param, test_name in tests:
        total += 1
        if run_test(parser, text, exp_dev, exp_param, test_name):
            passed += 1

    # ========================================================================
    # Category 2: Extra Space in Device Names (Busy Sentences)
    # ========================================================================
    print("=" * 80)
    print("Category 2: Extra Space in Device Names (Busy Sentences)")
    print("=" * 80)
    print()

    tests = [
        # Device name with extra spaces in busy sentences
        ("set track 1 8 dot ball feedback to 50%", "8DotBall", "Feedback", "8 dot ball → 8DotBall (busy sentence)"),
        ("increase return A 8 dot ball l time by 10ms", "8DotBall", "L Time", "8 dot ball in middle"),
    ]

    for text, exp_dev, exp_param, test_name in tests:
        total += 1
        if run_test(parser, text, exp_dev, exp_param, test_name):
            passed += 1

    # ========================================================================
    # Category 3: Missing Space in Parameters (Busy Sentences)
    # ========================================================================
    print("=" * 80)
    print("Category 3: Missing Space in Parameters (Busy Sentences)")
    print("=" * 80)
    print()

    tests = [
        # Parameter name without spaces in busy sentences
        ("set reverb roomsize to 80 on return A", "Reverb", "Room Size", "roomsize → Room Size (busy sentence)"),
        ("increase reverb decaytime by 1 second", "Reverb", "Decay Time", "decaytime → Decay Time (busy sentence)"),
        ("set reverb stereoimage to 100% on track 3", "Reverb", "Stereo Image", "stereoimage → Stereo Image"),
        ("adjust compressor outputgain to -6db", "Mix Gel", "Output Gain", "outputgain → Output Gain"),
    ]

    for text, exp_dev, exp_param, test_name in tests:
        total += 1
        if run_test(parser, text, exp_dev, exp_param, test_name):
            passed += 1

    # ========================================================================
    # Category 4: Combined Device + Parameter Space Typos (Busy Sentences)
    # ========================================================================
    print("=" * 80)
    print("Category 4: Combined Device + Parameter Space Typos")
    print("=" * 80)
    print()

    tests = [
        # Both device and parameter have space typos
        ("set mixgel outputgain to -3db on track 1", "Mix Gel", "Output Gain", "mixgel + outputgain"),
        ("increase 8dotball l time by 20ms on return A", "8DotBall", "L Time", "8dotball + l time"),
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
        print("✓ SUCCESS: All busy sentence space typo tests passed!")
        print("  Token-level space normalization is working correctly")
        return 0
    else:
        print(f"✗ FAILING: {total - passed} test(s) failed")
        print("  Token-level space normalization needs more work")
        return 1


if __name__ == "__main__":
    sys.exit(main())
