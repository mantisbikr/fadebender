#!/bin/bash
# Uninstall Fadebender user-level agent and Remote Script (User Library)
set -euo pipefail

PLIST="$HOME/Library/LaunchAgents/com.fadebender.agent.plist"
USER_RS="$HOME/Music/Ableton/User Library/Remote Scripts/Fadebender"

launchctl bootout gui/$(id -u) "$PLIST" 2>/dev/null || true
rm -f "$PLIST" "$HOME/.fadebender/run_server.sh"
rm -rf "$USER_RS"

echo "Removed Fadebender agent and User Library Remote Script (if present)."
echo "If you installed into the app bundle, remove it under Ableton Live.app/Contents/App-Resources/MIDI Remote Scripts/Fadebender"

