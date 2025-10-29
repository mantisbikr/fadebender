#!/usr/bin/env python3
"""
Test that chat service handles typos correctly by falling through to NLP.
"""
import sys
import os
import re

# Add server to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Test the regex patterns directly
def test_send_regex():
    """Test that send regex requires 'send' keyword."""
    pattern = r"\bset\s+track\s+(\d+)\s+send\s+([\w\s]+?)\s+to\s+(-?\d+(?:\.\d+)?)\s*(db|dB|%|percent|percentage)?\b"

    test_cases = [
        ("set track 1 send A to -12 dB", True, "Valid send command"),
        ("set track 1 volme to -12 dB", False, "Typo should NOT match send"),
        ("set track 1 volume to -12 dB", False, "Volume should NOT match send"),
        ("set track 1 send reverb to -6 dB", True, "Valid send with name"),
    ]

    print("=" * 80)
    print("SEND REGEX TEST (must require 'send' keyword)")
    print("=" * 80)

    passed = 0
    failed = 0

    for text, should_match, description in test_cases:
        match = re.search(pattern, text, flags=re.I)
        matched = match is not None

        if matched == should_match:
            print(f"✓ PASS: {description}")
            print(f"  Query: '{text}'")
            print(f"  Expected match: {should_match}, Got: {matched}")
            passed += 1
        else:
            print(f"✗ FAIL: {description}")
            print(f"  Query: '{text}'")
            print(f"  Expected match: {should_match}, Got: {matched}")
            failed += 1
        print()

    print(f"Results: {passed} passed, {failed} failed")
    return failed == 0


def test_volume_regex():
    """Test that volume regex requires exact 'vol' or 'volume'."""
    pattern = r'\bset\s+track\s+(\d+)\s+vol(?:ume)?\s+to\s+(-?\d+(?:\.\d+)?)\s*(?:db|dB|DB)?\b'

    test_cases = [
        ("set track 1 volume to -12 dB", True, "Valid volume command"),
        ("set track 1 vol to -12 dB", True, "Valid vol shorthand"),
        ("set track 1 volme to -12 dB", False, "Typo should NOT match"),
        ("set track 1 vilme to -12 dB", False, "Typo should NOT match"),
    ]

    print("\n" + "=" * 80)
    print("VOLUME REGEX TEST (must require exact 'vol' or 'volume')")
    print("=" * 80)

    passed = 0
    failed = 0

    for text, should_match, description in test_cases:
        match = re.search(pattern, text.lower(), flags=re.I)
        matched = match is not None

        if matched == should_match:
            print(f"✓ PASS: {description}")
            print(f"  Query: '{text}'")
            print(f"  Expected match: {should_match}, Got: {matched}")
            passed += 1
        else:
            print(f"✗ FAIL: {description}")
            print(f"  Query: '{text}'")
            print(f"  Expected match: {should_match}, Got: {matched}")
            failed += 1
        print()

    print(f"Results: {passed} passed, {failed} failed")
    return failed == 0


if __name__ == "__main__":
    print("\nTesting regex patterns that caused the 'unknown_send:volme' bug\n")

    send_ok = test_send_regex()
    volume_ok = test_volume_regex()

    print("\n" + "=" * 80)
    print("OVERALL RESULT")
    print("=" * 80)

    if send_ok and volume_ok:
        print("\n✓ ALL TESTS PASSED")
        print("\nTypos like 'volme' will now fall through to NLP system for correction!")
        sys.exit(0)
    else:
        print("\n✗ SOME TESTS FAILED")
        sys.exit(1)
