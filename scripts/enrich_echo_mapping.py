#!/usr/bin/env python3
"""
Enrich Echo device mapping with standardized schema.
Adds sections, grouping, control_type, categories, etc.

ONLY modifies Echo device (signature: 9bd78001e088fcbde50e2ead80ef01e393f3d0ba)
"""
import sys
import os
import argparse
os.environ["FIRESTORE_DATABASE_ID"] = "dev-display-value"
sys.path.insert(0, '/Users/sunils/ai-projects/fadebender')

from google.cloud import firestore
import json

ECHO_SIGNATURE = "9bd78001e088fcbde50e2ead80ef01e393f3d0ba"

def enrich_echo(auto_confirm=False):
    """Enrich Echo mapping from basic to standardized schema."""

    client = firestore.Client(database="dev-display-value")
    doc_ref = client.collection("device_mappings").document(ECHO_SIGNATURE)

    # Get current data
    doc = doc_ref.get()
    if not doc.exists:
        print(f"❌ Error: Echo device not found (signature: {ECHO_SIGNATURE})")
        return False

    data = doc.to_dict()
    print(f"✓ Loaded Echo device mapping")
    print(f"  Current device_name: {data.get('device_name')}")
    print(f"  Current device_type: {data.get('device_type')}")
    print(f"  Current params_meta count: {len(data.get('params_meta', []))}")

    # Update device metadata
    data["device_name"] = "Echo"
    data["device_type"] = "delay"  # Primary type
    data["categories"] = ["delay", "reverb"]  # Echo is hybrid

    # Process parameters
    params_meta = data.get("params_meta", [])

    # Step 1: Add control_type and standardize each parameter
    print("\n" + "="*80)
    print("STEP 1: Adding control_type and standardizing parameters")
    print("="*80)

    # Parameter metadata from Echo manual and reconciliation
    param_specs = {
        # Device
        "Device On": {"control_type": "binary", "labels": ["Off", "On"]},

        # Echo Tab - Delay Lines
        "L Sync": {"control_type": "binary", "labels": ["Free", "Sync"]},
        "L Time": {"control_type": "continuous", "unit": "ms", "min_display": 1.0, "max_display": 10000.0},
        "L 16th": {"control_type": "quantized", "unit": "", "min_display": 1.0, "max_display": 16.0},
        "L Sync Mode": {"control_type": "quantized", "labels": ["Notes", "Triplet", "Dotted", "16th"]},
        "L Offset": {"control_type": "continuous", "unit": "%", "min_display": -50.0, "max_display": 50.0},
        "R Sync": {"control_type": "binary", "labels": ["Free", "Sync"]},
        "R Time": {"control_type": "continuous", "unit": "ms", "min_display": 1.0, "max_display": 10000.0},
        "R 16th": {"control_type": "quantized", "unit": "", "min_display": 1.0, "max_display": 16.0},
        "R Sync Mode": {"control_type": "quantized", "labels": ["Notes", "Triplet", "Dotted", "16th"]},
        "R Offset": {"control_type": "continuous", "unit": "%", "min_display": -50.0, "max_display": 50.0},
        "Link": {"control_type": "binary", "labels": ["Off", "On"]},
        "Channel Mode": {"control_type": "quantized", "labels": ["Stereo", "Ping Pong", "Mid/Side"]},

        # Echo Tab - Input/Feedback
        "Input Gain": {"control_type": "continuous", "unit": "dB", "min_display": -12.0, "max_display": 12.0},
        "Clip Dry": {"control_type": "binary", "labels": ["Off", "On"]},
        "Feedback": {"control_type": "continuous", "unit": "%", "min_display": 0.0, "max_display": 100.0},
        "Feedback Inv": {"control_type": "binary", "labels": ["Off", "On"]},

        # Echo Tab - Filter
        "Filter On": {"control_type": "binary", "labels": ["Off", "On"]},
        "HP Freq": {"control_type": "continuous", "unit": "Hz", "min_display": 20.0, "max_display": 20000.0},
        "HP Res": {"control_type": "continuous", "unit": "%", "min_display": 0.0, "max_display": 100.0},
        "LP Freq": {"control_type": "continuous", "unit": "Hz", "min_display": 20.0, "max_display": 20000.0},
        "LP Res": {"control_type": "continuous", "unit": "%", "min_display": 0.0, "max_display": 100.0},

        # Modulation Tab
        "Mod Wave": {"control_type": "quantized", "labels": ["Sine", "Triangle", "Saw Up", "Saw Down", "Square", "Noise"]},
        "Mod Freq": {"control_type": "continuous", "unit": "Hz", "min_display": 0.01, "max_display": 40.0},
        "Mod Sync": {"control_type": "binary", "labels": ["Free", "Sync"]},
        "Mod Phase": {"control_type": "continuous", "unit": "degrees", "min_display": 0.0, "max_display": 180.0},
        "Dly < Mod": {"control_type": "continuous", "unit": "%", "min_display": 0.0, "max_display": 100.0},
        "Mod 4x": {"control_type": "binary", "labels": ["Off", "On"]},
        "Flt < Mod": {"control_type": "continuous", "unit": "%", "min_display": 0.0, "max_display": 100.0},
        "Env Mix": {"control_type": "continuous", "unit": "%", "min_display": 0.0, "max_display": 100.0},

        # Character Tab
        "Repitch": {"control_type": "binary", "labels": ["Off", "On"]},
        "Repitch Smoothing Time": {"control_type": "continuous", "unit": "ms", "min_display": 1.0, "max_display": 1000.0},
        "Gate On": {"control_type": "binary", "labels": ["Off", "On"]},
        "Gate Thr": {"control_type": "continuous", "unit": "dB", "min_display": -60.0, "max_display": 0.0},
        "Gate Release": {"control_type": "continuous", "unit": "ms", "min_display": 1.0, "max_display": 1000.0},
        "Duck On": {"control_type": "binary", "labels": ["Off", "On"]},
        "Duck Thr": {"control_type": "continuous", "unit": "dB", "min_display": -60.0, "max_display": 0.0},
        "Duck Release": {"control_type": "continuous", "unit": "ms", "min_display": 1.0, "max_display": 1000.0},
        "Noise On": {"control_type": "binary", "labels": ["Off", "On"]},
        "Noise Amt": {"control_type": "continuous", "unit": "%", "min_display": 0.0, "max_display": 100.0},
        "Noise Mrph": {"control_type": "continuous", "unit": "", "min_display": 0.0, "max_display": 100.0},
        "Wobble On": {"control_type": "binary", "labels": ["Off", "On"]},
        "Wobble Amt": {"control_type": "continuous", "unit": "%", "min_display": 0.0, "max_display": 100.0},
        "Wobble Mrph": {"control_type": "continuous", "unit": "", "min_display": 0.0, "max_display": 100.0},

        # Global Controls
        "Reverb Level": {"control_type": "continuous", "unit": "%", "min_display": 0.0, "max_display": 100.0},
        "Reverb Decay": {"control_type": "continuous", "unit": "s", "min_display": 0.1, "max_display": 10.0},
        "Reverb Loc": {"control_type": "quantized", "labels": ["Pre", "Post", "Feedback"]},
        "Stereo Width": {"control_type": "continuous", "unit": "%", "min_display": 0.0, "max_display": 200.0},
        "Output Gain": {"control_type": "continuous", "unit": "dB", "min_display": -12.0, "max_display": 12.0},
        "Dry Wet": {"control_type": "continuous", "unit": "%", "min_display": 0.0, "max_display": 100.0},
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
                if "labels" in spec:
                    param["labels"] = spec["labels"]
                    if "min" not in param:
                        param["min"] = 0.0
                    if "max" not in param:
                        param["max"] = float(len(spec["labels"]) - 1)
                    param["label_map"] = {str(float(i)): label for i, label in enumerate(spec["labels"])}
                    print(f"  ✓ {name}: quantized ({len(spec['labels'])} labels)")
                else:
                    # Numeric quantized like L 16th
                    param["unit"] = spec.get("unit", "")
                    param["min_display"] = spec["min_display"]
                    param["max_display"] = spec["max_display"]
                    if "min" not in param:
                        param["min"] = spec["min_display"]
                    if "max" not in param:
                        param["max"] = spec["max_display"]
                    print(f"  ✓ {name}: quantized numeric ({spec['min_display']} to {spec['max_display']})")

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
                    "function": "linear",
                    "coeffs": {
                        "a": spec["max_display"] - spec["min_display"],
                        "b": spec["min_display"]
                    },
                    "r_squared": 0.5  # Placeholder
                }
                print(f"  ✓ {name}: continuous ({spec['min_display']} to {spec['max_display']} {spec.get('unit', '')})")
        else:
            print(f"  ⚠ {name}: No spec found, skipping")

    # Step 2: Add sections
    print("\n" + "="*80)
    print("STEP 2: Adding sections")
    print("="*80)

    data["sections"] = {
        "Device": {
            "technical_name": "Device",
            "description": "Device on/off control",
            "sonic_focus": "Enable or disable the entire Echo effect",
            "technical_notes": [],
            "parameters": ["Device On"]
        },
        "Echo_Tab": {
            "technical_name": "Echo Tab",
            "description": "Delay line controls and filter parameters",
            "sonic_focus": "Control delay times, sync modes, feedback, and filtering",
            "technical_notes": [
                "Supports beat-synced or free-running delay times",
                "Independent Left/Right or Mid/Side delay lines",
                "Stereo Link synchronizes both channels",
                "High-pass and low-pass filters in feedback path"
            ],
            "parameters": [
                "L Sync", "L Time", "L 16th", "L Sync Mode", "L Offset",
                "R Sync", "R Time", "R 16th", "R Sync Mode", "R Offset",
                "Link", "Channel Mode",
                "Input Gain", "Clip Dry", "Feedback", "Feedback Inv",
                "Filter On", "HP Freq", "HP Res", "LP Freq", "LP Res"
            ]
        },
        "Modulation": {
            "technical_name": "Modulation Tab",
            "description": "LFO and envelope follower modulation",
            "sonic_focus": "Add movement via filter and delay time modulation",
            "technical_notes": [
                "Six waveform types available",
                "Can modulate both delay time and filter frequency",
                "Envelope follower can blend with LFO",
                "Mod 4x scales delay modulation by 4x for flanging effects"
            ],
            "parameters": [
                "Mod Wave", "Mod Freq", "Mod Sync", "Mod Phase",
                "Dly < Mod", "Mod 4x", "Flt < Mod", "Env Mix"
            ]
        },
        "Character": {
            "technical_name": "Character Tab",
            "description": "Dynamics and vintage character controls",
            "sonic_focus": "Add tape-like artifacts, gating, and ducking",
            "technical_notes": [
                "Gate mutes signal below threshold",
                "Ducking reduces wet signal when dry signal is present",
                "Noise simulates vintage tape hiss",
                "Wobble adds irregular pitch modulation like tape delays",
                "Repitch creates pitch shifts when changing delay time"
            ],
            "parameters": [
                "Repitch", "Repitch Smoothing Time",
                "Gate On", "Gate Thr", "Gate Release",
                "Duck On", "Duck Thr", "Duck Release",
                "Noise On", "Noise Amt", "Noise Mrph",
                "Wobble On", "Wobble Amt", "Wobble Mrph"
            ]
        },
        "Global": {
            "technical_name": "Global Controls",
            "description": "Reverb, stereo width, and output controls",
            "sonic_focus": "Add reverb, control stereo image, and set mix levels",
            "technical_notes": [
                "Reverb can be placed pre-delay, post-delay, or in feedback loop",
                "Stereo Width can exceed 100% for widened image",
                "Dry/Wet at 100% for return track use"
            ],
            "parameters": [
                "Reverb Level", "Reverb Decay", "Reverb Loc",
                "Stereo Width", "Output Gain", "Dry Wet"
            ]
        }
    }

    for section_name, section_data in data["sections"].items():
        print(f"  ✓ {section_name}: {len(section_data['parameters'])} parameters")

    # Step 3: Add grouping (master/dependent relationships)
    print("\n" + "="*80)
    print("STEP 3: Adding parameter grouping and dependencies")
    print("="*80)

    data["grouping"] = {
        "masters": [
            "L Sync", "R Sync", "Mod Sync", "Filter On",
            "Gate On", "Duck On", "Noise On", "Wobble On", "Repitch"
        ],
        "dependents": {
            # Left channel delay sync dependencies
            "L 16th": ["L Sync"],
            "L Sync Mode": ["L Sync"],

            # Right channel delay sync dependencies
            "R 16th": ["R Sync"],
            "R Sync Mode": ["R Sync"],

            # Modulation sync dependencies
            # Mod Freq depends on Mod Sync state (but both are always visible)

            # Filter dependencies
            "HP Freq": ["Filter On"],
            "HP Res": ["Filter On"],
            "LP Freq": ["Filter On"],
            "LP Res": ["Filter On"],

            # Gate dependencies
            "Gate Thr": ["Gate On"],
            "Gate Release": ["Gate On"],

            # Duck dependencies
            "Duck Thr": ["Duck On"],
            "Duck Release": ["Duck On"],

            # Noise dependencies
            "Noise Amt": ["Noise On"],
            "Noise Mrph": ["Noise On"],

            # Wobble dependencies
            "Wobble Amt": ["Wobble On"],
            "Wobble Mrph": ["Wobble On"],

            # Repitch dependencies
            "Repitch Smoothing Time": ["Repitch"]
        },
        "dependent_master_values": {
            # When L Sync = 1.0 (Sync), show beat division controls
            "L 16th": {"L Sync": [1.0]},
            "L Sync Mode": {"L Sync": [1.0]},

            # When R Sync = 1.0 (Sync), show beat division controls
            "R 16th": {"R Sync": [1.0]},
            "R Sync Mode": {"R Sync": [1.0]},

            # When Filter On = 1.0, show filter controls
            "HP Freq": {"Filter On": [1.0]},
            "HP Res": {"Filter On": [1.0]},
            "LP Freq": {"Filter On": [1.0]},
            "LP Res": {"Filter On": [1.0]},

            # When Gate On = 1.0, show gate controls
            "Gate Thr": {"Gate On": [1.0]},
            "Gate Release": {"Gate On": [1.0]},

            # When Duck On = 1.0, show duck controls
            "Duck Thr": {"Duck On": [1.0]},
            "Duck Release": {"Duck On": [1.0]},

            # When Noise On = 1.0, show noise controls
            "Noise Amt": {"Noise On": [1.0]},
            "Noise Mrph": {"Noise On": [1.0]},

            # When Wobble On = 1.0, show wobble controls
            "Wobble Amt": {"Wobble On": [1.0]},
            "Wobble Mrph": {"Wobble On": [1.0]},

            # When Repitch = 1.0, show smoothing time
            "Repitch Smoothing Time": {"Repitch": [1.0]}
        },
        "apply_order": [],  # No strict ordering needed for Echo
        "requires_for_effect": {}  # No parameters that are no-ops without others
    }

    print(f"  ✓ Masters: {len(data['grouping']['masters'])} parameters")
    print(f"  ✓ Dependents: {len(data['grouping']['dependents'])} parameters")

    # Preview summary
    print("\n" + "="*80)
    print("ENRICHMENT PREVIEW")
    print("="*80)
    print(f"Device: {data['device_name']}")
    print(f"Signature: {ECHO_SIGNATURE}")
    print(f"Device Type: {data['device_type']}")
    print(f"Categories: {data['categories']}")
    print(f"Sections: {len(data['sections'])}")
    print(f"Parameters: {len(params_meta)}")
    print(f"Masters: {len(data['grouping']['masters'])}")
    print(f"Dependents: {len(data['grouping']['dependents'])}")

    # Confirm
    print("\n" + "="*80)
    if auto_confirm:
        print("Auto-confirming changes...")
        response = 'yes'
    else:
        response = input("Apply enrichment to Firestore? (yes/no): ")

    if response.lower() not in ['yes', 'y']:
        print("❌ Aborted - no changes made")
        return False

    # Apply to Firestore
    print("\n" + "="*80)
    print("APPLYING TO FIRESTORE")
    print("="*80)

    doc_ref.set(data)

    print(f"\n✅ SUCCESS - Echo device enriched!")
    print(f"   Database: dev-display-value")
    print(f"   Signature: {ECHO_SIGNATURE}")
    print(f"   Device: {data['device_name']}")
    print(f"   Categories: {data['categories']}")
    print(f"   Sections: {len(data['sections'])}")
    print(f"   Parameters: {len(params_meta)}")

    return True


def main():
    parser = argparse.ArgumentParser(description="Enrich Echo device mapping with standardized schema")
    parser.add_argument('--yes', '-y', action='store_true', help='Auto-confirm changes without prompting')
    args = parser.parse_args()

    success = enrich_echo(auto_confirm=args.yes)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
