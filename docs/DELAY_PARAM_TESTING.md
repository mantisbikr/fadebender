Delay Return Device — Quick Test Plan
====================================

Goal
- Verify quick-learn mapping for Ableton Delay on a return track and confirm accurate parameter control in both sync and time modes with minimal steps.

Prerequisites
- Server running: `make run-server`
- UDP bridge: `make run-udp-bridge` (or Ableton Live with the remote script)
- Optional: Web chat UI `make run-chat`
- Param learn config already committed (quick mode defaults tuned)

1) Discover indices
- Returns:
  - `curl -s http://127.0.0.1:8722/returns | jq '.data.returns'`
- Devices on B:
  - `curl -s "http://127.0.0.1:8722/return/devices?index=1" | jq '.data.devices'`

2) Quick learn (fast)
- Run quick learn for Delay on return B (index 1, device 0):
  - `curl -s -X POST http://127.0.0.1:8722/return/device/learn_quick -H 'Content-Type: application/json' -d '{"return_index":1,"device_index":0}' | jq .`
- Expected to complete in ~20–40s with current config.

3) Verify mapping exists + summary
- Map summary (includes control_type, group/role, labels):
  - `curl -s "http://127.0.0.1:8722/return/device/map_summary?index=1&device=0" | jq .`

4) Core mode tests (Sync ↔ Time)
- Ensure config-based master enabling is active (L/R Sync): `/config/reload` if edited config.
- Set L Time (forces L Sync Off):
  - `curl -s -X POST http://127.0.0.1:8722/op/return/param_by_name -H 'Content-Type: application/json' -d '{"return_ref":"B","device_ref":"Delay","param_ref":"L Time","target_display":"250 ms"}' | jq .`
- Set R 16th (forces R Sync On):
  - `curl -s -X POST http://127.0.0.1:8722/op/return/param_by_name -H 'Content-Type: application/json' -d '{"return_ref":"B","device_ref":"Delay","param_ref":"R 16th","target_display":"5"}' | jq .`
- Readback (confirm values + modes):
  - `curl -s "http://127.0.0.1:8722/return/device/params?index=1&device=0" | jq -r '.data.params | map(select(.name=="L Sync" or .name=="L Time" or .name=="R Sync" or .name=="R 16th")) | map({name, display_value})'`

5) Additional parameter checks
- Feedback (relative +3 then -3):
  - `curl -s -X POST http://127.0.0.1:8722/op/return/param_by_name -H 'Content-Type: application/json' -d '{"return_ref":"B","device_ref":"Delay","param_ref":"Feedback","target_value":3,"mode":"relative"}' | jq .`
  - `curl -s -X POST http://127.0.0.1:8722/op/return/param_by_name -H 'Content-Type: application/json' -d '{"return_ref":"B","device_ref":"Delay","param_ref":"Feedback","target_value":-3,"mode":"relative"}' | jq .`
- Filter On → Filter Freq / Width:
  - `curl -s -X POST http://127.0.0.1:8722/op/return/param_by_name -H 'Content-Type: application/json' -d '{"return_ref":"B","device_ref":"Delay","param_ref":"Filter On","target_display":"On"}' | jq .`
  - `curl -s -X POST http://127.0.0.1:8722/op/return/param_by_name -H 'Content-Type: application/json' -d '{"return_ref":"B","device_ref":"Delay","param_ref":"Filter Freq","target_display":"1200 Hz"}' | jq .`
  - `curl -s -X POST http://127.0.0.1:8722/op/return/param_by_name -H 'Content-Type: application/json' -d '{"return_ref":"B","device_ref":"Delay","param_ref":"Filter Width","target_value":1,"mode":"relative"}' | jq .`
- Dry/Wet to 20%:
  - `curl -s -X POST http://127.0.0.1:8722/op/return/param_by_name -H 'Content-Type: application/json' -d '{"return_ref":"B","device_ref":"Delay","param_ref":"Dry/Wet","target_display":"20%"}' | jq .`

6) Optional toggles
- Link On/Off, Ping Pong On/Off:
  - `curl -s -X POST http://127.0.0.1:8722/op/return/param_by_name -H 'Content-Type: application/json' -d '{"return_ref":"B","device_ref":"Delay","param_ref":"Link","target_display":"On"}' | jq .`
  - `curl -s -X POST http://127.0.0.1:8722/op/return/param_by_name -H 'Content-Type: application/json' -d '{"return_ref":"B","device_ref":"Delay","param_ref":"Ping Pong","target_display":"On"}' | jq .`

7) Accuracy expectations
- Time / frequency parameters use fit inversion + multi-correction with bisection; expect exact display values (e.g., `250.0`).
- Sync division parameters (L/R 16th) use label matching; expect exact numeric labels.
- Relative controls (Feedback, Dry/Wet) apply with clamps and quick refine.

Troubleshooting
- If quick learn seems slow: reduce `defaults.sleep_ms_quick` (e.g., 5) and `defaults.max_extra_points_quick` (e.g., 1) in `configs/param_learn.json`, then `POST /config/reload`.
- If a dependent seems ineffectual, confirm master state (e.g., L/R Sync) via readback.
- For new devices, add grouping rules under `grouping.<device>` in `configs/param_learn.json`.

