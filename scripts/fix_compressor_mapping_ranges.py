#!/usr/bin/env python3
"""
Fix Compressor device mapping ranges based on actual Live testing.
Addresses all reported issues with parameter ranges and types.
"""
import sys
import os
os.environ["FIRESTORE_DATABASE_ID"] = "dev-display-value"
sys.path.insert(0, '/Users/sunils/ai-projects/fadebender')

from google.cloud import firestore
from server.services.ableton_client import request_op
import argparse

COMPRESSOR_SIG = "9e906e0ab3f18c4688107553744914f9ef6b9ee7"

def test_parameter_range(return_index, device_index, param_index):
    """Test a parameter by setting it to min and max to get display values."""
    # Set to min (0.0)
    request_op("set_return_device_param", return_index=return_index, device_index=device_index,
               param_index=param_index, value=0.0)
    result = request_op("get_return_device_params", return_index=return_index, device_index=device_index)
    params = result.get('data', {}).get('params', [])
    p_min = next((p for p in params if p['index'] == param_index), None)
    min_display = float(p_min['display_value']) if p_min else None

    # Set to max (1.0)
    request_op("set_return_device_param", return_index=return_index, device_index=device_index,
               param_index=param_index, value=1.0)
    result = request_op("get_return_device_params", return_index=return_index, device_index=device_index)
    params = result.get('data', {}).get('params', [])
    p_max = next((p for p in params if p['index'] == param_index), None)
    max_display = float(p_max['display_value']) if p_max else None

    return min_display, max_display


def fix_compressor_ranges(auto_confirm=False, test_ranges=False):
    """Fix all Compressor parameter ranges based on Live testing."""

    client = firestore.Client(database="dev-display-value")
    doc_ref = client.collection("device_mappings").document(COMPRESSOR_SIG)

    doc = doc_ref.get()
    if not doc.exists:
        print(f"❌ Error: Compressor device not found")
        return False

    data = doc.to_dict()
    params_meta = data.get("params_meta", [])

    print("=" * 80)
    print("COMPRESSOR MAPPING RANGE FIXES")
    print("=" * 80)

    # Corrected parameter specifications based on Live testing
    param_fixes = {
        "Threshold": {
            "min_display": -70.0,  # Was -60.0, should be -70.0
            "max_display": 6.0,  # Was 0.0, should be 6.0
        },
        "Ratio": {
            "min_display": 1.0,
            "max_display": 63.0,  # Actual usable max before infinity
        },
        "Expansion Ratio": {
            "min_display": 1.0,
            "max_display": 2.0,  # Was 10.0, should be 2.0
        },
        "Release": {
            "min_display": 1.0,  # Was 10.0, should be 1.0
            "max_display": 3000.0,  # Was 1000.0, should be 3000.0
        },
        "Knee": {
            "unit": "dB",  # Was "", should be "dB"
            "min_display": 0.0,
            "max_display": 18.0,  # Was 1.0, should be 18.0
        },
        "Output Gain": {
            "min_display": -36.0,  # Was 0.0, should be -36.0
            "max_display": 36.0,  # Was 30.0, should be 36.0
        },
        "LookAhead": {
            "control_type": "quantized",  # Was binary, should be quantized
            "labels": ["0 ms", "1 ms", "10 ms"],
        },
        "S/C Gain": {
            "min_display": -70.0,  # Was -24.0, should be -70.0
            "max_display": 24.0,
        },
        "S/C EQ Type": {
            "labels": ["Lowpass", "Bandpass", "Highpass", "Notch", "Peak", "Bell"],  # 6 types, was 5
        },
        "S/C EQ Freq": {
            "min_display": 30.0,  # Was 20.0, should be 30.0
            "max_display": 15000.0,  # Was 20000.0, should be 15000.0 (15 kHz)
        },
    }

    # If testing, query Live for actual ranges
    if test_ranges:
        print("\n📊 Testing parameter ranges in Live...")
        for idx in [1, 2, 3, 5]:  # Threshold, Ratio, Expansion Ratio, Release
            result = request_op("get_return_device_params", return_index=2, device_index=0)
            params = result.get('data', {}).get('params', [])
            param = next((p for p in params if p['index'] == idx), None)
            if param:
                min_d, max_d = test_parameter_range(2, 0, idx)
                print(f"  {param['name']:20s} (idx {idx}): {min_d} to {max_d}")

    # Apply fixes
    print("\n🔧 Applying fixes...")
    for param in params_meta:
        name = param.get("name")
        if name in param_fixes:
            fixes = param_fixes[name]
            for key, value in fixes.items():
                if value is not None:
                    old_value = param.get(key)
                    param[key] = value
                    print(f"  ✓ {name:30s} {key:20s}: {old_value} → {value}")

            # Update label_map for quantized parameters
            if fixes.get("control_type") == "quantized" and "labels" in fixes:
                param["control_type"] = "quantized"
                param["labels"] = fixes["labels"]
                param["label_map"] = {str(float(i)): label for i, label in enumerate(fixes["labels"])}
                param["max"] = float(len(fixes["labels"]) - 1)
                print(f"  ✓ {name:30s} Updated label_map with {len(fixes['labels'])} labels")

    # Fix index gap if needed (shift indices 12-22 down to 11-21 - already done in enrich script)

    # Preview changes
    print("\n" + "=" * 80)
    print("PREVIEW OF FIXED RANGES")
    print("=" * 80)
    for name, fixes in param_fixes.items():
        param = next((p for p in params_meta if p.get("name") == name), None)
        if param:
            ct = param.get("control_type")
            if ct == "continuous":
                min_d = param.get("min_display")
                max_d = param.get("max_display")
                unit = param.get("unit", "")
                print(f"{name:30s} {ct:12s} {min_d:8.1f} to {max_d:8.1f} {unit}")
            elif ct == "quantized":
                labels = param.get("labels", [])
                print(f"{name:30s} {ct:12s} {len(labels)} options: {', '.join(labels)}")

    # Confirm and update
    print("\n" + "=" * 80)
    if auto_confirm:
        response = 'yes'
    else:
        response = input("Apply these fixes to Firestore? (yes/no): ")

    if response.lower() not in ['yes', 'y']:
        print("❌ Aborted - no changes made")
        return False

    # Update Firestore
    data["params_meta"] = params_meta
    doc_ref.update({"params_meta": params_meta})

    print("\n✅ SUCCESS - Compressor ranges fixed!")
    print(f"  Database: dev-display-value")
    print(f"  Signature: {COMPRESSOR_SIG}")
    print(f"  Fixed parameters: {len(param_fixes)}")

    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fix Compressor parameter ranges")
    parser.add_argument('--yes', '-y', action='store_true', help='Auto-confirm changes')
    parser.add_argument('--test', '-t', action='store_true', help='Test ranges in Live first')
    args = parser.parse_args()

    success = fix_compressor_ranges(auto_confirm=args.yes, test_ranges=args.test)
    sys.exit(0 if success else 1)
