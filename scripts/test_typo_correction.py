#!/usr/bin/env python3
"""
Typo Correction Test Suite

Tests the parser's ability to handle:
1. Typos in device names
2. Typos in parameter names
3. Alternate sentence constructions

Goal: Establish baseline for current fuzzy matching, identify where LLM fallback is needed.
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
    """Run a single test and return (passed, result)."""
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
    print(f"      Input: \"{text}\"")
    print(f"      Result: device={result.device}, param={result.param}, conf={result.confidence:.2f}, method={result.method}")

    if not passed and issues:
        for issue in issues:
            print(f"      Issue: {issue}")

    print()
    return passed


def main():
    global parse_index

    print("=" * 80)
    print("Typo Correction Test Suite")
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
    # Category 1: Device Name Typos (Single Character)
    # ========================================================================
    print("=" * 80)
    print("Category 1: Device Name Typos (Single Character)")
    print("=" * 80)
    print()

    tests = [
        # Missing character
        ("Reverb → Reverb (missing 'b')", "reveb stereo image", "Reverb", "Stereo Image"),
        ("Screamer → Scremer (missing 'a')", "scremer gain", "Screamer", "Gain"),

        # Transposed characters
        ("Reverb → Rverb (transposed 'e' and 'v')", "rverb decay time", "Reverb", "Decay Time"),
        ("Screamer → Screame (missing 'r')", "screame drive", "Screamer", "Drive"),

        # Wrong character
        ("Mix Gel → Mix Gal (e→a)", "mix gal threshold", "Mix Gel", "Threshold"),
        ("8DotBall → 8DatBall (o→a)", "8datball feedback", "8DotBall", "Feedback"),
    ]

    for test_name, text, exp_dev, exp_param in tests:
        total += 1
        if run_test(parser, text, exp_dev, exp_param, test_name):
            passed += 1

    # ========================================================================
    # Category 2: Device Name Typos (Multiple Characters)
    # ========================================================================
    print("=" * 80)
    print("Category 2: Device Name Typos (Multiple Characters)")
    print("=" * 80)
    print()

    tests = [
        # Multiple typos
        ("Reverb → Reveb (missing 'r', wrong 'b')", "reveb predelay", "Reverb", "Predelay"),
        ("Screamer → Scramer (missing 'e')", "scramer tone", "Screamer", "Tone"),
        ("4th Bandpass → 4th Bandpas (missing 's')", "4th bandpas feedback", "4th Bandpass", "Feedback"),

        # Severe typos
        ("Mix Gel → Mixgel (no space)", "mixgel ratio", "Mix Gel", "Ratio"),
        ("8DotBall → 8dotbal (missing 'l', lowercase)", "8dotbal left delay", "8DotBall", "Left Delay"),
    ]

    for test_name, text, exp_dev, exp_param in tests:
        total += 1
        if run_test(parser, text, exp_dev, exp_param, test_name):
            passed += 1

    # ========================================================================
    # Category 3: Parameter Name Typos
    # ========================================================================
    print("=" * 80)
    print("Category 3: Parameter Name Typos")
    print("=" * 80)
    print()

    tests = [
        # Single character typos
        ("Feedback → Feedbak (missing 'c')", "delay feedbak", "4th Bandpass", "Feedback"),
        ("Stereo Image → Stero Image (missing 'e')", "reverb stero image", "Reverb", "Stereo Image"),
        ("Threshold → Threshol (missing 'd')", "compressor threshol", "Mix Gel", "Threshold"),

        # Multiple character typos
        ("Decay Time → Decai Time (y→i)", "reverb decai time", "Reverb", "Decay Time"),
        ("Predelay → Prdelay (missing 'e')", "reverb prdelay", "Reverb", "Predelay"),
        ("Room Size → Rom Size (missing 'o')", "reverb rom size", "Reverb", "Room Size"),
    ]

    for test_name, text, exp_dev, exp_param in tests:
        total += 1
        if run_test(parser, text, exp_dev, exp_param, test_name):
            passed += 1

    # ========================================================================
    # Category 4: Combined Device + Parameter Typos
    # ========================================================================
    print("=" * 80)
    print("Category 4: Combined Device + Parameter Typos")
    print("=" * 80)
    print()

    tests = [
        ("Reverb + Decay Time (both typos)", "reveb decai time", "Reverb", "Decay Time"),
        ("Screamer + Drive (both typos)", "scremer driv", "Screamer", "Drive"),
        ("Mix Gel + Threshold (both typos)", "mixgel threshol", "Mix Gel", "Threshold"),
    ]

    for test_name, text, exp_dev, exp_param in tests:
        total += 1
        if run_test(parser, text, exp_dev, exp_param, test_name):
            passed += 1

    # ========================================================================
    # Category 5: Alternate Sentence Constructions
    # ========================================================================
    print("=" * 80)
    print("Category 5: Alternate Sentence Constructions")
    print("=" * 80)
    print()

    tests = [
        # Parameter before track/return
        ("Param before track", "set delay feedback on track 1 to 30%", "4th Bandpass", "Feedback"),
        ("Param before return", "set reverb decay time on return A to 5 seconds", "Reverb", "Decay Time"),
        ("Param before track (device type)", "adjust compressor threshold on track 2 to -10db", "Mix Gel", "Threshold"),

        # Parameter after track/return
        ("Param after track", "set track 1 delay feedback to 30%", "4th Bandpass", "Feedback"),
        ("Param after return", "set return A reverb room size to 80", "Reverb", "Room Size"),
        ("Param after track (device type)", "adjust track 3 amp gain to 7", "Screamer", "Gain"),

        # Value in middle
        ("Value in middle", "set delay feedback to 40% on return B", "4th Bandpass", "Feedback"),
        ("Value at end", "on track 2 set reverb predelay to 20ms", "Reverb", "Predelay"),

        # Natural variations
        ("Increase verb", "increase screamer drive on track 1", "Screamer", "Drive"),
        ("Decrease verb", "decrease mix gel ratio on return A", "Mix Gel", "Ratio"),
        ("Bump verb", "bump delay time by 10ms", "4th Bandpass", "Time"),
        ("Lower verb", "lower reverb dry wet to 30%", "Reverb", "Dry/Wet"),
    ]

    for test_name, text, exp_dev, exp_param in tests:
        total += 1
        if run_test(parser, text, exp_dev, exp_param, test_name):
            passed += 1

    # ========================================================================
    # Category 6: Device Type Resolution with Typos
    # ========================================================================
    print("=" * 80)
    print("Category 6: Device Type Resolution with Typos")
    print("=" * 80)
    print()

    tests = [
        # Device type with parameter typo
        ("delay + feedbak", "delay feedbak", "4th Bandpass", "Feedback"),
        ("reverb + decai", "reverb decai time", "Reverb", "Decay Time"),
        ("amp + driv", "amp driv", "Screamer", "Drive"),

        # Device type typo + parameter
        ("dela + feedback", "dela feedback", "4th Bandpass", "Feedback"),
        ("rverb + decay time", "rverb decay time", "Reverb", "Decay Time"),
        ("compresor + threshold", "compresor threshold", "Mix Gel", "Threshold"),
    ]

    for test_name, text, exp_dev, exp_param in tests:
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

    # Category breakdown
    print("Category Breakdown:")
    print(f"  1. Device Name Typos (Single Char): 6 tests")
    print(f"  2. Device Name Typos (Multiple Char): 5 tests")
    print(f"  3. Parameter Name Typos: 6 tests")
    print(f"  4. Combined Typos: 3 tests")
    print(f"  5. Alternate Sentence Constructions: 12 tests")
    print(f"  6. Device Type Resolution with Typos: 6 tests")
    print()

    if passed == total:
        print("🎉 All tests passed! Current fuzzy matching is sufficient.")
        return 0
    else:
        print(f"⚠️  {total - passed} test(s) failed - these cases need LLM fallback")
        return 1


if __name__ == "__main__":
    sys.exit(main())
