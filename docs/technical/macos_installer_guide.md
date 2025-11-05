# Fadebender macOS Installer Guide

This guide describes three practical ways to ship a clickable installer on macOS to:
- Install the Ableton Remote Script to the user’s folder
- Install and auto‑start the local Fadebender server (LaunchAgent)
- Optionally copy/update the server files and show simple status logs

Pick one approach based on your audience. You can start simple and upgrade later.

> Scope note: This installer targets the Python Ableton Remote Script in `ableton_remote/Fadebender` and the local Python server. The native Swift bridge under `native-bridge-mac/` is not used in the current plan and is not installed.

---

## Option 1: Platypus App (Easiest Clickable App)

Use [Platypus](https://sveinbjorn.org/platypus) to wrap a shell/Python script into a .app. No Xcode required.

What you get
- A single .app users can double‑click
- Runs your installer script with a progress/log window
- Can be code‑signed later to reduce Gatekeeper prompts

Steps
1) Install Platypus
   - Download from the site or via Homebrew: `brew install --cask platypus`

2) Prepare your installer script
   - Use `scripts/install_fadebender_platypus.sh` (Platypus-aware)

3) Create the app in Platypus
   - Script: select `scripts/install_fadebender_platypus.sh`
   - Interface: Progress Bar (or Text Window)
   - Run As: `Normal` (not root)
   - Bundled Files: add `remote_script.zip` (create from `ableton_remote/Fadebender`) and optional icon
   - App Name: `Fadebender Installer`

4) Build → Test
   - Double‑click the .app, watch logs, verify: Remote Script installed, server running on login, logs writing to `/tmp`

5) (Optional) Sign & Notarize later (see section below)

---

## Option 2: .pkg Installer (Most “Official”)

Create a standard macOS Installer package. Best for broad distribution and managed installs.

Two ways:
- GUI: [Packages.app](http://s.sudre.free.fr/Software/Packages/about.html)
- CLI: `pkgbuild` + `productbuild`

Recommended layout
- Use a postinstall script to copy files into the user’s home and to create/load the LaunchAgent (since user‑level install is needed).

Folder structure (example)
```
installer/
  payload/                      # staged files that land under /usr/local/share/fadebender
    server/                     # optional copy of server files or a bootstrap script
    resources/
      remote_script.zip         # your Ableton Remote Script bundle
      run_server.sh             # the LaunchAgent target
  scripts/
    postinstall                 # postinstall shell script (executable)
```

postinstall script (example)
```
#!/bin/bash
set -euo pipefail

USER_HOME=$(eval echo ~"${SUDO_USER:-$USER}")
APP_DIR="$USER_HOME/.fadebender"
LAUNCHD_DIR="$USER_HOME/Library/LaunchAgents"
REMOTE_DST="$USER_HOME/Music/Ableton/User Library/MIDI Remote Scripts/Fadebender"

mkdir -p "$APP_DIR" "$LAUNCHD_DIR" "$REMOTE_DST"

# Copy resources installed to /usr/local/share/fadebender by pkg payload
SRC_ROOT="/usr/local/share/fadebender"
cp -f "$SRC_ROOT/resources/run_server.sh" "$APP_DIR/"
chmod +x "$APP_DIR/run_server.sh"

unzip -o "$SRC_ROOT/resources/remote_script.zip" -d "$REMOTE_DST" >/dev/null

# Write LaunchAgent plist
PLIST="$LAUNCHD_DIR/com.fadebender.agent.plist"
cat > "$PLIST" <<'PL'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>com.fadebender.agent</string>
  <key>ProgramArguments</key><array>
    <string>/bin/bash</string>
    <string>%USER_HOME%/.fadebender/run_server.sh</string>
  </array>
  <key>RunAtLoad</key><true/>
  <key>KeepAlive</key><true/>
  <key>StandardOutPath</key><string>/tmp/fadebender.log</string>
  <key>StandardErrorPath</key><string>/tmp/fadebender-error.log</string>
</dict></plist>
PL
sed -i '' "s|%USER_HOME%|$USER_HOME|g" "$PLIST"
chmod 644 "$PLIST"

# Load/enable LaunchAgent for the current user session
launchctl bootstrap gui/$(id -u "$USER") "$PLIST" || true
launchctl enable gui/$(id -u "$USER")/com.fadebender.agent || true
launchctl kickstart -k gui/$(id -u "$USER")/com.fadebender.agent || true

echo "Fadebender installed for $USER_HOME"
exit 0
```

Build with CLI
```
#!/bin/bash
set -euo pipefail
IDENT=com.fadebender.agent
BUILD_DIR=build
PAYLOAD=installer/payload
SCRIPTS=installer/scripts

mkdir -p "$BUILD_DIR"

# Stage payload to /usr/local/share/fadebender
pkgbuild \
  --root "$PAYLOAD" \
  --identifier "$IDENT" \
  --scripts "$SCRIPTS" \
  --install-location /usr/local/share/fadebender \
  "$BUILD_DIR/fadebender.pkg"

# Optional: sign & wrap with productbuild (see Signing section)
```

Using Packages.app
- Create a new project; payload root = `/usr/local/share/fadebender`
- Add `postinstall` script (execute as root)
- Build the .pkg

Note: For multi‑user machines, you may need a helper (first‑launch) to create user‑home files on first login; start simple with single‑user.

---

## Option 3: Automator App (Quickest Wrapper)

Create a small .app that runs a shell script.

Steps
1) Open Automator → New Document → Application
2) Add action: “Run Shell Script”
3) Paste your installer script or `bash /path/to/install_fadebender.sh`
4) Save as `Fadebender Installer.app`

Pros/Cons
- Easiest to make; less control over resources and UI
- Good for internal testing; not ideal for public distribution

---

## Core Installer Script (Reference)

Use this as the basis for Platypus or Automator. Adjust paths as needed.
```
#!/bin/bash
set -euo pipefail

USER_HOME=$(eval echo ~"${SUDO_USER:-$USER}")
APP_DIR="$USER_HOME/.fadebender"
LAUNCHD_DIR="$USER_HOME/Library/LaunchAgents"
REMOTE_DST="$USER_HOME/Music/Ableton/User Library/MIDI Remote Scripts/Fadebender"
REPO_DIR="$USER_HOME/ai-projects/fadebender"  # adjust if different

mkdir -p "$APP_DIR" "$LAUNCHD_DIR" "$REMOTE_DST"

# 1) Install Ableton Remote Script (download or copy)
# curl -L "https://example.com/remote_script.zip" -o /tmp/fb-remote.zip
# unzip -o /tmp/fb-remote.zip -d "$REMOTE_DST"

# 2) Write run_server.sh
cat > "$APP_DIR/run_server.sh" <<'SH'
#!/bin/bash
exec >> /tmp/fadebender.log 2>> /tmp/fadebender-error.log
export ENV=production
cd "$REPO_DIR"
# source .venv/bin/activate  # if you use a venv
/usr/bin/python3 -m uvicorn server.app:app --host 127.0.0.1 --port 8722 --workers 1
SH
chmod +x "$APP_DIR/run_server.sh"
sed -i '' "s|\$REPO_DIR|$REPO_DIR|g" "$APP_DIR/run_server.sh"

# 3) LaunchAgent plist
PLIST="$LAUNCHD_DIR/com.fadebender.agent.plist"
cat > "$PLIST" <<PL
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>com.fadebender.agent</string>
  <key>ProgramArguments</key><array>
    <string>/bin/bash</string>
    <string>$APP_DIR/run_server.sh</string>
  </array>
  <key>RunAtLoad</key><true/>
  <key>KeepAlive</key><true/>
  <key>StandardOutPath</key><string>/tmp/fadebender.log</string>
  <key>StandardErrorPath</key><string>/tmp/fadebender-error.log</string>
</dict></plist>
PL
chmod 644 "$PLIST"

# 4) Load agent now
launchctl bootstrap gui/$(id -u "$USER") "$PLIST" || true
launchctl enable gui/$(id -u "$USER")/com.fadebender.agent || true
launchctl kickstart -k gui/$(id -u "$USER")/com.fadebender.agent || true

echo "✅ Fadebender installed. Server will auto‑start at login."
```

---

## Signing & Notarization (When Ready)

You’ll need an Apple Developer ID certificate.

Sign a .app (Platypus/Automator)
```
codesign --deep --force --options runtime \
  --sign "Developer ID Application: Your Name (TEAMID)" \
  Fadebender\ Installer.app
```

Sign a .pkg
```
productbuild \
  --sign "Developer ID Installer: Your Name (TEAMID)" \
  --package build/fadebender.pkg \
  build/Fadebender-Installer-signed.pkg
```

Notarize (either .app or .pkg)
```
xcrun notarytool submit build/Fadebender-Installer-signed.pkg \
  --keychain-profile "AC_PASSWORD" --wait
xcrun stapler staple build/Fadebender-Installer-signed.pkg
```

---

## Uninstall

User‑level cleanup script
```
#!/bin/bash
set -e
PLIST=~/Library/LaunchAgents/com.fadebender.agent.plist
launchctl bootout gui/$(id -u) "$PLIST" || true
rm -f "$PLIST" ~/.fadebender/run_server.sh
rm -rf "~/Music/Ableton/User Library/MIDI Remote Scripts/Fadebender"
echo "Removed Fadebender agent and Remote Script."
```

---

## Troubleshooting
- Check logs: `tail -f /tmp/fadebender.log /tmp/fadebender-error.log`
- Verify agent status: `launchctl print gui/$(id -u)/com.fadebender.agent`
- Absolute paths only in scripts/plists (LaunchAgents inherit minimal PATH)
- If using a Python virtualenv, activate it in `run_server.sh`

---

## Quick Decision Guide
- Internal testing: Platypus app or Automator app wrapping the script
- Wider distribution: signed & notarized .pkg with postinstall script
