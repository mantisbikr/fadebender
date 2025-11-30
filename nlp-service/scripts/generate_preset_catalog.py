#!/usr/bin/env python3
"""
Generate preset-catalog.md from dev-display-value Firestore database.

This script pulls presets for approved structure signatures and generates
a markdown catalog for RAG indexing.
"""

from google.cloud import firestore
from datetime import datetime
from typing import List, Dict, Any
import json

# Approved device signatures (map to structure signatures)
# These correspond to the devices in the device catalog
APPROVED_DEVICE_SIGNATURES = {
    "64ccfc236b79371d0b45e913f81bf0f3a55c6db9": "Reverb",
    "9bfcc8b6e739d9675c03f6fe0664cfada9ef7df1": "Delay",
    "82da8ccee34e85facb2a264e3110618dc199938e": "Align Delay",
    "d554752f4be9eee62197c37b45b1c22237842c37": "Amp",
    "9e906e0ab3f18c4688107553744914f9ef6b9ee7": "Compressor"
}

OUTPUT_PATH = "knowledge/fadebender/preset-catalog.md"


def get_presets_for_device(db: firestore.Client, device_signature: str) -> List[Dict[str, Any]]:
    """Fetch all presets for a device signature."""
    # Query presets with matching structure_signature or device_signature
    presets = []

    # Try structure_signature field
    query = db.collection('presets').where('structure_signature', '==', device_signature)
    for doc in query.stream():
        preset_data = doc.to_dict()
        preset_data['id'] = doc.id
        presets.append(preset_data)

    # Also try device_signature field if structure_signature didn't match
    if not presets:
        query = db.collection('presets').where('device_signature', '==', device_signature)
        for doc in query.stream():
            preset_data = doc.to_dict()
            preset_data['id'] = doc.id
            presets.append(preset_data)

    return presets


def format_preset_parameter(param_name: str, param_value: Any) -> str:
    """Format a preset parameter value."""
    if isinstance(param_value, float):
        return f"{param_value:.2f}"
    return str(param_value)


def format_preset(preset: Dict[str, Any], device_name: str) -> str:
    """Format a single preset as markdown."""
    lines = []

    # Header
    preset_name = preset.get('preset_name', preset.get('name', preset.get('id', 'Unknown')))
    lines.append(f"### {preset_name}")
    lines.append("")

    # Metadata
    lines.append(f"**Device**: {device_name}")

    preset_id = preset.get('id', 'Unknown')
    lines.append(f"**Preset ID**: `{preset_id}`")

    # Description and character
    description = preset.get('description')
    if description:
        lines.append(f"**Description**: {description}")

    character = preset.get('character')
    if character:
        lines.append(f"**Sonic Character**: {character}")

    # Use cases
    use_cases = preset.get('use_cases', [])
    if use_cases:
        lines.append(f"**Best For**: {', '.join(use_cases)}")

    tags = preset.get('tags', [])
    if tags:
        lines.append(f"**Tags**: {', '.join(tags)}")

    category = preset.get('category')
    if category:
        lines.append(f"**Category**: {category}")

    lines.append("")

    # Parameter display values (human-readable)
    param_display_values = preset.get('parameter_display_values', {})
    if param_display_values:
        lines.append("**Parameter Settings**:")
        lines.append("")

        # Sort alphabetically
        param_list = sorted(param_display_values.items(), key=lambda x: x[0])

        for param_name, param_value in param_list:
            lines.append(f"- **{param_name}**: {param_value}")

    lines.append("")
    return "\n".join(lines)


def format_device_presets(device_signature: str, device_name: str, presets: List[Dict[str, Any]]) -> str:
    """Format all presets for a device."""
    lines = []

    # Header
    lines.append(f"## {device_name} Presets")
    lines.append("")
    lines.append(f"**Device Signature**: `{device_signature}`")
    lines.append(f"**Preset Count**: {len(presets)}")
    lines.append("")

    if not presets:
        lines.append("*No presets available for this device.*")
        lines.append("")
    else:
        for preset in sorted(presets, key=lambda p: p.get('name', p.get('id', ''))):
            lines.append(format_preset(preset, device_name))

    lines.append("---")
    lines.append("")

    return "\n".join(lines)


def generate_catalog():
    """Generate preset catalog from Firestore."""
    print("=" * 70)
    print("GENERATING PRESET CATALOG")
    print("=" * 70)

    # Connect to dev-display-value database
    db = firestore.Client(database='dev-display-value')
    print(f"\n✓ Connected to dev-display-value database")
    print(f"✓ Processing {len(APPROVED_DEVICE_SIGNATURES)} approved devices")

    # Generate markdown
    lines = []

    # Header
    lines.append("# Fadebender Preset Catalog")
    lines.append("")
    lines.append(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"**Source**: Firestore `dev-display-value` database")
    lines.append("")
    lines.append("This catalog contains preset configurations for Fadebender-supported Ableton Live devices.")
    lines.append("")
    lines.append("---")
    lines.append("")

    total_presets = 0

    # Process each device
    for device_signature, device_name in APPROVED_DEVICE_SIGNATURES.items():
        print(f"\nProcessing {device_name} ({device_signature[:8]}...)")

        presets = get_presets_for_device(db, device_signature)
        preset_count = len(presets)
        total_presets += preset_count

        print(f"  ✓ Found {preset_count} presets")

        lines.append(format_device_presets(device_signature, device_name, presets))

    # Write to file
    catalog_content = "\n".join(lines)

    print(f"\n{'=' * 70}")
    print("WRITING CATALOG")
    print("=" * 70)
    print(f"\nOutput: {OUTPUT_PATH}")
    print(f"Total presets: {total_presets}")

    with open(OUTPUT_PATH, 'w') as f:
        f.write(catalog_content)

    file_size = len(catalog_content.encode('utf-8'))
    print(f"✓ Wrote {file_size:,} bytes")

    print("\n" + "=" * 70)
    print("✅ PRESET CATALOG GENERATED SUCCESSFULLY")
    print("=" * 70)
    print("\nNext steps:")
    print("1. Review the generated catalog at knowledge/fadebender/preset-catalog.md")
    print("2. Index both catalogs (device + preset) into your RAG system")
    print("3. Test RAG queries about devices and presets")


if __name__ == "__main__":
    import sys
    try:
        generate_catalog()
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
