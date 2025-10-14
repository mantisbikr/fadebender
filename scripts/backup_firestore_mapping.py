#!/usr/bin/env python3
"""Backup device mapping from Firestore to local JSON file.

Usage:
  python3 scripts/backup_firestore_mapping.py --signature <SIG> --output <FILE>
  python3 scripts/backup_firestore_mapping.py --signature 64ccfc236b79371d0b45e913f81bf0f3a55c6db9 --output backups/reverb_$(date +%Y%m%d_%H%M%S).json
"""
import argparse
import json
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from google.cloud import firestore


def backup_device_mapping(signature: str, output_file: str, database: str = "dev-display-value"):
    """Backup complete device mapping from Firestore."""
    client = firestore.Client(database=database)

    # Get main document
    doc_ref = client.collection("device_mappings").document(signature)
    doc = doc_ref.get()

    if not doc.exists:
        print(f"Error: Document {signature} not found in {database}")
        return False

    data = doc.to_dict()

    # Get params subcollection if it exists
    params_subcoll = []
    for p in doc_ref.collection("params").stream():
        params_subcoll.append(p.to_dict())

    if params_subcoll:
        data["_params_subcollection"] = params_subcoll

    # Add backup metadata
    from datetime import datetime
    data["_backup_metadata"] = {
        "signature": signature,
        "database": database,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "params_meta_count": len(data.get("params_meta", [])),
        "params_subcollection_count": len(params_subcoll)
    }

    # Ensure output directory exists
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write to file
    with open(output_path, "w") as f:
        json.dump(data, f, indent=2)

    print(f"✓ Backed up device mapping to {output_file}")
    print(f"  Database: {database}")
    print(f"  Signature: {signature}")
    print(f"  params_meta: {len(data.get('params_meta', []))} params")
    if params_subcoll:
        print(f"  params subcollection: {len(params_subcoll)} params")

    return True


def main():
    parser = argparse.ArgumentParser(description="Backup device mapping from Firestore")
    parser.add_argument("--signature", required=True, help="Device signature hash")
    parser.add_argument("--output", required=True, help="Output JSON file path")
    parser.add_argument("--database", default="dev-display-value", help="Firestore database ID")

    args = parser.parse_args()

    # Set environment variable for Firestore
    os.environ["FIRESTORE_DATABASE_ID"] = args.database

    success = backup_device_mapping(args.signature, args.output, args.database)
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
