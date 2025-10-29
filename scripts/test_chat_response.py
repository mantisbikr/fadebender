#!/usr/bin/env python3
"""
Test that chat service returns proper response structure with capabilities.
"""
import sys
import os
import json

# Add paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'server'))

# Mock the Ableton client to avoid Live dependency
class MockAbletonClient:
    @staticmethod
    def request_op(op, **kwargs):
        if op == "get_overview":
            return {
                "ok": True,
                "data": {
                    "tracks": [{"index": 0, "name": "Track 1"}]
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
                    "pan": 0.0,
                    "mute": False,
                    "solo": False
                }
            }
        return {"ok": True}

# Patch before importing
sys.modules['server.services.ableton_client'] = type('MockModule', (), {
    'request_op': MockAbletonClient.request_op
})()

from server.services.chat_service import ChatBody, handle_chat

print("=" * 80)
print("TESTING CHAT RESPONSE STRUCTURE")
print("=" * 80)

# Test a simple volume command
test_cases = [
    ("set track 1 volume to -12 dB", "Volume command"),
]

for query, description in test_cases:
    print(f"\nTest: {description}")
    print(f"Query: '{query}'")
    print("-" * 80)

    try:
        body = ChatBody(text=query, confirm=True)
        result = handle_chat(body)

        print(f"✓ Command executed")
        print(f"  ok: {result.get('ok')}")
        print(f"  summary: {result.get('summary', 'N/A')}")

        if "data" in result:
            print(f"  ✓ data field present")
            if "capabilities" in result.get("data", {}):
                print(f"    ✓ capabilities present")
                caps = result["data"]["capabilities"]
                if isinstance(caps, dict):
                    print(f"      Keys: {list(caps.keys())}")
            else:
                print(f"    ✗ capabilities MISSING")
        else:
            print(f"  ✗ data field MISSING")

        if "intent" in result:
            print(f"  ✓ intent field present")

        if "canonical" in result:
            print(f"  ✓ canonical field present")

        print("\n  Full structure:")
        print(f"  {json.dumps({k: '...' if k in ('intent', 'canonical') else v for k, v in result.items()}, indent=2)}")

    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()

print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
print("\nThe response should include:")
print("  ✓ ok: true/false")
print("  ✓ summary: descriptive message")
print("  ✓ data: { capabilities: {...} }")
print("  ✓ intent: original NLP intent")
print("  ✓ canonical: canonical intent format")
print()
