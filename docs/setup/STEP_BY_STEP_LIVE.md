# Step‑By‑Step: Run Fadebender with Ableton Live

Follow these exact steps to control a real Live project and see it in the web UI.

Prerequisites
- Ableton Live 11/12 (Standard or Suite)
- macOS (these steps use /Applications paths)
- This repo cloned locally; services running on localhost

1) Stop any stubs (avoid port conflicts)
- `lsof -ti :19845 | xargs kill -9 2>/dev/null || true`

2) Install the Remote Script (once)
- `make install-remote`
- This copies `ableton_remote/Fadebender` into each Ableton Live app’s MIDI Remote Scripts folder under `/Applications/.../Contents/App-Resources/MIDI Remote Scripts/Fadebender`.

3) Launch Live with UDP enabled
- `make launch-live`
- This sets `FADEBENDER_UDP_ENABLE=1` so the Remote Script starts a UDP listener inside Live on `127.0.0.1:19845`.

4) Tell Live to load the script
- Live → Preferences → Link/Tempo/MIDI → Control Surfaces
- Pick an empty slot, set Control Surface = “Fadebender”
- Input: None, Output: None (not required)

5) Verify Live is listening
- `lsof -nP -iUDP:19845` → should list `Live` (not `python3`)
- `curl -s http://127.0.0.1:8722/ping | jq` → `{ "ok": true, ... }`

6) Start/Restart local services (server + UI)
- `make restart-all`
- Open http://localhost:3000

7) See your project in the UI
- In the left sidebar, click the “Project” tab
- Click “Refresh” → track list should show your Live tracks
- Terminal check: `make outline` → should list `data.tracks` with your track names

8) Execute a test command
- Toggle Execute in the header (not Preview)
- Type: `set track 1 volume to -6 dB` → Track 1 fader moves in Live
- Undo/Redo from the header if needed

Troubleshooting
- Still seeing “Track 1/2 audio”
  - Ensure the stub isn’t running; re‑check `lsof -nP -iUDP:19845`
  - Rename a track in Live and run `make outline` again — the new name should appear
  - Check Live log: `~/Library/Preferences/Ableton/<version>/Log.txt` for:
    - `(Fadebender) [Fadebender] Remote Script loaded`
    - `(Fadebender) [Fadebender] UDP bridge started`
- “Ping ok but no outline”
  - `curl -s "http://127.0.0.1:8722/track/status?index=1" | jq` to inspect per‑track status
- Input/Output in Live? Not required for this script

Notes
- Live Standard works for core features (mixer, sends, common devices); Suite adds more devices.
- The “Project → Refresh” button fetches the outline on demand; we will add a background agent to auto‑sync regularly.
