"""
Fix S/C Mix fit in Firestore for a specific Compressor mapping.

Usage:
  export FIRESTORE_PROJECT_ID=your-project
  export FIRESTORE_DATABASE_ID=(default)  # or your DB name
  python -m server.scripts.fix_sc_mix_fit --signature 9e906e0ab3f18c4688107553744914f9ef6b9ee7 --param "S/C Mix"

This script:
  - Sets unit to "%"
  - Ensures min_display=0, max_display=100
  - Writes a linear fit mapping display% -> normalized: y = 100*x + 0
    (so inversion does x = y/100)
  - Removes/overwrites any NaN r2
"""
from __future__ import annotations

import argparse
from typing import Any


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--signature", required=True, help="Device structure signature hash")
    parser.add_argument("--param", required=True, help="Parameter name (e.g., 'S/C Mix')")
    args = parser.parse_args()

    try:
        from google.cloud import firestore  # type: ignore
    except Exception as e:
        print("Firestore client not available:", e)
        return

    sig = str(args.signature)
    pname = str(args.param)
    doc_id = pname.replace("/", "_").replace("\\", "_")

    db = firestore.Client()
    root = db.collection("device_mappings").document(sig)

    def _update_param(doc_ref: Any) -> None:
        update_data = {
            "name": pname,
            "unit": "%",
            "min_display": 0.0,
            "max_display": 100.0,
            # Linear fit: display (percent) = 100 * normalized + 0
            # Our inversion uses a,b: x = (y - b) / a
            "fit": {
                "type": "linear",
                "coeffs": {"a": 100.0, "b": 0.0},
                "r2": 1.0,
            },
        }
        doc_ref.set(update_data, merge=True)

    # Update subcollection param doc
    pdoc = root.collection("params").document(doc_id)
    _update_param(pdoc)

    # Also try to update params_meta array in the root doc if present
    snap = root.get()
    if snap.exists:
        data = snap.to_dict() or {}
        pmeta = data.get("params_meta")
        if isinstance(pmeta, list):
            changed = False
            for item in pmeta:
                if str(item.get("name", "")).strip().lower() == pname.strip().lower():
                    item["unit"] = "%"
                    item["min_display"] = 0.0
                    item["max_display"] = 100.0
                    item["fit"] = {"type": "linear", "coeffs": {"a": 100.0, "b": 0.0}, "r2": 1.0}
                    changed = True
            if changed:
                root.set({"params_meta": pmeta}, merge=True)

    print(f"Updated mapping for signature={sig} param='{pname}'")


if __name__ == "__main__":
    main()

