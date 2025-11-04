#!/usr/bin/env python3
"""View and optionally clean up Firestore typo corrections.

This script shows all typo corrections in Firestore and allows you to remove
incorrect mappings like "reduce: cue" and "reack: track".
"""

import os
import sys

# Load .env file FIRST before any imports
from pathlib import Path
env_path = Path(__file__).parent.parent / '.env'
if env_path.exists():
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key.strip()] = value.strip()

# Add paths for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'nlp-service'))

from learning.typo_cache_store import force_refresh, save_typo_corrections


def main():
    print("=" * 80)
    print("Firestore Typo Corrections - View and Clean")
    print("=" * 80)

    # Load current corrections from Firestore
    print("\n[1/3] Loading typo corrections from Firestore...")
    corrections = force_refresh()

    if not corrections:
        print("  ⚠️  No corrections found in Firestore!")
        print("\n  Database: dev-display-value")
        print("  Collection: nlp_config")
        print("  Document: typo_corrections")
        return

    print(f"  ✓ Found {len(corrections)} corrections\n")

    # Display all corrections
    print(f"[2/3] Current typo corrections:")
    print("-" * 80)

    # Find problematic mappings
    problematic = []

    # "reduce" should NOT be mapped to "cue" (reduce is an action verb, not a typo)
    if "reduce" in corrections:
        problematic.append(("reduce", corrections["reduce"]))

    # "reack" -> "track" seems suspicious (is "reack" really a common typo of "track"?)
    if "reack" in corrections:
        problematic.append(("reack", corrections["reack"]))

    # Display corrections with problematic ones highlighted
    sorted_corrections = sorted(corrections.items())
    for typo, correction in sorted_corrections:
        is_problematic = (typo, correction) in problematic
        marker = " ⚠️  PROBLEMATIC" if is_problematic else ""
        print(f"  {typo:20} → {correction:20}{marker}")

    print("-" * 80)

    if not problematic:
        print("\n✓ No problematic mappings found!")
        return

    # Ask user if they want to remove problematic mappings
    print(f"\n[3/3] Found {len(problematic)} problematic mapping(s):")
    for typo, correction in problematic:
        print(f"  - {typo} → {correction}")

    print("\nReasons:")
    if ("reduce", corrections.get("reduce")) in problematic:
        print("  • 'reduce' is an action verb (decrease), not a typo of 'cue'")
    if ("reack", corrections.get("reack")) in problematic:
        print("  • 'reack' → 'track' seems like an incorrect/spurious mapping")

    response = input("\nRemove these problematic mappings? (y/N): ").strip().lower()

    if response != 'y':
        print("\n  Cancelled. No changes made.")
        return

    # Remove problematic mappings
    cleaned_corrections = {k: v for k, v in corrections.items()
                          if (k, v) not in problematic}

    print(f"\n  Removing {len(problematic)} mapping(s) from Firestore...")

    # Save cleaned corrections (overwrites the document)
    try:
        from google.cloud import firestore

        project_id = os.getenv("FIRESTORE_PROJECT_ID")
        database_id = os.getenv("FIRESTORE_DATABASE_ID", "(default)")

        if project_id and database_id and database_id != "(default)":
            client = firestore.Client(project=project_id, database=database_id)
        elif project_id:
            client = firestore.Client(project=project_id)
        else:
            client = firestore.Client()

        doc_ref = client.collection("nlp_config").document("typo_corrections")
        doc_ref.set({"corrections": cleaned_corrections})

        print(f"  ✓ Successfully removed {len(problematic)} mapping(s)")
        print(f"  ✓ Firestore now has {len(cleaned_corrections)} corrections")

        # Verify
        verified = force_refresh()
        if len(verified) == len(cleaned_corrections):
            print(f"  ✓ Verification successful!")
        else:
            print(f"  ⚠️  Warning: Expected {len(cleaned_corrections)}, found {len(verified)}")

    except Exception as e:
        print(f"  ✗ Error saving to Firestore: {e}")
        return

    print("\n" + "=" * 80)
    print("Cleanup Complete!")
    print("=" * 80)
    print("\nNext steps:")
    print("  1. Restart your server to clear any cached typo corrections")
    print("  2. Test with 'reduce master cue by 3db' to verify it still works")
    print("  3. The command should interpret 'reduce' as action (decrease), not map to 'cue'")
    print()


if __name__ == "__main__":
    main()
