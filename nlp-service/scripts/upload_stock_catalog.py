#!/usr/bin/env python3
"""
Upload stock device catalog to Firestore dev-display-value database.
This creates a stock_catalog collection for LLM-based device discovery.
"""

import json
from pathlib import Path
from google.cloud import firestore

CATALOG_FILE = Path(__file__).parent.parent.parent / "docs" / "technical" / "stock_device_catalog.json"


def upload_stock_catalog():
    """Upload stock device catalog to Firestore."""

    print("="*70)
    print("UPLOADING STOCK DEVICE CATALOG")
    print("="*70)

    # Load catalog
    print("\n[1/2] Loading stock catalog...")
    with open(CATALOG_FILE, 'r') as f:
        catalog_data = json.load(f)

    devices = catalog_data['devices']
    print(f"✓ Loaded catalog with {len(devices)} devices")

    # Upload to dev-display-value
    print("\n[2/2] Uploading to dev-display-value database...")
    db = firestore.Client(database='dev-display-value')

    uploaded_count = 0
    for device_name, device_info in devices.items():
        doc_ref = db.collection('stock_catalog').document(device_info['signature'])

        # Store with metadata
        catalog_entry = {
            'device_name': device_name,
            'category': device_info['category'],
            'sonic_character': device_info['sonic_character'],
            'use_cases': device_info['use_cases'],
            'key_capabilities': device_info['key_capabilities'],
            'typical_applications': device_info['typical_applications'],
            'sonic_descriptors': device_info['sonic_descriptors'],
            'stock_presets': device_info['stock_presets'],
            'common_parameter_adjustments': device_info['common_parameter_adjustments'],
            'catalog_version': catalog_data['catalog_version'],
            'last_updated': catalog_data['last_updated']
        }

        doc_ref.set(catalog_entry)
        uploaded_count += 1
        print(f"  ✓ {device_name}")

    print(f"\n✓ Uploaded {uploaded_count} devices to stock_catalog collection")

    # Verify
    print("\n" + "="*70)
    print("VERIFICATION")
    print("="*70)

    catalog_docs = list(db.collection('stock_catalog').stream())
    print(f"\nstock_catalog collection now has {len(catalog_docs)} devices:")
    for doc in catalog_docs:
        data = doc.to_dict()
        print(f"  ✓ {data['device_name']} ({len(data['use_cases'])} use cases)")

    print("\n✅ Stock catalog uploaded successfully!")
    print("\n💡 LLMs can now query this collection for device discovery")
    print("   Example: 'Find devices for making airy guitar sounds'")

    return True


if __name__ == "__main__":
    import sys
    sys.exit(0 if upload_stock_catalog() else 1)
