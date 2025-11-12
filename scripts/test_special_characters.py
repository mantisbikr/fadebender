#!/usr/bin/env python3
"""
Special Character Handling Test

Tests that presence/absence of special characters (/, &, -, <, >) in device/parameter names
is handled correctly. Uses ONLY real Firestore data.

User requirement: "dry wet" should match "Dry/Wet", "band pass spinner" should match "Band-pass Spinner", etc.

Note: 8DotBall is an outlier - it has "Dry Wet" (space) instead of "Dry/Wet" (slash) in Firestore.
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

# Real devices from Firestore with special characters
# Using actual device names that exist in Firestore
TEST_DEVICES = [
    "Gentle-Kneeless",   # Compressor with "S/C EQ Freq", "Dry/Wet", etc.
    "De-esser",          # Has "Dry/Wet", "Auto Release On/Off"
    "8DotBall",          # Echo device with "Dly < Mod", "Filter < Mod"
]


def run_test(parser, text, expected_device, expected_param, test_name):
    """Run a single test and return (passed, result, issues)."""
    result = parser.parse_device_param(text)

    passed = True
    issues = []

    if expected_device and result.device != expected_device:
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
    print("Special Character Handling Test (Real Firestore Data Only)")
    print("=" * 80)
    print()

    # Build parse index
    print("Building parse index...")
    parse_index = build_index_from_mock_liveset(TEST_DEVICES)
    parser = DeviceContextParser(parse_index)
    print(f"Loaded {len(parse_index['devices_in_set'])} devices")
    print()

    # Inspect what parameters we actually have
    print("Parameters with special characters:")
    for dev_name, dev_data in parse_index['params_by_device'].items():
        params = dev_data.get('params', [])
        special_params = [p for p in params if any(c in p for c in ['/', '&', '-', '<', '>'])]
        if special_params:
            print(f"  {dev_name}:")
            for p in special_params[:5]:  # Show first 5
                print(f"    - {p}")
    print()

    total = 0
    passed = 0

    # ========================================================================
    # Category 1: Slash (/) in Parameters
    # ========================================================================
    print("=" * 80)
    print("Category 1: Slash (/) in Parameters")
    print("=" * 80)
    print()

    tests = [
        # Test if "dry wet" matches "Dry/Wet"
        ("gentle kneeless dry wet", "Gentle-Kneeless", "Dry/Wet", "dry wet → Dry/Wet (missing slash)"),

        # Test if "s c eq freq" matches "S/C EQ Freq"
        ("gentle kneeless s c eq freq", "Gentle-Kneeless", "S/C EQ Freq", "s c eq freq → S/C EQ Freq (missing slashes)"),

        # Test if exact match with slash still works
        ("gentle kneeless dry/wet", "Gentle-Kneeless", "Dry/Wet", "dry/wet → Dry/Wet (exact match with slash)"),
    ]

    for text, exp_dev, exp_param, test_name in tests:
        total += 1
        if run_test(parser, text, exp_dev, exp_param, test_name):
            passed += 1

    # ========================================================================
    # Category 2: Less Than (<) in Parameters
    # ========================================================================
    print("=" * 80)
    print("Category 2: Less Than (<) in Parameters")
    print("=" * 80)
    print()

    tests = [
        # Test if "dly mod" matches "Dly < Mod"
        ("8dotball dly mod", "8DotBall", "Dly < Mod", "dly mod → Dly < Mod (missing <)"),

        # Test if "flt mod" matches "Flt < Mod" (actual parameter name is "Flt" not "Filter")
        ("8dotball flt mod", "8DotBall", "Flt < Mod", "flt mod → Flt < Mod (missing <)"),
    ]

    for text, exp_dev, exp_param, test_name in tests:
        total += 1
        if run_test(parser, text, exp_dev, exp_param, test_name):
            passed += 1

    # ========================================================================
    # Category 3: Hyphen (-) in Device Names
    # ========================================================================
    print("=" * 80)
    print("Category 3: Hyphen (-) in Device Names")
    print("=" * 80)
    print()

    tests = [
        # Test if "gentle kneeless" matches "Gentle-Kneeless"
        ("gentle kneeless threshold", "Gentle-Kneeless", "Threshold", "gentle kneeless → Gentle-Kneeless (missing hyphen)"),

        # Test if "de esser" matches "De-esser"
        ("de esser threshold", "De-esser", "Threshold", "de esser → De-esser (missing hyphen)"),

        # Test if exact match with hyphen still works
        ("gentle-kneeless threshold", "Gentle-Kneeless", "Threshold", "gentle-kneeless → Gentle-Kneeless (exact with hyphen)"),
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
        print("✓ SUCCESS: All special character tests passed!")
        print("  Parser handles presence/absence of special characters correctly")
        return 0
    else:
        print(f"✗ FAILING: {total - passed} test(s) failed")
        print("  Special character normalization needs implementation")
        return 1


if __name__ == "__main__":
    sys.exit(main())
