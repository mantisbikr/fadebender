#!/usr/bin/env python3
"""Migrate existing typo corrections from app_config.json to Firestore.

This is a one-time migration to seed Firestore with existing learned typos.
"""

import os
import sys

# Load .env file FIRST before any imports
from pathlib import Path
env_path = Path(__file__).parent.parent / '.env'
if env_path.exists():
    print(f"Loading environment from {env_path}")
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key.strip()] = value.strip()

# Verify environment variables
print(f"FIRESTORE_PROJECT_ID: {os.getenv('FIRESTORE_PROJECT_ID')}")
print(f"FIRESTORE_DATABASE_ID: {os.getenv('FIRESTORE_DATABASE_ID')}")
print()

# Add paths for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'server'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'nlp-service'))

from server.config.app_config import get_typo_corrections as get_local_typos
from learning.typo_cache_store import save_typo_corrections


def main():
    print("=" * 60)
    print("Migrating Typo Corrections to Firestore")
    print("=" * 60)

    # Load existing typos from local config
    print("\n[1/3] Loading typos from configs/app_config.json...")
    local_typos = get_local_typos()

    if not local_typos:
        print("  ⚠️  No typos found in local config!")
        return

    print(f"  ✓ Found {len(local_typos)} typo corrections")
    print(f"\n  Sample typos:")
    for i, (typo, correction) in enumerate(list(local_typos.items())[:5]):
        print(f"    - {typo} → {correction}")
    if len(local_typos) > 5:
        print(f"    ... and {len(local_typos) - 5} more")

    # Save to Firestore
    print("\n[2/3] Saving to Firestore (nlp_config/typo_corrections)...")
    success = save_typo_corrections(local_typos)

    if success:
        print(f"  ✓ Successfully saved {len(local_typos)} corrections to Firestore!")
    else:
        print("  ✗ Failed to save to Firestore")
        print("  Check that:")
        print("    - FIRESTORE_PROJECT_ID env var is set")
        print("    - FIRESTORE_DATABASE_ID is set to 'dev-display-value'")
        print("    - You have Firestore write permissions")
        sys.exit(1)

    # Verify
    print("\n[3/3] Verifying migration...")
    from learning.typo_cache_store import force_refresh

    loaded_typos = force_refresh()

    if len(loaded_typos) == len(local_typos):
        print(f"  ✓ Verification successful! {len(loaded_typos)} corrections in Firestore")
    else:
        print(f"  ⚠️  Warning: Expected {len(local_typos)}, but found {len(loaded_typos)} in Firestore")

    print("\n" + "=" * 60)
    print("Migration Complete!")
    print("=" * 60)
    print("\nNext steps:")
    print("  1. Check Firestore console:")
    print("     Database: dev-display-value")
    print("     Collection: nlp_config")
    print("     Document: typo_corrections")
    print("  2. Restart your server")
    print("  3. Test with a typo query (e.g., 'set track 1 volme to -20')")
    print()


if __name__ == "__main__":
    main()
