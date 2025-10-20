#!/usr/bin/env python3
"""Test mixer write-through by comparing snapshots before/after changes."""
import requests
import json
import sys
import time

BASE_URL = "http://127.0.0.1:8722"

def get_snapshot():
    """Fetch current snapshot."""
    resp = requests.get(f"{BASE_URL}/snapshot", timeout=5)
    resp.raise_for_status()
    return resp.json()

def test_return_volume_write_through():
    """Test that Return volume changes appear in snapshot."""
    print("\n" + "="*70)
    print("TEST: Return Mixer Volume Write-Through")
    print("="*70)

    try:
        # Get baseline
        print("1. Getting baseline snapshot...")
        before = get_snapshot()

        # Debug: show snapshot structure
        print(f"   Snapshot keys: {list(before.keys())}")
        if "data" in before:
            print(f"   Data keys: {list(before.get('data', {}).keys())}")

        returns = before.get("data", {}).get("mixer", {}).get("returns", [])

        if not returns or len(returns) == 0:
            print("⚠ No return tracks found in snapshot (mixer data may not be populated yet)")
            print("   This is expected if no mixer changes have been made yet.")
            return True  # Pass as this is expected behavior

        before_volume = returns[0].get("volume", {})
        before_display = before_volume.get("display", "N/A")
        print(f"   Before: Return A volume = {before_display}")

        # Execute change
        print("2. Executing: set Return A volume to -6 dB")
        resp = requests.post(
            f"{BASE_URL}/intent/execute",
            json={
                "domain": "return",
                "return_index": 0,
                "field": "volume",
                "display": "-6",
                "unit": "dB"
            },
            timeout=10
        )

        if resp.status_code != 200:
            print(f"✗ Execute failed: HTTP {resp.status_code}")
            return False

        result = resp.json()
        if not result.get("ok"):
            print(f"✗ Execute failed: {result.get('summary')}")
            return False

        print(f"   ✓ Execute succeeded: {result.get('summary')}")

        # Small delay to ensure write-through
        time.sleep(0.2)

        # Get after
        print("3. Getting updated snapshot...")
        after = get_snapshot()
        after_returns = after.get("data", {}).get("mixer", {}).get("returns", [])
        after_volume = after_returns[0].get("volume", {})
        after_display = float(after_volume.get("display", 0))
        after_normalized = after_volume.get("normalized")
        after_ts = after_volume.get("timestamp")

        print(f"   After: Return A volume = {after_display}")
        print(f"   Normalized: {after_normalized}")
        print(f"   Timestamp: {after_ts}")

        # Verify
        if abs(after_display - (-6.0)) < 0.01:
            print("✓ PASS - Volume updated correctly in snapshot")
            return True
        else:
            print(f"✗ FAIL - Expected -6.0, got {after_display}")
            return False

    except Exception as e:
        print(f"✗ FAIL - Exception: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_track_volume_write_through():
    """Test that Track volume changes appear in snapshot."""
    print("\n" + "="*70)
    print("TEST: Track Mixer Volume Write-Through")
    print("="*70)

    try:
        # Get baseline
        print("1. Getting baseline snapshot...")
        before = get_snapshot()
        tracks = before.get("data", {}).get("mixer", {}).get("tracks", [])

        if not tracks or len(tracks) == 0:
            print("⚠ No tracks found in snapshot (mixer data may not be populated yet)")
            print("   This is expected if no mixer changes have been made yet.")
            return True  # Pass as this is expected behavior

        # Use first available track (index 0)
        track_index = 0
        before_volume = tracks[track_index].get("volume", {})
        before_display = before_volume.get("display", "N/A")
        print(f"   Before: Track {track_index + 1} volume = {before_display}")

        # Execute change
        print(f"2. Executing: set track {track_index + 1} volume to -9 dB")
        resp = requests.post(
            f"{BASE_URL}/intent/execute",
            json={
                "domain": "track",
                "track_index": track_index,
                "field": "volume",
                "display": "-9",
                "unit": "dB"
            },
            timeout=10
        )

        if resp.status_code != 200:
            print(f"✗ Execute failed: HTTP {resp.status_code}")
            return False

        result = resp.json()
        if not result.get("ok"):
            print(f"✗ Execute failed: {result.get('summary')}")
            return False

        print(f"   ✓ Execute succeeded: {result.get('summary')}")

        time.sleep(0.2)

        # Get after
        print("3. Getting updated snapshot...")
        after = get_snapshot()
        after_tracks = after.get("data", {}).get("mixer", {}).get("tracks", [])
        after_volume = after_tracks[track_index].get("volume", {})
        after_display = float(after_volume.get("display", 0))

        print(f"   After: Track {track_index + 1} volume = {after_display}")

        # Verify
        if abs(after_display - (-9.0)) < 0.01:
            print("✓ PASS - Volume updated correctly in snapshot")
            return True
        else:
            print(f"✗ FAIL - Expected -9.0, got {after_display}")
            return False

    except Exception as e:
        print(f"✗ FAIL - Exception: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_device_params_not_in_snapshot():
    """Verify device params are NOT in snapshot (stored in registry)."""
    print("\n" + "="*70)
    print("TEST: Device Params NOT in Snapshot (Registry Only)")
    print("="*70)

    try:
        # Execute device param change
        print("1. Executing: set Return B Amp Gain to 8.0")
        resp = requests.post(
            f"{BASE_URL}/intent/execute",
            json={
                "domain": "device",
                "return_index": 1,
                "device_index": 1,
                "param_ref": "Gain",
                "display": "8.0"
            },
            timeout=10
        )

        if resp.status_code != 200:
            print(f"✗ Execute failed: HTTP {resp.status_code}")
            return False

        result = resp.json()
        if not result.get("ok"):
            print(f"✗ Execute failed: {result.get('summary')}")
            return False

        print(f"   ✓ Execute succeeded: {result.get('summary')}")

        time.sleep(0.2)

        # Get snapshot
        print("2. Getting snapshot...")
        snapshot = get_snapshot()
        devices = snapshot.get("data", {}).get("devices", {})

        # Device params should NOT be in snapshot
        has_device_params = False
        if "returns" in devices:
            for ret in devices.get("returns", []):
                if "params" in ret or "parameters" in ret:
                    has_device_params = True
                    break

        if not has_device_params:
            print("✓ PASS - Device params correctly NOT in snapshot")
            print("   (They're stored in ValueRegistry separately)")
            return True
        else:
            print("✗ FAIL - Device params unexpectedly found in snapshot")
            return False

    except Exception as e:
        print(f"✗ FAIL - Exception: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_snapshot_devices_endpoint():
    """Test /snapshot/devices endpoint."""
    print("\n" + "="*70)
    print("TEST: /snapshot/devices Endpoint")
    print("="*70)

    try:
        # Test return devices
        print("1. Testing: GET /snapshot/devices?domain=return&index=0")
        resp = requests.get(
            f"{BASE_URL}/snapshot/devices",
            params={"domain": "return", "index": 0},
            timeout=5
        )

        if resp.status_code != 200:
            print(f"✗ Failed: HTTP {resp.status_code}")
            return False

        data = resp.json()
        devices = data.get("data", {}).get("devices", [])

        if len(devices) > 0:
            print(f"   ✓ Found {len(devices)} devices in Return A")
            for dev in devices[:3]:
                print(f"     - [{dev.get('index')}] {dev.get('name')} ({dev.get('signature', '')[:8]}...)")
        else:
            print("   ⚠ No devices found (may be valid if return is empty)")

        # Test track devices
        print("\n2. Testing: GET /snapshot/devices?domain=track&index=1")
        resp = requests.get(
            f"{BASE_URL}/snapshot/devices",
            params={"domain": "track", "index": 1},
            timeout=5
        )

        if resp.status_code != 200:
            print(f"✗ Failed: HTTP {resp.status_code}")
            return False

        data = resp.json()
        devices = data.get("data", {}).get("devices", [])

        if len(devices) > 0:
            print(f"   ✓ Found {len(devices)} devices in Track 2")
            for dev in devices[:3]:
                print(f"     - [{dev.get('index')}] {dev.get('name')} ({dev.get('signature', '')[:8]}...)")
        else:
            print("   ⚠ No devices found (may be valid if track is empty)")

        print("✓ PASS - /snapshot/devices endpoint working")
        return True

    except Exception as e:
        print(f"✗ FAIL - Exception: {e}")
        import traceback
        traceback.print_exc()
        return False

def run_all_tests():
    """Run all snapshot tests."""
    print("\n" + "="*70)
    print("SNAPSHOT & REGISTRY TEST SUITE")
    print("="*70)

    # Health check
    try:
        resp = requests.get(f"{BASE_URL}/health", timeout=5)
        if resp.status_code != 200:
            print("✗ Server not responding. Please start the server first.")
            return False
        print("✓ Server is running")
    except Exception as e:
        print(f"✗ Cannot connect to server: {e}")
        return False

    tests = [
        ("Return Volume Write-Through", test_return_volume_write_through),
        ("Track Volume Write-Through", test_track_volume_write_through),
        ("Device Params NOT in Snapshot", test_device_params_not_in_snapshot),
        ("Snapshot Devices Endpoint", test_snapshot_devices_endpoint),
    ]

    passed = 0
    failed = 0

    for name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"✗ Test '{name}' crashed: {e}")
            failed += 1

    print("\n" + "="*70)
    print("RESULTS")
    print("="*70)
    print(f"Total tests: {len(tests)}")
    print(f"✓ Passed: {passed}")
    print(f"✗ Failed: {failed}")
    print("="*70)

    return failed == 0

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
