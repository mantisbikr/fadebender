#!/usr/bin/env python3
"""
Populate mixer parameter mappings in Firestore.

This script creates display value presets for mixer parameters like pan and volume,
enabling the intents API to handle human-readable values like "25L", "50R", "Center".
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from server.core.deps import get_store


def create_pan_mapping() -> dict:
    """Create pan parameter mapping with display value presets.

    Pan in Ableton Live:
    - Normalized range: -1.0 (full left) to +1.0 (full right)
    - Display range: -50 (50L) to +50 (50R)
    - Center: 0.0 normalized, 0 display
    """
    return {
        "param_name": "pan",
        "description": "Track/Return/Master pan control",
        "normalized_range": {
            "min": -1.0,
            "max": 1.0,
            "unit": "normalized"
        },
        "display_range": {
            "min": -50,
            "max": 50,
            "unit": "display_value",
            "format": "{value}{side}",  # e.g., "25L", "50R", ""
        },
        "conversion": {
            "type": "linear",
            "formula": "normalized = display / 50.0"
        },
        "display_value_presets": {
            # Extreme positions
            "hard left": -1.0,
            "full left": -1.0,
            "50l": -1.0,
            "50 left": -1.0,

            # Quarter positions
            "25l": -0.5,
            "25 left": -0.5,
            "left": -0.5,

            # Center
            "center": 0.0,
            "centre": 0.0,
            "middle": 0.0,
            "0": 0.0,

            # Quarter positions
            "25r": 0.5,
            "25 right": 0.5,
            "right": 0.5,

            # Extreme positions
            "hard right": 1.0,
            "full right": 1.0,
            "50r": 1.0,
            "50 right": 1.0,

            # Fine-grained presets (every 10 units)
            "40l": -0.8,
            "30l": -0.6,
            "20l": -0.4,
            "10l": -0.2,
            "10r": 0.2,
            "20r": 0.4,
            "30r": 0.6,
            "40r": 0.8,

            # Alternative formats
            "-50": -1.0,
            "-40": -0.8,
            "-30": -0.6,
            "-25": -0.5,
            "-20": -0.4,
            "-10": -0.2,
            "10": 0.2,
            "20": 0.4,
            "25": 0.5,
            "30": 0.6,
            "40": 0.8,
            "50": 1.0,
        },
        "examples": [
            {"input": "pan hard left", "normalized": -1.0, "display": "50L"},
            {"input": "pan center", "normalized": 0.0, "display": "C"},
            {"input": "pan 25R", "normalized": 0.5, "display": "25R"},
            {"input": "pan full right", "normalized": 1.0, "display": "50R"},
        ],
        "metadata": {
            "applies_to": ["track", "return", "master"],
            "created_by": "populate_mixer_mappings.py",
            "version": "1.0"
        }
    }


def create_cue_mapping() -> dict:
    """Create cue volume parameter mapping with display value presets.

    Cue Volume in Ableton Live:
    - Normalized range: 0.0 to 1.0
    - Display range: -∞ dB (off) to +6 dB
    - Unity: 0.85 normalized ≈ 0 dB
    - Same range as master/track volume
    """
    return {
        "param_name": "cue",
        "description": "Master cue volume control",
        "normalized_range": {
            "min": 0.0,
            "max": 1.0,
            "unit": "normalized"
        },
        "display_range": {
            "min": -60,  # Practical minimum (Live shows -inf below this)
            "max": 6,
            "unit": "dB"
        },
        "conversion": {
            "type": "logarithmic",
            "note": "Use db_to_live_float() function for accurate conversion"
        },
        "display_value_presets": {
            "off": 0.0,
            "silent": 0.0,

            "unity": 0.85,
            "0db": 0.85,
            "0 db": 0.85,

            "max": 1.0,
            "full": 1.0,
            "+6db": 1.0,
            "+6 db": 1.0,

            # Common levels
            "-6db": 0.75,
            "-6 db": 0.75,
            "-12db": 0.65,
            "-12 db": 0.65,
            "-18db": 0.55,
            "-18 db": 0.55,
        },
        "examples": [
            {"input": "cue unity", "normalized": 0.85, "display": "0.00 dB"},
            {"input": "cue -6db", "normalized": 0.75, "display": "-6.00 dB"},
            {"input": "cue max", "normalized": 1.0, "display": "+6.00 dB"},
        ],
        "metadata": {
            "applies_to": ["master"],
            "created_by": "populate_mixer_mappings.py",
            "version": "1.0"
        }
    }


def create_volume_mapping() -> dict:
    """Create volume parameter mapping with display value presets.

    Volume in Ableton Live:
    - Normalized range: 0.0 to 1.0
    - Display range: -∞ dB (off) to +6 dB
    - Unity: 0.85 normalized ≈ 0 dB
    """
    return {
        "param_name": "volume",
        "description": "Track/Return/Master volume control",
        "normalized_range": {
            "min": 0.0,
            "max": 1.0,
            "unit": "normalized"
        },
        "display_range": {
            "min": -60,  # Practical minimum (Live shows -inf below this)
            "max": 6,
            "unit": "dB"
        },
        "conversion": {
            "type": "logarithmic",
            "note": "Use db_to_live_float() function for accurate conversion"
        },
        "display_value_presets": {
            "off": 0.0,
            "silent": 0.0,
            "mute": 0.0,

            "unity": 0.85,
            "0db": 0.85,
            "0 db": 0.85,

            "max": 1.0,
            "full": 1.0,
            "+6db": 1.0,
            "+6 db": 1.0,

            # Common levels
            "-6db": 0.75,
            "-6 db": 0.75,
            "-12db": 0.65,
            "-12 db": 0.65,
            "-18db": 0.55,
            "-18 db": 0.55,
        },
        "examples": [
            {"input": "volume unity", "normalized": 0.85, "display": "0.00 dB"},
            {"input": "volume -6db", "normalized": 0.75, "display": "-6.00 dB"},
            {"input": "volume max", "normalized": 1.0, "display": "+6.00 dB"},
        ],
        "metadata": {
            "applies_to": ["track", "return", "master"],
            "created_by": "populate_mixer_mappings.py",
            "version": "1.0"
        }
    }


def create_api_config() -> dict:
    """Create API configuration including indexing rules.

    This centralizes API behavior configuration so we can adapt if Ableton
    changes their indexing scheme without modifying code.
    """
    return {
        "version": "1.0",
        "description": "Ableton Live API configuration for fadebender",
        "indexing": {
            "tracks": {
                "base": 1,
                "description": "Tracks use 1-based indexing (Track 1 = index 1)",
                "min_index": 1
            },
            "returns": {
                "base": 0,
                "description": "Returns use 0-based indexing (Return A = index 0)",
                "min_index": 0
            },
            "sends": {
                "base": 0,
                "description": "Sends use 0-based indexing (Send A = index 0)",
                "min_index": 0
            },
            "devices": {
                "base": 0,
                "description": "Devices use 0-based indexing (Device 1 = index 0)",
                "min_index": 0
            }
        },
        "notes": [
            "Ableton Live uses inconsistent indexing:",
            "- Tracks are 1-based (historical reasons)",
            "- Returns, Sends, and Devices are 0-based (standard programming)",
            "If Ableton unifies this in future, update this config only"
        ],
        "last_updated": "2025-10-14",
        "verified_with_live_version": "11.x"
    }


def main():
    """Populate mixer mappings in Firestore."""
    print("=" * 70)
    print("MIXER MAPPINGS SETUP")
    print("=" * 70)
    print()

    store = get_store()

    if not store.enabled:
        print(" Firestore is not enabled. Cannot save mixer mappings.")
        print("Please configure Firestore connection and try again.")
        return 1

    print(f"✓ Connected to Firestore ({store.backend})")
    print()

    # Create and save pan mapping
    print("Creating pan mapping...")
    pan_mapping = create_pan_mapping()
    print(f"  - Normalized range: [{pan_mapping['normalized_range']['min']}, {pan_mapping['normalized_range']['max']}]")
    print(f"  - Display range: [{pan_mapping['display_range']['min']}, {pan_mapping['display_range']['max']}]")
    print(f"  - Presets: {len(pan_mapping['display_value_presets'])} values")

    if store.save_mixer_param_mapping("pan", pan_mapping):
        print("✓ Pan mapping saved to Firestore")
    else:
        print("✗ Failed to save pan mapping")
        return 1

    print()

    # Create and save volume mapping
    print("Creating volume mapping...")
    volume_mapping = create_volume_mapping()
    print(f"  - Normalized range: [{volume_mapping['normalized_range']['min']}, {volume_mapping['normalized_range']['max']}]")
    print(f"  - Display range: [{volume_mapping['display_range']['min']}, {volume_mapping['display_range']['max']}] dB")
    print(f"  - Presets: {len(volume_mapping['display_value_presets'])} values")

    if store.save_mixer_param_mapping("volume", volume_mapping):
        print("✓ Volume mapping saved to Firestore")
    else:
        print("✗ Failed to save volume mapping")
        return 1

    print()

    # Create and save cue mapping
    print("Creating cue volume mapping...")
    cue_mapping = create_cue_mapping()
    print(f"  - Normalized range: [{cue_mapping['normalized_range']['min']}, {cue_mapping['normalized_range']['max']}]")
    print(f"  - Display range: [{cue_mapping['display_range']['min']}, {cue_mapping['display_range']['max']}] dB")
    print(f"  - Presets: {len(cue_mapping['display_value_presets'])} values")

    if store.save_mixer_param_mapping("cue", cue_mapping):
        print("✓ Cue mapping saved to Firestore")
    else:
        print("✗ Failed to save cue mapping")
        return 1

    print()
    print("=" * 70)
    print("✓ Mixer mappings successfully populated")
    print("=" * 70)
    print()
    print("Examples of supported pan values:")
    for example in pan_mapping["examples"]:
        print(f"  • {example['input']} → {example['normalized']} ({example['display']})")

    return 0


if __name__ == "__main__":
    sys.exit(main())
