#!/usr/bin/env python3
"""
Integrate audio engineering knowledge into Reverb device mapping.
Adds audio_knowledge field to each parameter in params_meta.
"""

import json
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from google.cloud import firestore

REVERB_SIGNATURE = "64ccfc236b79371d0b45e913f81bf0f3a55c6db9"
AUDIO_KNOWLEDGE_FILE = "/Users/sunils/ai-projects/fadebender/docs/technical/reverb_audio_knowledge.json"


def load_audio_knowledge():
    """Load audio knowledge JSON file."""
    with open(AUDIO_KNOWLEDGE_FILE, "r") as f:
        data = json.load(f)
    return data["audio_knowledge"]


def integrate_audio_knowledge():
    """Integrate audio knowledge into Firestore params_meta."""

    print("="*70)
    print("INTEGRATING AUDIO ENGINEERING KNOWLEDGE")
    print("="*70)

    # Initialize Firestore
    db = firestore.Client()
    doc_ref = db.collection("device_mappings").document(REVERB_SIGNATURE)

    print(f"\n[1/5] Loading current device mapping...")
    doc = doc_ref.get()
    if not doc.exists:
        print("❌ Error: Device mapping not found!")
        return False

    device_data = doc.to_dict()
    print(f"✓ Device: {device_data.get('device_name')}")

    print(f"\n[2/5] Reading params from subcollection...")
    params_col = doc_ref.collection("params")
    param_docs = list(params_col.stream())
    print(f"✓ Found {len(param_docs)} parameters in subcollection")

    print(f"\n[3/5] Loading audio knowledge...")
    audio_knowledge = load_audio_knowledge()
    print(f"✓ Loaded knowledge for {len(audio_knowledge)} parameters")

    print(f"\n[4/5] Building params_meta with audio knowledge...")
    params_meta = []
    updated_count = 0
    skipped_count = 0

    for param_doc in sorted(param_docs, key=lambda p: p.to_dict().get("index", 999)):
        param_data = param_doc.to_dict()
        param_name = param_doc.id  # Document ID is the parameter name

        # Build param metadata entry
        param_entry = {
            "name": param_name,
            "index": param_data.get("index"),
            "control_type": param_data.get("control_type", "continuous"),
        }

        # Add control type specific fields
        if param_data.get("control_type") == "binary":
            param_entry["labels"] = param_data.get("labels", ["off", "on"])
        elif param_data.get("control_type") == "quantized":
            param_entry["labels"] = param_data.get("labels", [])
            param_entry["label_map"] = param_data.get("label_map", {})
        elif param_data.get("fit"):
            # Continuous parameter with fit
            param_entry["fit"] = param_data.get("fit")
            param_entry["confidence"] = param_data.get("fit", {}).get("r2", 1.0)
            param_entry["min_display"] = param_data.get("min_display")
            param_entry["max_display"] = param_data.get("max_display")

        # Add audio knowledge if available
        if param_name in audio_knowledge:
            param_entry["audio_knowledge"] = audio_knowledge[param_name]
            updated_count += 1
            print(f"  ✓ {param_name}")
        else:
            skipped_count += 1
            print(f"  ⚠️  No audio knowledge for: {param_name}")

        params_meta.append(param_entry)

    print(f"\n✓ Built params_meta with {len(params_meta)} parameters")
    print(f"  - With audio knowledge: {updated_count}")
    print(f"  - Without audio knowledge: {skipped_count}")

    print(f"\n[5/5] Updating Firestore main document...")
    doc_ref.update({"params_meta": params_meta})
    print("✓ Firestore updated successfully")

    print("\n" + "="*70)
    print("INTEGRATION COMPLETE")
    print("="*70)
    print(f"\nSummary:")
    print(f"  - Total parameters: {len(params_meta)}")
    print(f"  - With audio knowledge: {updated_count}")
    print(f"  - Without audio knowledge: {skipped_count}")

    return True


if __name__ == "__main__":
    success = integrate_audio_knowledge()
    sys.exit(0 if success else 1)
