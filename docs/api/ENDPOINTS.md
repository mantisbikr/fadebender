# Fadebender API – Friendly Reference

Simple, copy‑pasteable commands to inspect and control Ableton Live via the Fadebender server. Examples assume the server is running locally at http://127.0.0.1:8722.

Basics
- Return tracks are zero‑indexed: A=0, B=1, C=2…
- Devices on a track/return are zero‑indexed: first device = 0
- Use `jq` for pretty output: `… | jq .`

Server Health
- Ping the server: `curl -sS http://127.0.0.1:8722/ping`
- Health info: `curl -sS http://127.0.0.1:8722/health | jq .`

Returns (A/B/C…)
- List return tracks: `curl -sS http://127.0.0.1:8722/returns | jq .data.returns`
- List devices on Return B (index=1): `curl -sS "http://127.0.0.1:8722/return/devices?index=1" | jq .data.devices`
- Get params for first device on Return B: `curl -sS "http://127.0.0.1:8722/return/device/params?index=1&device=0" | jq .data.params`
- Get sends for Return A: `curl -sS "http://127.0.0.1:8722/return/sends?index=0" | jq .data`
- Set a return→return send (Return A → Send B=1): `curl -sS -X POST http://127.0.0.1:8722/op/return/send -H 'Content-Type: application/json' -d '{"return_index":0,"send_index":1,"value":0.5}' | jq .`

Device Mapping (structure + analysis)
- Mapping summary (turns UI LED green): `curl -sS "http://127.0.0.1:8722/return/device/map_summary?index=0&device=0" | jq .`
- Mapping existence + type: `curl -sS "http://127.0.0.1:8722/return/device/map?index=0&device=0" | jq '{signature,exists,mapping_exists,learned_exists,device_type}'`
- Fetch full mapping (grouping + fits) by signature: `curl -sS "http://127.0.0.1:8722/device_mapping?signature=<SIG>" | jq .`
- Or derive from live indices: `curl -sS "http://127.0.0.1:8722/device_mapping?index=0&device=0" | jq .`
- Import mapping (grouping, params_meta): `curl -sS -X POST http://127.0.0.1:8722/device_mapping/import -H 'Content-Type: application/json' --data-binary @analysis.json | jq .`

Preset Capture & Apply
- Capture current device as a preset (user/stock):
  - POST /return/device/capture_preset with JSON body:
  - `curl -sS -X POST http://127.0.0.1:8722/return/device/capture_preset -H 'Content-Type: application/json' -d '{"return_index":1,"device_index":0,"preset_name":"my_preset","category":"user"}' | jq .`
- List presets (optionally by signature): `curl -sS "http://127.0.0.1:8722/presets?structure_signature=<SIG>" | jq .`
- Get full preset doc: `curl -sS "http://127.0.0.1:8722/presets/<preset_id>" | jq .`
- Apply a preset to a device: `curl -sS -X POST http://127.0.0.1:8722/return/device/apply_preset -H 'Content-Type: application/json' -d '{"return_index":1,"device_index":0,"preset_id":"reverb_cathedral"}' | jq .`
- Refresh preset metadata/values from live: `curl -sS -X POST http://127.0.0.1:8722/presets/refresh_metadata -H 'Content-Type: application/json' -d '{"preset_id":"reverb_cathedral","update_values_from_live":true,"return_index":1,"device_index":0}' | jq .`

Direct Parameter Control
- Set by index (fast path): `curl -sS -X POST http://127.0.0.1:8722/op/return/device/param -H 'Content-Type: application/json' -d '{"return_index":1,"device_index":0,"param_index":12,"value":0.58}' | jq .`
- Set by name or display label (uses mapping):
  - Absolute numeric: `curl -sS -X POST http://127.0.0.1:8722/op/return/param_by_name -H 'Content-Type: application/json' -d '{"return_ref":"B","device_ref":"0","param_ref":"Feedback","target_value":0.6}' | jq .`
  - Display label/units: `curl -sS -X POST http://127.0.0.1:8722/op/return/param_by_name -H 'Content-Type: application/json' -d '{"return_ref":"B","device_ref":"0","param_ref":"Density","target_display":"High"}' | jq .`

Learning (optional, legacy sample learning)
- Start learning (asynchronous sweep): `curl -sS -X POST http://127.0.0.1:8722/return/device/learn_start -H 'Content-Type: application/json' -d '{"return_index":1,"device_index":0,"resolution":41,"sleep_ms":20}' | jq .`
- Check status: `curl -sS "http://127.0.0.1:8722/return/device/learn_status?id=<job_id>" | jq .`

Track & Master Devices (basic)
- Track: list devices on Track 1: `curl -sS "http://127.0.0.1:8722/track/devices?index=1" | jq .data.devices`
- Track: params for device 0 on Track 1: `curl -sS "http://127.0.0.1:8722/track/device/params?index=1&device=0" | jq .data.params`
- Master: list devices: `curl -sS http://127.0.0.1:8722/master/devices | jq .data`
- Master: params for device 0: `curl -sS "http://127.0.0.1:8722/master/device/params?device=0" | jq .data.params`

Mixer (quick)
- Set track mixer: `curl -sS -X POST http://127.0.0.1:8722/op/mixer -H 'Content-Type: application/json' -d '{"track_index":1,"field":"volume","value":0.8}' | jq .`
- Set return mixer (volume/pan/mute/solo): `curl -sS -X POST http://127.0.0.1:8722/op/return/mixer -H 'Content-Type: application/json' -d '{"return_index":0,"field":"volume","value":0.6}' | jq .`

Tips
- Use letters for returns in name‑based ops: A/B/C… (e.g., `"return_ref":"B"`).
- If something returns `{ok:false}`, ensure Ableton Live is running with the remote script enabled, or use `make dev-returns` to run the return‑aware UDP bridge.

