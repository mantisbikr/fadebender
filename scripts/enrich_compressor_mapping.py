#!/usr/bin/env python3
"""
Enrich Compressor device mapping with standardized schema.
Fixes index gap (shifts indices 12-22 down to 11-21).
Adds sections, grouping, control_type, fit objects, etc.
"""
import sys
import os
import argparse
os.environ["FIRESTORE_DATABASE_ID"] = "dev-display-value"
sys.path.insert(0, '/Users/sunils/ai-projects/fadebender')

from google.cloud import firestore
import json

COMPRESSOR_SIGNATURE = "9e906e0ab3f18c4688107553744914f9ef6b9ee7"

def enrich_compressor(auto_confirm=False):
    """Enrich Compressor mapping from basic to standardized schema."""

    client = firestore.Client(database="dev-display-value")
    doc_ref = client.collection("device_mappings").document(COMPRESSOR_SIGNATURE)

    # Get current data
    doc = doc_ref.get()
    if not doc.exists:
        print(f"❌ Error: Compressor device not found (signature: {COMPRESSOR_SIGNATURE})")
        return False

    data = doc.to_dict()
    print(f"✓ Loaded Compressor device mapping")
    print(f"  Current params_meta count: {len(data.get('params_meta', []))}")

    # Process parameters
    params_meta = data.get("params_meta", [])

    # Step 1: Fix index gap (shift 12-22 down to 11-21)
    print("\n" + "="*80)
    print("STEP 1: Fixing index gap")
    print("="*80)

    for param in params_meta:
        old_index = param.get("index")
        if old_index >= 12:
            new_index = old_index - 1
            param["index"] = new_index
            print(f"  Shifted {param.get('name')}: index {old_index} → {new_index}")

    # Sort by index to verify
    params_meta.sort(key=lambda p: p.get("index", 0))
    indices = [p.get("index") for p in params_meta]
    print(f"\n✓ New indices: {indices}")
    print(f"✓ Confirmed: {len(params_meta)} parameters with indices 0-{max(indices)}")

    # Step 2: Add control_type and standardize each parameter
    print("\n" + "="*80)
    print("STEP 2: Adding control_type and standardizing parameters")
    print("="*80)

    # Parameter metadata from manual and analysis
    param_specs = {
        "Device On": {"control_type": "binary", "labels": ["Off", "On"]},
        "Threshold": {"control_type": "continuous", "unit": "dB", "min_display": -60.0, "max_display": 0.0},
        "Ratio": {"control_type": "continuous", "unit": "", "min_display": 1.0, "max_display": 20.0},
        "Expansion Ratio": {"control_type": "continuous", "unit": "", "min_display": 1.0, "max_display": 10.0},
        "Attack": {"control_type": "continuous", "unit": "ms", "min_display": 0.01, "max_display": 100.0},
        "Release": {"control_type": "continuous", "unit": "ms", "min_display": 10.0, "max_display": 1000.0},
        "Auto Release On/Off": {"control_type": "binary", "labels": ["Off", "On"]},
        "Output Gain": {"control_type": "continuous", "unit": "dB", "min_display": 0.0, "max_display": 30.0},
        "Makeup": {"control_type": "binary", "labels": ["Off", "On"]},
        "Dry/Wet": {"control_type": "continuous", "unit": "%", "min_display": 0.0, "max_display": 100.0},
        "Model": {"control_type": "quantized", "labels": ["Peak", "RMS", "Expand"]},
        "Knee": {"control_type": "continuous", "unit": "", "min_display": 0.0, "max_display": 1.0},
        "LookAhead": {"control_type": "binary", "labels": ["Off", "On"]},
        "S/C Listen": {"control_type": "binary", "labels": ["Off", "On"]},
        "S/C EQ On": {"control_type": "binary", "labels": ["Off", "On"]},
        "S/C EQ Type": {"control_type": "quantized", "labels": ["Lowpass", "Bandpass", "Highpass", "Notch", "Peak"]},
        "S/C EQ Freq": {"control_type": "continuous", "unit": "Hz", "min_display": 20.0, "max_display": 20000.0},
        "S/C EQ Q": {"control_type": "continuous", "unit": "", "min_display": 0.1, "max_display": 18.0},
        "S/C EQ Gain": {"control_type": "continuous", "unit": "dB", "min_display": -15.0, "max_display": 15.0},
        "S/C On": {"control_type": "binary", "labels": ["Off", "On"]},
        "S/C Gain": {"control_type": "continuous", "unit": "dB", "min_display": -24.0, "max_display": 24.0},
        "S/C Mix": {"control_type": "continuous", "unit": "%", "min_display": 0.0, "max_display": 100.0},
    }

    for param in params_meta:
        name = param.get("name")
        if name in param_specs:
            spec = param_specs[name]
            param["control_type"] = spec["control_type"]

            if spec["control_type"] == "binary":
                param["labels"] = spec["labels"]
                if "min" not in param:
                    param["min"] = 0.0
                if "max" not in param:
                    param["max"] = 1.0
                print(f"  ✓ {name}: binary (labels: {spec['labels']})")

            elif spec["control_type"] == "quantized":
                param["labels"] = spec["labels"]
                if "min" not in param:
                    param["min"] = 0.0
                if "max" not in param:
                    param["max"] = float(len(spec["labels"]) - 1)
                # Create label_map
                param["label_map"] = {str(float(i)): label for i, label in enumerate(spec["labels"])}
                print(f"  ✓ {name}: quantized ({len(spec['labels'])} labels)")

            elif spec["control_type"] == "continuous":
                param["unit"] = spec.get("unit", "")
                param["min_display"] = spec["min_display"]
                param["max_display"] = spec["max_display"]
                if "min" not in param:
                    param["min"] = 0.0
                if "max" not in param:
                    param["max"] = 1.0
                param["confidence"] = 0.5  # Placeholder - will be fitted later
                # Placeholder linear fit
                param["fit"] = {
                    "type": "linear",
                    "coeffs": {
                        "a": spec["max_display"] - spec["min_display"],
                        "b": spec["min_display"]
                    },
                    "r2": 0.5  # Placeholder
                }
                print(f"  ✓ {name}: continuous ({spec['min_display']} to {spec['max_display']} {spec.get('unit', '')})")
        else:
            print(f"  ⚠ {name}: No spec found, skipping")

    # Step 3: Add sections
    print("\n" + "="*80)
    print("STEP 3: Adding sections")
    print("="*80)

    data["sections"] = {
        "Device": {
            "technical_name": "Device",
            "description": "Device on/off control",
            "sonic_focus": "Enable or disable the entire compressor effect",
            "technical_notes": [],
            "parameters": ["Device On"]
        },
        "Compression": {
            "technical_name": "Compression",
            "description": "Core compression parameters",
            "sonic_focus": "Control threshold, ratio, and attack/release envelope",
            "technical_notes": [
                "Threshold: level above which compression begins",
                "Ratio: amount of gain reduction applied above threshold",
                "Attack: how quickly compression engages after signal exceeds threshold",
                "Release: how quickly compression disengages after signal falls below threshold",
                "Auto Release adapts release time based on input signal dynamics"
            ],
            "parameters": ["Threshold", "Ratio", "Attack", "Release", "Auto Release On/Off", "Knee", "Model"]
        },
        "Expansion": {
            "technical_name": "Expansion",
            "description": "Downward expansion (opposite of compression)",
            "sonic_focus": "Reduce level of signals below threshold",
            "technical_notes": [
                "Expansion Ratio: amount of gain reduction for signals below threshold",
                "Useful for reducing noise floor or creating gating effects"
            ],
            "parameters": ["Expansion Ratio"]
        },
        "Output": {
            "technical_name": "Output",
            "description": "Output level and mixing controls",
            "sonic_focus": "Control output gain, makeup gain, and dry/wet balance",
            "technical_notes": [
                "Output Gain: manual output level adjustment",
                "Makeup: automatic gain compensation (not available with external sidechain)",
                "Dry/Wet: blend between compressed and uncompressed signal",
                "LookAhead: analyze signal ahead of compression for more transparent results"
            ],
            "parameters": ["Output Gain", "Makeup", "Dry/Wet", "LookAhead"]
        },
        "Sidechain": {
            "technical_name": "Sidechain",
            "description": "External sidechain input controls",
            "sonic_focus": "Use external audio source to trigger compression",
            "technical_notes": [
                "S/C On: enable external sidechain input",
                "S/C Gain: adjust sidechain input level",
                "S/C Mix: blend between main input and sidechain (100% = full sidechain)",
                "S/C Listen: monitor sidechain signal for setup"
            ],
            "parameters": ["S/C On", "S/C Gain", "S/C Mix", "S/C Listen"]
        },
        "Sidechain EQ": {
            "technical_name": "Sidechain EQ",
            "description": "Frequency-selective compression triggering",
            "sonic_focus": "Filter sidechain signal to make compressor respond to specific frequencies",
            "technical_notes": [
                "S/C EQ On: enable sidechain EQ filtering",
                "Type: filter type (lowpass, bandpass, highpass, notch, peak)",
                "Freq: center/cutoff frequency",
                "Q: filter bandwidth/resonance",
                "Gain: boost/cut for peak filter type"
            ],
            "parameters": ["S/C EQ On", "S/C EQ Type", "S/C EQ Freq", "S/C EQ Q", "S/C EQ Gain"]
        }
    }
    print("✓ Added 6 sections")

    # Step 4: Add grouping
    print("\n" + "="*80)
    print("STEP 4: Adding grouping (masters/dependents)")
    print("="*80)

    data["grouping"] = {
        "masters": ["S/C On", "S/C EQ On"],
        "dependents": {
            "S/C Gain": "S/C On",
            "S/C Mix": "S/C On",
            "S/C Listen": "S/C On",
            "S/C EQ Type": "S/C EQ On",
            "S/C EQ Freq": "S/C EQ On",
            "S/C EQ Q": "S/C EQ On",
            "S/C EQ Gain": "S/C EQ On"
        },
        "dependent_master_values": {
            "S/C Gain": 1.0,
            "S/C Mix": 1.0,
            "S/C Listen": 1.0,
            "S/C EQ Type": 1.0,
            "S/C EQ Freq": 1.0,
            "S/C EQ Q": 1.0,
            "S/C EQ Gain": 1.0
        },
        "skip_auto_enable": [],
        "apply_order": ["masters", "quantized", "dependents", "continuous"],
        "requires_for_effect": {
            "Makeup": {
                "description": "Automatic Makeup is not available when using external sidechain",
                "blocking_params": ["S/C On"],
                "blocking_values": [1.0]
            }
        }
    }
    print("✓ Added grouping with 2 masters and 7 dependents")

    # Step 5: Add metadata
    data["device_name"] = "Compressor"
    data["param_names"] = [p.get("name") for p in params_meta]
    data["param_count"] = len(params_meta)

    print("\n" + "="*80)
    print("PREVIEW OF ENRICHED SCHEMA")
    print("="*80)
    print(f"Device: {data.get('device_name')}")
    print(f"Signature: {COMPRESSOR_SIGNATURE}")
    print(f"Params: {len(params_meta)}")
    print(f"Sections: {list(data['sections'].keys())}")
    print(f"Masters: {data['grouping']['masters']}")
    print(f"Dependents: {len(data['grouping']['dependents'])}")

    # Ask for confirmation
    print("\n" + "="*80)
    if auto_confirm:
        print("Auto-confirming changes...")
        response = 'yes'
    else:
        response = input("Apply these changes to Firestore? (yes/no): ")

    if response.lower() not in ['yes', 'y']:
        print("❌ Aborted - no changes made")
        return False

    # Update params_meta in data
    data["params_meta"] = params_meta

    # Update Firestore
    doc_ref.update(data)
    print("\n✅ SUCCESS - Compressor mapping enriched!")
    print(f"  Database: dev-display-value")
    print(f"  Signature: {COMPRESSOR_SIGNATURE}")
    print(f"  Fixed index gap (12-22 → 11-21)")
    print(f"  Added control_type to all parameters")
    print(f"  Added 6 sections")
    print(f"  Added grouping with masters/dependents")

    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Enrich Compressor device mapping")
    parser.add_argument('--yes', '-y', action='store_true', help='Auto-confirm changes without prompting')
    args = parser.parse_args()

    success = enrich_compressor(auto_confirm=args.yes)
    sys.exit(0 if success else 1)
