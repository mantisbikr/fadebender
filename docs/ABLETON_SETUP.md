# Ableton Live Setup (Fadebender Remote Script)

Use this when you’re ready to control a real Live set instead of the UDP stub.

Prerequisites
- Ableton Live 11/12 (Suite recommended)
- macOS (paths below); adjust for your OS/Live version

What we install
- A simple Live Remote Script that exposes a UDP JSON bridge
- It handles: ping, get_overview, get_track_status, set_mixer, set_send, set_device_param

Folder layout in this repo
- `ableton_remote/` — Python files for Live’s Remote Script (LOM + UDP)
- `server/` — FastAPI that talks to the Remote Script via UDP

Install the Remote Script
1) Quit Ableton Live
2) Create a folder for the script inside the Live app bundle (macOS):
   - `/Applications/Ableton Live <VERSION>.app/Contents/App-Resources/MIDI Remote Scripts/Fadebender/`
3) Copy the contents of `ableton_remote/` from this repo into that folder
   - Required files (once implemented): `__init__.py`, `Fadebender.py`, `bridge.py`, `lom_ops.py`
4) Start Ableton Live
5) Preferences → Link/Tempo/MIDI
   - You do NOT need to select a Control Surface for this script; it runs as a non‑UI bridge

Configure ports
- Default UDP host/port: `127.0.0.1:19845`
- Ensure your `.env` uses the same values for `ABLETON_UDP_HOST` and `ABLETON_UDP_PORT`

Sanity checks
- Start your local server stack: `make restart-all`
- From terminal: `curl http://127.0.0.1:8722/ping` → `{ "ok": true, ... }`
- In the web chat (Execute ON): `set track 1 volume to -6 dB` → Track 1 fader moves

Troubleshooting
- Ping returns `ok:false` → The Remote Script may not be listening; check port and firewall
- Clarification Needed → Add explicit track numbers or names
- Nothing happens → Try the UDP stub to confirm server works: `make udp-stub`; then switch back to Live

Next steps
- We will gradually add: readback (overview + per‑track), sends, device params, change events.

Standard vs Suite
- Live Standard works for core features (mixer, sends, common devices)
- Suite provides more devices; Fadebender will work with whichever devices exist in your project
