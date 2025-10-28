#!/usr/bin/env python3
"""
Debug capabilities for "set track 1 pan to 30R" command.
Tests the entire chain to see where capabilities are lost.
"""
import sys
import os
import json

# Add paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'server'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'nlp-service'))

# Mock the Ableton client to avoid Live dependency
def _mock_request_op(op, **kwargs):
    if op == "get_overview":
        return {
            "ok": True,
            "data": {
                "tracks": [
                    {"index": 0, "name": "Track 1"},
                    {"index": 1, "name": "Track 2"}
                ]
            }
        }
    elif op == "set_mixer":
        return {
            "ok": True
        }
    elif op == "get_track_mixer":
        return {
            "ok": True,
            "data": {
                "volume": 0.85,
                "pan": 0.3,  # 30R
                "mute": False,
                "solo": False
            }
        }
    return {"ok": True}

def _mock_data_or_raw(resp):
    """Helper to extract data field or return raw response."""
    if not resp:
        return None
    data = resp.get("data") if isinstance(resp, dict) else None
    return data if data is not None else resp

# Create a module-like object with function attributes
from types import SimpleNamespace
mock_module = SimpleNamespace(
    request_op=_mock_request_op,
    data_or_raw=_mock_data_or_raw
)

# Patch before importing
sys.modules['server.services.ableton_client'] = mock_module

print("=" * 80)
print("DEBUGGING CAPABILITIES FOR: 'set track 1 pan to 30R'")
print("=" * 80)

command = "set track 1 pan to 30R"

# Step 1: Test NLP parsing
print("\n[STEP 1] NLP Parsing")
print("-" * 80)
try:
    from llm_daw import interpret_daw_command
    intent = interpret_daw_command(command)
    print(f"✓ Intent parsed:")
    print(f"  intent: {intent.get('intent')}")
    print(f"  Full: {json.dumps(intent, indent=2, default=str)}")
except Exception as e:
    print(f"✗ NLP parsing failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Step 2: Test intent mapping
print("\n[STEP 2] Intent Mapping")
print("-" * 80)
try:
    from server.services.intent_mapper import map_llm_to_canonical
    canonical, errors = map_llm_to_canonical(intent)
    print(f"✓ Canonical intent:")
    print(f"  domain: {canonical.get('domain')}")
    print(f"  field: {canonical.get('field')}")
    print(f"  track_index: {canonical.get('track_index')}")
    print(f"  value: {canonical.get('value')}")
    print(f"  Full: {json.dumps(canonical, indent=2, default=str)}")
    if errors:
        print(f"  Errors: {errors}")
except Exception as e:
    print(f"✗ Intent mapping failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Step 3: Test execute_intent
print("\n[STEP 3] Execute Intent")
print("-" * 80)
try:
    from server.api.intents import execute_intent
    from server.models.intents_api import CanonicalIntent
    canonical_intent = CanonicalIntent(**canonical)
    result = execute_intent(canonical_intent, debug=False)

    print(f"✓ Execution result:")
    print(f"  ok: {result.get('ok')}")
    print(f"  Keys in result: {list(result.keys())}")

    if "data" in result:
        print(f"  ✓ 'data' field present")
        data = result["data"]
        if isinstance(data, dict):
            print(f"    Keys in data: {list(data.keys())}")
            if "capabilities" in data:
                print(f"    ✓ 'capabilities' present in data")
                caps = data["capabilities"]
                if isinstance(caps, dict):
                    print(f"      Keys in capabilities: {list(caps.keys())}")
                else:
                    print(f"      ✗ capabilities is not a dict: {type(caps)}")
            else:
                print(f"    ✗ 'capabilities' MISSING in data")
        else:
            print(f"    ✗ data is not a dict: {type(data)}")
    else:
        print(f"  ✗ 'data' field MISSING from result")

    print(f"\n  Full result:")
    print(json.dumps(result, indent=2, default=str))
except Exception as e:
    print(f"✗ Execution failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Step 4: Test cap_utils directly
print("\n[STEP 4] Testing ensure_capabilities directly")
print("-" * 80)
try:
    from server.api.cap_utils import ensure_capabilities

    # Mock response from set_mixer
    mock_resp = {"ok": True}
    track_idx = 1

    print(f"Before ensure_capabilities:")
    print(f"  Response: {mock_resp}")

    result_with_caps = ensure_capabilities(mock_resp, domain="track", track_index=track_idx)

    print(f"\nAfter ensure_capabilities:")
    print(f"  Response keys: {list(result_with_caps.keys())}")

    if "data" in result_with_caps:
        print(f"  ✓ 'data' field present")
        data = result_with_caps["data"]
        if isinstance(data, dict):
            print(f"    Keys in data: {list(data.keys())}")
            if "capabilities" in data:
                print(f"    ✓ 'capabilities' present")
            else:
                print(f"    ✗ 'capabilities' MISSING")
        else:
            print(f"    ✗ data is not a dict")
    else:
        print(f"  ✗ 'data' field MISSING")

    print(f"\n  Full response:")
    print(json.dumps(result_with_caps, indent=2, default=str))
except Exception as e:
    print(f"✗ ensure_capabilities failed: {e}")
    import traceback
    traceback.print_exc()

# Step 5: Test get_track_mixer_capabilities directly
print("\n[STEP 5] Testing get_track_mixer_capabilities directly")
print("-" * 80)
try:
    from server.api.tracks import get_track_mixer_capabilities

    # Test with 0-based index (as API expects)
    caps = get_track_mixer_capabilities(index=0)  # Track 1 = index 0

    print(f"Result from get_track_mixer_capabilities(index=0):")
    print(f"  ok: {caps.get('ok') if isinstance(caps, dict) else 'not a dict'}")
    print(f"  Keys: {list(caps.keys()) if isinstance(caps, dict) else 'N/A'}")

    if isinstance(caps, dict) and caps.get("ok"):
        if "data" in caps:
            print(f"  ✓ 'data' present in capabilities response")
            print(f"    Data keys: {list(caps['data'].keys()) if isinstance(caps['data'], dict) else 'not a dict'}")
        else:
            print(f"  ✗ 'data' MISSING from capabilities response")

    print(f"\n  Full capabilities:")
    print(json.dumps(caps, indent=2, default=str))
except Exception as e:
    print(f"✗ get_track_mixer_capabilities failed: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
print("\nIf capabilities are missing at any step above, that's where the problem is.")
print("Check for import errors, Firestore access issues, or data structure mismatches.")
