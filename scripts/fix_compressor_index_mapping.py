#!/usr/bin/env python3
"""
Fix Compressor index mapping - shift indices 11-21 back to 12-22.
The index gap fix was wrong - Live actually has no parameter at index 11.
"""
import os
os.environ["FIRESTORE_DATABASE_ID"] = "dev-display-value"
import sys
sys.path.insert(0, '/Users/sunils/ai-projects/fadebender')

from google.cloud import firestore

COMPRESSOR_SIG = "9e906e0ab3f18c4688107553744914f9ef6b9ee7"

def fix_indices():
    """Shift indices 11-21 back to 12-22."""
    client = firestore.Client(database="dev-display-value")
    doc_ref = client.collection("device_mappings").document(COMPRESSOR_SIG)
    doc = doc_ref.get()

    if not doc.exists:
        print("❌ Compressor document not found")
        return False

    data = doc.to_dict()
    params_meta = data.get("params_meta", [])

    print("=" * 80)
    print("FIXING COMPRESSOR INDEX MAPPING")
    print("=" * 80)
    print("\nShifting indices 11-21 → 12-22")
    print("\nChanges:")
    print(f"{'Old Index':>10s} {'New Index':>10s} {'Parameter Name':<25s}")
    print("-" * 50)

    # Shift indices 11-21 up by 1
    for param in params_meta:
        old_index = param['index']
        if old_index >= 11:
            new_index = old_index + 1
            param['index'] = new_index
            print(f"{old_index:>10d} → {new_index:>10d} {param['name']:<25s}")

    # Save
    doc_ref.update({"params_meta": params_meta})

    print("\n✅ SUCCESS - Index mapping fixed!")
    print("\nVerifying...")

    # Verify
    doc = doc_ref.get()
    data = doc.to_dict()
    params_meta = data.get("params_meta", [])

    print(f"\n{'Index':>5s} {'Name':<25s}")
    print("-" * 35)
    for p in params_meta:
        print(f"{p['index']:>5d} {p['name']:<25s}")

    return True

if __name__ == "__main__":
    fix_indices()
