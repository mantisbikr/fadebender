#!/usr/bin/env python3
"""
Install the Fadebender Remote Script into Ableton Live's MIDI Remote Scripts folder (macOS).

Usage:
  python3 scripts/install_remote_script.py [--dry-run]

This copies ableton_remote/Fadebender ->
  /Applications/Ableton Live */Contents/App-Resources/MIDI\ Remote\ Scripts/Fadebender

Note: Requires write permission to the Ableton app bundle. You may be prompted
for admin rights if copying into /Applications.
"""
from __future__ import annotations

import argparse
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "ableton_remote" / "Fadebender"


def find_live_paths() -> list[Path]:
    """Find all Ableton Live installations in /Applications."""
    paths: list[Path] = []
    apps_dir = Path("/Applications")

    if not apps_dir.exists():
        return paths

    # Search for Live installations with specific version and edition patterns
    for version in ["12", "11", "10", "9"]:
        for edition in ["Suite", "Standard", "Intro", "Lite"]:
            app = apps_dir / f"Ableton Live {version} {edition}.app"
            if app.exists() and app.is_dir():
                paths.append(app)

    # Also check for generic "Ableton Live.app" or "Ableton Live X.app" patterns
    for item in apps_dir.glob("Ableton Live*.app"):
        if item.is_dir() and item not in paths:
            paths.append(item)

    return sorted(paths, reverse=True)  # Sort newest first


def install(dst_root: Path, dry_run: bool = False) -> None:
    target = dst_root / "Contents" / "App-Resources" / "MIDI Remote Scripts" / "Fadebender"
    print(f"Installing to: {target}")
    if dry_run:
        return
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(SRC, target)
    print("✔ Installed Fadebender Remote Script")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if not SRC.exists():
        print(f"Source not found: {SRC}")
        return 1

    lives = find_live_paths()
    if not lives:
        print("No Ableton Live app found under /Applications")
        return 1
    for app in lives:
        print(f"Found Live: {app}")
        install(app, dry_run=args.dry_run)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

