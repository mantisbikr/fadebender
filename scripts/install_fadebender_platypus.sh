#!/bin/bash
# Fadebender installer wrapper for Platypus (.app)
# - Prefers a bundled remote_script.zip inside the app Resources
# - Falls back to repo copy if not bundled
# - Sets up LaunchAgent to auto-start local server on login

set -euo pipefail

INFO() { echo "[fadebender] $*"; }
ERR()  { echo "[fadebender][error] $*" >&2; }

# Resolve Platypus Resources path if available
APP_RES="${RESOURCE_PATH:-}"
if [[ -z "$APP_RES" ]]; then
  # Try relative to script location (useful for testing outside Platypus)
  APP_RES=$(cd "$(dirname "$0")/../Resources" 2>/dev/null && pwd || true)
fi

# Optional override for repo dir (for fallback and server launch)
REPO_DIR_DEFAULT="$HOME/ai-projects/fadebender"
REPO_DIR="$REPO_DIR_DEFAULT"
if [[ $# -ge 2 && "$1" == "--repo-dir" ]]; then
  REPO_DIR="$2"; shift 2
fi

USER_HOME="$HOME"
APP_DIR="$USER_HOME/.fadebender"
LAUNCHD_DIR="$USER_HOME/Library/LaunchAgents"

mkdir -p "$APP_DIR" "$LAUNCHD_DIR"

# 1) Locate Ableton Live app (optional fallback)
LIVE_APP=$(ls -d /Applications/Ableton\ Live*.app "$HOME"/Applications/Ableton\ Live*.app 2>/dev/null | head -n1 || true)
if [[ -z "${LIVE_APP:-}" ]]; then
  LIVE_APP=$(mdfind "kMDItemCFBundleIdentifier == 'com.ableton.live'" | head -n1 || true)
fi

# 2) Locate or create User Library
USER_LIB="$HOME/Music/Ableton/User Library"
if [[ ! -d "$USER_LIB" ]]; then
  # Try to infer from preferences, otherwise create the default path
  PREF=$(ls "$HOME/Library/Preferences/Ableton"/Live*/Preferences.cfg 2>/dev/null | head -n1 || true)
  if [[ -f "$PREF" ]]; then
    CAND=$(grep -E "User Library|UserLibrary" "$PREF" | sed -E 's/.*Value=\"(.*)\".*/\1/' | head -n1 || true)
    if [[ -n "${CAND:-}" ]]; then USER_LIB="$CAND"; fi
  fi
  mkdir -p "$USER_LIB"
fi

# 3) Install Remote Script
USER_RS_BASE="$USER_LIB/Remote Scripts"
USER_RS="$USER_RS_BASE/Fadebender"
mkdir -p "$USER_RS_BASE"

if [[ -n "${APP_RES:-}" && -f "$APP_RES/remote_script.zip" ]]; then
  INFO "Installing Remote Script from bundled zip"
  # Unzip so the result is .../Remote Scripts/Fadebender
  unzip -o "$APP_RES/remote_script.zip" -d "$USER_RS_BASE" >/dev/null
  # Ensure folder name is exactly Fadebender (zip should already contain that)
  if [[ ! -d "$USER_RS" ]]; then
    # Attempt to move if extracted under a different name
    EXTRACTED=$(zipinfo -1 "$APP_RES/remote_script.zip" | head -n1 | cut -d/ -f1)
    if [[ -n "$EXTRACTED" && -d "$USER_RS_BASE/$EXTRACTED" ]]; then
      mv "$USER_RS_BASE/$EXTRACTED" "$USER_RS"
    fi
  fi
  INFO "Installed Remote Script to $USER_RS"
else
  SRC_REMOTE_SCRIPT="$REPO_DIR/ableton_remote/Fadebender"
  if [[ -d "$SRC_REMOTE_SCRIPT" ]]; then
    INFO "Bundled zip not found; installing from repo: $SRC_REMOTE_SCRIPT"
    rsync -a --delete "$SRC_REMOTE_SCRIPT/" "$USER_RS/"
    INFO "Installed Remote Script to $USER_RS"
  else
    ERR "No bundled remote_script.zip and repo path missing: $SRC_REMOTE_SCRIPT"
    ERR "Please rebuild the app with bundled files or pass --repo-dir"
    exit 1
  fi
fi

# 4) Create run_server.sh
RUN_SH="$APP_DIR/run_server.sh"
cat > "$RUN_SH" <<SH
#!/bin/bash
exec >> /tmp/fadebender.log 2>> /tmp/fadebender-error.log
export ENV=production
REPO_DIR="$REPO_DIR"
cd "\$REPO_DIR"
# Uncomment if using a venv:
# if [ -f .venv/bin/activate ]; then source .venv/bin/activate; fi
/usr/bin/python3 -m uvicorn server.app:app --host 127.0.0.1 --port 8722 --workers 1
SH
chmod +x "$RUN_SH"

# 5) LaunchAgent plist
PLIST="$LAUNCHD_DIR/com.fadebender.agent.plist"
cat > "$PLIST" <<PL
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>com.fadebender.agent</string>
  <key>ProgramArguments</key><array>
    <string>/bin/bash</string>
    <string>$RUN_SH</string>
  </array>
  <key>RunAtLoad</key><true/>
  <key>KeepAlive</key><true/>
  <key>StandardOutPath</key><string>/tmp/fadebender.log</string>
  <key>StandardErrorPath</key><string>/tmp/fadebender-error.log</string>
</dict></plist>
PL
chmod 644 "$PLIST"

# 6) Load/enable now
launchctl bootstrap gui/$(id -u "$USER") "$PLIST" || true
launchctl enable gui/$(id -u "$USER")/com.fadebender.agent || true
launchctl kickstart -k gui/$(id -u "$USER")/com.fadebender.agent || true

INFO "✅ Fadebender installed. Server will auto-start at login."
INFO "Logs: tail -f /tmp/fadebender.log /tmp/fadebender-error.log"

