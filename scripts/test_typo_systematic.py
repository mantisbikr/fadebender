#!/usr/bin/env python3
"""
Systematic Typo Correction Test Suite

Tests all major typo categories against current fuzzy matching + Firestore corrections.
Establishes baseline for what works and what needs enhancement.

Categories:
1. Missing character
2. Transposed characters
3. Wrong character
4. Missing special character (/, -)
5. Extra space (should be no space)
6. Missing space (should have space)
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


def run_test(parser, typo_text, correct_device, correct_param, test_name, typo_type):
    """Run a single test and return (passed, result, issues)."""
    result = parser.parse_device_param(typo_text)

    passed = True
    issues = []

    if result.device != correct_device:
        passed = False
        issues.append(f"device: got '{result.device}', expected '{correct_device}'")

    if result.param != correct_param:
        passed = False
        issues.append(f"param: got '{result.param}', expected '{correct_param}'")

    if result.confidence < 0.5:
        passed = False
        issues.append(f"low confidence: {result.confidence:.2f}")

    return passed, result, issues


def print_test_result(passed, test_name, typo_text, result, issues):
    """Print formatted test result."""
    status = "✓ PASS" if passed else "✗ FAIL"
    print(f"  {status} {test_name}")
    print(f"      Input: \"{typo_text}\"")
    print(f"      Result: device={result.device}, param={result.param}, conf={result.confidence:.2f}, method={result.method}")

    if not passed and issues:
        for issue in issues:
            print(f"      Issue: {issue}")

    print()


def main():
    print("=" * 80)
    print("Systematic Typo Correction Test Suite")
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
    results_by_category = {}

    # ========================================================================
    # Category 1: Missing Character
    # ========================================================================
    print("=" * 80)
    print("Category 1: Missing Character")
    print("=" * 80)
    print()

    tests = [
        # Device names
        ("dela feedback", "4th Bandpass", "Feedback", "delay → dela (missing 'y')"),
        ("reverb deca time", "Reverb", "Decay Time", "decay → deca (missing 'y')"),
        ("revrb predelay", "Reverb", "Predelay", "reverb → revrb (missing 'e')"),
        ("screamr gain", "Screamer", "Gain", "screamer → screamr (missing 'e')"),
        ("mixgel threshold", "Mix Gel", "Threshold", "mix gel → mixgel (missing space)"),

        # Parameters
        ("delay feedbak", "4th Bandpass", "Feedback", "feedback → feedbak (missing 'c')"),
        ("reverb stero image", "Reverb", "Stereo Image", "stereo → stero (missing 'e')"),
        ("compressor threshol", "Mix Gel", "Threshold", "threshold → threshol (missing 'd')"),
        ("reverb rom size", "Reverb", "Room Size", "room → rom (missing 'o')"),
        ("delay tie", "4th Bandpass", "Time", "time → tie (missing 'm')"),
    ]

    category_passed = 0
    category_total = len(tests)

    for typo_text, exp_dev, exp_param, test_name in tests:
        total += 1
        p, result, issues = run_test(parser, typo_text, exp_dev, exp_param, test_name, "missing_char")
        print_test_result(p, test_name, typo_text, result, issues)
        if p:
            passed += 1
            category_passed += 1

    results_by_category["Missing Character"] = (category_passed, category_total)

    # ========================================================================
    # Category 2: Transposed Characters
    # ========================================================================
    print("=" * 80)
    print("Category 2: Transposed Characters")
    print("=" * 80)
    print()

    tests = [
        # Device names
        ("rverb decay time", "Reverb", "Decay Time", "reverb → rverb (e↔v)"),
        ("dela feedback", "4th Bandpass", "Feedback", "delay → dela (a↔y)"),
        ("scremear gain", "Screamer", "Gain", "screamer → scremear (e↔a)"),

        # Parameters
        ("delay tiem", "4th Bandpass", "Time", "time → tiem (i↔e)"),
        ("reverb dacay time", "Reverb", "Decay Time", "decay → dacay (e↔c)"),
        ("compressor ataack", "Mix Gel", "Attack", "attack → ataack (t↔a)"),
    ]

    category_passed = 0
    category_total = len(tests)

    for typo_text, exp_dev, exp_param, test_name in tests:
        total += 1
        p, result, issues = run_test(parser, typo_text, exp_dev, exp_param, test_name, "transposed")
        print_test_result(p, test_name, typo_text, result, issues)
        if p:
            passed += 1
            category_passed += 1

    results_by_category["Transposed Characters"] = (category_passed, category_total)

    # ========================================================================
    # Category 3: Wrong Character
    # ========================================================================
    print("=" * 80)
    print("Category 3: Wrong Character")
    print("=" * 80)
    print()

    tests = [
        # Device names
        ("deday feedback", "4th Bandpass", "Feedback", "delay → deday (l→d)"),
        ("reverv decay time", "Reverb", "Decay Time", "reverb → reverv (b→v)"),

        # Parameters
        ("delay feedbakc", "4th Bandpass", "Feedback", "feedback → feedbakc (c→k→c)"),
        ("reverb decai time", "Reverb", "Decay Time", "decay → decai (y→i)"),
        ("compressor threzhold", "Mix Gel", "Threshold", "threshold → threzhold (s→z)"),
    ]

    category_passed = 0
    category_total = len(tests)

    for typo_text, exp_dev, exp_param, test_name in tests:
        total += 1
        p, result, issues = run_test(parser, typo_text, exp_dev, exp_param, test_name, "wrong_char")
        print_test_result(p, test_name, typo_text, result, issues)
        if p:
            passed += 1
            category_passed += 1

    results_by_category["Wrong Character"] = (category_passed, category_total)

    # ========================================================================
    # Category 4: Missing Special Character
    # ========================================================================
    print("=" * 80)
    print("Category 4: Missing Special Character (/, -)")
    print("=" * 80)
    print()

    tests = [
        ("reverb dry wet", "Reverb", "Dry/Wet", "dry/wet → dry wet (missing '/')"),
        ("reverb drywet", "Reverb", "Dry/Wet", "dry/wet → drywet (missing '/')"),
        ("4th bandpass ping pong", "4th Bandpass", "Ping Pong", "ping pong → ping-pong (space vs -)"),
        ("echo left delay", "8DotBall", "Left Delay", "left delay (space is correct)"),
    ]

    category_passed = 0
    category_total = len(tests)

    for typo_text, exp_dev, exp_param, test_name in tests:
        total += 1
        p, result, issues = run_test(parser, typo_text, exp_dev, exp_param, test_name, "missing_special")
        print_test_result(p, test_name, typo_text, result, issues)
        if p:
            passed += 1
            category_passed += 1

    results_by_category["Missing Special Character"] = (category_passed, category_total)

    # ========================================================================
    # Category 5: Extra Space (should be no space)
    # ========================================================================
    print("=" * 80)
    print("Category 5: Extra Space (should be no space)")
    print("=" * 80)
    print()

    tests = [
        # This tests if "mix gel" is treated same as "mixgel" when device is "Mix Gel"
        ("mix gel threshold", "Mix Gel", "Threshold", "Mix Gel with space (correct)"),

        # Multi-word device names split differently
        ("8 dot ball feedback", "8DotBall", "Feedback", "8DotBall → 8 dot ball (extra spaces)"),
        ("4 th bandpass feedback", "4th Bandpass", "Feedback", "4th Bandpass → 4 th bandpass"),
    ]

    category_passed = 0
    category_total = len(tests)

    for typo_text, exp_dev, exp_param, test_name in tests:
        total += 1
        p, result, issues = run_test(parser, typo_text, exp_dev, exp_param, test_name, "extra_space")
        print_test_result(p, test_name, typo_text, result, issues)
        if p:
            passed += 1
            category_passed += 1

    results_by_category["Extra Space"] = (category_passed, category_total)

    # ========================================================================
    # Category 6: Missing Space (should have space)
    # ========================================================================
    print("=" * 80)
    print("Category 6: Missing Space (should have space)")
    print("=" * 80)
    print()

    tests = [
        # Multi-word parameters without space
        ("reverb roomsize", "Reverb", "Room Size", "room size → roomsize (missing space)"),
        ("reverb decaytime", "Reverb", "Decay Time", "decay time → decaytime (missing space)"),
        ("reverb stereoimage", "Reverb", "Stereo Image", "stereo image → stereoimage (missing space)"),
        ("compressor outputgain", "Mix Gel", "Output Gain", "output gain → outputgain (missing space)"),
    ]

    category_passed = 0
    category_total = len(tests)

    for typo_text, exp_dev, exp_param, test_name in tests:
        total += 1
        p, result, issues = run_test(parser, typo_text, exp_dev, exp_param, test_name, "missing_space")
        print_test_result(p, test_name, typo_text, result, issues)
        if p:
            passed += 1
            category_passed += 1

    results_by_category["Missing Space"] = (category_passed, category_total)

    # ========================================================================
    # Summary
    # ========================================================================
    print("=" * 80)
    print("Test Summary")
    print("=" * 80)
    print()
    print(f"Total tests: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}")
    print(f"Overall success rate: {100 * passed / total:.1f}%")
    print()

    print("Results by Category:")
    print()
    for category, (cat_passed, cat_total) in results_by_category.items():
        rate = 100 * cat_passed / cat_total if cat_total > 0 else 0
        status = "✓" if rate >= 80 else "⚠" if rate >= 50 else "✗"
        print(f"  {status} {category:30s}: {cat_passed:2d}/{cat_total:2d} ({rate:5.1f}%)")

    print()
    print("=" * 80)

    if passed == total:
        print("🎉 All tests passed!")
        return 0
    else:
        print(f"⚠️  {total - passed} test(s) failed")
        print()
        print("Next steps:")
        print("  - Categories with <80% need improvement")
        print("  - Consider space normalization for space-related issues")
        print("  - Consider enhanced fuzzy matching for character errors")
        print("  - LLM fallback for severe cases")
        return 1


if __name__ == "__main__":
    sys.exit(main())
