#!/usr/bin/env python3
"""
Test suite for Device Context Parser

Tests device-context-aware parsing with reverb, delay, amp, and compressor combinations.
Validates that parameter ambiguities are resolved correctly using device type context.
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


# Test devices from the benchmark
TEST_DEVICES = [
    "Reverb",          # reverb
    "4th Bandpass",    # delay
    "Screamer",        # amp
    "8DotBall",        # echo
    "Ambience",        # reverb (second instance)
    "Bass Roundup",    # amp (second instance)
    "Discrete",        # amp (third instance)
    "Mix Gel",         # compressor
    "8th Groove",      # delay (second instance)
    "Chopped Delay",   # delay (third instance)
]


def run_test_case(parser, test_name, text, expected_device, expected_param, expect_success=True):
    """Run a single test case and report results."""
    result = parser.parse_device_param(text)

    passed = True
    issues = []

    if expect_success:
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
    print(f"      Result: device={result.device}, param={result.param}, type={result.device_type}, conf={result.confidence:.2f}, method={result.method}")

    if not passed and issues:
        for issue in issues:
            print(f"      Issue: {issue}")

    print()
    return passed


def main():
    print("=" * 80)
    print("Device Context Parser Test Suite")
    print("=" * 80)
    print()

    # Build parse index
    print("Building parse index from test devices...")
    parse_index = build_index_from_mock_liveset(TEST_DEVICES)
    print(f"  Loaded {len(parse_index['devices_in_set'])} devices, {sum(len(p['params']) for p in parse_index['params_by_device'].values())} params total")
    print()

    # Initialize parser
    parser = DeviceContextParser(parse_index)

    # Test suite
    total_tests = 0
    passed_tests = 0

    print("=" * 80)
    print("Test Category: Reverb Device")
    print("=" * 80)
    print()

    # Reverb tests (using actual Firestore parameter names)
    tests = [
        ("Exact device + exact param", "reverb decay time", "Reverb", "Decay Time"),
        ("Device + partial param", "reverb decay", "Reverb", "Decay Time"),
        ("Exact param: stereo image", "reverb stereo image", "Reverb", "Stereo Image"),
        ("Exact param: dry/wet", "reverb dry wet", "Reverb", "Dry/Wet"),
        ("Exact param: predelay", "reverb predelay", "Reverb", "Predelay"),
        ("Exact param: room size", "reverb room size", "Reverb", "Room Size"),
    ]

    for test_name, text, exp_dev, exp_param in tests:
        total_tests += 1
        if run_test_case(parser, test_name, text, exp_dev, exp_param):
            passed_tests += 1

    print("=" * 80)
    print("Test Category: Delay Device")
    print("=" * 80)
    print()

    # Delay tests
    tests = [
        ("Exact device + exact param", "delay time", "4th Bandpass", "Time"),
        ("Device + feedback", "delay feedback", "4th Bandpass", "Feedback"),
        ("Delay sync param", "delay sync", "4th Bandpass", "Sync"),
        ("Delay dry/wet", "delay dry wet", "4th Bandpass", "Dry/Wet"),
        ("Fuzzy device name", "bandpass time", "4th Bandpass", "Time"),
    ]

    for test_name, text, exp_dev, exp_param in tests:
        total_tests += 1
        if run_test_case(parser, test_name, text, exp_dev, exp_param):
            passed_tests += 1

    print("=" * 80)
    print("Test Category: Amp/Distortion Device")
    print("=" * 80)
    print()

    # Amp tests
    tests = [
        ("Exact device + gain", "screamer drive", "Screamer", "Drive"),
        ("Amp tone control", "screamer tone", "Screamer", "Tone"),
        ("Amp dry/wet", "screamer dry wet", "Screamer", "Dry/Wet"),
        ("Fuzzy device + param", "scremer drive", "Screamer", "Drive"),
    ]

    for test_name, text, exp_dev, exp_param in tests:
        total_tests += 1
        if run_test_case(parser, test_name, text, exp_dev, exp_param):
            passed_tests += 1

    print("=" * 80)
    print("Test Category: Compressor Device")
    print("=" * 80)
    print()

    # Compressor tests
    tests = [
        ("Compressor threshold", "mix gel threshold", "Mix Gel", "Threshold"),
        ("Compressor ratio", "mix gel ratio", "Mix Gel", "Ratio"),
        ("Compressor attack", "mix gel attack", "Mix Gel", "Attack"),
        ("Compressor release", "mix gel release", "Mix Gel", "Release"),
        ("Compressor dry/wet", "mix gel mix", "Mix Gel", "Dry/Wet"),
    ]

    for test_name, text, exp_dev, exp_param in tests:
        total_tests += 1
        if run_test_case(parser, test_name, text, exp_dev, exp_param):
            passed_tests += 1

    print("=" * 80)
    print("Test Category: Echo Device (Complex Parameters)")
    print("=" * 80)
    print()

    # Echo tests (device with many parameters)
    tests = [
        ("Echo left delay", "8dotball left delay", "8DotBall", "Left Delay"),
        ("Echo right delay", "8dotball right delay", "8DotBall", "Right Delay"),
        ("Echo feedback", "8dotball feedback", "8DotBall", "Feedback"),
        ("Echo stereo width", "8dotball stereo width", "8DotBall", "Stereo Width"),  # NOT Stereo Image
        ("Echo modulation rate", "8dotball modulation rate", "8DotBall", "Modulation Rate"),
    ]

    for test_name, text, exp_dev, exp_param in tests:
        total_tests += 1
        if run_test_case(parser, test_name, text, exp_dev, exp_param):
            passed_tests += 1

    print("=" * 80)
    print("Test Category: Device Ordinals")
    print("=" * 80)
    print()

    # Ordinal tests
    tests_ordinal = [
        ("Delay with ordinal", "delay 2 time", "4th Bandpass", "Time", 2),
        ("Amp with ordinal", "screamer #1 drive", "Screamer", "Drive", 1),
        ("Reverb with ordinal", "reverb 2 decay", "Reverb", "Decay", 2),
    ]

    for test_name, text, exp_dev, exp_param, exp_ordinal in tests_ordinal:
        total_tests += 1
        result = parser.parse_device_param(text)

        passed = True
        issues = []

        if result.device != exp_dev:
            passed = False
            issues.append(f"device: got '{result.device}', expected '{exp_dev}'")

        if result.param != exp_param:
            passed = False
            issues.append(f"param: got '{result.param}', expected '{exp_param}'")

        if result.device_ordinal != exp_ordinal:
            passed = False
            issues.append(f"ordinal: got {result.device_ordinal}, expected {exp_ordinal}")

        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  {status} {test_name}")
        print(f"      Input: \"{text}\"")
        print(f"      Result: device={result.device}, param={result.param}, ordinal={result.device_ordinal}, conf={result.confidence:.2f}")

        if not passed and issues:
            for issue in issues:
                print(f"      Issue: {issue}")

        print()

        if passed:
            passed_tests += 1

    print("=" * 80)
    print("Test Category: Ambiguity Resolution")
    print("=" * 80)
    print()

    # Ambiguity tests (same param name in different devices)
    tests = [
        ("Decay in reverb context", "reverb decay", "Reverb", "Decay"),
        ("Time in delay context", "delay time", "4th Bandpass", "Time"),
        ("Dry/Wet in any context", "reverb dry wet", "Reverb", "Dry/Wet"),
    ]

    for test_name, text, exp_dev, exp_param in tests:
        total_tests += 1
        if run_test_case(parser, test_name, text, exp_dev, exp_param):
            passed_tests += 1

    # Summary
    print("=" * 80)
    print("Test Summary")
    print("=" * 80)
    print(f"Total tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {total_tests - passed_tests}")
    print(f"Success rate: {100 * passed_tests / total_tests:.1f}%")
    print()

    if passed_tests == total_tests:
        print("🎉 All tests passed!")
        return 0
    else:
        print(f"⚠️  {total_tests - passed_tests} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
