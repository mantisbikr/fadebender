#!/usr/bin/env python3
"""
Copy the track volume piecewise fit to Compressor Threshold parameter.
Both have the same -70 to +6 dB range.
"""
import sys
import os
os.environ["FIRESTORE_DATABASE_ID"] = "dev-display-value"
sys.path.insert(0, '/Users/sunils/ai-projects/fadebender')

from google.cloud import firestore

COMPRESSOR_SIG = "9e906e0ab3f18c4688107553744914f9ef6b9ee7"

def copy_volume_fit_to_threshold():
    """Copy the piecewise volume fit to Threshold."""
    client = firestore.Client(database="dev-display-value")

    # Get track volume fit
    print("Reading track volume fit...")
    mixer_doc = client.collection("mixer_mappings").document("track_channel").get()
    if not mixer_doc.exists:
        print("❌ track_channel not found")
        return False

    mixer_data = mixer_doc.to_dict()
    params_meta = mixer_data.get("params_meta", [])
    if not params_meta:
        print("❌ No params_meta found")
        return False

    volume_fit = params_meta[0].get("fit")
    if not volume_fit:
        print("❌ No volume fit found")
        return False

    print(f"✓ Found volume fit: {volume_fit.get('type')} with {len(volume_fit.get('points', []))} points")

    # Get Compressor device
    print("\nReading Compressor device mapping...")
    comp_doc = client.collection("device_mappings").document(COMPRESSOR_SIG).get()
    if not comp_doc.exists:
        print("❌ Compressor device not found")
        return False

    comp_data = comp_doc.to_dict()
    comp_params = comp_data.get("params_meta", [])

    # Find Threshold parameter
    threshold_param = None
    for param in comp_params:
        if param.get("name") == "Threshold":
            threshold_param = param
            break

    if not threshold_param:
        print("❌ Threshold parameter not found")
        return False

    print(f"✓ Found Threshold parameter (index {threshold_param.get('index')})")

    # Apply the fit
    print("\nApplying volume fit to Threshold...")
    threshold_param["fit"] = volume_fit
    threshold_param["confidence"] = 1.0  # High confidence since it's manually calibrated

    # Save to Firestore
    comp_data["params_meta"] = comp_params
    comp_doc_ref = client.collection("device_mappings").document(COMPRESSOR_SIG)
    comp_doc_ref.update({"params_meta": comp_params})

    print("\n✅ SUCCESS!")
    print(f"  Copied piecewise fit ({len(volume_fit.get('points', []))} points)")
    print(f"  From: track_channel/volume")
    print(f"  To: Compressor/Threshold")
    print(f"  Range: -70 to +6 dB")

    return True

if __name__ == "__main__":
    copy_volume_fit_to_threshold()
