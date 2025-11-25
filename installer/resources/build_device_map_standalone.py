#!/usr/bin/env python3
"""
Standalone device map builder for installer.
No dependencies on server code - can run standalone during installation.
"""
import json
import sys
from pathlib import Path
from typing import Dict, Any, Optional


def find_live_library() -> Optional[Path]:
    """Find Ableton Live library by checking common locations."""
    apps = Path("/Applications")

    # Check for Live 12, 11, 10 in Suite, Standard, Intro editions
    for version in ["12", "11", "10"]:
        for edition in ["Suite", "Standard", "Intro"]:
            core_lib = apps / f"Ableton Live {version} {edition}.app" / "Contents" / "App-Resources" / "Core Library"
            if core_lib.exists() and (core_lib / "Devices").exists():
                return core_lib

    return None


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

        # Skip if no presets found
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
            rel_parts = default_preset.relative_to(devices_path / folder_name).parts
            device_path = [device_type] + list(rel_parts)

        # Scan for all preset files and build preset map
        presets = {}
        for item in preset_files:
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
    """Build complete device map from Live library."""
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
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: build_device_map_standalone.py <output_path>", file=sys.stderr)
        print("  Example: build_device_map_standalone.py ~/.fadebender/device_map.json", file=sys.stderr)
        return 1

    output_path = Path(sys.argv[1]).expanduser()

    # Find Live library
    live_library = find_live_library()
    if not live_library:
        print("ERROR: Could not find Ableton Live library in /Applications", file=sys.stderr)
        print("Device map generation skipped.", file=sys.stderr)
        return 1

    print(f"Found Live library: {live_library}")

    # Build device map
    try:
        device_map = build_device_map(live_library)
    except Exception as e:
        print(f"ERROR building device map: {e}", file=sys.stderr)
        return 1

    print(f"Found {len(device_map)} devices")

    # Ensure parent directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write to file
    with open(output_path, "w") as f:
        json.dump(device_map, f, indent=2, sort_keys=True)

    print(f"Device map written to: {output_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
