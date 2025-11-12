#!/usr/bin/env python3
"""Quick test for Layer 3: Device/Param Parser"""

import sys
import requests
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import os
os.environ['FIRESTORE_DATABASE_ID'] = 'dev-display-value'

from server.services.nlp.device_param_parser import parse_device_param
from server.services.parse_index import ParseIndexBuilder

BASE_URL = "http://127.0.0.1:8722"


def test_device_param_parser():
    """Test device/param parser with mixer params and device params"""

    # Check server
    print("Checking server...")
    try:
        health = requests.get(f"{BASE_URL}/health", timeout=2)
        if health.status_code != 200:
            print("✗ Server not responding. Start server with: npm run server")
            return False
        print("✓ Server is running\n")
    except Exception as e:
        print(f"✗ Cannot connect to server: {e}")
        return False

    # Fetch snapshot
    print("Fetching snapshot from Ableton Live...")
    try:
        snapshot_resp = requests.get(f"{BASE_URL}/snapshot", timeout=5)
        if snapshot_resp.status_code != 200:
            print(f"✗ Failed to fetch snapshot: HTTP {snapshot_resp.status_code}")
            return False
        snapshot = snapshot_resp.json()
        print("✓ Snapshot fetched\n")
    except Exception as e:
        print(f"✗ Error fetching snapshot: {e}")
        return False

    # Extract devices from snapshot
    live_devices = []
    devices_data = snapshot.get("data", {}).get("devices", {})

    # Get devices from returns
    returns_data = devices_data.get("returns", {})
    for ret_index, ret_data in returns_data.items():
        for device in ret_data.get("devices", []):
            live_devices.append({
                "name": device.get("name"),
                "device_type": device.get("device_type", "unknown").lower(),
                "ordinals": 1
            })

    # Build parse index from Live set
    print(f"Building parse index from {len(live_devices)} devices...")
    builder = ParseIndexBuilder()
    parse_index = builder.build_from_live_set(live_devices)
    print(f"✓ Parse index built with {len(parse_index['devices_in_set'])} devices\n")

    tests = [
        # Mixer parameters (should return device="mixer")
        ("set track 1 volume to -10", "mixer", "Volume"),
        ("increase return A pan by 10", "mixer", "Pan"),
        ("mute track 2", "mixer", "Mute"),
        ("set track 3 send a to -6", "mixer", "Send A"),

        # Device parameters (should return device name, NOT "mixer")
        # Note: Param names come from Firestore and may have device prefix
        ("set return A reverb decay to 5 seconds", "reverb", "Reverb Decay"),
        ("increase return C echo time by 100 ms", "echo", "L Time"),  # 8DotBall has L/R Time
        ("set return A delay feedback to 50%", "delay", "Feedback"),

        # Ambiguous parameter (volume) - should be mixer if no device context
        ("set track 1 volume to -10", "mixer", "Volume"),
    ]

    passed = 0
    failed = 0

    print("=" * 70)
    print("LAYER 3: DEVICE/PARAM PARSER TESTS")
    print("=" * 70)
    print()

    for text, expected_device_type, expected_param in tests:
        result = parse_device_param(text.lower(), parse_index)

        # Check if device type matches (or starts with expected for fuzzy matches)
        device_matches = (
            (result.device_type == expected_device_type) or
            (result.device == expected_device_type) or
            (expected_device_type == "mixer" and result.device == "mixer")
        )

        # Check if param matches (case-insensitive)
        param_matches = (
            result.param and
            result.param.lower() == expected_param.lower()
        )

        if device_matches and param_matches:
            print(f"✓ {text}")
            print(f"  → device={result.device}, device_type={result.device_type}, param={result.param}")
            passed += 1
        else:
            print(f"✗ {text}")
            print(f"  Expected: device_type={expected_device_type}, param={expected_param}")
            print(f"  Got:      device={result.device}, device_type={result.device_type}, param={result.param}")
            failed += 1

        print()

    print("=" * 70)
    print(f"SUMMARY: {passed} passed, {failed} failed")
    print("=" * 70)

    return failed == 0


if __name__ == "__main__":
    success = test_device_param_parser()
    sys.exit(0 if success else 1)
