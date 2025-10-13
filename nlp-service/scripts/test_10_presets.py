#!/usr/bin/env python3
"""
Test loading 10 Reverb presets and verify all parameters match.
"""

import requests
import json
import sys

SERVER_URL = "http://127.0.0.1:8722"
RETURN_INDEX = 0
DEVICE_INDEX = 0

# 10 diverse presets to test
TEST_PRESETS = [
    "reverb_guitar_room",
    "reverb_bright_room",
    "reverb_vocal_hall",
    "reverb_cathedral",
    "reverb_small_room",
    "reverb_plate_damped",
    "reverb_arena_tail",
    "reverb_living_room",
    "reverb_stadium",
    "reverb_warm_reverb_long"
]


def test_preset(preset_id):
    """Test loading a single preset and verify values."""

    # Get preset values
    try:
        preset_resp = requests.get(f"{SERVER_URL}/presets/{preset_id}", timeout=5)
        preset_resp.raise_for_status()
        preset = preset_resp.json()
        preset_name = preset.get("name", preset_id)
        preset_values = preset.get("parameter_values", {})
    except Exception as e:
        return {"success": False, "preset_id": preset_id, "error": f"Failed to get preset: {e}"}

    # Apply preset
    try:
        apply_resp = requests.post(
            f"{SERVER_URL}/return/device/apply_preset",
            json={
                "return_index": RETURN_INDEX,
                "device_index": DEVICE_INDEX,
                "preset_id": preset_id
            },
            timeout=10
        )
        apply_resp.raise_for_status()
        result = apply_resp.json()

        if not result.get("ok"):
            return {"success": False, "preset_id": preset_id, "error": "Apply failed"}

        applied = result.get("applied", 0)
        errors = result.get("errors") or []

    except Exception as e:
        return {"success": False, "preset_id": preset_id, "error": f"Failed to apply: {e}"}

    # Read back and verify
    try:
        live_resp = requests.get(
            f"{SERVER_URL}/return/device/params",
            params={"index": RETURN_INDEX, "device": DEVICE_INDEX},
            timeout=5
        )
        live_resp.raise_for_status()
        live_data = live_resp.json()
        live_params = live_data.get("data", {}).get("params", [])

        # Compare all parameters
        matches = 0
        mismatches = 0

        for param_name, expected_value in preset_values.items():
            live_param = next((p for p in live_params if p.get("name") == param_name), None)
            if not live_param:
                mismatches += 1
                continue

            actual_value = live_param.get("value")
            if abs(actual_value - expected_value) < 0.001:
                matches += 1
            else:
                mismatches += 1

        return {
            "success": mismatches == 0,
            "preset_id": preset_id,
            "preset_name": preset_name,
            "applied": applied,
            "total": len(preset_values),
            "matches": matches,
            "mismatches": mismatches,
            "apply_errors": len(errors)
        }

    except Exception as e:
        return {"success": False, "preset_id": preset_id, "error": f"Failed to verify: {e}"}


def main():
    print("="*70)
    print("TESTING 10 REVERB PRESETS")
    print("="*70)
    print(f"\nTarget: Return {RETURN_INDEX}, Device {DEVICE_INDEX}")
    print(f"Testing {len(TEST_PRESETS)} presets...\n")

    results = []

    for i, preset_id in enumerate(TEST_PRESETS, 1):
        print(f"[{i}/{len(TEST_PRESETS)}] Testing: {preset_id}...", end=" ")

        result = test_preset(preset_id)
        results.append(result)

        if result.get("success"):
            matches = result.get("matches", 0)
            total = result.get("total", 0)
            apply_errors = result.get("apply_errors", 0)
            status = "✓" if apply_errors == 0 else f"✓ ({apply_errors} apply errors)"
            print(f"{status} {matches}/{total} params verified")
        else:
            print(f"✗ {result.get('error', 'Unknown error')}")

    # Summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)

    successful = sum(1 for r in results if r.get("success"))
    total_tests = len(results)

    print(f"\nResults: {successful}/{total_tests} presets passed")
    print(f"\nDetails:")

    for result in results:
        status = "✓" if result.get("success") else "✗"
        name = result.get("preset_name", result.get("preset_id"))

        if result.get("success"):
            matches = result.get("matches", 0)
            total = result.get("total", 0)
            apply_errors = result.get("apply_errors", 0)
            error_note = f" ({apply_errors} apply errors)" if apply_errors > 0 else ""
            print(f"  {status} {name:25s} {matches}/{total} verified{error_note}")
        else:
            print(f"  {status} {name:25s} FAILED")

    if successful == total_tests:
        print(f"\n✅ ALL {total_tests} PRESETS PASSED!")
        print("   - All parameters verified correctly in Live")
        print("   - dev-display-value database working perfectly")
        return True
    else:
        print(f"\n⚠️  {total_tests - successful} preset(s) failed")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
