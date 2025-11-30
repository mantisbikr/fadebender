#!/usr/bin/env python3
"""
Generate comprehensive device and preset catalogs from dev-display-value Firestore database.

This script pulls ALL available information:
- Device parameters with min/max display values and units
- Audio knowledge (sonic effects, use cases, typical values)
- Sections/grouping information
- Master/dependent relationships
- Preset parameter values and use cases
"""

from google.cloud import firestore
from datetime import datetime
from typing import List, Dict, Any
import json

# Approved device signatures for RAG
APPROVED_DEVICES = {
    "64ccfc236b79371d0b45e913f81bf0f3a55c6db9": "Reverb",
    "9bfcc8b6e739d9675c03f6fe0664cfada9ef7df1": "Delay",
    "82da8ccee34e85facb2a264e3110618dc199938e": "Align Delay",
    "d554752f4be9eee62197c37b45b1c22237842c37": "Amp",
    "9e906e0ab3f18c4688107553744914f9ef6b9ee7": "Compressor"
}

DEVICE_CATALOG_PATH = "knowledge/fadebender/device-catalog.md"
PRESET_CATALOG_PATH = "knowledge/fadebender/preset-catalog.md"


def format_audio_knowledge(knowledge: Dict[str, Any]) -> str:
    """Format audio knowledge as readable markdown."""
    lines = []

    # Audio function
    if 'audio_function' in knowledge:
        lines.append(f"**Function**: {knowledge['audio_function']}")

    # Sonic effects
    if 'sonic_effect' in knowledge:
        sonic = knowledge['sonic_effect']
        if 'increasing' in sonic:
            lines.append(f"**Increasing**: {sonic['increasing']}")
        if 'decreasing' in sonic:
            lines.append(f"**Decreasing**: {sonic['decreasing']}")

    # Technical detail
    if 'technical_detail' in knowledge:
        lines.append(f"**Technical**: {knowledge['technical_detail']}")

    # Use cases
    if 'use_cases' in knowledge:
        use_cases = knowledge['use_cases']
        if isinstance(use_cases, list):
            lines.append("**Use Cases**:")
            for use_case in use_cases:
                lines.append(f"  - {use_case}")
        else:
            lines.append(f"**Use Cases**: {use_cases}")

    # Typical values
    if 'typical_values' in knowledge:
        typ_vals = knowledge['typical_values']
        lines.append("**Typical Values**:")
        for context, value in typ_vals.items():
            lines.append(f"  - {context}: {value}")

    return "\n".join(lines)


def format_parameter(param: Dict[str, Any]) -> str:
    """Format a single parameter with all available information."""
    lines = []

    name = param.get('name', 'Unknown')
    lines.append(f"#### {name}")
    lines.append("")

    # Control type
    control_type = param.get('control_type', 'unknown')
    lines.append(f"**Control Type**: {control_type}")

    # Range with units
    if control_type == 'continuous':
        min_display = param.get('min_display')
        max_display = param.get('max_display')
        unit = param.get('unit', '')

        if min_display is not None and max_display is not None:
            range_str = f"{min_display} to {max_display}"
            if unit:
                range_str += f" {unit}"
            lines.append(f"**Range**: {range_str}")
    elif control_type == 'binary':
        labels = param.get('labels', ['off', 'on'])
        lines.append(f"**Values**: {labels[0]} / {labels[1]}")
    elif control_type == 'discrete':
        labels = param.get('labels', [])
        if labels:
            lines.append(f"**Options**: {', '.join(labels)}")

    lines.append("")

    # Audio knowledge
    audio_knowledge = param.get('audio_knowledge')
    if audio_knowledge:
        lines.append(format_audio_knowledge(audio_knowledge))
        lines.append("")

    # Manual context (official Ableton documentation)
    manual_context = param.get('manual_context')
    if manual_context:
        if 'official_description' in manual_context:
            lines.append(f"**Ableton Manual**: {manual_context['official_description']}")
        if 'technical_spec' in manual_context:
            lines.append(f"**Technical Spec**: {manual_context['technical_spec']}")
        if 'acoustic_principle' in manual_context:
            lines.append(f"**Acoustic Principle**: {manual_context['acoustic_principle']}")
        lines.append("")

    lines.append("---")
    lines.append("")
    return "\n".join(lines)


def format_section(section_name: str, section_data: Dict[str, Any], params: List[Dict[str, Any]]) -> str:
    """Format a section with its parameters."""
    lines = []

    lines.append(f"### {section_name}")
    lines.append("")

    # Section metadata
    if 'description' in section_data:
        lines.append(f"**Description**: {section_data['description']}")

    if 'sonic_focus' in section_data:
        lines.append(f"**Sonic Focus**: {section_data['sonic_focus']}")

    if 'technical_notes' in section_data and section_data['technical_notes']:
        lines.append("")
        lines.append("**Technical Notes**:")
        for note in section_data['technical_notes']:
            lines.append(f"- {note}")

    lines.append("")
    lines.append("---")
    lines.append("")

    # Parameters in this section
    for param in params:
        lines.append(format_parameter(param))

    return "\n".join(lines)


def format_device(signature: str, device_name: str, mapping: Dict[str, Any]) -> str:
    """Format a complete device with all information."""
    lines = []

    # Header
    lines.append(f"## {device_name}")
    lines.append("")
    lines.append(f"**Device Signature**: `{signature}`")

    # Device description
    device_desc = mapping.get('device_description')
    if device_desc:
        lines.append(f"**Description**: {device_desc}")

    device_type = mapping.get('device_type')
    if device_type:
        lines.append(f"**Type**: {device_type}")

    param_count = len(mapping.get('params_meta', []))
    lines.append(f"**Parameters**: {param_count}")

    lines.append("")
    lines.append("---")
    lines.append("")

    # Sections
    sections_data = mapping.get('sections', {})
    params_meta = mapping.get('params_meta', [])

    # Create param lookup by name
    params_by_name = {p['name']: p for p in params_meta}

    # Format each section
    for section_name in sorted(sections_data.keys()):
        section_info = sections_data[section_name]
        section_param_names = section_info.get('parameters', [])

        # Get full param objects for this section
        section_params = []
        for param_name in section_param_names:
            if param_name in params_by_name:
                section_params.append(params_by_name[param_name])

        if section_params:
            lines.append(format_section(section_name, section_info, section_params))

    # Master/Dependent relationships
    grouping = mapping.get('grouping', {})
    if grouping:
        lines.append("### Parameter Relationships")
        lines.append("")

        masters = grouping.get('masters', [])
        if masters:
            lines.append("**Master Parameters** (control other parameters):")
            for master in masters:
                lines.append(f"- {master}")
            lines.append("")

        dependents_map = grouping.get('dependents', {})
        if dependents_map:
            lines.append("**Dependencies**:")
            for master, deps in dependents_map.items():
                if deps:
                    lines.append(f"- **{master}** controls: {', '.join(deps)}")
            lines.append("")

    lines.append("---")
    lines.append("")

    return "\n".join(lines)


def format_preset(preset: Dict[str, Any], device_name: str) -> str:
    """Format a preset with all parameter values and use cases."""
    lines = []

    # Header
    preset_name = preset.get('preset_name', preset.get('name', preset.get('id', 'Unknown')))
    lines.append(f"### {preset_name}")
    lines.append("")

    # Metadata
    lines.append(f"**Device**: {device_name}")
    lines.append(f"**Preset ID**: `{preset.get('id', 'Unknown')}`")

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

    category = preset.get('category')
    if category:
        lines.append(f"**Category**: {category}")

    lines.append("")

    # Parameter display values (human-readable values)
    param_display_values = preset.get('parameter_display_values', {})
    if param_display_values:
        lines.append("**Parameter Settings**:")
        lines.append("")

        # Sort alphabetically
        param_list = sorted(param_display_values.items(), key=lambda x: x[0])

        for param_name, param_value in param_list:
            lines.append(f"- **{param_name}**: {param_value}")

    lines.append("")
    lines.append("---")
    lines.append("")

    return "\n".join(lines)


def generate_device_catalog(db: firestore.Client) -> str:
    """Generate comprehensive device catalog."""
    lines = []

    # Header
    lines.append("# Fadebender Device Catalog")
    lines.append("")
    lines.append(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"**Source**: Firestore `dev-display-value` database")
    lines.append(f"**Devices**: {len(APPROVED_DEVICES)}")
    lines.append("")
    lines.append("This catalog contains comprehensive information about Ableton Live devices:")
    lines.append("- Parameter ranges with units (min/max display values)")
    lines.append("- Audio knowledge (sonic effects, use cases, typical values)")
    lines.append("- Sections and grouping")
    lines.append("- Master/dependent parameter relationships")
    lines.append("- Official Ableton manual descriptions")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Process each device
    for signature, device_name in APPROVED_DEVICES.items():
        print(f"\nProcessing {device_name} ({signature[:8]}...)")

        doc = db.collection('device_mappings').document(signature).get()
        if not doc.exists:
            print(f"  ⚠️  Device not found in database!")
            continue

        mapping = doc.to_dict()
        params_count = len(mapping.get('params_meta', []))
        print(f"  ✓ Found {params_count} parameters")

        lines.append(format_device(signature, device_name, mapping))

    return "\n".join(lines)


def generate_preset_catalog(db: firestore.Client) -> str:
    """Generate comprehensive preset catalog."""
    lines = []

    # Header
    lines.append("# Fadebender Preset Catalog")
    lines.append("")
    lines.append(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"**Source**: Firestore `dev-display-value` database")
    lines.append("")
    lines.append("This catalog contains presets for all supported devices with:")
    lines.append("- Preset descriptions and sonic character")
    lines.append("- Use cases and best applications")
    lines.append("- All parameter values (display values)")
    lines.append("- When to use each preset")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Process each device
    total_presets = 0
    for signature, device_name in APPROVED_DEVICES.items():
        print(f"\nFetching presets for {device_name}...")

        # Query presets with matching structure_signature
        query = db.collection('presets').where('structure_signature', '==', signature)
        presets = []
        for doc in query.stream():
            preset_data = doc.to_dict()
            preset_data['id'] = doc.id
            presets.append(preset_data)

        if not presets:
            print(f"  ⚠️  No presets found")
            continue

        print(f"  ✓ Found {len(presets)} presets")
        total_presets += len(presets)

        # Device header
        lines.append(f"## {device_name} Presets")
        lines.append("")
        lines.append(f"**Device Signature**: `{signature}`")
        lines.append(f"**Preset Count**: {len(presets)}")
        lines.append("")
        lines.append("---")
        lines.append("")

        # Sort presets by name
        presets.sort(key=lambda p: p.get('preset_name', p.get('name', p.get('id', ''))))

        # Format each preset
        for preset in presets:
            lines.append(format_preset(preset, device_name))

    print(f"\nTotal presets: {total_presets}")
    return "\n".join(lines)


def main():
    """Generate both catalogs."""
    print("=" * 70)
    print("GENERATING COMPREHENSIVE FADEBENDER CATALOGS")
    print("=" * 70)

    # Connect to dev-display-value database
    db = firestore.Client(database='dev-display-value')
    print(f"\n✓ Connected to dev-display-value database")
    print(f"✓ Processing {len(APPROVED_DEVICES)} approved devices")

    # Generate device catalog
    print("\n" + "=" * 70)
    print("GENERATING DEVICE CATALOG")
    print("=" * 70)
    device_catalog = generate_device_catalog(db)

    with open(DEVICE_CATALOG_PATH, 'w') as f:
        f.write(device_catalog)

    device_size = len(device_catalog.encode('utf-8'))
    print(f"\n✓ Device catalog: {device_size:,} bytes → {DEVICE_CATALOG_PATH}")

    # Generate preset catalog
    print("\n" + "=" * 70)
    print("GENERATING PRESET CATALOG")
    print("=" * 70)
    preset_catalog = generate_preset_catalog(db)

    with open(PRESET_CATALOG_PATH, 'w') as f:
        f.write(preset_catalog)

    preset_size = len(preset_catalog.encode('utf-8'))
    print(f"\n✓ Preset catalog: {preset_size:,} bytes → {PRESET_CATALOG_PATH}")

    print("\n" + "=" * 70)
    print("✅ CATALOGS GENERATED SUCCESSFULLY")
    print("=" * 70)
    print("\nNext steps:")
    print("1. Review the generated catalogs")
    print("2. Convert to HTML: python3 scripts/convert_fadebender_catalogs.py")
    print("3. Upload to GCS and reindex in Vertex AI Search")
    print("\nThe catalogs now include:")
    print("- Min/max display values with units for all parameters")
    print("- Audio knowledge and use cases")
    print("- Section groupings and sonic focus")
    print("- Master/dependent parameter relationships")
    print("- Preset parameter values and descriptions")


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
