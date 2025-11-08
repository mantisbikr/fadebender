#!/usr/bin/env python3
"""Fix Amp Dual Mono labels to match label_map."""
import os
os.environ["FIRESTORE_DATABASE_ID"] = "dev-display-value"

from google.cloud import firestore

def fix_dual_mono_labels():
    client = firestore.Client(database="dev-display-value")
    sig = "d554752f4be9eee62197c37b45b1c22237842c37"
    doc_ref = client.collection("device_mappings").document(sig)

    doc = doc_ref.get()
    data = doc.to_dict()

    params_meta = data.get("params_meta", [])

    for param in params_meta:
        if param.get("name") == "Dual Mono":
            # Extract labels from label_map in sorted order by value
            label_map = param.get("label_map", {})
            if label_map:
                # Sort by value (the normalized value Live expects)
                sorted_items = sorted(label_map.items(), key=lambda x: float(x[0]))
                param["labels"] = [label for _, label in sorted_items]

                print(f"Fixed Dual Mono labels:")
                print(f"  Old: ['Off', 'On']")
                print(f"  New: {param['labels']}")
                print(f"  From label_map: {label_map}")
                break

    # Update Firestore
    doc_ref.update({"params_meta": params_meta})
    print("\n✅ Fixed Dual Mono labels in Firestore")

if __name__ == "__main__":
    fix_dual_mono_labels()
