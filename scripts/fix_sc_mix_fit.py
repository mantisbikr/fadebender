#!/usr/bin/env python3
"""
Fix S/C Mix fit with correct linear coefficients.
display = 100.0 * norm + 0.0 (simple percentage)
"""
import os
os.environ["FIRESTORE_DATABASE_ID"] = "dev-display-value"
import sys
sys.path.insert(0, '/Users/sunils/ai-projects/fadebender')

from google.cloud import firestore

COMPRESSOR_SIG = "9e906e0ab3f18c4688107553744914f9ef6b9ee7"

def fix_sc_mix_fit():
    """Update S/C Mix with correct linear fit."""
    print("=" * 80)
    print("FIXING S/C MIX FIT")
    print("=" * 80)

    client = firestore.Client(database="dev-display-value")
    doc_ref = client.collection("device_mappings").document(COMPRESSOR_SIG)
    doc = doc_ref.get()

    if not doc.exists:
        print("❌ Compressor document not found")
        return False

    data = doc.to_dict()
    params_meta = data.get("params_meta", [])

    # Find S/C Mix
    for param in params_meta:
        if param.get("name") == "S/C Mix":
            print(f"\nFound S/C Mix parameter (index {param.get('index')})")

            # Show old fit
            old_fit = param.get("fit", {})
            print(f"\nOld fit:")
            print(f"  Type: {old_fit.get('type', 'N/A')}")
            if old_fit.get('type') == 'linear':
                coeffs = old_fit.get('coeffs', {})
                print(f"  a: {coeffs.get('a', 'N/A')}")
                print(f"  b: {coeffs.get('b', 'N/A')}")
                print(f"  R²: {old_fit.get('r_squared', 'N/A')}")

            # Apply new fit
            param["fit"] = {
                "type": "linear",
                "function": "linear",
                "coeffs": {
                    "a": 100.0,
                    "b": 0.0
                },
                "r_squared": 1.0
            }
            param["confidence"] = 1.0

            print(f"\nNew fit:")
            print(f"  Type: linear")
            print(f"  Formula: display = 100.0 * norm + 0.0")
            print(f"  a: 100.0")
            print(f"  b: 0.0")
            print(f"  R²: 1.0")

            break
    else:
        print("❌ S/C Mix parameter not found")
        return False

    # Save
    data["params_meta"] = params_meta
    doc_ref.update({"params_meta": params_meta})

    print("\n✅ SUCCESS - S/C Mix fit updated!")
    print("   Formula: display = 100.0 * norm")
    print("   Range: 0% to 100%")
    print("   Database: dev-display-value")

    return True

if __name__ == "__main__":
    fix_sc_mix_fit()
