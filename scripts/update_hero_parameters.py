#!/usr/bin/env python3
"""
Update device mappings and presets with hero parameter information.

This script:
1. Marks hero parameters in device mappings with 'hero': true
2. Adds character, intent_tags, and coarse_roles to presets
3. Preserves all existing data carefully

Usage:
    python3 scripts/update_hero_parameters.py [--database DB] [--dry-run]
"""
import sys
import os
import argparse
import json
from pathlib import Path
from typing import Dict, List, Optional

# Add project root to path
sys.path.insert(0, '/Users/sunils/ai-projects/fadebender')

from google.cloud import firestore


# Device configuration
DEVICES = {
    'Echo': {
        'signature': '9bd78001e088fcbde50e2ead80ef01e393f3d0ba',
        'hero_params_file': '/Users/sunils/Desktop/preset_feature_analysis/echo_hero_parameters.json',
        'presets_tagged_file': '/Users/sunils/Desktop/preset_feature_analysis/echo_presets_tagged.json',
    },
    'Reverb': {
        'signature': '64ccfc236b79371d0b45e913f81bf0f3a55c6db9',
        'hero_params_file': None,  # No hero params file yet
        'presets_tagged_file': '/Users/sunils/Desktop/preset_feature_analysis/reverb_presets_tagged.json',
    },
    'Delay': {
        'signature': '9bfcc8b6e739d9675c03f6fe0664cfada9ef7df1',
        'hero_params_file': None,  # No hero params file yet
        'presets_tagged_file': '/Users/sunils/Desktop/preset_feature_analysis/delay_presets_tagged.json',
    },
    'Align Delay': {
        'signature': '82da8ccee34e85facb2a264e3110618dc199938e',
        'hero_params_file': None,  # No hero params file yet
        'presets_tagged_file': '/Users/sunils/Desktop/preset_feature_analysis/align_delay_presets_tagged.json',
    },
}


def load_hero_parameters(filepath: str) -> List[str]:
    """Load hero parameter names from analysis file."""
    if not filepath or not os.path.exists(filepath):
        return []

    with open(filepath, 'r') as f:
        data = json.load(f)

    hero_params = data.get('hero_parameters', [])
    return [p['name'] for p in hero_params]


def load_preset_tags(filepath: str) -> Dict:
    """Load preset tags from analysis file."""
    if not os.path.exists(filepath):
        return {}

    with open(filepath, 'r') as f:
        return json.load(f)


def update_device_mapping(client, device_name: str, signature: str, hero_params: List[str], dry_run: bool = False):
    """Update device mapping with hero parameter flags."""
    print(f"\n[Device: {device_name}]")
    print("="*80)

    # Get device mapping
    device_ref = client.collection('device_mappings').document(signature)
    device_doc = device_ref.get()

    if not device_doc.exists:
        print(f"  ✗ Device mapping not found: {signature}")
        return False

    device_data = device_doc.to_dict()
    params_meta = device_data.get('params_meta', [])

    print(f"  Device: {device_data.get('device_name', 'Unknown')}")
    print(f"  Total parameters: {len(params_meta)}")
    print(f"  Hero parameters to mark: {len(hero_params)}")

    if not hero_params:
        print(f"  ⚠ No hero parameters defined - skipping device mapping update")
        return True

    # Mark hero parameters
    updated_count = 0
    for param in params_meta:
        param_name = param.get('name')

        # Check if this is a hero parameter
        is_hero = param_name in hero_params

        # Only update if the hero flag doesn't exist or is different
        if 'hero' not in param or param['hero'] != is_hero:
            param['hero'] = is_hero
            if is_hero:
                updated_count += 1

    if dry_run:
        print(f"  [DRY RUN] Would mark {updated_count} parameters as hero")
        print(f"  [DRY RUN] Hero parameters: {', '.join(hero_params[:3])}...")
    else:
        # Update device mapping
        device_ref.update({'params_meta': params_meta})
        print(f"  ✓ Marked {updated_count} parameters as hero")
        print(f"  ✓ Hero parameters: {', '.join(hero_params[:3])}...")

    return True


def update_presets(client, device_name: str, signature: str, preset_tags: Dict, dry_run: bool = False):
    """Update presets with character, intent_tags, and coarse_roles."""
    print(f"\n  [Presets for {device_name}]")
    print("  " + "-"*78)

    if not preset_tags:
        print(f"  ⚠ No preset tags defined - skipping preset updates")
        return True

    # Get all presets for this device
    presets_query = client.collection('presets').where('structure_signature', '==', signature)
    preset_docs = list(presets_query.stream())

    print(f"  Total presets in database: {len(preset_docs)}")
    print(f"  Total presets in analysis: {len(preset_tags)}")

    updated_count = 0
    missing_count = 0

    for preset_doc in preset_docs:
        preset_id = preset_doc.id
        preset_data = preset_doc.to_dict()
        preset_name = preset_data.get('preset_name', preset_id)

        # Find matching tag data
        # Match by document ID first (most reliable), then by preset_name, then by generated key
        tag_data = None
        for tag_key, tag_value in preset_tags.items():
            # Try matching by document ID (e.g., "delay_8dotball", "reverb_ambience")
            if tag_key == preset_id:
                tag_data = tag_value
                break
            # Try matching by preset_name
            if tag_key == preset_name:
                tag_data = tag_value
                break
            # Try matching by the generated key in the analysis file
            if tag_value.get('key') == f"{device_name.lower().replace(' ', '_')}_{preset_id}":
                tag_data = tag_value
                break

        if not tag_data:
            missing_count += 1
            continue

        # Check if update is needed
        needs_update = False
        updates = {}

        if 'character' in tag_data and preset_data.get('character') != tag_data['character']:
            updates['character'] = tag_data['character']
            needs_update = True

        if 'intent_tags' in tag_data and preset_data.get('intent_tags') != tag_data['intent_tags']:
            updates['intent_tags'] = tag_data['intent_tags']
            needs_update = True

        if 'coarse_roles' in tag_data and preset_data.get('coarse_roles') != tag_data['coarse_roles']:
            updates['coarse_roles'] = tag_data['coarse_roles']
            needs_update = True

        if needs_update:
            if dry_run:
                pass  # Don't print each preset in dry run
            else:
                # Update preset
                client.collection('presets').document(preset_id).update(updates)
            updated_count += 1

    if dry_run:
        print(f"  [DRY RUN] Would update {updated_count} presets with character/tags/roles")
        if missing_count > 0:
            print(f"  [DRY RUN] {missing_count} presets not found in analysis file")
    else:
        print(f"  ✓ Updated {updated_count} presets with character/tags/roles")
        if missing_count > 0:
            print(f"  ⚠ {missing_count} presets not found in analysis file")

    return True


def main():
    parser = argparse.ArgumentParser(
        description='Update device mappings and presets with hero parameter information',
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument('--database', '-d',
                        default='dev-display-value',
                        help='Firestore database name (default: dev-display-value)')
    parser.add_argument('--dry-run',
                        action='store_true',
                        help='Show what would be updated without making changes')
    parser.add_argument('--device',
                        choices=list(DEVICES.keys()),
                        help='Update only this device (default: all devices)')

    args = parser.parse_args()

    print("="*80)
    print("HERO PARAMETER UPDATE")
    print("="*80)
    print(f"Database: {args.database}")
    print(f"Mode: {'DRY RUN' if args.dry_run else 'LIVE UPDATE'}")
    print()

    # Set database environment variable
    os.environ["FIRESTORE_DATABASE_ID"] = args.database

    # Connect to Firestore
    client = firestore.Client(database=args.database)

    # Determine which devices to update
    devices_to_update = {args.device: DEVICES[args.device]} if args.device else DEVICES

    # Process each device
    for device_name, config in devices_to_update.items():
        signature = config['signature']
        hero_params_file = config.get('hero_params_file')
        presets_tagged_file = config.get('presets_tagged_file')

        # Load analysis files
        hero_params = load_hero_parameters(hero_params_file) if hero_params_file else []
        preset_tags = load_preset_tags(presets_tagged_file) if presets_tagged_file else {}

        # Update device mapping with hero flags
        if hero_params:
            update_device_mapping(client, device_name, signature, hero_params, args.dry_run)

        # Update presets with tags
        if preset_tags:
            update_presets(client, device_name, signature, preset_tags, args.dry_run)

    print("\n" + "="*80)
    if args.dry_run:
        print("DRY RUN COMPLETE - No changes were made")
        print("Run without --dry-run to apply changes")
    else:
        print("UPDATE COMPLETE")
        print("All hero parameters and preset tags have been updated")
    print("="*80)


if __name__ == "__main__":
    main()
