#!/usr/bin/env python3
"""Quick test for Layer 2: Track/Return Parser"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from server.services.nlp.track_parser import parse_track


def test_track_parser():
    """Test track parser with various commands"""

    tests = [
        # Track references (1-indexed input, 0-indexed output)
        ("track 1", "track", 0, "Track 1"),
        ("track 5", "track", 4, "Track 5"),
        ("track 12", "track", 11, "Track 12"),
        ("set track 3 volume to -10", "track", 2, "Track 3"),  # Track in context

        # Return references (A=0, B=1, C=2, D=3)
        ("return A", "return", 0, "Return A"),
        ("return B", "return", 1, "Return B"),
        ("return C", "return", 2, "Return C"),
        ("return D", "return", 3, "Return D"),
        ("return a", "return", 0, "Return A"),  # Case insensitive
        ("open return A reverb", "return", 0, "Return A"),  # Return in context

        # Master reference
        ("master", "master", None, "Master"),
        ("set master volume to -3", "master", None, "Master"),  # Master in context
    ]

    passed = 0
    failed = 0

    print("=" * 70)
    print("LAYER 2: TRACK/RETURN PARSER TESTS")
    print("=" * 70)
    print()

    for text, expected_domain, expected_index, expected_ref in tests:
        result = parse_track(text.lower())

        if result:
            if (result.domain == expected_domain and
                result.index == expected_index and
                result.reference == expected_ref):

                print(f"✓ {text}")
                print(f"  → domain={result.domain}, index={result.index}, ref={result.reference}")
                passed += 1
            else:
                print(f"✗ {text}")
                print(f"  Expected: domain={expected_domain}, index={expected_index}, ref={expected_ref}")
                print(f"  Got:      domain={result.domain}, index={result.index}, ref={result.reference}")
                failed += 1
        else:
            print(f"✗ {text} - NO MATCH")
            failed += 1

        print()

    print("=" * 70)
    print(f"SUMMARY: {passed} passed, {failed} failed")
    print("=" * 70)

    return failed == 0


if __name__ == "__main__":
    success = test_track_parser()
    sys.exit(0 if success else 1)
