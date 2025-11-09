#!/usr/bin/env python3
"""
Standardize Amp device mapping from legacy to standard schema.
Additive approach - preserves legacy fields for backward compatibility.
"""
import sys
import os
os.environ["FIRESTORE_DATABASE_ID"] = "dev-display-value"
sys.path.insert(0, '/Users/sunils/ai-projects/fadebender')

from google.cloud import firestore
import json

AMP_SIGNATURE = "d554752f4be9eee62197c37b45b1c22237842c37"

def standardize_amp():
    """Convert Amp from legacy schema to standard schema."""

    client = firestore.Client(database="dev-display-value")
    doc_ref = client.collection("device_mappings").document(AMP_SIGNATURE)

    # Get current data
    doc = doc_ref.get()
    if not doc.exists:
        print(f"❌ Error: Amp device not found (signature: {AMP_SIGNATURE})")
        return False

    data = doc.to_dict()
    print(f"✓ Loaded Amp device mapping")
    print(f"  Current params_meta count: {len(data.get('params_meta', []))}")

    # Process each parameter
    params_meta = data.get("params_meta", [])
    updated_count = 0

    for param in params_meta:
        fit_type = param.get("fit_type")
        param_name = param.get("name", "Unknown")

        if fit_type == "binary":
            # Binary: add control_type and labels
            param["control_type"] = "binary"

            # Extract labels from label_map if labels don't exist (like quantized params)
            if "labels" not in param and "label_map" in param:
                # Sort by numeric key to get proper order (0="Off", 1="On" etc)
                sorted_items = sorted(
                    param["label_map"].items(),
                    key=lambda x: float(x[0])
                )
                param["labels"] = [label for _, label in sorted_items]
            elif "labels" not in param:
                # Fallback to default binary labels only if no label_map
                param["labels"] = ["Off", "On"]

            if "min" not in param:
                param["min"] = 0.0
            if "max" not in param:
                param["max"] = 1.0
            updated_count += 1
            print(f"  ✓ {param_name}: converted binary (labels: {param.get('labels', [])})")

        elif fit_type == "quantized":
            # Quantized: add control_type, ensure labels exist
            param["control_type"] = "quantized"

            # Extract labels from label_map if labels don't exist
            if "labels" not in param and "label_map" in param:
                # Sort by numeric key to get proper order
                sorted_items = sorted(
                    param["label_map"].items(),
                    key=lambda x: float(x[0])
                )
                param["labels"] = [label for _, label in sorted_items]

            if "min" not in param:
                param["min"] = 0.0
            if "max" not in param:
                # Max should be number of labels - 1
                num_labels = len(param.get("labels", []))
                param["max"] = float(num_labels - 1) if num_labels > 0 else 1.0

            updated_count += 1
            print(f"  ✓ {param_name}: converted quantized (labels: {param.get('labels', [])})")

        elif fit_type == "linear":
            # Linear continuous: add control_type and fit object
            param["control_type"] = "continuous"

            # Get display range
            coeffs = param.get("coefficients", [0.0, 1.0])
            display_range = param.get("display_range", coeffs)

            min_display = display_range[0]
            max_display = display_range[1]

            # Create fit object for linear: y = a*x + b
            # Where x goes from 0 to 1, y goes from min_display to max_display
            # y = (max_display - min_display) * x + min_display
            param["fit"] = {
                "type": "linear",
                "coeffs": {
                    "a": max_display - min_display,  # slope
                    "b": min_display                  # intercept
                },
                "r2": 1.0  # Linear fit is exact
            }
            param["min_display"] = min_display
            param["max_display"] = max_display
            param["confidence"] = 1.0

            # Add min/max if missing
            if "min" not in param:
                param["min"] = 0.0
            if "max" not in param:
                param["max"] = 1.0

            updated_count += 1
            print(f"  ✓ {param_name}: converted linear continuous ({min_display} to {max_display})")

    print(f"\n✓ Updated {updated_count} parameters")

    # Add grouping if missing
    if "grouping" not in data:
        data["grouping"] = {
            "masters": [],
            "dependents": {},
            "skip_auto_enable": [],
            "apply_order": ["masters", "quantized", "dependents", "continuous"],
            "requires_for_effect": {}
        }
        print("✓ Added grouping structure")

    # Add sections if missing
    if "sections" not in data:
        data["sections"] = {
            "Device": {
                "technical_name": "Device",
                "description": "Device on/off control",
                "sonic_focus": "Enable or disable the entire effect",
                "technical_notes": [],
                "parameters": ["Device On"]
            },
            "Amp Model": {
                "technical_name": "Amp Model",
                "description": "Amplifier selection",
                "sonic_focus": "Choose between seven classic amp models",
                "technical_notes": [
                    "Each model has distinct tonal characteristics and distortion curves",
                    "Physical modeling technology emulates electrical characteristics"
                ],
                "parameters": ["Amp Type"]
            },
            "Tone Controls": {
                "technical_name": "Tone Controls",
                "description": "EQ shaping in preamp and power amp stages",
                "sonic_focus": "Shape frequency response and tonal character",
                "technical_notes": [
                    "Bass/Middle/Treble: preamp stage EQ",
                    "Presence: power amp stage high-frequency control",
                    "Controls interact non-linearly with each other and with gain"
                ],
                "parameters": ["Bass", "Middle", "Treble", "Presence"]
            },
            "Drive & Output": {
                "technical_name": "Drive & Output",
                "description": "Gain staging and output controls",
                "sonic_focus": "Control distortion amount and output level",
                "technical_notes": [
                    "Gain: primary distortion control (preamp)",
                    "Volume: output level; adds power amp distortion on some models",
                    "Dual Mono: doubles CPU, creates stereo width"
                ],
                "parameters": ["Gain", "Volume", "Dual Mono", "Dry/Wet"]
            }
        }
        print("✓ Added sections structure")

    # Add param_names and param_count if missing
    if "param_names" not in data:
        data["param_names"] = [p.get("name") for p in params_meta]
        print(f"✓ Added param_names ({len(data['param_names'])} params)")

    if "param_count" not in data or data["param_count"] != len(params_meta):
        data["param_count"] = len(params_meta)
        print(f"✓ Set param_count to {data['param_count']}")

    # Preview changes
    print("\n" + "="*80)
    print("PREVIEW OF STANDARDIZED SCHEMA")
    print("="*80)
    print(f"Device: {data.get('device_name')}")
    print(f"Signature: {AMP_SIGNATURE[:16]}...")
    print(f"Params: {len(params_meta)}")
    print(f"\nGrouping keys: {list(data['grouping'].keys())}")
    print(f"Sections: {list(data['sections'].keys())}")
    print(f"\nSample param (Bass):")
    bass_param = next((p for p in params_meta if p.get('name') == 'Bass'), None)
    if bass_param:
        print(json.dumps({
            "name": bass_param.get("name"),
            "index": bass_param.get("index"),
            "control_type": bass_param.get("control_type"),
            "unit": bass_param.get("unit"),
            "min": bass_param.get("min"),
            "max": bass_param.get("max"),
            "min_display": bass_param.get("min_display"),
            "max_display": bass_param.get("max_display"),
            "fit": bass_param.get("fit"),
            "legacy_fit_type": bass_param.get("fit_type"),
            "legacy_coefficients": bass_param.get("coefficients"),
            "legacy_display_range": bass_param.get("display_range")
        }, indent=2))

    # Ask for confirmation
    print("\n" + "="*80)
    response = input("Apply these changes to Firestore? (yes/no): ")

    if response.lower() not in ['yes', 'y']:
        print("❌ Aborted - no changes made")
        return False

    # Update Firestore
    doc_ref.update(data)
    print("\n✅ SUCCESS - Amp mapping standardized!")
    print(f"  Database: dev-display-value")
    print(f"  Signature: {AMP_SIGNATURE}")
    print(f"  Updated {updated_count} parameters")
    print(f"  Added grouping and sections")

    return True

if __name__ == "__main__":
    success = standardize_amp()
    sys.exit(0 if success else 1)
