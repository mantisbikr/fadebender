# Fadebender Installer Assets

This folder contains scripts to build and run a simple macOS installer.

Contents
- `build_pkg.sh` — builds an unsigned `.pkg` using `pkgbuild`
- `scripts/postinstall` — postinstall script run by the pkg to install files to the user’s home

Quick start (pkg)
1) Build the package:
   - `bash installer/build_pkg.sh`
   - Output: `build/fadebender.pkg`
2) Distribute and run `fadebender.pkg` on a Mac user account
   - It will:
     - Install the Ableton Remote Script to `~/Music/Ableton/User Library/Remote Scripts/Fadebender`
     - Create `~/.fadebender/run_server.sh` and a LaunchAgent
     - Start the agent immediately

Notes
- The pkg is unsigned. For broader distribution, sign and notarize per the main guide.
- `run_server.sh` assumes the Fadebender repo lives at `~/ai-projects/fadebender`. Adjust after install if needed.

