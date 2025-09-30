Fadebender Quickstart
=====================

Run with stubbed returns (fastest)
- One command (starts Server + Chat + return‑aware UDP bridge):
- `make dev-returns`

Run with Ableton Live (return‑aware Remote Script)
1) Install Remote Script (one‑time):
- `make install-remote`
2) Start Server + Chat and launch Live (with UDP enabled):
- `make dev-live`
3) Alternatively, launch Live only (in a separate terminal):
- `make live-dev` (stops UDP stub if any, reinstalls Remote, launches Live)

Minimal separate commands (if you prefer)
- Server + Chat in parallel: `make run-server-chat`
- Launch Live with UDP: `make launch-live`
- Return‑aware UDP bridge stub: `make run-udp-bridge`
- Stop UDP process (default port 19845): `make stop-udp`

Verify wiring
- Check return tracks/devices/params via the backend:
- `make returns-status`

Common ports
- Chat UI: http://127.0.0.1:3000
- Server: http://127.0.0.1:8722
- NLP (optional): http://127.0.0.1:8000

Configuration
- Tunables live in `configs/app_config.json` and can be edited from the UI Settings accordion:
  - `ui.refresh_ms`: global auto‑refresh interval
  - `ui.sends_open_refresh_ms`: fast refresh while Sends accordion is open
  - `ui.sse_throttle_ms`: SSE refresh throttle for track status
  - `server.send_aliases`: name → send index (e.g., reverb→0, delay→1)

Notes
- For returns to appear with real data, use `make dev-live` (Ableton Live) or `make dev-returns` (return‑aware UDP bridge). The simple `make udp-stub` does not implement return ops.
- If you see “No returns”, ensure no old UDP stub is running: `make stop-udp`.

