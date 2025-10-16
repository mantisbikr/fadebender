#!/usr/bin/env python3
"""
Fix Reverb device parameters in dev-display-value database:
1. Remove incorrect "dB" units from LowShelf Gain and HiShelf Gain (they use 0.0-1.0 range)
2. Remove any dependencies from Freeze On, Flat On, Cut On (they are independent toggles)
"""

from google.cloud import firestore

# Connect to dev-display-value database
client = firestore.Client(database="dev-display-value")

# Reverb signature
REVERB_SIG = "64ccfc236b79371d0b45e913f81bf0f3a55c6db9"

print("=" * 70)
print("FIX REVERB GAIN PARAMETERS AND TOGGLES")
print("=" * 70)
print()

# Get Reverb device mapping
doc_ref = client.collection("device_mappings").document(REVERB_SIG)
doc = doc_ref.get()

if not doc.exists:
    print(f"✗ Reverb mapping not found (signature: {REVERB_SIG})")
    exit(1)

data = doc.to_dict()
device_name = data.get("device_name", "unknown")
print(f"Found device: {device_name}")
print(f"Signature: {REVERB_SIG}")
print()

# Update params_meta
params_meta = data.get("params_meta", [])
if not params_meta:
    print("✗ No params_meta found")
    exit(1)

updated_count = 0

# Fix Gain parameters - remove "dB" unit
for pm in params_meta:
    param_name = pm.get("name", "")

    if param_name in ["LowShelf Gain", "HiShelf Gain"]:
        old_unit = pm.get("unit", "")
        if old_unit == "dB":
            pm["unit"] = ""
            updated_count += 1
            print(f"✓ {param_name:30} removed 'dB' unit (uses 0.0-1.0 range)")

# Fix toggle parameters - remove any dependencies
for pm in params_meta:
    param_name = pm.get("name", "")

    if param_name in ["Freeze On", "Flat On", "Cut On"]:
        if "dependencies" in pm and pm["dependencies"]:
            old_deps = pm["dependencies"]
            pm["dependencies"] = []
            updated_count += 1
            print(f"✓ {param_name:30} removed dependencies: {old_deps}")

print()
print(f"Updated {updated_count} parameter(s)")
print()

# Write back to Firestore
if updated_count > 0:
    doc_ref.set(data)
    print("✓ Saved updates to dev-display-value database")
else:
    print("No changes needed")

print()
print("=" * 70)
