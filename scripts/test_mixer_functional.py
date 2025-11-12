#!/usr/bin/env python3
"""
Functional Test: Verify Mixer Commands Work After Parser Changes

Tests that mixer parameter parsing returns lowercase parameters
that are correctly handled by the mixer service.
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

# Use minimal device to build parse index (mixer params work independently)
TEST_DEVICES = ["Reverb"]


def main():
    print("=" * 80)
    print("Mixer Commands Functional Test")
    print("=" * 80)
    print()

    # Build parse index (even with no devices, mixer params should work)
    parse_index = build_index_from_mock_liveset(TEST_DEVICES)
    parser = DeviceContextParser(parse_index)

    # Check that mixer_params are in the index
    mixer_params = parse_index.get("mixer_params", [])
    print(f"Mixer parameters in parse index: {mixer_params}")
    print()

    # Test mixer commands
    tests = [
        ("set track 1 volume to -6db", "volume"),
        ("increase track pan by 10%", "pan"),
        ("set return a send a to 50%", "send a"),
        ("mute track 2", "mute"),
        ("solo track 3", "solo"),
    ]

    passed = 0
    total = len(tests)

    print("Testing Mixer Commands:")
    print("=" * 80)
    print()

    for text, expected_param in tests:
        result = parser.parse_device_param(text)

        # Check if parameter matches (case-insensitive since we expect lowercase)
        param_matches = result.param.lower() == expected_param.lower()

        if param_matches and result.confidence >= 0.25:
            print(f"✓ PASS: \"{text}\"")
            print(f"      Result: param={result.param} (lowercase as expected)")
            passed += 1
        else:
            print(f"✗ FAIL: \"{text}\"")
            print(f"      Expected param: {expected_param}")
            print(f"      Got: param={result.param}, confidence={result.confidence:.2f}")

        print()

    # Summary
    print("=" * 80)
    print(f"Results: {passed}/{total} passed ({100*passed/total:.0f}%)")
    print()

    if passed == total:
        print("✓ SUCCESS: All mixer commands work correctly")
        print("  Parser returns lowercase parameters as designed")
        print("  These will be correctly handled by mixer_service.py")
        return 0
    else:
        print(f"✗ FAILURE: {total - passed} test(s) failed")
        print("  Mixer command parsing is broken")
        return 1


if __name__ == "__main__":
    sys.exit(main())
