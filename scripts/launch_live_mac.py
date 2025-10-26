#!/usr/bin/env python3
"""
Launch Ableton Live on macOS with environment variables for Fadebender.

Usage:
  python3 scripts/launch_live_mac.py [--app-name "Ableton Live 12 Suite.app"]

Finds an Ableton Live app under /Applications if not specified, sets
FADEBENDER_UDP_ENABLE=1 and ABLETON_UDP_* env, and execs the Live binary.

Selection order when --app-name is not provided:
  1) LIVE_APP_NAME or ABLETON_APP_NAME env (exact bundle name)
  2) Prefer editions in order: Suite > Standard > Intro > (deprioritize Trial)
  3) First glob match
"""
from __future__ import annotations

import argparse
import glob
import os
import subprocess
from pathlib import Path
from typing import Iterable


def _score_name(name: str) -> int:
    n = name.lower()
    # Higher is better
    if "suite" in n:
        return 400
    if "standard" in n:
        return 300
    if "intro" in n:
        return 200
    # Trial is deprioritized
    if "trial" in n:
        return 0
    # Neutral default
    return 100


def _prefer(matches: Iterable[str]) -> Path | None:
    items = list(matches)
    if not items:
        return None
    items.sort(key=lambda s: (_score_name(s), s), reverse=True)
    return Path(items[0])


def find_live_app(app_name: str | None) -> Path | None:
    # 1) explicit CLI arg
    if app_name:
        p = Path("/Applications") / app_name
        return p if p.exists() else None
    # 2) environment override for exact bundle name
    env_choice = os.getenv("LIVE_APP_NAME") or os.getenv("ABLETON_APP_NAME")
    if env_choice:
        p = Path("/Applications") / env_choice
        if p.exists():
            return p
    # 3) prefer editions (Suite > Standard > Intro > Trial)
    matches = glob.glob("/Applications/Ableton Live *.app") or glob.glob("/Applications/Ableton Live*.app")
    return _prefer(matches)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--app-name", default=None, help="Exact app bundle name, e.g., 'Ableton Live 12 Suite.app'")
    ap.add_argument("--host", default=os.getenv("ABLETON_UDP_HOST", "127.0.0.1"))
    ap.add_argument("--port", default=os.getenv("ABLETON_UDP_PORT", "19845"))
    args = ap.parse_args()

    app = find_live_app(args.app_name)
    if not app:
        print("Could not find Ableton Live in /Applications")
        return 1

    live_bin = app / "Contents" / "MacOS" / "Live"
    if not live_bin.exists():
        print(f"Live binary not found: {live_bin}")
        return 1

    env = os.environ.copy()
    env["FADEBENDER_UDP_ENABLE"] = "1"
    env["ABLETON_UDP_HOST"] = str(args.host)
    env["ABLETON_UDP_PORT"] = str(args.port)
    # Event notifications (RS -> Server over UDP JSON)
    # Server should bind ABLETON_EVENT_PORT (default 19846); Live (RS) sends to ABLETON_UDP_CLIENT_HOST/PORT.
    env.setdefault("ABLETON_UDP_CLIENT_HOST", env.get("ABLETON_UDP_HOST", "127.0.0.1"))
    env.setdefault("ABLETON_UDP_CLIENT_PORT", os.getenv("ABLETON_EVENT_PORT", "19846"))

    # Gate LOM listeners. Must be set in .env - no fallback!
    if "FADEBENDER_LISTENERS" not in env:
        print("WARNING: FADEBENDER_LISTENERS not set! Please set it in .env")
        print("Example: FADEBENDER_LISTENERS=tracks,returns")
        print("Continuing without listeners enabled...")
        env["FADEBENDER_LISTENERS"] = ""
    else:
        listeners = env["FADEBENDER_LISTENERS"]

    print(
        "Launching: {}\n  FADEBENDER_UDP_ENABLE=1 ABLETON_UDP_HOST={} ABLETON_UDP_PORT={} ABLETON_UDP_CLIENT_HOST={} ABLETON_UDP_CLIENT_PORT={} FADEBENDER_LISTENERS={}".format(
            live_bin, env['ABLETON_UDP_HOST'], env['ABLETON_UDP_PORT'], env.get('ABLETON_UDP_CLIENT_HOST'), env.get('ABLETON_UDP_CLIENT_PORT'), env.get('FADEBENDER_LISTENERS')
        )
    )
    # Launch detached
    subprocess.Popen([str(live_bin)], env=env)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
