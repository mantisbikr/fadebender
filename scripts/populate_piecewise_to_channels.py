#!/usr/bin/env python3
"""
Populate correct piecewise fit data to channel documents from volume_map.csv.

This script:
1. Loads piecewise data from volume_map.csv (-70 to +6 dB)
2. Creates correct send piecewise data (-76 to 0 dB) - FULL RANGE
3. Updates track_channel, return_channel, master_channel with piecewise fits
"""

import sys
import csv
from pathlib import Path
from google.cloud import firestore
from typing import List, Dict, Any

# Source file
VOLUME_MAP_FILE = Path(__file__).parent.parent / "docs" / "architecture" / "volume_map.csv"


def load_volume_mapping() -> List[Dict[str, float]]:
    """Load volume mapping from CSV."""
    if not VOLUME_MAP_FILE.exists():
        raise RuntimeError(f"Volume map file not found: {VOLUME_MAP_FILE}")

    mapping = []
    with open(VOLUME_MAP_FILE, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            mapping.append({
                'db': float(row['db']),
                'normalized': float(row['float'])  # Note: using 'normalized' key
            })

    return mapping


def create_send_mapping(volume_mapping: List[Dict[str, float]]) -> List[Dict[str, float]]:
    """Create send mapping with CORRECT range (-76 to 0 dB).

    The bug in upload_mixer_mappings.py filtered points where db <= 0.0,
    which created a range of -76 to -6 dB.

    We need ALL points from volume mapping (up to +6 dB),
    which after subtracting 6 dB gives us -76 to 0 dB.
    """
    send_mapping = [
        {
            'db': point['db'] - 6.0,
            'normalized': point['normalized']
        }
        for point in volume_mapping
    ]

    return send_mapping


def update_param_fit(params_meta: List[Dict], param_name: str, piecewise_points: List[Dict]) -> bool:
    """Update a parameter's fit with piecewise data."""
    for param in params_meta:
        if param.get('name') == param_name:
            param['fit'] = {
                'type': 'piecewise',
                'points': piecewise_points
            }
            return True
    return False


def main():
    """Populate piecewise fit data to channel documents."""
    print("=" * 70)
    print("POPULATING PIECEWISE FIT DATA TO CHANNEL DOCUMENTS")
    print("=" * 70)
    print()

    # Load volume mapping
    print(f"[1/3] Loading volume mapping from {VOLUME_MAP_FILE}...")
    volume_mapping = load_volume_mapping()
    print(f"  ✓ Loaded {len(volume_mapping)} points")
    print(f"    Range: {volume_mapping[0]['db']} dB to {volume_mapping[-1]['db']} dB")
    print(f"    Normalized: {volume_mapping[0]['normalized']} to {volume_mapping[-1]['normalized']}")
    print()

    # Create send mapping with FULL range
    print(f"[2/3] Creating send mapping with FULL range...")
    send_mapping = create_send_mapping(volume_mapping)
    print(f"  ✓ Created {len(send_mapping)} points")
    print(f"    Range: {send_mapping[0]['db']} dB to {send_mapping[-1]['db']} dB")
    print(f"    Normalized: {send_mapping[0]['normalized']} to {send_mapping[-1]['normalized']}")
    print()

    # Connect to Firestore
    print(f"[3/3] Updating channel documents in Firestore...")
    client = firestore.Client(database='dev-display-value')

    # Update track_channel
    print("\n  Updating track_channel...")
    track_ref = client.collection('mixer_mappings').document('track_channel')
    track_doc = track_ref.get()

    if not track_doc.exists:
        print("    ✗ track_channel document not found!")
        return 1

    track_data = track_doc.to_dict()
    params_meta = track_data.get('params_meta', [])

    # Update volume fit
    if update_param_fit(params_meta, 'volume', volume_mapping):
        print(f"    ✓ Updated volume fit ({len(volume_mapping)} points)")
    else:
        print("    ✗ volume parameter not found")
        return 1

    # Update sends fit
    if update_param_fit(params_meta, 'sends', send_mapping):
        print(f"    ✓ Updated sends fit ({len(send_mapping)} points)")
    else:
        print("    ✗ sends parameter not found")
        return 1

    # Save track_channel
    track_ref.update({'params_meta': params_meta})
    print("    ✓ Saved track_channel")

    # Update return_channel
    print("\n  Updating return_channel...")
    return_ref = client.collection('mixer_mappings').document('return_channel')
    return_doc = return_ref.get()

    if not return_doc.exists:
        print("    ✗ return_channel document not found!")
        return 1

    return_data = return_doc.to_dict()
    params_meta = return_data.get('params_meta', [])

    # Update volume fit
    if update_param_fit(params_meta, 'volume', volume_mapping):
        print(f"    ✓ Updated volume fit ({len(volume_mapping)} points)")
    else:
        print("    ✗ volume parameter not found")
        return 1

    # Update sends fit
    if update_param_fit(params_meta, 'sends', send_mapping):
        print(f"    ✓ Updated sends fit ({len(send_mapping)} points)")
    else:
        print("    ✗ sends parameter not found")
        return 1

    # Save return_channel
    return_ref.update({'params_meta': params_meta})
    print("    ✓ Saved return_channel")

    # Update master_channel
    print("\n  Updating master_channel...")
    master_ref = client.collection('mixer_mappings').document('master_channel')
    master_doc = master_ref.get()

    if not master_doc.exists:
        print("    ✗ master_channel document not found!")
        return 1

    master_data = master_doc.to_dict()
    params_meta = master_data.get('params_meta', [])

    # Update volume fit
    if update_param_fit(params_meta, 'volume', volume_mapping):
        print(f"    ✓ Updated volume fit ({len(volume_mapping)} points)")
    else:
        print("    ✗ volume parameter not found")
        return 1

    # Update cue fit (same as volume)
    if update_param_fit(params_meta, 'cue', volume_mapping):
        print(f"    ✓ Updated cue fit ({len(volume_mapping)} points)")
    else:
        print("    ✗ cue parameter not found")
        return 1

    # Save master_channel
    master_ref.update({'params_meta': params_meta})
    print("    ✓ Saved master_channel")

    print()
    print("=" * 70)
    print("✅ PIECEWISE FIT DATA POPULATED SUCCESSFULLY")
    print("=" * 70)
    print()
    print("Summary:")
    print(f"  • Volume/Cue: {len(volume_mapping)} points, {volume_mapping[0]['db']} to {volume_mapping[-1]['db']} dB")
    print(f"  • Sends: {len(send_mapping)} points, {send_mapping[0]['db']} to {send_mapping[-1]['db']} dB")
    print()
    print("Next step: Update fadebender_lom/volume.py to read from channel documents")

    return 0


if __name__ == "__main__":
    sys.exit(main())
