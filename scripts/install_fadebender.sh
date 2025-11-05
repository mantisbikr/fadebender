#!/bin/bash
# Fadebender installer (user-level) for macOS
# - Installs Ableton Remote Script to User Library (preferred) or app bundle (fallback)
# - Creates LaunchAgent to auto-start local server on login
# - Starts the agent immediately

set -euo pipefail

INFO() { echo "[fadebender] $*"; }
ERR()  { echo "[fadebender][error] $*" >&2; }

# Defaults (override with --repo-dir)
REPO_DIR_DEFAULT="$HOME/ai-projects/fadebender"
REPO_DIR="$REPO_DIR_DEFAULT"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --repo-dir)
      REPO_DIR="${2:-$REPO_DIR_DEFAULT}"; shift 2;;
    --help|-h)
      cat <<USAGE
Usage: $0 [--repo-dir /path/to/fadebender]

Installs the Fadebender Ableton Remote Script and sets up a LaunchAgent to
run the local server at login.
USAGE
      exit 0;;
    *)
      ERR "Unknown arg: $1"; exit 1;;
  esac
done

SRC_REMOTE_SCRIPT="$REPO_DIR/ableton_remote/Fadebender"
if [[ ! -d "$SRC_REMOTE_SCRIPT" ]]; then
  ERR "Remote Script not found at $SRC_REMOTE_SCRIPT"
  exit 1
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

# 2) Locate User Library (default or from prefs)
USER_LIB="$HOME/Music/Ableton/User Library"
PREF=$(ls "$HOME/Library/Preferences/Ableton"/Live*/Preferences.cfg 2>/dev/null | head -n1 || true)
if [[ -f "$PREF" ]]; then
  # Extract possible custom user library path
  CAND=$(grep -E "User Library|UserLibrary" "$PREF" | sed -E 's/.*Value=\"(.*)\".*/\1/' | head -n1 || true)
  if [[ -n "${CAND:-}" && -d "$CAND" ]]; then USER_LIB="$CAND"; fi
fi

# 3) Install Remote Script
USER_RS="$USER_LIB/Remote Scripts/Fadebender"
if [[ -d "$USER_LIB" ]]; then
  mkdir -p "$USER_RS"
  rsync -a --delete "$SRC_REMOTE_SCRIPT/" "$USER_RS/"
  INFO "Installed Remote Script to $USER_RS"
else
  if [[ -n "${LIVE_APP:-}" && -d "$LIVE_APP" ]]; then
    SYS_RS="$LIVE_APP/Contents/App-Resources/MIDI Remote Scripts/Fadebender"
    INFO "User Library not found; installing into app bundle (admin required)"
    sudo mkdir -p "$SYS_RS"
    sudo rsync -a --delete "$SRC_REMOTE_SCRIPT/" "$SYS_RS/"
    INFO "Installed Remote Script to $SYS_RS"
  else
    ERR "Could not find User Library or Ableton Live app. Please open Live once, then re-run."
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

