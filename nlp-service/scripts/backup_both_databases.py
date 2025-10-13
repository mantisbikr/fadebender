#!/usr/bin/env python3
"""
Backup both Firestore databases completely.
Creates comprehensive backups of DEFAULT and dev-display-value databases.
"""

import json
from datetime import datetime
from pathlib import Path
from google.cloud import firestore


def backup_database(client, database_name, output_dir):
    """Backup all collections from a Firestore database."""

    print(f"\n{'='*70}")
    print(f"BACKING UP: {database_name}")
    print(f"{'='*70}")

    backup_data = {
        '_metadata': {
            'database': database_name,
            'timestamp': datetime.now().isoformat(),
            'backup_type': 'full'
        },
        'collections': {}
    }

    # Backup device_mappings collection
    print(f"\n[1/3] Backing up device_mappings collection...")
    device_mappings = []
    for doc in client.collection('device_mappings').stream():
        doc_data = doc.to_dict()
        doc_data['_id'] = doc.id

        # Also backup params subcollection if it exists
        params = []
        try:
            for param_doc in doc.reference.collection('params').stream():
                param_data = param_doc.to_dict()
                param_data['_id'] = param_doc.id
                params.append(param_data)
        except Exception as e:
            print(f"  Note: No params subcollection for {doc.id}")

        if params:
            doc_data['_params_subcollection'] = params

        device_mappings.append(doc_data)

    backup_data['collections']['device_mappings'] = device_mappings
    print(f"  ✓ Backed up {len(device_mappings)} device mappings")

    # Backup presets collection
    print(f"\n[2/3] Backing up presets collection...")
    presets = []
    for doc in client.collection('presets').stream():
        doc_data = doc.to_dict()
        doc_data['_id'] = doc.id
        presets.append(doc_data)

    backup_data['collections']['presets'] = presets
    print(f"  ✓ Backed up {len(presets)} presets")

    # Backup other collections
    print(f"\n[3/3] Backing up other collections...")
    other_collections = ['prompt_templates', 'schemas']
    for collection_name in other_collections:
        docs = []
        try:
            for doc in client.collection(collection_name).stream():
                doc_data = doc.to_dict()
                doc_data['_id'] = doc.id
                docs.append(doc_data)
            backup_data['collections'][collection_name] = docs
            print(f"  ✓ Backed up {len(docs)} {collection_name}")
        except Exception as e:
            print(f"  ⚠️  Could not backup {collection_name}: {e}")

    # Save to file
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"{database_name.replace('(', '').replace(')', '')}_{timestamp}.json"
    filepath = output_dir / filename

    with open(filepath, 'w') as f:
        json.dump(backup_data, f, indent=2, default=str)

    print(f"\n✓ Backup saved: {filepath}")
    print(f"  File size: {filepath.stat().st_size / 1024:.1f} KB")

    return filepath


def main():
    print("="*70)
    print("FIRESTORE DATABASE BACKUP")
    print("="*70)

    # Create backup directory
    backup_dir = Path('/Users/sunils/ai-projects/fadebender/backups/database_backups')
    backup_dir.mkdir(parents=True, exist_ok=True)
    print(f"\nBackup directory: {backup_dir}")

    backups_created = []

    # Backup DEFAULT database
    try:
        client_default = firestore.Client()
        filepath = backup_database(client_default, 'default', backup_dir)
        backups_created.append(('default', filepath))
    except Exception as e:
        print(f"\n❌ Error backing up DEFAULT database: {e}")
        import traceback
        traceback.print_exc()

    # Backup dev-display-value database
    try:
        client_dev = firestore.Client(database='dev-display-value')
        filepath = backup_database(client_dev, 'dev-display-value', backup_dir)
        backups_created.append(('dev-display-value', filepath))
    except Exception as e:
        print(f"\n❌ Error backing up dev-display-value database: {e}")
        import traceback
        traceback.print_exc()

    # Summary
    print("\n" + "="*70)
    print("BACKUP SUMMARY")
    print("="*70)

    if backups_created:
        print("\n✅ Backups created:")
        for db_name, filepath in backups_created:
            size_kb = filepath.stat().st_size / 1024
            print(f"  {db_name}: {filepath.name} ({size_kb:.1f} KB)")

        print(f"\n📁 All backups in: {backup_dir}")
        print("\n✅ Safe to proceed with consolidation!")
        return True
    else:
        print("\n❌ No backups created!")
        return False


if __name__ == "__main__":
    import sys
    sys.exit(0 if main() else 1)
