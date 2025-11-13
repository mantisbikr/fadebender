#!/usr/bin/env python3
"""Integration test for Layer 4: Intent Builder & Full Layered Pipeline

Tests the complete 4-layer NLP architecture end-to-end.
"""

import sys
import requests
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import os
os.environ['FIRESTORE_DATABASE_ID'] = 'dev-display-value'

from server.services.nlp.intent_builder import parse_command_layered
from server.services.parse_index import ParseIndexBuilder

BASE_URL = "http://127.0.0.1:8722"


def test_layered_pipeline():
    """Test full layered pipeline (Layers 1-4) for various commands"""

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
        # ================================================================
        # TRANSPORT INTENTS (no targets)
        # ================================================================
        {
            "text": "play",
            "expected_intent": "transport",
            "expected_operation": {"action": "play", "value": None, "unit": None}
        },
        {
            "text": "stop",
            "expected_intent": "transport",
            "expected_operation": {"action": "stop", "value": None, "unit": None}
        },
        {
            "text": "set tempo to 120 bpm",
            "expected_intent": "transport",
            "expected_operation": {"action": None, "value": 120.0, "unit": "bpm"}
        },

        # ================================================================
        # MIXER PARAMETER INTENTS (plugin=None)
        # ================================================================
        {
            "text": "set track 1 volume to -10 dB",
            "expected_intent": "set_parameter",
            "expected_targets": [{
                "track": "Track 1",
                "plugin": None,
                "parameter": "Volume"
            }],
            "expected_operation": {"type": "absolute", "value": -10.0, "unit": "dB"}
        },
        {
            "text": "increase return A pan by 10",
            "expected_intent": "set_parameter",
            "expected_targets": [{
                "track": "Return A",
                "plugin": None,
                "parameter": "Pan"
            }],
            "expected_operation": {"type": "relative", "value": 10.0, "unit": "display"}
        },
        {
            "text": "mute track 2",
            "expected_intent": "set_parameter",
            "expected_targets": [{
                "track": "Track 2",
                "plugin": None,
                "parameter": "Mute"
            }],
            "expected_operation": {"type": "absolute", "value": True, "unit": None}
        },

        # ================================================================
        # DEVICE PARAMETER INTENTS (plugin=device name)
        # ================================================================
        {
            "text": "set return A reverb decay to 5 seconds",
            "expected_intent": "set_parameter",
            "expected_targets": [{
                "track": "Return A",
                "plugin": "Reverb",  # Capitalized device name from DeviceContextParser
                "parameter": "Reverb Decay"  # Actual param from Firestore
                # device_ordinal may be included (depends on parse_index)
            }],
            "expected_operation": {"type": "absolute", "value": 5.0, "unit": "s"}
        },
        {
            "text": "increase return C echo time by 100 ms",
            "expected_intent": "set_parameter",
            "expected_targets": [{
                "track": "Return C",
                "plugin": "8DotBall",  # Echo device type resolves to 8DotBall
                "parameter": "L Time"  # 8DotBall has separate L/R Time params
            }],
            "expected_operation": {"type": "relative", "value": 100.0, "unit": "ms"}
        },

        # ================================================================
        # NAVIGATION INTENTS
        # ================================================================
        {
            "text": "open track 1",
            "expected_intent": "open_capabilities",
            "expected_target": "Track 1"
        },
        {
            "text": "list tracks",
            "expected_intent": "list_capabilities",
            "expected_target": None
        },
    ]

    passed = 0
    failed = 0

    print("=" * 70)
    print("LAYER 4: INTENT BUILDER & FULL PIPELINE TESTS")
    print("=" * 70)
    print()

    for test in tests:
        text = test["text"]
        result = parse_command_layered(text, parse_index)

        if not result:
            print(f"✗ {text}")
            print(f"  Expected intent, got None")
            failed += 1
            print()
            continue

        # Check intent type
        intent_match = result.get("intent") == test.get("expected_intent")

        # Check based on intent type
        if test.get("expected_intent") == "transport":
            # Transport: check operation
            op = result.get("operation", {})
            expected_op = test.get("expected_operation", {})
            operation_match = (
                op.get("action") == expected_op.get("action") and
                op.get("value") == expected_op.get("value") and
                op.get("unit") == expected_op.get("unit")
            )

            if intent_match and operation_match:
                print(f"✓ {text}")
                print(f"  → intent={result['intent']}, operation={result['operation']}")
                passed += 1
            else:
                print(f"✗ {text}")
                print(f"  Expected: intent={test['expected_intent']}, op={expected_op}")
                print(f"  Got:      intent={result.get('intent')}, op={op}")
                failed += 1

        elif test.get("expected_intent") == "set_parameter":
            # Parameter intent: check targets and operation
            targets = result.get("targets", [])
            expected_targets = test.get("expected_targets", [])

            targets_match = len(targets) == len(expected_targets)
            if targets_match and len(targets) > 0:
                t = targets[0]
                et = expected_targets[0]
                # Compare only specified fields (ignore device_ordinal if not specified in expected)
                targets_match = (
                    t.get("track") == et.get("track") and
                    t.get("plugin") == et.get("plugin") and
                    t.get("parameter") == et.get("parameter")
                )
                # If device_ordinal is specified in expected, check it
                if "device_ordinal" in et:
                    targets_match = targets_match and t.get("device_ordinal") == et.get("device_ordinal")

            op = result.get("operation", {})
            expected_op = test.get("expected_operation", {})
            operation_match = (
                op.get("type") == expected_op.get("type") and
                op.get("value") == expected_op.get("value") and
                op.get("unit") == expected_op.get("unit")
            )

            if intent_match and targets_match and operation_match:
                print(f"✓ {text}")
                print(f"  → intent={result['intent']}, target={targets[0]}, op={result['operation']}")
                passed += 1
            else:
                print(f"✗ {text}")
                print(f"  Expected: intent={test['expected_intent']}, targets={expected_targets}, op={expected_op}")
                print(f"  Got:      intent={result.get('intent')}, targets={targets}, op={op}")
                failed += 1

        elif test.get("expected_intent") in ("open_capabilities", "list_capabilities"):
            # Navigation intent: check target
            target_match = result.get("target") == test.get("expected_target")

            if intent_match and target_match:
                print(f"✓ {text}")
                print(f"  → intent={result['intent']}, target={result.get('target')}")
                passed += 1
            else:
                print(f"✗ {text}")
                print(f"  Expected: intent={test['expected_intent']}, target={test.get('expected_target')}")
                print(f"  Got:      intent={result.get('intent')}, target={result.get('target')}")
                failed += 1

        else:
            print(f"✗ {text} - Unknown test type")
            failed += 1

        print()

    print("=" * 70)
    print(f"SUMMARY: {passed} passed, {failed} failed")
    print("=" * 70)

    return failed == 0


if __name__ == "__main__":
    success = test_layered_pipeline()
    sys.exit(0 if success else 1)
