#!/usr/bin/env python3
"""
List all parameter names for Reverb device from Firestore.
"""

from google.cloud import firestore

# Connect to dev-display-value database
client = firestore.Client(database="dev-display-value")

# Search for Reverb device mappings
mappings_ref = client.collection("device_mappings")

print("Searching for Reverb device mappings...")
for doc in mappings_ref.stream():
    data = doc.to_dict()
    device_name = data.get("device_name", "")
    if "reverb" in device_name.lower():
        print(f"\n{'='*70}")
        print(f"Device: {device_name}")
        print(f"Signature: {doc.id}")
        print(f"{'='*70}\n")

        params_meta = data.get("params_meta", [])
        if params_meta:
            print(f"All {len(params_meta)} parameters:\n")
            for i, pm in enumerate(params_meta, 1):
                name = pm.get("name", "unknown")
                unit = pm.get("unit", "")
                control_type = pm.get("control_type", "")
                print(f"{i:2}. {name:30} (type: {control_type:12} unit: {unit if unit else 'none'})")
        break
