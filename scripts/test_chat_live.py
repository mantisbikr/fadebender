#!/usr/bin/env python3
"""
Test chat endpoint to see actual response structure.
Run your server first, then run this script.
"""
import requests
import json

# Test with your running server
url = "http://localhost:8722/chat"

test_commands = [
    "set track 1 volume to -12 dB",
    "set track 1 pan to 30R",
]

print("=" * 80)
print("TESTING LIVE CHAT RESPONSES")
print("=" * 80)
print("\nMake sure your server is running on http://localhost:8722")
print()

for cmd in test_commands:
    print(f"\n{'='*80}")
    print(f"Command: {cmd}")
    print(f"{'='*80}")

    try:
        response = requests.post(url, json={"text": cmd, "confirm": True}, timeout=10)

        if response.status_code == 200:
            data = response.json()

            print(f"✓ Status: {response.status_code}")
            print(f"  ok: {data.get('ok')}")
            print(f"  summary: {data.get('summary', 'N/A')}")

            if "data" in data:
                print(f"  ✓ data field present")
                if "capabilities" in data.get("data", {}):
                    print(f"    ✓ capabilities present")
                    caps = data["data"]["capabilities"]
                    print(f"      Keys: {list(caps.keys()) if isinstance(caps, dict) else 'not a dict'}")
                else:
                    print(f"    ✗ capabilities MISSING in data")
                    print(f"      data keys: {list(data['data'].keys())}")
            else:
                print(f"  ✗ data field MISSING")

            print("\n  Full response structure:")
            print(json.dumps(data, indent=2, default=str))

        else:
            print(f"✗ HTTP {response.status_code}")
            print(f"  {response.text}")

    except requests.exceptions.ConnectionError:
        print(f"✗ Connection failed - is the server running?")
    except Exception as e:
        print(f"✗ Error: {e}")

print("\n" + "=" * 80)
print("DIAGNOSTICS")
print("=" * 80)
print("\nIf 'data.capabilities' is missing, the issue is in the server.")
print("If 'data.capabilities' is present but not showing in WebUI, the issue is in the client.")
print()
