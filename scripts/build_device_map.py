#!/usr/bin/env python3
"""
Build device_map.json by scanning Ableton Live's Core Library.

This script should be run:
1. During installer setup (auto-detect Live location)
2. By developers to generate a default map
3. By users to update after Live version changes

Usage:
    # Auto-detect Live location
    python scripts/build_device_map.py

    # Specify Live library path
    python scripts/build_device_map.py --live-library "/Applications/Ableton Live 11 Suite.app/Contents/App-Resources/Core Library"

    # Specify output path
    python scripts/build_device_map.py --output ~/custom_device_map.json
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, Any, Optional

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from server.config.paths import find_live_library, get_device_map_path


def scan_device_folder(devices_path: Path, device_type: str) -> Dict[str, Any]:
    """
    Scan a device folder (Audio Effects, MIDI Effects, Instruments).

    Args:
        devices_path: Path to Devices folder
        device_type: "audio_effects", "midi_effects", or "instruments"

    Returns:
        Dict mapping device names to their paths and presets
    """
    type_folder_map = {
        "audio_effects": "Audio Effects",
        "midi_effects": "MIDI Effects",
        "instruments": "Instruments"
    }

    folder_name = type_folder_map.get(device_type)
    if not folder_name:
        return {}

    type_path = devices_path / folder_name
    if not type_path.exists():
        return {}

    device_map = {}

    # Scan each device folder
    for device_folder in sorted(type_path.iterdir()):
        if not device_folder.is_dir():
            continue

        device_name = device_folder.name

        # Skip metadata folders
        if device_name == "Ableton Folder Info":
            continue

        # Scan for all preset files (.adg and .adv)
        preset_files = list(device_folder.rglob("*.adg")) + list(device_folder.rglob("*.adv"))

        # Skip if no presets found at all
        if not preset_files:
            continue

        # Build base path for device
        device_path = [device_type, device_name]

        # Look for default preset in root (preferred)
        default_preset = None
        for ext in [".adg", ".adv"]:
            candidate = device_folder / f"{device_name}{ext}"
            if candidate.exists():
                default_preset = candidate
                device_path = [device_type, device_name, f"{device_name}{ext}"]
                break

        # If no default preset in root, use first preset found
        if not default_preset and preset_files:
            default_preset = sorted(preset_files)[0]
            # Build path to first preset
            rel_parts = default_preset.relative_to(devices_path / folder_name).parts
            device_path = [device_type] + list(rel_parts)

        # Scan for all preset files and build preset map
        presets = {}
        for item in preset_files:
            # Build path from device type to preset file
            rel_parts = item.relative_to(devices_path / folder_name).parts
            preset_name = item.stem
            preset_path = [device_type] + list(rel_parts)
            presets[preset_name] = preset_path

        device_map[device_name] = {
            "path": device_path,
            "type": device_type,
        }

        if presets:
            device_map[device_name]["presets"] = presets

    return device_map


def build_device_map(live_library: Path) -> Dict[str, Any]:
    """
    Build complete device map from Live library.

    Args:
        live_library: Path to Live's Core Library

    Returns:
        Complete device map dict
    """
    devices_path = live_library / "Devices"
    if not devices_path.exists():
        raise ValueError(f"Devices folder not found at {devices_path}")

    device_map = {}

    # Scan each device type
    for device_type in ["audio_effects", "midi_effects", "instruments"]:
        type_map = scan_device_folder(devices_path, device_type)
        device_map.update(type_map)

    return device_map


def main():
    parser = argparse.ArgumentParser(
        description="Build device_map.json from Ableton Live library"
    )
    parser.add_argument(
        "--live-library",
        type=Path,
        help="Path to Live's Core Library (auto-detected if not specified)"
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Output path for device_map.json (default: config directory)"
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Verbose output"
    )

    args = parser.parse_args()

    # Find Live library
    live_library = args.live_library
    if not live_library:
        if args.verbose:
            print("Auto-detecting Ableton Live library...")
        live_library = find_live_library()
        if not live_library:
            print("ERROR: Could not find Ableton Live library.", file=sys.stderr)
            print("Please specify path with --live-library", file=sys.stderr)
            return 1

    if args.verbose:
        print(f"Using Live library: {live_library}")

    # Build device map
    try:
        device_map = build_device_map(live_library)
    except Exception as e:
        print(f"ERROR building device map: {e}", file=sys.stderr)
        return 1

    if args.verbose:
        print(f"Found {len(device_map)} devices")

    # Determine output path
    output_path = args.output or get_device_map_path()

    # Ensure parent directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write to file
    with open(output_path, "w") as f:
        json.dump(device_map, f, indent=2, sort_keys=True)

    print(f"Device map written to: {output_path}")
    print(f"Total devices: {len(device_map)}")

    # Show sample
    if args.verbose and device_map:
        print("\nSample devices:")
        for i, (name, info) in enumerate(list(device_map.items())[:5]):
            preset_count = len(info.get("presets", {}))
            print(f"  - {name} ({info['type']}, {preset_count} presets)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
