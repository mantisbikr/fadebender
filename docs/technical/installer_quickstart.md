# Installer Quick Start (macOS)

Two easy ways to install Fadebender locally without touching your current code.

Option A — One-liner script (fastest)
- Installs the Ableton Remote Script to your User Library
- Sets up a LaunchAgent to auto‑start the server on login

Commands
- `bash scripts/install_fadebender.sh`
- Optional: `bash scripts/install_fadebender.sh --repo-dir /path/to/fadebender`

Check status
- Logs: `tail -f /tmp/fadebender.log /tmp/fadebender-error.log`
- Agent: `launchctl print gui/$(id -u)/com.fadebender.agent`

Uninstall
- `bash scripts/uninstall_fadebender.sh`

Option B — Build a .pkg installer (shareable)
1) Build the package
   - `bash installer/build_pkg.sh`
   - Output: `build/fadebender.pkg`
2) Run `build/fadebender.pkg`
   - Installs the Remote Script and LaunchAgent for the current user

Notes
- The pkg is unsigned; for distribution, sign and notarize per docs/technical/macos_installer_guide.md
- The server launch script assumes the repo is at `~/ai-projects/fadebender`. You can edit `~/.fadebender/run_server.sh` to point elsewhere.

