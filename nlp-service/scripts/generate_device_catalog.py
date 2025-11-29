#!/usr/bin/env python3
"""
Generate device-catalog.md from dev-display-value Firestore database.

This script pulls device mappings for approved devices and generates
a markdown catalog for RAG indexing.
"""

from google.cloud import firestore
from datetime import datetime
from typing import List, Dict, Any
import json

# Approved device signatures for RAG
APPROVED_DEVICES = {
    "64ccfc236b79371d0b45e913f81bf0f3a55c6db9": {
        "name": "Reverb",
        "status": "Captured → Fitted → Audio Knowledge"
    },
    "9bfcc8b6e739d9675c03f6fe0664cfada9ef7df1": {
        "name": "Delay",
        "status": "Captured → Fitted → Audio Knowledge"
    },
    "82da8ccee34e85facb2a264e3110618dc199938e": {
        "name": "Align Delay",
        "status": "Captured → Fitted"
    },
    "d554752f4be9eee62197c37b45b1c22237842c37": {
        "name": "Amp",
        "status": "Captured → Fitted → Audio Knowledge"
    },
    "9e906e0ab3f18c4688107553744914f9ef6b9ee7": {
        "name": "Compressor",
        "status": "Captured → Fitted → Audio Knowledge"
    }
}

OUTPUT_PATH = "knowledge/fadebender/device-catalog.md"


def get_device_mapping(db: firestore.Client, signature: str) -> Dict[str, Any]:
    """Fetch device mapping from Firestore."""
    doc = db.collection('device_mappings').document(signature).get()
    if not doc.exists:
        return None
    return doc.to_dict()


def format_parameter(param: Dict[str, Any]) -> str:
    """Format a single parameter for markdown."""
    lines = []

    name = param.get('name', 'Unknown')
    display_name = param.get('display_name', name)

    lines.append(f"#### {display_name}")
    lines.append(f"- **Technical name**: `{name}`")

    # Display range
    min_display = param.get('min_display')
    max_display = param.get('max_display')
    unit = param.get('unit', '')
    if min_display is not None and max_display is not None:
        lines.append(f"- **Range**: {min_display} to {max_display} {unit}".strip())

    # Default value
    default = param.get('default_display')
    if default is not None:
        lines.append(f"- **Default**: {default} {unit}".strip())

    # Audio knowledge
    audio_knowledge = param.get('audio_knowledge')
    if audio_knowledge:
        lines.append(f"- **Description**: {audio_knowledge}")

    # Section/group
    section = param.get('section')
    if section:
        lines.append(f"- **Section**: {section}")

    lines.append("")
    return "\n".join(lines)


def format_device(signature: str, device_info: Dict[str, str], mapping: Dict[str, Any]) -> str:
    """Format a device mapping as markdown."""
    lines = []

    # Header
    lines.append(f"## {device_info['name']}")
    lines.append("")
    lines.append(f"**Device Signature**: `{signature}`")
    lines.append(f"**Status**: {device_info['status']}")
    lines.append("")

    # Metadata
    metadata = mapping.get('metadata', {})
    device_type = metadata.get('device_type', 'Unknown')
    lines.append(f"**Type**: {device_type}")

    description = metadata.get('description')
    if description:
        lines.append("")
        lines.append(f"**Description**: {description}")

    lines.append("")
    lines.append("---")
    lines.append("")

    # Parameters by section
    params_meta = mapping.get('params_meta', [])

    # Group by section
    sections = {}
    for param in params_meta:
        section = param.get('section', 'General')
        if section not in sections:
            sections[section] = []
        sections[section].append(param)

    # Output each section
    for section_name, params in sorted(sections.items()):
        lines.append(f"### {section_name}")
        lines.append("")

        for param in params:
            lines.append(format_parameter(param))

    lines.append("---")
    lines.append("")

    return "\n".join(lines)


def generate_catalog():
    """Generate device catalog from Firestore."""
    print("=" * 70)
    print("GENERATING DEVICE CATALOG")
    print("=" * 70)

    # Connect to dev-display-value database
    db = firestore.Client(database='dev-display-value')
    print(f"\n✓ Connected to dev-display-value database")
    print(f"✓ Processing {len(APPROVED_DEVICES)} approved devices")

    # Generate markdown
    lines = []

    # Header
    lines.append("# Fadebender Device Catalog")
    lines.append("")
    lines.append(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"**Source**: Firestore `dev-display-value` database")
    lines.append(f"**Devices**: {len(APPROVED_DEVICES)}")
    lines.append("")
    lines.append("This catalog contains detailed information about Ableton Live devices that Fadebender can control.")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Process each device
    for signature, device_info in APPROVED_DEVICES.items():
        print(f"\nProcessing {device_info['name']} ({signature[:8]}...)")

        mapping = get_device_mapping(db, signature)
        if not mapping:
            print(f"  ⚠️  Device not found in database!")
            continue

        params_count = len(mapping.get('params_meta', []))
        print(f"  ✓ Found {params_count} parameters")

        lines.append(format_device(signature, device_info, mapping))

    # Write to file
    catalog_content = "\n".join(lines)

    print(f"\n{'=' * 70}")
    print("WRITING CATALOG")
    print("=" * 70)
    print(f"\nOutput: {OUTPUT_PATH}")

    with open(OUTPUT_PATH, 'w') as f:
        f.write(catalog_content)

    file_size = len(catalog_content.encode('utf-8'))
    print(f"✓ Wrote {file_size:,} bytes")

    print("\n" + "=" * 70)
    print("✅ DEVICE CATALOG GENERATED SUCCESSFULLY")
    print("=" * 70)
    print("\nNext steps:")
    print("1. Review the generated catalog at knowledge/fadebender/device-catalog.md")
    print("2. Run the preset catalog generation script")
    print("3. Index both catalogs into your RAG system")


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
