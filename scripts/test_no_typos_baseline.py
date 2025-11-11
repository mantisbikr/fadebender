#!/usr/bin/env python3
"""
NO-TYPO Baseline Test

Tests correctly-spelled device and parameter combinations.
This establishes a baseline to ensure space normalization doesn't introduce false positives.

Expected: 100% pass rate on clean inputs
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


def run_test(parser, text, expected_device, expected_param):
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

    return passed, result, issues


def print_result(passed, test_name, text, result, issues):
    """Print formatted test result."""
    status = "✓ PASS" if passed else "✗ FAIL"
    print(f"  {status} {test_name}")
    if not passed:
        print(f"      Input: \"{text}\"")
        print(f"      Result: device={result.device}, param={result.param}, conf={result.confidence:.2f}, method={result.method}")
        for issue in issues:
            print(f"      Issue: {issue}")
        print()


def build_tests_from_parse_index(parse_index):
    """Dynamically build test cases from actual device parameters in parse_index.

    This ensures we only test VALID device + parameter combinations.
    """
    tests_by_category = {
        "exact_device_param": [],
        "device_type_param": [],
        "multi_word_params": [],
        "device_with_spaces": [],
    }

    params_by_device = parse_index.get("params_by_device", {})
    device_type_index = parse_index.get("device_type_index", {})

    # Build reverse lookup: device_name -> device_type
    device_to_type = {}
    for dev_type, dev_names in device_type_index.items():
        for dev_name in dev_names:
            device_to_type[dev_name] = dev_type

    for device_name, device_data in params_by_device.items():
        param_names = device_data.get("params", [])
        device_type = device_data.get("device_type", "unknown")

        if not param_names:
            continue

        # Select up to 3 parameters per device for testing
        selected_params = param_names[:3]

        for param_name in selected_params:
            # Test 1: Exact device name + param
            text = f"{device_name.lower()} {param_name.lower()}"
            tests_by_category["exact_device_param"].append((text, device_name, param_name))

            # Test 2: Device type + param (if device type is not "unknown")
            if device_type and device_type != "unknown":
                text_type = f"{device_type.lower()} {param_name.lower()}"
                tests_by_category["device_type_param"].append((text_type, device_name, param_name))

            # Test 3: Multi-word parameters (if param has space)
            if " " in param_name:
                tests_by_category["multi_word_params"].append((text, device_name, param_name))

            # Test 4: Device names with spaces (if device has space)
            if " " in device_name:
                tests_by_category["device_with_spaces"].append((text, device_name, param_name))

    return tests_by_category


def main():
    print("=" * 80)
    print("NO-TYPO Baseline Test (Clean Inputs Only)")
    print("=" * 80)
    print()

    # Build parse index
    print("Building parse index...")
    parse_index = build_index_from_mock_liveset(TEST_DEVICES)
    parser = DeviceContextParser(parse_index)
    print(f"Loaded {len(parse_index['devices_in_set'])} devices")
    print()

    # Build tests from actual parse index data
    print("Building test cases from parse index (valid parameters only)...")
    tests_by_category = build_tests_from_parse_index(parse_index)
    print()

    total = 0
    passed = 0

    # ========================================================================
    # Exact Device Name + Exact Parameter Name
    # ========================================================================
    print("=" * 80)
    print("Clean Inputs: Exact Device + Exact Parameter")
    print("=" * 80)
    print()

    tests = tests_by_category["exact_device_param"]

    for text, exp_dev, exp_param in tests:
        total += 1
        p, result, issues = run_test(parser, text, exp_dev, exp_param)
        print_result(p, f"\"{text}\"", text, result, issues)
        if p:
            passed += 1

    # ========================================================================
    # Device Type + Parameter Name
    # ========================================================================
    print()
    print("=" * 80)
    print("Clean Inputs: Device Type + Parameter")
    print("=" * 80)
    print()

    tests = tests_by_category["device_type_param"]

    for text, exp_dev, exp_param in tests:
        total += 1
        p, result, issues = run_test(parser, text, exp_dev, exp_param)
        print_result(p, f"\"{text}\"", text, result, issues)
        if p:
            passed += 1

    # ========================================================================
    # Multi-word Parameters (Clean)
    # ========================================================================
    print()
    print("=" * 80)
    print("Clean Inputs: Multi-word Parameters")
    print("=" * 80)
    print()

    tests = tests_by_category["multi_word_params"]

    for text, exp_dev, exp_param in tests:
        total += 1
        p, result, issues = run_test(parser, text, exp_dev, exp_param)
        print_result(p, f"\"{text}\"", text, result, issues)
        if p:
            passed += 1

    # ========================================================================
    # Device Names with Spaces (Clean)
    # ========================================================================
    print()
    print("=" * 80)
    print("Clean Inputs: Device Names with Spaces")
    print("=" * 80)
    print()

    tests = tests_by_category["device_with_spaces"]

    for text, exp_dev, exp_param in tests:
        total += 1
        p, result, issues = run_test(parser, text, exp_dev, exp_param)
        print_result(p, f"\"{text}\"", text, result, issues)
        if p:
            passed += 1

    # ========================================================================
    # Summary
    # ========================================================================
    print()
    print("=" * 80)
    print("BASELINE Test Summary")
    print("=" * 80)
    print(f"Total tests: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}")
    print(f"Success rate: {100 * passed / total:.1f}%")
    print()

    if passed == total:
        print("✓ BASELINE ESTABLISHED: All clean inputs pass")
        print("  Safe to implement space normalization fallback")
        return 0
    else:
        print(f"✗ BASELINE BROKEN: {total - passed} clean input(s) failed")
        print("  Do NOT implement space normalization - fix existing parser first")
        return 1


if __name__ == "__main__":
    sys.exit(main())
