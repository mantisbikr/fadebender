#!/usr/bin/env python3
"""
Check what units are stored for Reverb device parameters in Firestore.
"""

from google.cloud import firestore

# Connect to dev-display-value database
client = firestore.Client(database="dev-display-value")

# Search for Reverb device mappings
mappings_ref = client.collection("device_mappings")
reverb_docs = []

print("Searching for Reverb device mappings...")
for doc in mappings_ref.stream():
    data = doc.to_dict()
    device_name = data.get("device_name", "")
    if "reverb" in device_name.lower():
        reverb_docs.append((doc.id, device_name, data))
        print(f"\nFound: {device_name} (signature: {doc.id})")

if not reverb_docs:
    print("\n✗ No Reverb device mappings found in dev-display-value")
    exit(1)

# Check the first Reverb device found
sig, name, data = reverb_docs[0]
print(f"\n{'='*70}")
print(f"Checking parameters for: {name}")
print(f"Signature: {sig}")
print(f"{'='*70}\n")

# Get params_meta which has the unit information
params_meta = data.get("params_meta", [])
if not params_meta:
    print("✗ No params_meta found - checking old params structure...")
    params = data.get("params", [])
    if params:
        print(f"Found {len(params)} params in old structure")
        for p in params[:10]:  # Show first 10
            print(f"  {p.get('name', 'unknown')}: unit={p.get('unit', 'NOT SET')}")
else:
    print(f"Found {len(params_meta)} parameters with metadata:\n")

    # Check the parameters used in Part 13
    target_params = ["decay", "predelay", "dry", "wet"]

    for pm in params_meta:
        name = pm.get("name", "").lower()
        if any(target in name for target in target_params):
            unit = pm.get("unit")
            control_type = pm.get("control_type")
            fit = pm.get("fit", {})
            fit_type = fit.get("type") if fit else None

            print(f"Parameter: {pm.get('name')}")
            print(f"  Unit: {unit if unit else 'NOT SET'}")
            print(f"  Control Type: {control_type}")
            print(f"  Fit Type: {fit_type}")
            print()
