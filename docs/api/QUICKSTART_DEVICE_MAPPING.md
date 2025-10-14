# Device Mapping Quickstart (Reverb example, works for new devices too)

Use this 1‑pager to capture presets, add grouping/labels, fit continuous parameters, and verify mapping for any device. Commands assume the server is at http://127.0.0.1:8722 and `jq` is installed.

Prereqs
- Ableton Live running with the return‑aware Remote Script (or `make dev-returns`).
- Open the UI and expand the return so devices/params are fetched (auto‑capture kicks in).

Step 1 — Get the device signature
- For Return A, first device: `SIG=$(curl -sS "http://127.0.0.1:8722/return/device/map?index=0&device=0" | jq -r .signature)`

Step 2 — (Optional) Export digest for LLM
- `make export-digest SIG=$SIG OUT=/tmp/digest.json`
- Digest summarizes numeric displays and labels across captured presets.

Step 3 — Create analysis.json (grouping + labels)
- Save this template (adjust names to match your device’s params; example is for Reverb):

```
{
  "signature": "<SIG>",
  "device_type": "reverb",
  "grouping": {
    "masters": ["ER Spin On", "Chorus On", "LowShelf On", "HiShelf On", "Freeze"],
    "dependents": {
      "ER Spin Rate": "ER Spin On",
      "ER Spin Amount": "ER Spin On",
      "Chorus Rate": "Chorus On",
      "Chorus Amount": "Chorus On",
      "LowShelf Freq": "LowShelf On",
      "LowShelf Gain": "LowShelf On",
      "HiShelf Freq": "HiShelf On",
      "HiShelf Gain": "HiShelf On",
      "Flat": "Freeze",
      "Cut": "Freeze"
    },
    "dependent_master_values": {
      "ER Spin Rate": 1.0, "ER Spin Amount": 1.0,
      "Chorus Rate": 1.0, "Chorus Amount": 1.0,
      "LowShelf Freq": 1.0, "LowShelf Gain": 1.0,
      "HiShelf Freq": 1.0, "HiShelf Gain": 1.0,
      "Flat": 1.0, "Cut": 1.0
    },
    "apply_order": ["masters", "quantized", "dependents", "continuous"],
    "skip_auto_enable": ["Freeze"]
  },
  "params_meta": [
    { "name": "Density", "control_type": "quantized",
      "labels": ["Sparse","Low","Mid","High"],
      "label_map": { "Sparse": 0.0, "Low": 0.33, "Mid": 0.66, "High": 1.0 },
      "confidence": 1.0 },
    { "name": "Diffusion", "control_type": "continuous" },
    { "name": "Scale",     "control_type": "continuous" }
  ],
  "analysis_status": "partial_fits"
}
```

Step 4 — Import grouping/labels
- `make import-mapping FILE=/full/path/analysis.json`

Step 5 — Fit continuous params from captured presets
- Generate fits (no import yet):
  - `python3 scripts/fit_params_from_presets.py --signature "$SIG" > /tmp/fits.json`
- Merge grouping + fits and import:
  - `jq -s '
      def uniq_by_name(a): a | unique_by(.name);
      (.[0]) as $g | (.[1]) as $f |
      { signature: ($g.signature // $f.signature),
        device_type: $g.device_type,
        grouping: $g.grouping,
        analysis_status: "partial_fits",
        params_meta: uniq_by_name( (($g.params_meta // []) + ($f.params_meta // [])) ),
        sources: { preset_count: $f.preset_count, fit_run_id: $f.run_id } }' \
     /full/path/analysis.json /tmp/fits.json > /tmp/combined_analysis.json`
  - `curl -sS -X POST http://127.0.0.1:8722/device_mapping/import -H 'Content-Type: application/json' --data-binary @/tmp/combined_analysis.json | jq .`

Step 6 — Verify mapping
- `curl -sS "http://127.0.0.1:8722/device_mapping?signature=$SIG" | jq '{signature, summary}'`
- Expected: `summary.fitted_count` > 0; `missing_continuous` may list any params with insufficient data.

Step 7 — (Optional) Mark mapping as analyzed
- `echo '{"signature":"'$SIG'","analysis_status":"analyzed"}' | curl -sS -X POST http://127.0.0.1:8722/device_mapping/import -H 'Content-Type: application/json' --data-binary @- | jq .`

Notes for new devices
- Replace names in the template to match Live’s reported parameter names for that device.
- Quantized params (e.g., modes) should list exact display labels. For precise normalized steps, compute medians per label from your presets and update `label_map` later.
- You can repeat Steps 5–7 anytime as more presets are captured.

