#!/usr/bin/env python3
"""
End-to-end test: Load presets to Ableton Live and verify parameters.

Tests:
1. Apply preset to Return 0 Device 0 (Reverb)
2. Read back parameters from Live
3. Verify values match what we sent
"""

import requests
import json
import sys
from pathlib import Path

# Server configuration
SERVER_URL = "http://127.0.0.1:8722"

# Test configuration
RETURN_INDEX = 0
DEVICE_INDEX = 0
TEST_PRESETS = [
    "reverb_guitar_room",
    "reverb_bright_room",
    "reverb_vocal_hall"
]


def test_preset_loading():
    """Test end-to-end preset loading to Live."""

    print("="*70)
    print("END-TO-END PRESET LOADING TEST")
    print("="*70)

    # Check server health
    print(f"\n[1/5] Checking server connection...")
    try:
        response = requests.get(f"{SERVER_URL}/ping", timeout=2)
        response.raise_for_status()
        print(f"✓ Server is running at {SERVER_URL}")
    except Exception as e:
        print(f"❌ Cannot connect to server: {e}")
        print(f"   Make sure server is running: cd server && make dev-returns")
        return False

    # Check device exists
    print(f"\n[2/5] Checking Return {RETURN_INDEX} Device {DEVICE_INDEX}...")
    try:
        response = requests.get(
            f"{SERVER_URL}/return/device/params",
            params={"index": RETURN_INDEX, "device": DEVICE_INDEX},
            timeout=5
        )
        response.raise_for_status()
        data = response.json()

        if not data.get("ok"):
            print(f"❌ Device not found or not accessible")
            return False

        device_data = data.get("data", {})
        device_name = device_data.get("device_name", "Unknown")
        params = device_data.get("params", [])

        print(f"✓ Found device: {device_name}")
        print(f"  Parameters: {len(params)}")

        if len(params) == 0:
            print(f"⚠️  No parameters found - is device loaded in Live?")
            return False

    except Exception as e:
        print(f"❌ Error checking device: {e}")
        return False

    # Test each preset
    print(f"\n[3/5] Testing preset loading...")

    results = []

    for preset_id in TEST_PRESETS:
        print(f"\n  Testing: {preset_id}")
        print(f"  " + "-"*60)

        # Get preset data from Firestore
        try:
            response = requests.get(f"{SERVER_URL}/presets/{preset_id}", timeout=5)
            response.raise_for_status()
            preset = response.json()

            preset_name = preset.get("name", "Unknown")
            param_values = preset.get("parameter_values", {})

            print(f"    ✓ Loaded preset: {preset_name}")
            print(f"      Parameters to set: {len(param_values)}")

        except Exception as e:
            print(f"    ❌ Failed to get preset: {e}")
            results.append({"preset_id": preset_id, "success": False, "error": str(e)})
            continue

        # Apply preset to device
        print(f"    → Applying to Live...")
        try:
            response = requests.post(
                f"{SERVER_URL}/return/device/apply_preset",
                json={
                    "return_index": RETURN_INDEX,
                    "device_index": DEVICE_INDEX,
                    "preset_id": preset_id
                },
                timeout=10
            )
            response.raise_for_status()
            result = response.json()

            if not result.get("ok"):
                error = result.get("error", "Unknown error")
                print(f"    ❌ Failed to apply: {error}")
                results.append({"preset_id": preset_id, "success": False, "error": error})
                continue

            applied_count = result.get("applied", 0)
            print(f"    ✓ Applied {applied_count} parameters")

        except Exception as e:
            print(f"    ❌ Error applying preset: {e}")
            results.append({"preset_id": preset_id, "success": False, "error": str(e)})
            continue

        # Read back parameters from Live
        print(f"    → Reading back from Live...")
        try:
            response = requests.get(
                f"{SERVER_URL}/return/device/params",
                params={"index": RETURN_INDEX, "device": DEVICE_INDEX},
                timeout=5
            )
            response.raise_for_status()
            data = response.json()

            params = data.get("data", {}).get("params", [])

            # Compare sample parameters
            mismatches = 0
            matches = 0
            sample_params = ["Predelay", "Decay Time", "Room Size", "Dry/Wet"]

            print(f"    → Verifying sample parameters...")
            for param_name in sample_params:
                if param_name not in param_values:
                    continue

                expected = param_values[param_name]

                # Find actual value in Live
                param_obj = next((p for p in params if p.get("name") == param_name), None)
                if not param_obj:
                    continue

                actual = param_obj.get("value")

                # Allow small floating point differences
                if abs(actual - expected) < 0.001:
                    matches += 1
                    print(f"      ✓ {param_name}: {actual:.3f} (expected {expected:.3f})")
                else:
                    mismatches += 1
                    print(f"      ✗ {param_name}: {actual:.3f} (expected {expected:.3f})")

            success = mismatches == 0 and matches > 0
            results.append({
                "preset_id": preset_id,
                "preset_name": preset_name,
                "success": success,
                "matches": matches,
                "mismatches": mismatches
            })

            if success:
                print(f"    ✓ Verification PASSED ({matches} params matched)")
            else:
                print(f"    ⚠️  Verification issues ({mismatches} mismatches)")

        except Exception as e:
            print(f"    ❌ Error reading back: {e}")
            results.append({"preset_id": preset_id, "success": False, "error": str(e)})
            continue

    # Summary
    print(f"\n[4/5] Test Summary")
    print("="*70)

    successful = sum(1 for r in results if r.get("success"))
    total = len(results)

    print(f"\nResults: {successful}/{total} presets loaded successfully\n")

    for result in results:
        status = "✓" if result.get("success") else "✗"
        name = result.get("preset_name", result.get("preset_id"))
        print(f"  {status} {name}")
        if "matches" in result:
            print(f"     {result['matches']} params verified")
        if "error" in result:
            print(f"     Error: {result['error']}")

    print(f"\n[5/5] Conclusion")
    print("="*70)

    if successful == total:
        print(f"\n✅ ALL TESTS PASSED!")
        print(f"   - Presets loaded to Live successfully")
        print(f"   - Parameters verified correctly")
        print(f"   - dev-display-value database working perfectly")
        return True
    else:
        print(f"\n⚠️  {total - successful} test(s) failed")
        print(f"   Check server logs for details")
        return False


if __name__ == "__main__":
    success = test_preset_loading()
    sys.exit(0 if success else 1)
