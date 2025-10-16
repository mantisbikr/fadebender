#!/usr/bin/env python3
"""
Fix Reverb grouping.dependents in dev-display-value database:
Remove incorrect dependencies for Freeze On, Flat On, Cut On (they are independent toggles).
"""

from google.cloud import firestore

# Connect to dev-display-value database
client = firestore.Client(database="dev-display-value")

# Reverb signature
REVERB_SIG = "64ccfc236b79371d0b45e913f81bf0f3a55c6db9"

print("=" * 70)
print("FIX REVERB GROUPING DEPENDENCIES")
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

# Update grouping.dependents
grouping = data.get("grouping", {})
dependents = grouping.get("dependents", {})

if not dependents:
    print("No grouping.dependents found")
    exit(0)

print("Current grouping.dependents:")
for dep, master in dependents.items():
    print(f"  {dep:30} -> {master}")
print()

# Remove Flat On and Cut On from dependents (they are independent toggles, not dependent on Freeze On)
removed = []
for toggle in ["Flat On", "Cut On"]:
    if toggle in dependents:
        removed.append(f"{toggle} -> {dependents[toggle]}")
        del dependents[toggle]

if removed:
    print("Removed dependencies:")
    for r in removed:
        print(f"  ✓ {r}")
    print()

    # Update grouping
    data["grouping"]["dependents"] = dependents

    # Write back to Firestore
    doc_ref.set(data)
    print("✓ Saved updates to dev-display-value database")
else:
    print("No changes needed")

print()
print(f"Remaining grouping.dependents: {len(dependents)}")
for dep, master in dependents.items():
    print(f"  {dep:30} -> {master}")

print()
print("=" * 70)
