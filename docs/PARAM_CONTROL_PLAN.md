Parameter Control: Implementation Plan
======================================

Purpose
-------
Make return‑device parameter control precise, reusable, and intent‑driven by:
- Learning device parameter mappings (value↔display) once and sharing them.
- Storing robust metadata (control_type, units, labels, groups).
- Enabling group‑aware execution (auto‑enable masters like Freeze, Chorus On).
- Providing simple name/display APIs for testing and LLM intents.

Scope (Phased)
--------------
Phase 1 — Data Model + Storage
- Param metadata (Firestore + local JSON):
  - control_type: "binary" | "quantized" | "continuous"
  - unit: e.g., "ms", "s", "%", "Hz", "dB" (parsed from display)
  - labels: ["Low","Mid","High"] (for quantized)
  - min, max
  - fit: { type: "linear"|"log"|"exp"|"piecewise", r2, params/points }
  - samples: [{ value, display, display_num }]
  - group: "Input Filter" | "Early" | "Tail" | "Chorus" | "Global" | "Output"
  - role: "master" | "dependent" (e.g., "Chorus On" → masters [Rate, Amount])
- Device groups (per signature):
  - groups: [{ name, master, dependents[] }]
- Firestore layout:
  - device_mappings/{signature}
    - device_name, signature, tags, groups[]
    - params/{param_id} (sanitized id)
      - index, control_type, unit, labels[], min, max, fit{}, samples[]
- Local cache path (avoids dev reload): `~/.fadebender/param_maps` (override via FB_LOCAL_MAP_DIR)

Phase 2 — Learn Improvements
- Classify parameters before deep sampling:
  - Binary: capture 0/1 snapshots; mark role=master if it gates others (e.g., Freeze, Chorus On, Shelf Enabled)
  - Quantized: detect small label sets; persist label→value map
  - Continuous: sample grid (e.g., 41) and store numeric display_num; compute fit
- Group detection:
  - Name heuristics (from knowledge/ableton-live/reverb.md) for master/dependents
  - Optional learned hints: compare snapshots master=0 vs master=1 for affected dependents
- Always restore original values; skip destructive transitions (e.g., Freeze handling) during audio

Phase 3 — Execution
- Name/display API (done): `/op/return/param_by_name`
  - Resolve return/device/param by name or index
  - For continuous: invert fit → set → 1–2 readback refinements
  - For quantized: exact label
  - For binary: 0/1
  - Auto‑enable masters for dependents (Chorus On, Shelf Enabled, etc.)
- Relative mode: allow deltas (e.g., Decay +0.5 s, Wet +3 dB) with safe clamps

Phase 4 — Knowledge + Aliasing
- Files (LLM‑ready):
  - knowledge/ableton-live/reverb.md (you added — use sections to drive grouping)
  - knowledge/mixing/distance-and-depth.md (upfront vs push‑back)
  - knowledge/mixing/reverb-usage.md (practical defaults, pitfalls)
  - knowledge/ontology/param_ontology.md (canonical names per device family)
  - knowledge/aliases/ableton_reverb_aliases.md (Dry/Wet↔Wet, Pre‑Delay↔PreDelay, etc.)
- LLM intents:
  - Map user goals → canonical params + deltas → execute via name/display API

Phase 5 — Migration + Admin
- Backfill existing maps with control_type/unit/labels/groups
- Recompute fits where samples exist
- Endpoints:
  - /mappings/migrate_schema?signature=… (augment existing docs)
  - /mappings/rebuild_fit?signature=… (refit from samples)

Endpoints (current + planned)
-----------------------------
- Learn
  - POST /return/device/learn_start { return_index, device_index, resolution, sleep_ms }
  - GET  /return/device/learn_status?id=JOB
  - POST /mappings/fit?signature=… or ?index=&device=
  - POST /mappings/push_local (push one/all local maps to Firestore)
- Inspect
  - GET  /return/device/map?index=&device= (exists)
  - GET  /return/device/map_summary?index=&device= (param names + sample counts)
- Execute
  - POST /op/return/param_by_name { return_ref, device_ref, param_ref, target_display | target_value, mode }
  - (Planned) relative mode and master auto‑enable by group metadata

Testing Matrix
--------------
- Binary: Freeze → On/Off; confirm snapshot behavior under audio
- Quantized: e.g., Density labels (High/Mid/Low/Sparse); set by label and verify display
- Continuous: Pre‑Delay (ms), Decay (s), Size (%), Dry/Wet (%) → set by target display and verify readback

Risks & Mitigations
-------------------
- Third‑party plugins without numeric display → treat as quantized (label map) and consider audio‑based heuristics in future
- Uvicorn reloads on file write → local cache outside repo (done) or run without --reload
- Firestore write failures → local save first, push later (done)

Rollout
-------
1) Implement schema + learn classifier updates (binary/quantized/continuous + groups)
2) Migrate Reverb mapping; verify Freeze and groupings recorded
3) Extend /op/return/param_by_name with master auto‑enable + relative deltas
4) Seed knowledge/… docs; wire to /help and LLM prompt context
5) Run full test plan; push to Firestore

Context / Process Notes
-----------------------
- This plan is documented to minimize chat context requirements. You can start a new chat at any time and reference this doc (commit hash + file path) to continue seamlessly.
- Suggested cadence:
  - Phase 1 commit (schema + learn updates) → short test
  - Phase 3 commit (execute enhancements) → full test
  - Phase 4 commit (knowledge + aliasing) → LLM intent trials

