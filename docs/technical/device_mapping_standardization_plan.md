# Device Mapping Standardization Plan

Goal: Standardize device_mappings schema across devices (Reverb, Delay, Align Delay as reference), then migrate Amp to the standard without breaking current behavior.

## Current State Snapshot
- Reverb (64ccfc...db9): params_meta with `fit` (linear/exp), display ranges, grouping, sections. OK.
- Delay (9bfcc8...df1): params_meta with `fit.points` ({x,y}) splines, labels/label_map, grouping, sections. OK.
- Align Delay (82da8c...38e): params_meta uses `fit.points` ({x,y}), labels/label_map; extra `grouping.mode_dependent_params` (harmless). OK.
- Amp (d55475...c37): params_meta uses `fit_type`, `coefficients`, `display_range` instead of `fit`; no `fit` object. Works via readback fallback but less efficient. Needs enrichment to add `fit` and `min_display/max_display`.

## Standard Schema (Reference)
- Template: `docs/technical/device_mapping_standard.json`
- Key expectations used by code today:
  - `params_meta[]` with:
    - continuous: `min/max` (0..1), `min_display/max_display`, and `fit`:
      - closed-form: `{type: linear|exp|log, coeffs: {a,b}, r2?}`
      - piecewise/spline: `{type: spline|piecewise, points: [{x,y}], r2?}`
    - quantized/binary: `labels` and optional `label_map`
  - `grouping` with `masters`, `dependents`, `skip_auto_enable`, `apply_order`, optional `dependent_master_values`
  - Top-level: `signature`, `device_name`, `device_type`, `created_at`, `analysis_status`, optional `sources`, `sections`, `param_names`, `param_count`

Notes:
- Keep `fit.points` keys as `{x,y}` (code expects this).
- Per‑param requires‑for‑effect: supported at `params_meta[i].requires_for_effect`. Top‑level `grouping.requires_for_effect` is OK to store but not currently read by write path.

## Pre‑Flight
1) Back up Firestore completely
   - `. nlp-service/.venv/bin/activate`
   - `python3 nlp-service/scripts/backup_both_databases.py`
   - Outputs to `backups/database_backups/` (includes device_mappings + params subcollections and presets)

2) (Optional) Per‑device backups for quick diffs
   - `python3 scripts/backup_firestore_mapping.py --signature <SIG> --output backups/<name>.json --database dev-display-value`

## Branching Strategy
Option A (recommended after you finish improve-audio-assistant):
- Complete current feature work first to minimize context switching.

Option B (parallel, additive):
- `git stash push -m "wip: improve-audio-assistant"`
- `git switch -c schema-standardization-device-mappings`
- Work additively (do not remove/rename existing keys), ship, then merge back.

## Implementation Steps (Additive, Non‑Breaking)
1) Validator/Normalizer script
   - Path: `scripts/validate_normalize_device_mapping.py`
   - Capabilities:
     - Validate presence of top‑level keys and `params_meta` shape.
     - For continuous params: warn if `fit` missing or only legacy fields present.
     - If `display_range: [lo,hi]` present and knob is 0..10 (Amp style), generate a default linear `fit`:
       - `fit = {"type":"linear","coeffs":{"a": hi - lo, "b": lo}}` and set `min_display=lo`, `max_display=hi`.
     - Preserve existing legacy keys for back‑compat; only add `fit`/`min_display`/`max_display` if absent.
     - Optional: emit a standardized JSON to stdout or write `--out`.

2) Code support for top‑level requires_for_effect (optional but useful)
   - File: `server/services/intents/param_service.py`
   - Extend `check_requires_for_effect(...)` to also look at `mapping.grouping.requires_for_effect[target_param_name]` and support:
     - `all_of`: ["Param A", {"param":"Param B","value":0.0}]
     - `any_of`: same structure
     - Default value for string items = 1.0
   - Keep existing per‑param `params_meta[i].requires_for_effect` handling intact.

3) Keep fit.points format
   - No changes needed. `invert_fit_to_value` already handles `{x,y}` points.

4) Amp enrichment plan
   - Source: `backups/amp.json` and live device if needed.
   - For continuous knobs (e.g., Bass, Middle, Treble, Presence, Gain, Volume):
     - If range is 0..10, add linear `fit` with `min_display=0.0`, `max_display=10.0`.
     - If device displays different units/ranges, measure a few samples and fit linear/exp as appropriate.
   - For quantized/binary: ensure `labels` exist; keep `label_map` as needed.
   - Update Firestore via API or script:
     - API: `POST /device_mapping/import` with `{ signature, params_meta, device_type }`
     - Or write a small updater in `scripts/` to merge in the added `fit` fields.

5) Tooling updates (optional)
   - If desired, update `scripts/backup_firestore_mapping.py` to normalize output (ensure single `signature` key, keep `_params_subcollection` for backups).

## Validation & Tests
- Endpoint checks (replace SIG):
  - `curl -s "http://127.0.0.1:8722/device_mapping?signature=64ccfc...db9" | jq .summary`
  - `curl -s "http://127.0.0.1:8722/device_mapping/fits?signature=9bfcc8...df1" | jq .count,.fits[0]`
  - `curl -s "http://127.0.0.1:8722/device_mapping/validate?signature=82da8c...38e" | jq .`
- Runtime behavior:
  - With `fit` present, display‑to‑value conversion should not log `approx_preview_no_fit` and should apply without extra readback iterations.
  - Auto‑enable of masters (from grouping) should remain unchanged.
  - If step 2 implemented, requires_for_effect at top‑level grouping should trigger prereq writes.

## Rollout & Rollback
Rollout
1) Backup DB (full snapshot) and affected device docs per‑device.
2) Apply additive schema updates (Amp fits) using script/API.
3) Validate via endpoints and a quick manual session.

Rollback
1) Restore individual docs from `backups/*.json` using a small uploader, or
2) Restore full DB from `backups/database_backups/<file>.json` (write a restore script mirroring the backup structure if needed).

## Checklist
- [ ] Full Firestore backup created
- [ ] Feature branch created (or proceed after improve-audio-assistant)
- [ ] Validator/normalizer script added
- [ ] Optional: param_service supports top‑level grouping.requires_for_effect (all_of/any_of)
- [ ] Amp params enriched with `fit` and display ranges
- [ ] Reverb/Delay/Align Delay verified unchanged
- [ ] Endpoints validated (/device_mapping, /fits, /validate)
- [ ] Rollback path documented

## Time & Effort (est.)
- Validator/normalizer: 1–2 hrs
- Amp enrichment (basic linear fits): 1 hr; more if measuring non‑linear
- Optional code support for grouping.requires_for_effect: 1 hr
- Validation + docs: 0.5 hr

