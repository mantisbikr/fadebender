#!/usr/bin/env python3
"""
Automatic S/C Gain calibration - sweeps through values and captures points.
"""
import sys
import os
os.environ["FIRESTORE_DATABASE_ID"] = "dev-display-value"
sys.path.insert(0, '/Users/sunils/ai-projects/fadebender')

from google.cloud import firestore
from server.services.ableton_client import request_op
import time

COMPRESSOR_SIG = "9e906e0ab3f18c4688107553744914f9ef6b9ee7"

def read_sc_gain():
    """Read current S/C Gain value (both norm and display)."""
    result = request_op("get_return_device_params", return_index=2, device_index=0)
    if result:
        params = result.get('data', {}).get('params', [])
        sc_gain = next((p for p in params if p['index'] == 21), None)
        if sc_gain:
            return {
                'norm': float(sc_gain['value']),
                'display': float(sc_gain['display_value'])
            }
    return None

def set_sc_gain(norm_value):
    """Set S/C Gain to a normalized value."""
    # Enable S/C On first
    request_op("set_return_device_param", return_index=2, device_index=0,
               param_index=20, value=1.0)

    # Set S/C Gain
    request_op("set_return_device_param", return_index=2, device_index=0,
               param_index=21, value=norm_value)

    time.sleep(0.1)  # Small delay for Live to update

def calibrate_sc_gain():
    """Calibrate S/C Gain by sampling across the range."""
    print("=" * 80)
    print("S/C GAIN AUTOMATIC CALIBRATION")
    print("=" * 80)

    # Sample normalized values from 0.0 to 1.0
    norm_samples = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]

    points = []

    print("\nSampling S/C Gain across the range...")
    print(f"{'Norm':>12s} {'Display (dB)':>15s}")
    print("-" * 30)

    for norm in norm_samples:
        # Set value
        set_sc_gain(norm)

        # Read back
        data = read_sc_gain()
        if data:
            points.append({
                'norm': data['norm'],
                'display': data['display']
            })
            print(f"{data['norm']:>12.6f} {data['display']:>15.2f}")
        else:
            print(f"{norm:>12.6f} {'ERROR':>15s}")

    if len(points) < 2:
        print(f"\n❌ ERROR: Only got {len(points)} valid points")
        return False

    # Sort by display value
    points = sorted(points, key=lambda p: p['display'])

    # Convert to Firestore format
    points_dict = {}
    for i, p in enumerate(points):
        points_dict[f"p{i}"] = {
            "norm": float(p['norm']),
            "display": float(p['display'])
        }

    # Apply to Firestore
    print("\n" + "=" * 80)
    print(f"Captured {len(points)} calibration points")
    print(f"Range: {points[0]['display']:.1f} to {points[-1]['display']:.1f} dB")
    print("\nApplying to Firestore...")

    client = firestore.Client(database="dev-display-value")
    doc_ref = client.collection("device_mappings").document(COMPRESSOR_SIG)
    doc = doc_ref.get()

    if not doc.exists:
        print("❌ Compressor device not found")
        return False

    data = doc.to_dict()
    params_meta = data.get("params_meta", [])

    # Find S/C Gain
    for param in params_meta:
        if param.get("name") == "S/C Gain":
            param["fit"] = {
                "type": "point_based",
                "points": points_dict,
                "point_count": len(points),
                "interpolation": "linear"
            }
            param["confidence"] = 1.0
            break
    else:
        print("❌ S/C Gain parameter not found")
        return False

    # Save
    data["params_meta"] = params_meta
    doc_ref.update({"params_meta": params_meta})

    print("\n✅ SUCCESS - S/C Gain calibrated!")
    print(f"   Points: {len(points)}")
    print(f"   Range: {points[0]['display']:.1f} to {points[-1]['display']:.1f} dB")
    print(f"   Database: dev-display-value")

    return True

if __name__ == "__main__":
    calibrate_sc_gain()
