# Device Mapping Checklist

Quick reference for mapping a new device. Target: **5-6 hours from start to finish** (includes new structure initialization + audio knowledge).

---

## Pre-Flight (5 min)

- [ ] Load device in Live (Return Track A, Device 0)
- [ ] Device responds to `GET /return/device/params?index=0&device=0`
- [ ] Server and Live connection stable

---

## Phase 0: KB Reconciliation (15 min) - IF manual docs exist

⚠️ **CRITICAL FIRST STEP** - Do NOT skip if you have manual documentation!

### Problem
- [ ] Ableton manual parameter names often DON'T match Live API names
- [ ] Example: Manual says "Early Refl Spin", Live says "ER Spin On"
- [ ] This causes hours of wasted time on incorrect grouping/dependencies

### Reconciliation Process
- [ ] Get actual names: `curl http://127.0.0.1:8722/return/device/params?index=0&device=0 | jq '.data.params[] | .name'`
- [ ] Compare with manual (e.g., `docs/kb/reverb.md`)
- [ ] Create reconciliation table:
  ```markdown
  | Manual Name | Live API Name | Notes |
  |-------------|---------------|-------|
  | ... | ... | ... |
  ```
- [ ] Update KB document with corrected Live API names
- [ ] Add reconciliation table to top of KB document
- [ ] Mark any sections where grouping may be affected by name mismatch

### Time Investment
- [ ] 15 minutes now saves 2-4 hours of debugging later
- [ ] Ensures grouping and dependencies use correct parameter names
- [ ] Prevents "parameter not found" errors

---

## Phase 1: Learning & Capture (30 min)

- [ ] Learn device structure: `POST /return/learn_device`
- [ ] Verify device signature created in Firestore
- [ ] Capture all presets + screenshots: `POST /return/auto_capture_presets`
- [ ] Check status: `GET /return/device/mapping_status`
- [ ] Verify: `preset_count > 35` and each param has 35+ samples
- [ ] Gather device documentation (e.g., `knowledge/ableton-live/audio-effects/delay.md`)
- [ ] Gather manual text with grouping hints (if available)

---

## Phase 2: Initialize Device Structure (30-45 min) **NEW**

### Run Initialization Script
- [ ] `python3 scripts/initialize_device_structure.py --signature <sig> --device-doc knowledge/ableton-live/audio-effects/<device>.md`
- [ ] Script analyzes params + docs and proposes complete structure

### Review Proposed Structure
- [ ] Review `sections` (descriptions, sonic_focus, technical_notes)
- [ ] Review `grouping` (masters, dependents, dependent_master_values, apply_order, requires_for_effect)
- [ ] Review `params_meta` (control_type, **units**, labels, min/max)

### Confirm/Correct Structure
- [ ] **Sections**: Add/remove/rename sections as needed
- [ ] **Grouping**: Correct masters/dependents
- [ ] **Units**: Confirm or change units for each parameter (ms vs s, Hz, dB, %)
- [ ] **Labels**: Confirm quantized parameter labels
- [ ] **Control types**: Correct any misclassified parameters

### Apply Structure
- [ ] Save corrections to `structure_confirmed.json`
- [ ] `python3 scripts/initialize_device_structure.py --signature <sig> --apply structure_confirmed.json`
- [ ] Verify Firestore has `sections`, `grouping`, `params_meta` in main document

---

## Phase 3: Classification & Boundaries (30 min)

For each parameter in `/tmp/device.json`:

### Binary Toggles
- [ ] Name contains "On"?
- [ ] min=0, max=1, display only "0.0" or "1.0"?
- [ ] Mark as `control_type: "binary"`, `labels: ["off", "on"]`

### Quantized Parameters
- [ ] Only 2-5 unique values across all samples?
- [ ] Display values are labels (strings) or evenly-spaced?
- [ ] Mark as `control_type: "quantized"`
- [ ] Create label_map: `{label: normalized_value}`

### Continuous Parameters
- [ ] Everything else
- [ ] Mark as `control_type: "continuous"`
- [ ] Determine min/max display from samples OR probe Live

### Boundary Values
For each continuous param:
- [ ] Check min/max in samples
- [ ] If presets don't cover full range, probe Live:
  - Set param to 0.0, read display_value (= min_display)
  - Set param to 1.0, read display_value (= max_display)
- [ ] Record boundaries for fitting step

---

## Phase 4: Fitting (2 hours)

### For Each Continuous Parameter:

#### Choose Fit Type
- [ ] **Linear** if: uniform increase (percentages, gains)
- [ ] **Exponential** if: wide range (frequencies, times > 100x range)
- [ ] **Piecewise** if: dB values or irregular curve

#### Run Fit Script
- [ ] Copy template from playbook
- [ ] Add parameter name and boundaries
- [ ] **CRITICAL**: Add boundary points to samples
  ```python
  xy_pairs.append((0.0, min_display))
  xy_pairs.append((1.0, max_display))
  ```
- [ ] Run fit
- [ ] Check R² > 0.999 (or R²=1.0 for piecewise)
- [ ] **Verify at boundaries**: predicted values match expected
- [ ] **Test inversion**: given display value, compute x, verify round-trip
- [ ] Update Firestore with fit

#### Common Fit Issues
- [ ] If inverted (min→max, max→min): boundaries in wrong order
- [ ] If low R²: wrong fit type, try different one
- [ ] If boundaries off: didn't include boundary points

### Batch Fitting (Alternative)
- [ ] Run: `make fit-from-presets-apply SIG=<sig>`
- [ ] Review all fits, check R² values
- [ ] Manually fix any params with R² < 0.999
- [ ] Add boundary corrections where presets incomplete

---

## Phase 5: Verify Metadata (30 min)

### Build params_meta
- [ ] All parameters present (check count matches Live)
- [ ] All binary have: `control_type`, `labels`
- [ ] All quantized have: `control_type`, `labels`, `label_map`
- [ ] All continuous have:
  - [ ] `control_type: "continuous"`
  - [ ] `fit: {type, coeffs/points, r2}`
  - [ ] `confidence: <r2>`
  - [ ] `min_display: <float>`
  - [ ] `max_display: <float>`

### Verification Script
```python
params_meta = doc.to_dict().get("params_meta", [])
continuous = [p for p in params_meta if p.get("control_type") == "continuous"]
missing_range = [p["name"] for p in continuous
                 if p.get("min_display") is None or p.get("max_display") is None]
assert len(missing_range) == 0, f"Missing ranges: {missing_range}"
```

- [ ] Run verification
- [ ] Fix any missing fields
- [ ] Update Firestore

---

## Phase 6: Testing (1 hour)

### Test Binary Parameters
For each binary param:
- [ ] Set to "off": `target_display: "off"`
- [ ] Verify: `applied.display = "0.0"` or `"0"`
- [ ] Set to "on": `target_display: "on"`
- [ ] Verify: `applied.display = "1.0"` or `"1"`

### Test Quantized Parameters
For each quantized param:
- [ ] Test each label in label_map
- [ ] Verify: `applied.value` matches expected value from label_map
- [ ] Verify: `applied.display` converts back to label correctly

### Test Continuous Parameters
For each continuous param:
- [ ] Test at **min boundary**: `target_display: "<min_display>"`
  - Verify: `applied.display` ≈ min_display (within 1%)
- [ ] Test at **max boundary**: `target_display: "<max_display>"`
  - Verify: `applied.display` ≈ max_display (within 1%)
- [ ] Test at **midpoint**: calculate mid = (min+max)/2
  - Verify: `applied.display` ≈ mid (within 2%)
- [ ] Test at **quarter points** if exponential (25%, 75%)

### Create Test Script
```python
#!/usr/bin/env python3
"""Test all parameters for <Device>."""
import requests

BASE = "http://127.0.0.1:8722"

# Test binary
def test_binary(param_name):
    for val in ["off", "on"]:
        resp = requests.post(f"{BASE}/op/return/param_by_name", json={
            "return_ref": "0", "device_ref": "<device>",
            "param_ref": param_name, "target_display": val
        }).json()
        print(f"{param_name}={val}: {resp['applied']['display']}")

# Test continuous
def test_continuous(param_name, values):
    for val in values:
        resp = requests.post(f"{BASE}/op/return/param_by_name", json={
            "return_ref": "0", "device_ref": "<device>",
            "param_ref": param_name, "target_display": str(val)
        }).json()
        applied = float(resp['applied']['display'])
        error = abs(applied - val) / val * 100 if val != 0 else 0
        status = "✓" if error < 2 else "✗"
        print(f"{status} {param_name}={val}: applied={applied:.2f} (error={error:.1f}%)")

# Run tests
test_binary("device on")
test_continuous("decay time", [200, 1000, 20000, 60000])
# ... add all params
```

- [ ] Run test script
- [ ] All tests pass (< 2% error)
- [ ] Fix any failing params (refit if needed)

---

## Phase 7: Audio Knowledge Curation (30-60 min) **NEW**

### Research All Parameters
- [ ] Create `data/audio_knowledge/<device>_accurate.json`
- [ ] For each parameter, research from authoritative sources:
  - [ ] Official Ableton documentation
  - [ ] Ableton forum discussions
  - [ ] Technical DSP knowledge
  - [ ] Production blogs (Sound on Sound, Beat Production)

### Structure Audio Knowledge
For each parameter:
- [ ] `audio_function`: Brief technical description
- [ ] `sonic_effect.increasing`: What happens when increasing
- [ ] `sonic_effect.decreasing`: What happens when decreasing
- [ ] `technical_detail`: DSP/algorithm details (optional)
- [ ] `use_cases`: When/why to use (production scenarios)
- [ ] `typical_values`: Value ranges with context

### Quality Check
- [ ] Technically accurate (actual DSP behavior, not vague)
- [ ] Specific (uses precise terms: modulation, filtering, etc.)
- [ ] Contextual (explains *why* and *when* to use)
- [ ] Measurable (numeric ranges, units, typical values)
- [ ] Avoid: vague terms, misleading metaphors, generic descriptions

### Apply to Firestore
- [ ] Dry run: `python3 scripts/apply_audio_knowledge.py data/audio_knowledge/<device>_accurate.json --dry-run`
- [ ] Review changes
- [ ] Apply: `python3 scripts/apply_audio_knowledge.py data/audio_knowledge/<device>_accurate.json`
- [ ] Verify in WebUI tooltips
- [ ] Test chat responses use correct knowledge

---

## Phase 8: Finalization (30 min)

### Backup
- [ ] `make backup-firestore SIG=<sig> OUT=backups/<device>_$(date +%Y%m%d_%H%M%S).json`
- [ ] Verify backup file created
- [ ] Check backup file size reasonable (> 10 KB)

### Documentation
- [ ] Count parameters by type (binary/quantized/continuous)
- [ ] Count fit types (linear/exp/piecewise/log)
- [ ] Document any special parameter behaviors
- [ ] Note any auto-enable dependencies

### Commit
```bash
# Commit device mapping
git add backups/<device>_*.json
git commit -m "feat(devices): complete <Device Name> mapping

- <N> parameters: <B> binary, <Q> quantized, <C> continuous
- All continuous params have fits (<L> linear, <E> exp, <P> piecewise)
- All tested and verified working (< 2% error)
- Signature: <signature>

Closes #<issue-number> (if applicable)"

# Commit audio knowledge
git add data/audio_knowledge/<device>_accurate.json
git commit -m "feat(audio-knowledge): add research-based knowledge for <Device Name>

- Curated knowledge for all <N> parameters
- Sources: Ableton docs, forums, technical DSP knowledge
- Applied to dev-display-value database"
```

- [ ] Both commits created
- [ ] Push to remote

---

## Final Verification

- [ ] **Structure**: `sections`, `grouping`, `params_meta` all complete in Firestore
- [ ] **Parameters**: Total params in params_meta matches Live param count
- [ ] **Fitting**: All continuous params R² > 0.999 (or 1.0 for piecewise)
- [ ] **Ranges**: All continuous params have min_display and max_display
- [ ] **Units**: All parameters have correct units confirmed
- [ ] **Testing**: All params tested and working
- [ ] **Audio Knowledge**: All params have accurate, researched knowledge
- [ ] **Backup**: Mapping and audio knowledge backed up to git
- [ ] Total time: < 6 hours ✅

---

## If Something Goes Wrong

### Fit Inverted
**Symptom:** Min gives max, max gives min

**Fix:**
```python
# Ensure boundary points correct order
xy_pairs = [(0.0, MIN_DISPLAY), (1.0, MAX_DISPLAY)] + samples
```

### Low R²
**Symptom:** R² < 0.99

**Fix:**
- Try different fit type (linear ↔ exponential)
- Or use piecewise linear (always R²=1.0)

### Parameter Not Working
**Symptom:** Set value doesn't match applied value

**Debug:**
1. Check fit type in Firestore
2. Check coefficients not NaN/Infinity
3. Test inversion manually
4. Refit with boundary points

### Missing Parameters
**Symptom:** Param count doesn't match Live

**Fix:**
- Check for "Device On" (often missing)
- Compare Live param list with params_meta
- Add missing params manually

### Data Loss
**Symptom:** Updating one param deleted others

**Fix:**
- **NEVER** replace params_meta array
- **ALWAYS** read existing, update specific param, write back entire array
```python
params_meta = doc.to_dict().get("params_meta", [])
for param in params_meta:
    if param.get("name") == TARGET:
        param.update(new_data)  # Merge!
doc_ref.update({"params_meta": params_meta})
```

---

## Time Tracking

Use this to stay on target:

| Phase | Target | Actual | Notes |
|-------|--------|--------|-------|
| Pre-flight | 5 min | __ | |
| KB Reconciliation | 15 min | __ | IF manual docs exist |
| Learning & Capture | 30 min | __ | |
| **Initialize Structure** | **30-45 min** | __ | **NEW** |
| Classification & Boundaries | 30 min | __ | |
| Fitting | 2 hours | __ | |
| Verify Metadata | 30 min | __ | |
| Testing | 1 hour | __ | |
| **Audio Knowledge** | **30-60 min** | __ | **NEW** |
| Finalization | 30 min | __ | |
| **TOTAL** | **5.5-6.5 hours** | __ | |

**Target: < 6.5 hours for complete mapping** (includes new structure + audio knowledge phases)
