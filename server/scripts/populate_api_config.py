#!/usr/bin/env python3
"""
Populate Live API configuration in Firestore.

This script stores the Ableton Live API indexing configuration in Firestore,
allowing us to adapt if Ableton changes their indexing scheme without modifying code.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from server.core.deps import get_store


def create_api_config() -> dict:
    """Create API configuration including indexing rules.

    This centralizes API behavior configuration so we can adapt if Ableton
    changes their indexing scheme without modifying code.

    Note: Fadebender uses 0-based indexing internally for consistency.
    This config defines the translation to Live's actual API.
    """
    return {
        "version": "1.0",
        "description": "Ableton Live API indexing configuration for fadebender",
        "indexing": {
            "tracks": {
                "internal_base": 0,
                "live_base": 1,
                "description": "Tracks: internal 0-based → Live 1-based (Track 1 = internal index 0, Live index 1)",
                "example": "Track 1 (first track) = internal_index: 0 → live_index: 1"
            },
            "returns": {
                "internal_base": 0,
                "live_base": 0,
                "description": "Returns: both 0-based (Return A = internal index 0, Live index 0)",
                "example": "Return A (first return) = internal_index: 0 → live_index: 0"
            },
            "sends": {
                "internal_base": 0,
                "live_base": 0,
                "description": "Sends: both 0-based (Send A = internal index 0, Live index 0)",
                "example": "Send A (first send) = internal_index: 0 → live_index: 0"
            },
            "devices": {
                "internal_base": 0,
                "live_base": 0,
                "description": "Devices: both 0-based (Device 1 = internal index 0, Live index 0)",
                "example": "Device 1 (first device) = internal_index: 0 → live_index: 0"
            }
        },
        "notes": [
            "Ableton Live uses INCONSISTENT indexing (as of Live 11.x):",
            "  - Tracks are 1-based (historical quirk)",
            "  - Returns, Sends, and Devices are 0-based (standard programming)",
            "",
            "Fadebender strategy:",
            "  - Use 0-based indexing EVERYWHERE internally for consistency",
            "  - Translate to Live's scheme only when making API calls",
            "  - If Ableton unifies indexing in future, update this config only"
        ],
        "last_updated": "2025-10-14",
        "verified_with_live_version": "11.x",
        "tested_by": "Manual testing with intents API"
    }


def main():
    """Populate API configuration in Firestore."""
    print("=" * 70)
    print("LIVE API CONFIGURATION SETUP")
    print("=" * 70)
    print()

    store = get_store()

    if not store.enabled:
        print("✗ Firestore is not enabled. Cannot save API configuration.")
        print("Please configure Firestore connection and try again.")
        return 1

    print(f"✓ Connected to Firestore ({store.backend})")
    print()

    # Create API configuration
    print("Creating Live API configuration...")
    api_config = create_api_config()

    print()
    print("Indexing Configuration:")
    print("-" * 70)
    for entity, config in api_config["indexing"].items():
        internal = config["internal_base"]
        live = config["live_base"]
        offset = "NO TRANSLATION" if internal == live else f"OFFSET +{live - internal}"
        print(f"  {entity.upper():12} internal:{internal}-based → Live:{live}-based  [{offset}]")
        print(f"               {config['example']}")
    print("-" * 70)

    # Save to Firestore
    try:
        if not store._client:
            print("✗ No Firestore client available")
            return 1

        doc = store._client.collection("api_config").document("live_api")
        doc.set(api_config, merge=True)
        print()
        print("✓ API configuration saved to Firestore")
        print()
        print("  Collection: api_config")
        print("  Document ID: live_api")
    except Exception as e:
        print(f"✗ Failed to save API configuration: {e}")
        import traceback
        traceback.print_exc()
        return 1

    print()
    print("=" * 70)
    print("✓ Live API configuration successfully populated")
    print("=" * 70)
    print()
    print("Important notes:")
    for note in api_config["notes"]:
        print(f"  {note}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
