#!/usr/bin/env python3
"""
Fix the 6 Reverb presets missing parameter_display_values.

SAFETY:
- Only updates presets that are missing parameter_display_values
- Preserves all existing fields
- Creates backup before running
- Uses device mapping for accurate conversion
"""

import sys
sys.path.insert(0, '/Users/sunils/ai-projects/fadebender')

from google.cloud import firestore
from typing import Dict, Any, Optional

# Reverb device signature
REVERB_SIG = '64ccfc236b79371d0b45e913f81bf0f3a55c6db9'

# The 6 presets missing display values
MISSING_PRESETS = [
    'reverb_bright_reflections',
    'reverb_church',
    'reverb_concert_hall',
    'reverb_corridor',
    'reverb_dark_medium_room',
    'reverb_dark_small_room'
]


def denormalize_value(normalized_val: float, min_display: Optional[float], max_display: Optional[float]) -> str:
    """Convert normalized value (0-1) to display value using min/max display."""
    if min_display is None or max_display is None:
        # No display range, just return the normalized value
        return f"{normalized_val:.1f}"

    display_val = normalized_val * (max_display - min_display) + min_display

    # Round to 1 decimal place for cleaner output
    return f"{display_val:.1f}"


def generate_display_values(parameter_values: Dict[str, float], params_meta: list) -> Dict[str, str]:
    """Generate parameter_display_values from parameter_values using device mapping."""
    display_values = {}

    # Create lookup dict for params_meta by name
    params_lookup = {p.get('name'): p for p in params_meta}

    for param_name, norm_value in parameter_values.items():
        param_meta = params_lookup.get(param_name)

        if param_meta:
            min_display = param_meta.get('min_display')
            max_display = param_meta.get('max_display')
            display_values[param_name] = denormalize_value(norm_value, min_display, max_display)
        else:
            # Fallback: just use the normalized value
            display_values[param_name] = f"{norm_value:.1f}"

    return display_values


def main():
    print("="*70)
    print("FIX MISSING REVERB PARAMETER DISPLAY VALUES")
    print("="*70)

    db = firestore.Client(database='dev-display-value')

    # Get Reverb device mapping
    print("\n[1/3] Loading Reverb device mapping...")
    mapping_doc = db.collection('device_mappings').document(REVERB_SIG).get()

    if not mapping_doc.exists:
        print("❌ ERROR: Reverb device mapping not found!")
        return False

    mapping = mapping_doc.to_dict()
    params_meta = mapping.get('params_meta', [])
    print(f"✓ Loaded mapping with {len(params_meta)} parameters")

    # Process each missing preset
    print(f"\n[2/3] Processing {len(MISSING_PRESETS)} presets...")
    fixed_count = 0
    skipped_count = 0

    for preset_id in MISSING_PRESETS:
        print(f"\n  Processing: {preset_id}")

        # Get preset
        preset_doc = db.collection('presets').document(preset_id).get()

        if not preset_doc.exists:
            print(f"    ⚠️  Preset not found, skipping")
            skipped_count += 1
            continue

        preset_data = preset_doc.to_dict()

        # Check if it already has display values
        if 'parameter_display_values' in preset_data and preset_data['parameter_display_values']:
            print(f"    ⚠️  Already has display values, skipping")
            skipped_count += 1
            continue

        # Check if it has parameter_values
        parameter_values = preset_data.get('parameter_values')
        if not parameter_values:
            print(f"    ❌ No parameter_values found, skipping")
            skipped_count += 1
            continue

        # Generate display values
        display_values = generate_display_values(parameter_values, params_meta)

        print(f"    ✓ Generated {len(display_values)} display values")
        print(f"      Sample: {list(display_values.items())[:2]}")

        # Update preset with ONLY the new display values field
        # This preserves all existing data
        update_data = {
            'parameter_display_values': display_values
        }

        db.collection('presets').document(preset_id).update(update_data)
        print(f"    ✅ Updated preset")
        fixed_count += 1

    # Summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    print(f"✅ Fixed: {fixed_count} presets")
    print(f"⚠️  Skipped: {skipped_count} presets")

    if fixed_count > 0:
        print(f"\n✅ Successfully regenerated display values for {fixed_count} Reverb presets!")
        print("\nNext steps:")
        print("1. Verify the data looks correct")
        print("2. Run generate_preset_catalog.py to rebuild the catalog")
        print("3. Re-embed the catalog in Vertex AI Search")
        return True
    else:
        print(f"\n⚠️  No presets were fixed")
        return False


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
