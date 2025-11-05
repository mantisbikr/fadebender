# Fadebender Windows Installer Guide

This guide shows how to install Fadebender on Windows as a desktop companion (Ableton + server on PC), with an auto‑start agent and the Remote Script in the Ableton User Library.

---

## Option A — PowerShell Script (recommended for dev/test)

Files
- `scripts/install_fadebender_windows.ps1` — installs Remote Script, creates auto‑start Task, opens firewall (optional), starts server now.
- `scripts/uninstall_fadebender_windows.ps1` — removes Task, Remote Script, and run script.

Usage
- Open PowerShell and run:
  - `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` (first time only)
  - `powershell -ExecutionPolicy Bypass -File scripts\install_fadebender_windows.ps1`
  - Optional repo path: `... -RepoDir C:\Users\<You>\ai-projects\fadebender`
  - Optional port: `... -Port 8722`

What it does
- Installs Remote Script to: `C:\Users\<You>\Documents\Ableton\User Library\Remote Scripts\Fadebender`
  - If a custom User Library is set in Ableton Preferences, it installs there instead.
- Creates `C:\Users\<You>\.fadebender\run_server.ps1`
- Registers Task Scheduler entry “FadebenderAgent” to start on login
- Opens Windows Firewall for TCP port 8722 (prompts for admin)
- Starts the server now

Check
- Health: `http://localhost:8722/health`
- Logs: `%TEMP%\fadebender.log`
- Task: Task Scheduler → Task Scheduler Library → FadebenderAgent

Uninstall
- `powershell -ExecutionPolicy Bypass -File scripts\uninstall_fadebender_windows.ps1`

---

## Option B — Packaged Installer (later)

When ready to distribute broadly, wrap the same steps into a GUI installer:
- Inno Setup or NSIS: copy Remote Script, write `run_server.ps1`, register Task, add firewall rule.
- Code signing: recommended for a smooth install experience.

---

## Notes
- Server binds to `0.0.0.0` so LAN devices (e.g., iPad) can connect to `http://<pc-ip>:8722`.
- If your environment uses a Python venv, add activation to `~\.fadebender\run_server.ps1`.
- If your network blocks LAN, ensure Wi‑Fi is on the same subnet and AP isolation is disabled.

