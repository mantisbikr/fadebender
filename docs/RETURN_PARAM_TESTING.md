Return Device Parameter Learning & Testing
=========================================

This guide shows how to learn mappings for return‑device parameters, fit models, push to Firestore, and test precise param changes by name/display.

Prerequisites
- Server running: `make run-server`
- Web Chat (optional): `make run-chat`
- Live path (pick one):
  - Ableton Live: `make dev-live` (after `make install-remote` once)
  - Return‑aware UDP bridge (stub): `make run-udp-bridge`
- Firestore (for cloud storage):
  - In server venv: `pip install google-cloud-firestore`
  - Export: `GOOGLE_APPLICATION_CREDENTIALS=/absolute/path/to/service-account.json`

Local map cache directory
- Defaults to: `~/.fadebender/param_maps`
- Override: `FB_LOCAL_MAP_DIR=/abs/path` before starting server
- Helpers:
  - Migrate repo maps → cache dir: `make migrate-local-maps`
  - List cache maps: `make list-local-maps`

1) Discover indices
- Returns (get `return_index`):
  - `curl -s http://127.0.0.1:8722/returns | jq '.data.returns'`
- Devices on a return (get `device_index`):
  - `curl -s "http://127.0.0.1:8722/return/devices?index=RETURN_INDEX" | jq '.data.devices'`
- (Optional) Params on a device:
  - `curl -s "http://127.0.0.1:8722/return/device/params?index=RETURN_INDEX&device=DEVICE_INDEX" | jq '.data.params'`

2) Learn a device (async)
- Start job (example: return 0, device 0):
  - `curl -s -X POST http://127.0.0.1:8722/return/device/learn_start -H 'Content-Type: application/json' -d '{"return_index":0,"device_index":0,"resolution":41,"sleep_ms":20}'`
  - Copy the `job_id` from response
- Poll status:
  - `curl -s "http://127.0.0.1:8722/return/device/learn_status?id=JOB_ID" | jq .`
  - Wait for `state: "done"` (status shows `local_saved: true` on success)

3) Fit the local map (adds per‑param model)
- Fit by signature:
  - `curl -s -X POST "http://127.0.0.1:8722/mappings/fit?signature=SIGNATURE" | jq .`
- Or by indices (server computes signature):
  - `curl -s -X POST "http://127.0.0.1:8722/mappings/fit?index=0&device=0" | jq .`
- The local JSON at `~/.fadebender/param_maps/SIGNATURE.json` is updated with a `fit` block per param (type: linear/log/exp or piecewise).

4) Push local map(s) to Firestore
- Push one signature:
  - `curl -s -X POST "http://127.0.0.1:8722/mappings/push_local?signature=SIGNATURE" | jq .`
- Push all local maps:
  - `curl -s -X POST http://127.0.0.1:8722/mappings/push_local | jq .`

5) Verify stored mapping
- Exists:
  - `curl -s "http://127.0.0.1:8722/return/device/map?index=0&device=0" | jq .`
  - Expect `backend: "firestore"` and `exists: true` if saved in cloud
- Summary (param names + sample counts):
  - `curl -s "http://127.0.0.1:8722/return/device/map_summary?index=0&device=0" | jq .`

6) Precise set by name/display (easy testing)
- Endpoint: `POST /op/return/param_by_name`
- Body fields:
  - `return_ref`: "A" | "0" | substring of return name
  - `device_ref`: substring of device name (e.g., "Reverb")
  - `param_ref`: substring of parameter name as shown in Live (e.g., "Pre-Delay", "Dry/Wet")
  - `target_display` (optional): human string like "25 ms", "20%", "High"
  - `target_value` (optional): numeric display target (e.g., 25 for 25 ms)

Examples (numeric params)
- Set Reverb Dry/Wet to 20%:
  - `curl -s -X POST http://127.0.0.1:8722/op/return/param_by_name -H 'Content-Type: application/json' -d '{"return_ref":"A","device_ref":"Reverb","param_ref":"Dry/Wet","target_display":"20%"}' | jq .`
- Set Pre‑Delay to 25 ms:
  - `curl -s -X POST http://127.0.0.1:8722/op/return/param_by_name -H 'Content-Type: application/json' -d '{"return_ref":"A","device_ref":"Reverb","param_ref":"Pre","target_display":"25 ms"}' | jq .`
- Set Decay to 2.0 s:
  - `curl -s -X POST http://127.0.0.1:8722/op/return/param_by_name -H 'Content-Type: application/json' -d '{"return_ref":"A","device_ref":"Reverb","param_ref":"Decay","target_display":"2.0 s"}' | jq .`

Example (quantized/labels)
- Set Density to High:
  - `curl -s -X POST http://127.0.0.1:8722/op/return/param_by_name -H 'Content-Type: application/json' -d '{"return_ref":"A","device_ref":"Reverb","param_ref":"Density","target_display":"High"}' | jq .`

Verify readback
- Inspect display values to confirm:
  - `curl -s "http://127.0.0.1:8722/return/device/params?index=0&device=0" | jq '.data.params | map({name, display_value})'`

Cleanup / Re‑learn
- Delete mapping (by indices):
  - `curl -s -X POST http://127.0.0.1:8722/return/device/map_delete -H 'Content-Type: application/json' -d '{"return_index":0,"device_index":0}' | jq .`
- Re‑learn:
  - See step 2

Troubleshooting
- Server restarts during learn: ensure local map dir is outside repo (default: `~/.fadebender/param_maps`).
- Firestore writes fail (`saved: false`): install `google-cloud-firestore` in the server venv and export `GOOGLE_APPLICATION_CREDENTIALS` before `make run-server`.
- `exists: true` but old/no samples: delete the mapping via `map_delete` and re‑learn.

