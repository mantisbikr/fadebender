#!/usr/bin/env python3
"""
Test script to verify volume command integration.
"""

import sys
import pathlib

# Add server directory to path
server_dir = pathlib.Path(__file__).resolve().parent / "server"
sys.path.insert(0, str(server_dir))

from volume_parser import parse_volume_command


def test_integration():
    """Test that the volume parser integrates correctly."""

    # Test the exact case that was failing
    test_cases = [
        "set track 1 volume to -7.0",
        "set track 4 volume to -15.0",
        "set track 2 vol to -10.5 dB",
    ]

    print("Testing volume command integration:")
    print("=" * 50)

    for test in test_cases:
        result = parse_volume_command(test)

        if result:
            print(f"✓ Input: '{test}'")
            print(f"  Track: {result['track_index']}")
            print(f"  dB Value: {result['db_value']}")
            print(f"  Live Float: {result['live_float']:.4f}")
            print(f"  Expected result: Track {result['track_index']} volume set to {result['db_value']} dB")
            print()
        else:
            print(f"✗ FAILED: '{test}' - No match found")
            print()


if __name__ == "__main__":
    test_integration()