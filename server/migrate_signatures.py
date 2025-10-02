#!/usr/bin/env python3
"""
Migrate device mappings from old signature format to new structure-based format.

OLD: SHA1(device_name|param_count|param_names)
NEW: SHA1(param_count|param_names)  # No device name

This enables all Ableton Reverb presets (Arena Tail, Vocal Hall, etc.) to share
one structure mapping.
"""

import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add server to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from server.services.mapping_store import MappingStore


def compute_old_signature(device_name: str, params: List[Dict[str, Any]]) -> str:
    """Compute OLD signature (includes device name)."""
    param_names = ",".join([str(p.get("name", "")) for p in params])
    base = f"{device_name}|{len(params)}|{param_names}"
    return hashlib.sha1(base.encode("utf-8")).hexdigest()


def compute_new_signature(params: List[Dict[str, Any]]) -> str:
    """Compute NEW signature (excludes device name)."""
    param_names = ",".join([str(p.get("name", "")) for p in params])
    base = f"{len(params)}|{param_names}"
    return hashlib.sha1(base.encode("utf-8")).hexdigest()


def detect_device_type(params: List[Dict[str, Any]]) -> str:
    """Detect device type from parameter fingerprints."""
    param_set = set(p.get("name", "") for p in params)

    # Ableton Reverb signature parameters
    if {"ER Spin On", "Freeze On", "Chorus On", "Diffusion"}.issubset(param_set):
        return "reverb"

    # Ableton Delay signature parameters
    if {"L Time", "R Time", "Ping Pong", "Feedback"}.issubset(param_set):
        return "delay"

    # Ableton Compressor signature parameters
    if {"Threshold", "Ratio", "Attack", "Release", "Knee"}.issubset(param_set):
        return "compressor"

    # Ableton EQ Eight signature parameters
    if {"1 Frequency A", "2 Frequency A", "3 Frequency A"}.issubset(param_set):
        return "eq8"

    # Ableton Auto Filter
    if {"Filter Type", "Frequency", "Resonance", "LFO Amount"}.issubset(param_set):
        return "autofilter"

    # Ableton Saturator
    if {"Drive", "Dry/Wet", "Color", "Type"}.issubset(param_set):
        return "saturator"

    return "unknown"


def migrate_local_file(old_path: Path, store: MappingStore, dry_run: bool = True) -> Optional[str]:
    """Migrate a single local mapping file.

    Args:
        old_path: Path to old signature JSON file
        store: MappingStore instance
        dry_run: If True, only print what would happen

    Returns:
        New signature if migrated, None otherwise
    """
    try:
        with open(old_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        device_name = data.get("device_name", "Unknown")
        params = data.get("params", [])
        groups = data.get("groups", [])

        if not params:
            print(f"  ⚠️  {old_path.name}: No params, skipping")
            return None

        # Compute new signature
        new_sig = compute_new_signature(params)
        old_sig = old_path.stem

        # Detect device type
        device_type = detect_device_type(params)

        print(f"\n  📄 {device_name}")
        print(f"     Old signature: {old_sig}")
        print(f"     New signature: {new_sig}")
        print(f"     Device type:   {device_type}")
        print(f"     Params:        {len(params)}")

        if dry_run:
            print(f"     [DRY RUN] Would save to structures/{new_sig}.json")
        else:
            # Save with new signature to structures/
            device_meta = {
                "name": device_name,
                "device_type": device_type,
                "groups": groups,
            }
            success = store.save_device_map_local(new_sig, device_meta, params)
            if success:
                print(f"     ✅ Saved to structures/{new_sig}.json")
            else:
                print(f"     ❌ Failed to save")
                return None

        return new_sig

    except Exception as e:
        print(f"  ❌ Error migrating {old_path.name}: {e}")
        return None


def migrate_all_local(store: MappingStore, dry_run: bool = True) -> Dict[str, Any]:
    """Migrate all local mapping files.

    Args:
        store: MappingStore instance
        dry_run: If True, only print what would happen

    Returns:
        Migration summary
    """
    local_dir = store._local_dir
    if not local_dir or not local_dir.exists():
        return {"error": "No local directory found"}

    # Find all JSON files in root (exclude structures/ subdirectory)
    old_files = [f for f in local_dir.glob("*.json")]

    if not old_files:
        return {"error": "No files to migrate"}

    print(f"Found {len(old_files)} local mapping files to migrate\n")

    migrated = []
    for old_path in old_files:
        new_sig = migrate_local_file(old_path, store, dry_run)
        if new_sig:
            migrated.append({
                "old_file": old_path.name,
                "new_signature": new_sig,
            })

    summary = {
        "total": len(old_files),
        "migrated": len(migrated),
        "dry_run": dry_run,
        "files": migrated,
    }

    print(f"\n{'='*60}")
    print(f"Migration Summary:")
    print(f"  Total files: {summary['total']}")
    print(f"  Migrated:    {summary['migrated']}")
    print(f"  Dry run:     {summary['dry_run']}")
    print(f"{'='*60}\n")

    return summary


def migrate_firestore(store: MappingStore, dry_run: bool = True) -> Dict[str, Any]:
    """Migrate Firestore device mappings.

    Args:
        store: MappingStore instance
        dry_run: If True, only print what would happen

    Returns:
        Migration summary
    """
    if not store.enabled or store.backend != "firestore":
        return {"error": "Firestore not enabled"}

    # For now, just note this needs implementation
    # Firestore migration is more complex - need to query all documents
    print("⚠️  Firestore migration not yet implemented")
    print("   Use /mappings/push_local after local migration to sync to Firestore")

    return {"status": "not_implemented"}


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Migrate device signatures to new format")
    parser.add_argument("--execute", action="store_true", help="Actually perform migration (default is dry-run)")
    parser.add_argument("--firestore", action="store_true", help="Also migrate Firestore (requires --execute)")
    parser.add_argument("--yes", "-y", action="store_true", help="Skip confirmation prompt")
    args = parser.parse_args()

    dry_run = not args.execute

    if dry_run:
        print("🔍 DRY RUN MODE - No changes will be made")
        print("   Run with --execute to actually migrate\n")
    else:
        print("⚡ EXECUTE MODE - Changes will be written")
        if not args.yes:
            try:
                response = input("   Continue? (yes/no): ")
                if response.lower() != "yes":
                    print("   Aborted")
                    sys.exit(0)
            except EOFError:
                print("\n   Non-interactive mode detected. Use --yes flag to confirm.")
                sys.exit(1)
        print()

    store = MappingStore()
    print(f"Storage backend: {store.backend}")
    print(f"Local directory: {store._local_dir}\n")

    # Migrate local files
    local_summary = migrate_all_local(store, dry_run)

    # Optionally migrate Firestore
    if args.firestore and not dry_run:
        print("\n" + "="*60)
        firestore_summary = migrate_firestore(store, dry_run)

    if not dry_run:
        print("\n✅ Migration complete!")
        print("   Old files are still in place (not deleted)")
        print("   New files saved to structures/")
        print("\n   Next steps:")
        print("   1. Test that devices show as learned in UI")
        print("   2. If working, delete old files: rm ~/.fadebender/param_maps/*.json")
        print("   3. Sync to Firestore: POST /mappings/push_local")
