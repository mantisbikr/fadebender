#!/usr/bin/env python3
"""
Upload mixer mappings (volume, send conversions) to Firestore.

This replaces local CSV files with Firestore-backed mappings.
Stores:
- volume: dB ↔ Live float mapping (track/return volume)
- send: dB ↔ Live float mapping (send levels, with +6dB offset)
"""

import sys
import csv
from pathlib import Path
from google.cloud import firestore
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Source file
VOLUME_MAP_FILE = Path(__file__).parent.parent.parent / "docs" / "architecture" / "volume_map.csv"


def upload_mixer_mappings():
    """Upload mixer mappings to Firestore dev-display-value database."""

    print("="*70)
    print("UPLOADING MIXER MAPPINGS TO FIRESTORE")
    print("="*70)

    # Load CSV data
    print(f"\n[1/3] Loading volume mapping from {VOLUME_MAP_FILE}...")
    if not VOLUME_MAP_FILE.exists():
        print(f"❌ Error: {VOLUME_MAP_FILE} not found!")
        return False

    volume_mapping = []
    with open(VOLUME_MAP_FILE, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            volume_mapping.append({
                'db': float(row['db']),
                'float': float(row['float'])
            })

    print(f"✓ Loaded {len(volume_mapping)} volume mapping points")
    print(f"  Range: {volume_mapping[0]['db']}dB to {volume_mapping[-1]['db']}dB")
    print(f"  Float: {volume_mapping[0]['float']:.4f} to {volume_mapping[-1]['float']:.4f}")

    # Connect to Firestore
    print(f"\n[2/3] Connecting to Firestore...")
    db = firestore.Client(database='dev-display-value')

    # Upload volume mapping
    print(f"\n[3/3] Uploading mappings...")

    # Volume mapping (for tracks, returns, master)
    doc_ref = db.collection('mixer_mappings').document('volume')
    doc_ref.set({
        'type': 'volume',
        'description': 'Track/Return/Master volume dB to Live float conversion',
        'range_db': {
            'min': volume_mapping[0]['db'],
            'max': volume_mapping[-1]['db']
        },
        'range_float': {
            'min': volume_mapping[0]['float'],
            'max': volume_mapping[-1]['float']
        },
        'mapping': volume_mapping,
        'version': '1.0',
        'source': 'Measured from Ableton Live 12'
    })
    print(f"  ✓ volume mapping ({len(volume_mapping)} points)")

    # Send mapping (same data, but with +6dB offset documentation)
    send_mapping = [
        {
            'db': point['db'] - 6.0,  # Send range is -60 to 0dB
            'float': point['float']
        }
        for point in volume_mapping
        if point['db'] <= 0.0  # Sends only go up to 0dB
    ]

    doc_ref = db.collection('mixer_mappings').document('send')
    doc_ref.set({
        'type': 'send',
        'description': 'Send level dB to Live float conversion (with +6dB offset)',
        'range_db': {
            'min': send_mapping[0]['db'],
            'max': send_mapping[-1]['db']
        },
        'range_float': {
            'min': send_mapping[0]['float'],
            'max': send_mapping[-1]['float']
        },
        'mapping': send_mapping,
        'offset_db': 6.0,
        'note': 'Send dB values are offset by +6dB relative to track volume',
        'version': '1.0',
        'source': 'Derived from volume mapping with +6dB offset'
    })
    print(f"  ✓ send mapping ({len(send_mapping)} points, -60dB to 0dB)")

    # Verification
    print(f"\n" + "="*70)
    print("VERIFICATION")
    print("="*70)

    docs = list(db.collection('mixer_mappings').stream())
    print(f"\nmixer_mappings collection now has {len(docs)} documents:")
    for doc in docs:
        data = doc.to_dict()
        print(f"  ✓ {doc.id}: {data['description']}")
        print(f"     dB range: {data['range_db']['min']} to {data['range_db']['max']}")
        print(f"     Float range: {data['range_float']['min']:.4f} to {data['range_float']['max']:.4f}")
        print(f"     Points: {len(data['mapping'])}")

    print(f"\n✅ Mixer mappings uploaded successfully!")
    print(f"\n💡 Now update volume.py to read from Firestore instead of CSV")

    return True


if __name__ == "__main__":
    success = upload_mixer_mappings()
    sys.exit(0 if success else 1)
