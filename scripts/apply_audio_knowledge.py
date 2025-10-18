#!/usr/bin/env python3
"""
Apply accurate audio knowledge from JSON files to Firestore.

This script reads curated audio knowledge from JSON files and updates
device parameters in Firestore.

Usage:
    # Update all parameters in a device knowledge file
    python scripts/apply_audio_knowledge.py data/audio_knowledge/reverb_accurate.json

    # Dry run to see what would change
    python scripts/apply_audio_knowledge.py data/audio_knowledge/reverb_accurate.json --dry-run

    # Update specific parameter only
    python scripts/apply_audio_knowledge.py data/audio_knowledge/reverb_accurate.json --param "ER Spin Rate"
"""

import argparse
import json
from pathlib import Path
from typing import Any, Dict

from google.cloud import firestore


def load_audio_knowledge(filepath: str) -> Dict[str, Any]:
    """Load audio knowledge from JSON file."""
    with open(filepath, 'r') as f:
        return json.load(f)


def update_device_audio_knowledge(
    knowledge_data: Dict[str, Any],
    param_filter: str = None,
    dry_run: bool = False
) -> None:
    """Update audio knowledge for device parameters in Firestore.

    Args:
        knowledge_data: Loaded JSON with device and parameter knowledge
        param_filter: If provided, only update this parameter name
        dry_run: If True, show changes without updating
    """
    client = firestore.Client(project='fadebender', database='dev-display-value')

    device_sig = knowledge_data['device_signature']
    device_name = knowledge_data['device_name']
    parameters = knowledge_data['parameters']

    # Filter parameters if requested
    if param_filter:
        if param_filter not in parameters:
            print(f"❌ Parameter '{param_filter}' not found in knowledge file")
            return
        parameters = {param_filter: parameters[param_filter]}

    doc_ref = client.collection('device_mappings').document(device_sig)

    # Read current document
    doc = doc_ref.get()
    if not doc.exists:
        print(f"❌ Document {device_sig} not found")
        return

    data = doc.to_dict()
    params_meta = data.get('params_meta', [])

    updates_made = []
    not_found = []

    # Update each parameter
    for param_name, new_knowledge in parameters.items():
        # Find parameter in params_meta
        param_index = None
        for i, p in enumerate(params_meta):
            if p.get('name') == param_name:
                param_index = i
                break

        if param_index is None:
            not_found.append(param_name)
            continue

        old_knowledge = params_meta[param_index].get('audio_knowledge', {})

        if dry_run:
            print(f"\n{'='*80}")
            print(f"PARAMETER: {param_name}")
            print(f"{'='*80}")
            print("\n📋 OLD:")
            print(json.dumps(old_knowledge, indent=2))
            print("\n✨ NEW:")
            print(json.dumps(new_knowledge, indent=2))
        else:
            params_meta[param_index]['audio_knowledge'] = new_knowledge
            updates_made.append(param_name)

    if not_found:
        print(f"\n⚠️  Parameters not found in Firestore:")
        for pname in not_found:
            print(f"  - {pname}")

    if dry_run:
        print(f"\n{'='*80}")
        print(f"DRY RUN COMPLETE - No changes made")
        print(f"Would update {len(updates_made)} parameters in {device_name}")
        print(f"{'='*80}")
        return

    # Apply updates to Firestore
    if updates_made:
        try:
            doc_ref.update({'params_meta': params_meta})
            print(f"\n✅ Updated {len(updates_made)} parameters in {device_name}:")
            for pname in updates_made:
                print(f"  ✓ {pname}")
        except Exception as e:
            print(f"\n❌ Error updating Firestore: {e}")
    else:
        print(f"\n⚠️  No parameters updated")


def main():
    parser = argparse.ArgumentParser(
        description='Apply curated audio knowledge from JSON to Firestore',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Update all parameters from reverb knowledge file
  python scripts/apply_audio_knowledge.py data/audio_knowledge/reverb_accurate.json

  # Preview changes without updating (dry run)
  python scripts/apply_audio_knowledge.py data/audio_knowledge/reverb_accurate.json --dry-run

  # Update only ER Spin Rate parameter
  python scripts/apply_audio_knowledge.py data/audio_knowledge/reverb_accurate.json --param "ER Spin Rate"
        """
    )
    parser.add_argument('knowledge_file', help='Path to audio knowledge JSON file')
    parser.add_argument('--param', help='Only update this specific parameter')
    parser.add_argument('--dry-run', action='store_true', help='Show changes without updating')

    args = parser.parse_args()

    # Validate file exists
    if not Path(args.knowledge_file).exists():
        print(f"❌ File not found: {args.knowledge_file}")
        return

    # Load knowledge data
    try:
        knowledge_data = load_audio_knowledge(args.knowledge_file)
    except Exception as e:
        print(f"❌ Error loading JSON: {e}")
        return

    # Update Firestore
    update_device_audio_knowledge(
        knowledge_data,
        param_filter=args.param,
        dry_run=args.dry_run
    )


if __name__ == '__main__':
    main()
