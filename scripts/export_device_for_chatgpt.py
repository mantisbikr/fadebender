#!/usr/bin/env python3
"""
Export device mapping and presets for ChatGPT audio engineering analysis.

Usage:
    python3 scripts/export_device_for_chatgpt.py <signature> [--output-dir DIR] [--database DB]

Example:
    python3 scripts/export_device_for_chatgpt.py 9bd78001e088fcbde50e2ead80ef01e393f3d0ba
"""
import sys
import os
import argparse
import json
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, '/Users/sunils/ai-projects/fadebender')

from google.cloud import firestore


def export_device_for_chatgpt(signature, output_dir, database='dev-display-value'):
    """Export device mapping and presets for ChatGPT analysis."""

    print("="*80)
    print("DEVICE EXPORT FOR CHATGPT ANALYSIS")
    print("="*80)
    print(f"Signature: {signature}")
    print(f"Database: {database}")
    print(f"Output: {output_dir}")

    # Set database environment variable
    os.environ["FIRESTORE_DATABASE_ID"] = database

    # Connect to Firestore
    client = firestore.Client(database=database)

    # Get device mapping
    print("\n[1/2] Fetching device mapping...")
    device_ref = client.collection('device_mappings').document(signature)
    device_doc = device_ref.get()

    if not device_doc.exists:
        print(f"❌ Device not found: {signature}")
        return False

    device_data = device_doc.to_dict()
    device_name = device_data.get('device_name', 'Unknown')
    print(f"  ✓ Found device: {device_name}")
    print(f"  ✓ Parameters: {len(device_data.get('params_meta', []))}")

    # Get all presets for this device
    print("\n[2/2] Fetching presets...")
    presets_query = client.collection('presets').where('structure_signature', '==', signature)
    preset_docs = list(presets_query.stream())

    print(f"  ✓ Found {len(preset_docs)} presets")

    # Prepare device mapping export
    print("\n" + "="*80)
    print("PREPARING DEVICE MAPPING EXPORT")
    print("="*80)

    device_export = {
        "device_name": device_data.get('device_name'),
        "device_type": device_data.get('device_type'),
        "categories": device_data.get('categories', [device_data.get('device_type')]),
        "structure_signature": signature,
        "total_parameters": len(device_data.get('params_meta', [])),
        "parameters": []
    }

    # Export each parameter with relevant info
    for param in device_data.get('params_meta', []):
        param_export = {
            "name": param.get('name'),
            "index": param.get('index'),
            "control_type": param.get('control_type'),
            "min": param.get('min'),
            "max": param.get('max')
        }

        # Add type-specific info
        if param.get('control_type') == 'continuous':
            param_export['unit'] = param.get('unit', '')
            param_export['min_display'] = param.get('min_display')
            param_export['max_display'] = param.get('max_display')
            if 'fit' in param:
                param_export['has_fit'] = True
                param_export['fit_type'] = param['fit'].get('function', param['fit'].get('type'))
                param_export['fit_r_squared'] = param['fit'].get('r_squared')
        elif param.get('control_type') in ['binary', 'quantized']:
            param_export['labels'] = param.get('labels', [])

        # Add master/dependent info if available
        if 'grouping' in device_data:
            if param.get('name') in device_data['grouping'].get('masters', []):
                param_export['is_master'] = True
            if param.get('name') in device_data['grouping'].get('dependents', {}):
                param_export['depends_on'] = device_data['grouping']['dependents'][param.get('name')]

        device_export['parameters'].append(param_export)

    # Add sections info if available
    if 'sections' in device_data:
        device_export['sections'] = {}
        for section_name, section_data in device_data['sections'].items():
            device_export['sections'][section_name] = {
                "description": section_data.get('description'),
                "sonic_focus": section_data.get('sonic_focus'),
                "parameters": section_data.get('parameters', [])
            }

    # Prepare presets export
    print("\nPREPARING PRESETS EXPORT")
    print("="*80)

    presets_export = {}

    for preset_doc in preset_docs:
        preset_data = preset_doc.to_dict()
        preset_name = preset_data.get('preset_name', preset_doc.id)

        preset_export = {
            "preset_name": preset_name,
            "key": f"{device_name.lower().replace(' ', '_')}_{preset_name.lower().replace(' ', '_').replace('/', '_')}",
            "parameters": {}
        }

        # Extract parameter values
        param_values = preset_data.get('parameter_values', {})
        param_display_values = preset_data.get('parameter_display_values', {})

        for param in device_data.get('params_meta', []):
            param_name = param.get('name')

            if param_name in param_values:
                preset_export['parameters'][param_name] = {
                    "normalized": param_values[param_name],
                    "display_value": param_display_values.get(param_name, param_values[param_name])
                }

        presets_export[preset_name] = preset_export

    # Save files
    print("\n" + "="*80)
    print("SAVING EXPORT FILES")
    print("="*80)

    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Save device mapping
    device_filename = f"{device_name.lower().replace(' ', '_')}_device_mapping.json"
    device_filepath = output_path / device_filename
    with open(device_filepath, 'w') as f:
        json.dump(device_export, f, indent=2, default=str)
    print(f"✓ Device mapping: {device_filepath}")
    print(f"  Size: {device_filepath.stat().st_size / 1024:.1f} KB")

    # Save presets
    presets_filename = f"{device_name.lower().replace(' ', '_')}_presets.json"
    presets_filepath = output_path / presets_filename
    with open(presets_filepath, 'w') as f:
        json.dump(presets_export, f, indent=2, default=str)
    print(f"✓ Presets: {presets_filepath}")
    print(f"  Size: {presets_filepath.stat().st_size / 1024:.1f} KB")

    # Create ChatGPT prompt file
    prompt_filename = f"{device_name.lower().replace(' ', '_')}_chatgpt_prompt.txt"
    prompt_filepath = output_path / prompt_filename

    prompt_text = f"""# Audio Engineering Analysis Request for {device_name}

I need you to analyze this Ableton Live device and its presets to identify hero parameters and create sonic descriptors.

## Files Provided:
1. {device_filename} - Complete device parameter mapping
2. {presets_filename} - All {len(presets_export)} presets with parameter values

## Your Task:

### 1. Identify Hero Parameters (6-8 parameters)
Based on audio engineering principles, identify the 6-8 most impactful parameters that should be exposed in the UI. Consider:
- Which parameters have the most significant sonic impact?
- Which are most commonly adjusted by audio engineers?
- Which represent the "80/20" rule - 20% of controls that create 80% of the effect?

For each hero parameter, provide:
- Parameter name
- Rationale for why it's a hero parameter
- Typical use cases

### 2. Analyze Each Preset
For each preset, provide:
- **Character**: A 4-part descriptor (e.g., "medium / very_long / wide / warm")
  - Part 1: Main characteristic (size, length, intensity, etc.)
  - Part 2: Secondary characteristic
  - Part 3: Spatial quality (wide, narrow, normal, ultra, etc.)
  - Part 4: Tonal quality (warm, neutral, bright, airy, dark, etc.)

- **Intent Tags**: 3-5 tags describing the sonic intent (e.g., ["clarity", "warm", "motion"])
  Common tags: tempo_sync, pingpong, warm, bright, clarity, wide, cinematic, motion, rhythmic, etc.

- **Coarse Roles**: Musical contexts where this preset shines (e.g., ["rhythmic/repeats", "pads/ambient"])
  Common roles: rhythmic/repeats, groove/slapback, pads/ambient, cinematic/fx, etc.

- **Hero Defaults**: The values of hero parameters in this preset (with appropriate units)

### 3. Output Format
Please provide three JSON files:

**File 1: {device_name.lower().replace(' ', '_')}_hero_parameters.json**
```json
{{
  "hero_parameters": [
    {{
      "name": "Parameter Name",
      "rationale": "Why this is a hero parameter",
      "use_cases": ["use case 1", "use case 2"]
    }}
  ]
}}
```

**File 2: {device_name.lower().replace(' ', '_')}_presets_tagged.json**
```json
{{
  "Preset Name": {{
    "key": "device_preset_name",
    "character": "descriptor1 / descriptor2 / descriptor3 / descriptor4",
    "intent_tags": ["tag1", "tag2", "tag3"],
    "coarse_roles": ["role1/subrole1", "role2/subrole2"],
    "hero_defaults": {{
      "Hero Param 1": value,
      "Hero Param 2": value
    }}
  }}
}}
```

**File 3: {device_name.lower().replace(' ', '_')}_presets_feature_vectors.json**
(Optional - if you can compute sonic feature vectors like size_norm, decay_sec, etc.)

## Reference Examples:
Look at these examples for the pattern:
- Reverb: /Users/sunils/Desktop/preset_feature_analysis/reverb_presets_tagged.json
- Delay: /Users/sunils/Desktop/preset_feature_analysis/delay_presets_tagged.json

## Begin Analysis:
"""

    with open(prompt_filepath, 'w') as f:
        f.write(prompt_text)
    print(f"✓ ChatGPT prompt: {prompt_filepath}")

    # Summary
    print("\n" + "="*80)
    print("EXPORT COMPLETE")
    print("="*80)
    print(f"\n✅ Exported {device_name} device for ChatGPT analysis")
    print(f"\n📁 Output directory: {output_path}")
    print(f"   - {device_filename}")
    print(f"   - {presets_filename}")
    print(f"   - {prompt_filename}")
    print(f"\n📋 Next steps:")
    print(f"   1. Review the device mapping and presets JSONs")
    print(f"   2. Copy the contents to ChatGPT along with the prompt")
    print(f"   3. ChatGPT will identify hero parameters and tag all presets")
    print(f"   4. Use the output to mark hero flags and fit only hero params")

    return True


def main():
    parser = argparse.ArgumentParser(
        description='Export device mapping and presets for ChatGPT audio engineering analysis',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Export Echo device
  python3 scripts/export_device_for_chatgpt.py 9bd78001e088fcbde50e2ead80ef01e393f3d0ba

  # Export to custom directory
  python3 scripts/export_device_for_chatgpt.py <signature> --output-dir ~/Desktop/echo_export

  # Export from different database
  python3 scripts/export_device_for_chatgpt.py <signature> --database default
        """
    )

    parser.add_argument('signature', help='Device structure signature')
    parser.add_argument('--output-dir', '-o',
                        default='/Users/sunils/Desktop/device_exports',
                        help='Output directory (default: ~/Desktop/device_exports)')
    parser.add_argument('--database', '-d',
                        default='dev-display-value',
                        help='Firestore database name (default: dev-display-value)')

    args = parser.parse_args()

    success = export_device_for_chatgpt(
        signature=args.signature,
        output_dir=args.output_dir,
        database=args.database
    )

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
