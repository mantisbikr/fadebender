# Fadebender API – Friendly Reference

Simple, copy‑pasteable commands to inspect and control Ableton Live via the Fadebender server. Examples assume the server is running locally at http://127.0.0.1:8722.

This document is intended for internal/API users (not end users). For the chat/user experience, see the Fadebender user guides instead.

Basics
- Return tracks are zero‑indexed: A=0, B=1, C=2…
- Devices on a track/return are zero‑indexed: first device = 0
- Use `jq` for pretty output: `… | jq .`

Server Health
- Ping the server: `curl -sS http://127.0.0.1:8722/ping`
- Health info: `curl -sS http://127.0.0.1:8722/health | jq .`
 - Readiness: `curl -sS http://127.0.0.1:8722/ready | jq .`

Chat and Help
- Execute a natural language command:
  - ```bash
    curl -s http://127.0.0.1:8722/chat \
      -X POST -H "Content-Type: application/json" \
      -d '{"text":"set track 1 volume to -6 dB","confirm":true}' | jq .
    ```
  - Response includes:
    - `ok`: boolean
    - `summary`: human-readable summary
    - `intent` / `canonical`: normalized intent (domain, field, value, etc.)
- Query information via chat:
  - ```bash
    curl -s http://127.0.0.1:8722/chat \
      -X POST -H "Content-Type: application/json" \
      -d '{"text":"what is track 1 volume","confirm":true}' | jq .
    ```
  - Look for `values` / `answer` fields.
- Knowledge-backed help (audio engineering, Ableton, Fadebender usage):
  - ```bash
    curl -s http://127.0.0.1:8722/help \
      -X POST -H "Content-Type: application/json" \
      -d '{"query":"my vocals sound weak"}' | jq .
    ```
  - Response:
    - `ok`: boolean
    - `answer`: markdown-formatted answer string
    - `sources`: `[{"source","title"}]`
    - `suggested_intents`: example commands the UI can surface

Contracts
- `/chat` (POST)
  - Request body (`ChatBody`):
    - `text: string` – user message
    - `confirm: boolean` – if false, treat as dry-run where supported
    - `model?: string`, `strict?: boolean` – optional overrides/flags
  - Response (typical):
    - `ok: boolean`
    - `summary: string`
    - `intent?: object` – structured intent used/extracted
    - `canonical?: object` – canonical intent (when available)
    - `data?: object` – extra fields (values, capabilities, etc.)
  - Errors:
    - HTTP 400/500 for parser/execution failures; body includes `detail` or `{ok:false, reason:...}`.
- `/help` (POST)
  - Request body (`HelpBody`):
    - `query: string`
    - `context?: object` – optional device/track context (e.g., `{ "return_index":0,"device_index":0 }`)
  - Response:
    - `ok: boolean`
    - `answer: string` – markdown help text
    - `sources: {source:string,title:string}[]`
    - `suggested_intents: string[]`

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
- Validate names vs live (catch mismatches early): `curl -sS "http://127.0.0.1:8722/device_mapping/validate?index=0&device=0" | jq .`
- Sanity probe (set by display, read back, restore):
  - `curl -sS -X POST http://127.0.0.1:8722/device_mapping/sanity_probe -H 'Content-Type: application/json' -d '{"return_index":0,"device_index":0,"param_ref":"HiFilter Freq","target_display":"7000","restore":true}' | jq .`
 - Enumerate labels for a quantized param (build label_map):
  - `curl -sS "http://127.0.0.1:8722/device_mapping/enumerate_labels?index=0&device=0&param_ref=HiFilter%20Type" | jq .`
   - Note: This briefly sweeps the parameter on the device to discover labels.

Preset Capture & Apply
- Capture current device as a preset (user/stock):
  - POST /return/device/capture_preset with JSON body:
  - `curl -sS -X POST http://127.0.0.1:8722/return/device/capture_preset -H 'Content-Type: application/json' -d '{"return_index":1,"device_index":0,"preset_name":"my_preset","category":"user"}' | jq .`
- List presets (optionally by signature): `curl -sS "http://127.0.0.1:8722/presets?structure_signature=<SIG>" | jq .`
- Get full preset doc: `curl -sS "http://127.0.0.1:8722/presets/<preset_id>" | jq .`
- Delete a preset (user presets): `curl -sS -X DELETE http://127.0.0.1:8722/presets/<preset_id> | jq .`
- Apply a preset to a device: `curl -sS -X POST http://127.0.0.1:8722/return/device/apply_preset -H 'Content-Type: application/json' -d '{"return_index":1,"device_index":0,"preset_id":"reverb_cathedral"}' | jq .`
- Refresh preset metadata/values from live: `curl -sS -X POST http://127.0.0.1:8722/presets/refresh_metadata -H 'Content-Type: application/json' -d '{"preset_id":"reverb_cathedral","update_values_from_live":true,"return_index":1,"device_index":0}' | jq .`

Direct Parameter Control
- Set by index (fast path): `curl -sS -X POST http://127.0.0.1:8722/op/return/device/param -H 'Content-Type: application/json' -d '{"return_index":1,"device_index":0,"param_index":12,"value":0.58}' | jq .`
- Set by name or display label (uses mapping fits/labels when available):
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

Snapshots and Overview
- Get a high-level snapshot of the Live set:
  - ```bash
    curl -sS http://127.0.0.1:8722/snapshot | jq .
    ```
  - Response:
    - `tracks`: `[{index,name,type}]`
    - `returns`: `[{index,name,devices:[...]}]`
    - `track_count`, `return_count`, `sends_per_track`

Snapshot Contract
- `/snapshot` (GET)
  - Query params:
    - `force_refresh?: bool` – bypass caches and re-query Live
  - Response:
    - `ok: boolean`
    - `tracks: {index:number,name:string,type:string,devices:any[]}[]`
    - `track_count: number`
    - `returns: {index:number,name:string,devices:any[]}[]`
    - `return_count: number`
    - `mixer: { track: {index,fields}[], return: {index,fields}[], master: object }`
    - `devices: { tracks:any, returns:any, master:any }`

Scenes and Clips
- List scenes:
  - `curl -sS http://127.0.0.1:8722/scenes | jq .`
- Fire and stop a scene:
  - ```bash
    curl -sS -X POST http://127.0.0.1:8722/scene/fire \
      -H 'Content-Type: application/json' \
      -d '{"scene_index":2,"select":true}' | jq .

    curl -sS -X POST http://127.0.0.1:8722/scene/stop \
      -H 'Content-Type: application/json' \
      -d '{"scene_index":2}' | jq .
    ```
- Capture and insert a scene from currently playing clips:
  - ```bash
    curl -sS -X POST http://127.0.0.1:8722/scene/capture_insert \
      -H 'Content-Type: application/json' \
      -d '{}' | jq .
    ```
- Create a MIDI clip (Session view):
  - ```bash
    curl -sS -X POST http://127.0.0.1:8722/clip/create \
      -H 'Content-Type: application/json' \
      -d '{"track_index":2,"scene_index":4,"length_beats":4}' | jq .
    ```

Views and Naming
- Switch views:
  - ```bash
    curl -sS -X POST http://127.0.0.1:8722/view \
      -H 'Content-Type: application/json' \
      -d '{"mode":"session"}' | jq .
    ```
- Rename track/scene/clip:
  - ```bash
    curl -sS -X POST http://127.0.0.1:8722/track/name \
      -H 'Content-Type: application/json' \
      -d '{"track_index":3,"name":"Guitars"}' | jq .

    curl -sS -X POST http://127.0.0.1:8722/scene/name \
      -H 'Content-Type: application/json' \
      -d '{"scene_index":2,"name":"Chorus"}' | jq .

    curl -sS -X POST http://127.0.0.1:8722/clip/name \
      -H 'Content-Type: application/json' \
      -d '{"track_index":2,"scene_index":4,"name":"Hook"}' | jq .
    ```

Intents API
- Execute a canonical intent:
  - ```bash
    curl -sS -X POST http://127.0.0.1:8722/intent/execute \
      -H 'Content-Type: application/json' \
      -d '{"domain":"track","action":"set","track_index":1,"field":"volume","value":0.8}' | jq .
    ```
- Read a value via canonical read intent:
  - ```bash
    curl -sS -X POST http://127.0.0.1:8722/intent/read \
      -H 'Content-Type: application/json' \
      -d '{"domain":"track","track_index":1,"field":"volume"}' | jq .
    ```

Intent Contracts
- `/intent/execute` (POST, `CanonicalIntent`)
  - Fields (subset):
    - `domain: "track"|"return"|"master"|"device"|"transport"`
    - `action: string` – semantic action (e.g., "set","increase","scene_fire","rename_track")
    - Target: `track_index?`, `return_index?`/`return_ref?`, `device_index?`, etc.
    - Selection: `field?`, `send_index?`/`send_ref?`, `param_index?`/`param_ref?`
    - Value: `value?`, `unit?`, `display?`
    - Options: `dry_run?: bool`, `clamp?: bool`
  - Response:
    - `ok: boolean`
    - `summary: string`
    - `resp?: any` – raw response from Ableton/ops layer
- `/intent/read` (POST, `ReadIntent`)
  - Fields:
    - `domain: "track"|"return"|"master"|"device"|"transport"`
    - Target selection (same pattern as `CanonicalIntent`)
    - Selection: `field?`, `param_index?`, `param_ref?`, `send_index?`, `send_ref?`
  - Response (typical):
    - `ok: boolean`
    - `value?: any`
    - `unit?: string`
    - `display_value?: string`
    - `suggested_intents?: string[]`

Tips
- Use letters for returns in name‑based ops: A/B/C… (e.g., `"return_ref":"B"`).
- If something returns `{ok:false}`, ensure Ableton Live is running with the remote script enabled, or use `make dev-returns` to run the return‑aware UDP bridge.
