#!/usr/bin/env python3
"""
Simple test suite for Device Context Parser using ACTUAL Firestore parameter names.

Tests device-type resolution and device-context-aware parsing.
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


def test_parser(text, expected_device, expected_param, expected_method_prefix=None):
    """Run a test and return (passed, result)."""
    parser = DeviceContextParser(parse_index)
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

    if expected_method_prefix and not result.method.startswith(expected_method_prefix):
        passed = False
        issues.append(f"method: got '{result.method}', expected to start with '{expected_method_prefix}'")

    return passed, result, issues


def main():
    global parse_index

    print("=" * 80)
    print("Simple Device Context Parser Test Suite")
    print("=" * 80)
    print()

    # Build parse index
    print("Building parse index...")
    parse_index = build_index_from_mock_liveset(TEST_DEVICES)
    print(f"Loaded {len(parse_index['devices_in_set'])} devices")
    print()

    total = 0
    passed = 0

    print("=" * 80)
    print("Test Category 1: Exact Device Name + Exact Parameter Name")
    print("=" * 80)
    print()

    tests = [
        ("reverb stereo image", "Reverb", "Stereo Image"),
        ("reverb predelay", "Reverb", "Predelay"),
        ("4th bandpass feedback", "4th Bandpass", "Feedback"),
        ("screamer gain", "Screamer", "Gain"),
        ("mix gel threshold", "Mix Gel", "Threshold"),
        ("mix gel ratio", "Mix Gel", "Ratio"),
        ("8dotball feedback", "8DotBall", "Feedback"),
    ]

    for text, exp_dev, exp_param in tests:
        total += 1
        p, result, issues = test_parser(text, exp_dev, exp_param)

        status = "✓ PASS" if p else "✗ FAIL"
        print(f"{status} '{text}'")
        print(f"  → device={result.device}, param={result.param}, conf={result.confidence:.2f}, method={result.method}")
        if issues:
            for issue in issues:
                print(f"  Issue: {issue}")
        print()

        if p:
            passed += 1

    print("=" * 80)
    print("Test Category 2: Device Type Resolution (NO device name, uses type)")
    print("=" * 80)
    print()

    tests_type_resolution = [
        ("delay feedback", "4th Bandpass", "Feedback"),  # "delay" is device type
        ("reverb predelay", "Reverb", "Predelay"),        # "reverb" is both device name and type
        ("amp gain", "Screamer", "Gain"),                 # "amp" is device type
        ("compressor threshold", "Mix Gel", "Threshold"), # "compressor" is device type
        ("echo feedback", "8DotBall", "Feedback"),        # "echo" is device type
    ]

    for text, exp_dev, exp_param in tests_type_resolution:
        total += 1
        p, result, issues = test_parser(text, exp_dev, exp_param)

        status = "✓ PASS" if p else "✗ FAIL"
        print(f"{status} '{text}'")
        print(f"  → device={result.device}, param={result.param}, conf={result.confidence:.2f}, method={result.method}")
        if issues:
            for issue in issues:
                print(f"  Issue: {issue}")
        print()

        if p:
            passed += 1

    print("=" * 80)
    print("Test Category 3: Multi-word Parameters")
    print("=" * 80)
    print()

    tests_multiword = [
        ("reverb decay time", "Reverb", "Decay Time"),
        ("reverb room size", "Reverb", "Room Size"),
        ("reverb stereo image", "Reverb", "Stereo Image"),
        ("4th bandpass delay mode", "4th Bandpass", "Delay Mode"),
        ("4th bandpass ping pong", "4th Bandpass", "Ping Pong"),
        ("screamer amp type", "Screamer", "Amp Type"),
        ("mix gel output gain", "Mix Gel", "Output Gain"),
    ]

    for text, exp_dev, exp_param in tests_multiword:
        total += 1
        p, result, issues = test_parser(text, exp_dev, exp_param)

        status = "✓ PASS" if p else "✗ FAIL"
        print(f"{status} '{text}'")
        print(f"  → device={result.device}, param={result.param}, conf={result.confidence:.2f}, method={result.method}")
        if issues:
            for issue in issues:
                print(f"  Issue: {issue}")
        print()

        if p:
            passed += 1

    print("=" * 80)
    print("Test Category 4: Fuzzy Matching")
    print("=" * 80)
    print()

    tests_fuzzy = [
        ("reverb stero image", "Reverb", "Stereo Image"),  # typo: stero
        ("scremar gain", "Screamer", "Gain"),              # typo: scremar
        ("mixgel threshold", "Mix Gel", "Threshold"),      # no space
    ]

    for text, exp_dev, exp_param in tests_fuzzy:
        total += 1
        p, result, issues = test_parser(text, exp_dev, exp_param)

        status = "✓ PASS" if p else "✗ FAIL"
        print(f"{status} '{text}'")
        print(f"  → device={result.device}, param={result.param}, conf={result.confidence:.2f}, method={result.method}")
        if issues:
            for issue in issues:
                print(f"  Issue: {issue}")
        print()

        if p:
            passed += 1

    # Summary
    print("=" * 80)
    print("Test Summary")
    print("=" * 80)
    print(f"Total tests: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}")
    print(f"Success rate: {100 * passed / total:.1f}%")
    print()

    if passed == total:
        print("🎉 All tests passed!")
        return 0
    else:
        print(f"⚠️  {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
