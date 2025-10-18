# Device Mapping Playbook

**Goal**: Map any Ableton Live device from scratch to completion in ~4 hours

**What we achieved with Reverb**: 33 parameters fully mapped in 3 days (learning as we went)

**Target for future devices**: Complete mapping in 4 hours using this playbook

---

## Overview

Device mapping creates a bidirectional translation between:
- **Live's normalized values** (0.0 to 1.0)
- **Display values** (user-friendly units like Hz, dB, %, ms)

This enables NLP commands like "set reverb decay to 5 seconds" to work accurately.

---

## Phase 0: Knowledge Base Reconciliation (15 min) - CRITICAL

### 0.1 Obtain Ableton Manual Section

If you have the Ableton Live manual section for the device (e.g., `docs/kb/reverb.md`):

**⚠️ CRITICAL ISSUE**: Parameter names in Ableton's manual often DO NOT match the actual parameter names returned by Live's API.

### 0.2 Reconcile Parameter Names

**Problem discovered with Reverb:**
- Manual uses different names than what Live API returns
- This caused significant confusion in initial grouping and dependency mapping
- Wasted substantial time trying to match mismatched names

**Solution - Name Reconciliation Process:**

1. **Get actual parameter names from Live first:**
   ```bash
   curl http://127.0.0.1:8722/return/device/params?index=0&device=0 | jq '.data.params[] | .name'
   ```

2. **Create reconciliation table:**
   | Manual Name | Live API Name | Notes |
   |-------------|---------------|-------|
   | Example: "Early Refl Spin" | "ER Spin On" | Manual abbreviates |
   | Example: "Reflection Level" | "Reflect Level" | Manual uses full word |

3. **Update knowledge base document:**
   - Create corrected version with actual Live parameter names
   - Add reconciliation table at top of document
   - Mark any parameters where manual grouping may be incorrect due to name mismatch

4. **Only then proceed with grouping/dependency analysis**

**Why this matters:**
- Grouping parameters requires matching names exactly
- Master/dependent relationships need accurate parameter references
- Mismatched names lead to incorrect dependency mapping
- Wastes hours debugging why parameters "don't exist"

**Time saved by doing this first:** 2-4 hours of debugging and rework

---

## Phase 1: Device Learning & Preset Capture (30 min)

### 1.1 Load Device in Live
- Add device to Return Track A (index 0), Device 0
- Verify via: `GET /return/device/params?index=0&device=0`

### 1.2 Capture Device Signature & Structure
```bash
# Learn the device (captures parameter structure)
POST /return/learn_device
{
  "return_index": 0,
  "device_index": 0
}
```

**What this creates in Firestore:**
```json
{
  "device_name": "Reverb",
  "signature": "64ccfc...",
  "param_count": 33,
  "param_names": ["Device On", "Predelay", ...],
  "device_type": "unknown",
  "groups": []  // Empty - will populate in Phase 2
}
```

**Plus params subcollection** (`device_mappings/<sig>/params/<param_name>`):
- Basic param metadata (name, index, min, max)
- Empty samples array (filled in next step)
- Null control_type, unit, fit (populated later)

### 1.3 Load and Capture Factory Presets
```bash
# Capture all factory presets (auto-discovers them)
POST /return/auto_capture_presets
{
  "return_index": 0,
  "device_index": 0
}
```

**What this captures:**
- For EACH factory preset:
  - All parameter normalized values (0-1)
  - All parameter display values (strings from Live)
  - Screenshot of device (stored in GCS, linked to preset)
- Stores as `samples` array in Firestore `params` subcollection
- Typically 40-50 samples per parameter

**Verification:**
```bash
# Check we got presets
GET /return/device/mapping_status?index=0&device=0
```

Should show:
- `learned: true`
- `preset_count: 40+`
- Each param should have 40+ samples

### 1.4 Gather Device Documentation
You provide:
- Device documentation file (e.g., `knowledge/ableton-live/audio-effects/delay.md`)
- Manual text sections with grouping hints
- Any known parameter relationships (master/dependent)

**What you need to provide:**
- Technical descriptions of parameter groups
- Expected units for parameters (ms, Hz, dB, %)
- Special behaviors or dependencies

---

## Phase 2: Initialize Device Structure (30-45 min)

**NEW: This phase converts learn_device output to complete Reverb-style format**

### 2.1 Run Structure Initialization Script

```bash
# Initialize device structure with proposed sections/grouping
python3 scripts/initialize_device_structure.py \
  --signature <device_signature> \
  --device-doc knowledge/ableton-live/audio-effects/<device>.md \
  --manual-text "Optional manual text with grouping hints"
```

**What this script does:**
1. Reads params from subcollection (with samples)
2. Analyzes device doc + manual text for grouping hints
3. Proposes complete structure:
   - `sections` (with descriptions, sonic_focus, technical_notes)
   - `grouping` (masters, dependents, dependent_master_values, apply_order, requires_for_effect)
   - `params_meta` (with proposed control_type, unit, labels)
4. **Outputs JSON for your review**

### 2.2 Review Proposed Structure

The script outputs a JSON proposal like this:

```json
{
  "device_name": "Delay",
  "signature": "abc123...",
  "sections": {
    "Device": {
      "technical_name": "Device",
      "description": "Device on/off control",
      "sonic_focus": "Enable or disable the entire effect",
      "parameters": ["Device On"],
      "technical_notes": []
    },
    "Delay Timing": {
      "technical_name": "Delay Timing",
      "description": "Control delay time and synchronization",
      "sonic_focus": "Rhythmic timing of echoes",
      "parameters": ["Delay Time", "Sync Mode", "Time Unit"],
      "technical_notes": ["Sync Mode syncs delay to project tempo"]
    }
  },
  "grouping": {
    "masters": ["Sync Mode", "Filter On"],
    "dependents": {
      "Filter Freq": "Filter On",
      "Filter Q": "Filter On"
    },
    "dependent_master_values": {
      "Filter Freq": 1.0,
      "Filter Q": 1.0
    },
    "apply_order": ["masters", "quantized", "dependents", "continuous"]
  },
  "params_meta": [
    {
      "name": "Delay Time",
      "index": 1,
      "control_type": "continuous",
      "unit": "ms",  // ← CONFIRM THIS
      "min_display": 0.1,
      "max_display": 10000.0
    },
    {
      "name": "Filter Type",
      "index": 5,
      "control_type": "quantized",
      "unit": null,
      "labels": ["Low-pass", "High-pass", "Band-pass"]
    }
  ]
}
```

### 2.3 Confirm or Correct Structure

**You respond with corrections:**
- Sections: Add/remove/rename sections
- Grouping: Correct masters/dependents
- **Units**: Confirm or change units for each parameter
- Labels: Confirm quantized parameter labels
- Control types: Correct any misclassified parameters

**Example corrections:**
```
Changes needed:
1. Delay Time unit should be "s" not "ms"
2. Add "Stereo" section with Width, Pan Left, Pan Right
3. Remove "Time Unit" from masters (it's just a display preference)
4. Add requires_for_effect: Sync Rate needs Sync Mode = On
```

### 2.4 Apply Confirmed Structure

```bash
# Apply your confirmed structure to Firestore
python3 scripts/initialize_device_structure.py \
  --signature <device_signature> \
  --apply structure_confirmed.json
```

**What this updates in Firestore:**
- Adds `sections` to main document
- Adds `grouping` to main document
- Creates `params_meta` array in main document (NOT subcollection)
- Params subcollection remains for fitting reference

---

## Phase 3: Parameter Classification & Boundary Detection (30 min)

**Now that structure is confirmed, classify parameters and detect boundaries**

### 3.1 Review All Parameters

Get current state from Live:
```bash
curl http://127.0.0.1:8722/return/device/params?index=0&device=0 | jq .
```

For each parameter, classify as (already proposed in Phase 2, now verify):

#### **Binary Toggle** (on/off, 0.0/1.0)
- Examples: "Device On", "Chorus On", "Filter On"
- Criteria:
  - min=0.0, max=1.0
  - display_value is "0.0" or "1.0"
  - Name contains "On"

#### **Quantized** (discrete labeled values)
- Examples: "Filter Type" (Shelving/Low-pass), "Density" (Sparse/Low/Mid/High)
- Criteria:
  - Fixed number of distinct values
  - Display values are labels (strings) or evenly-spaced numbers
  - Check samples: if only 2-4 unique values across 40 presets → quantized

#### **Continuous** (needs curve fitting)
- Everything else: frequencies, times, levels, gains, amounts
- Needs mathematical fit to map 0-1 → display range

### 2.2 Determine Boundary Values

For each continuous parameter, get min/max display values:

**Method 1: From samples**
```python
# Check preset samples
samples = param.get("samples", [])
display_vals = [s["display_num"] for s in samples]
min_val = min(display_vals)
max_val = max(display_vals)
```

**Method 2: Probe directly**
```bash
# Set to 0.0, read back
POST /op/return/device/param {"return_index": 0, "device_index": 0, "param_index": X, "value": 0.0}
GET /return/device/params?index=0&device=0  # Read display_value

# Set to 1.0, read back
POST /op/return/device/param {"return_index": 0, "device_index": 0, "param_index": X, "value": 1.0}
```

**Method 3: Check Live documentation**
- Sometimes boundaries aren't in presets
- Example: Reverb Room Size went 0.22-500m, but presets only covered subset

---

## Phase 4: Fit Continuous Parameters (2 hours)

### 3.1 Choose Fit Type

For each continuous parameter, determine the best fit:

#### **Linear Fit**: `y = a*x + b`
**Use when:** Display values increase uniformly
- Examples: percentages (0-100%), linear gains, stereo width
- Test: Plot samples, look for straight line
- R² threshold: > 0.999

#### **Exponential Fit**: `y = a * exp(b*x)`
**Use when:** Wide range, exponential growth
- Examples: frequencies (20-20000 Hz), time (0.5-250 ms), decay (200-60000 ms)
- Characteristic: Each doubling of x roughly doubles y
- R² threshold: > 0.999

#### **Piecewise Linear Fit**
**Use when:** Non-linear relationship that can't be modeled with single formula
- Examples: dB levels (already logarithmic), volume faders
- Uses 40+ (x,y) points, interpolates between them
- Always R² = 1.0 (passes through all points exactly)
- Slower than parametric fits but always accurate

#### **Log Fit**: `y = a*ln(x) + b`
**Rarely needed** - most "logarithmic" params are better fit with exponential or piecewise

### 3.2 Run Fitting Script

Create fitting script (use `/tmp/refit_<param>.py` pattern):

```python
#!/usr/bin/env python3
import sys, math, os
os.environ["FIRESTORE_DATABASE_ID"] = "dev-display-value"
sys.path.insert(0, '/Users/sunils/ai-projects/fadebender')

from server.services.mapping_store import MappingStore

def fit_exp(xs, ys):
    """Fit y = a * exp(b*x) using log linearization"""
    n = len(xs)
    if n < 3:
        return None

    # ln(y) = ln(a) + b*x
    lnys = [math.log(max(y, 1e-9)) for y in ys]

    sx = sum(xs)
    sy = sum(lnys)
    sxx = sum(x*x for x in xs)
    sxy = sum(x*lny for x, lny in zip(xs, lnys))

    denom = n * sxx - sx * sx
    if abs(denom) < 1e-9:
        return None

    b = (n * sxy - sx * sy) / denom
    ln_a = (sy - b * sx) / n
    a = math.exp(ln_a)

    # Calculate R²
    y_pred = [a * math.exp(b * x) for x in xs]
    ybar = sum(ys) / n
    ss_tot = sum((y - ybar)**2 for y in ys)
    ss_res = sum((y - yp)**2 for y, yp in zip(ys, y_pred))
    r2 = 1.0 - (ss_res / ss_tot) if ss_tot > 0 else 0.0

    return a, b, r2, y_pred

def main():
    store = MappingStore()
    sig = "YOUR_DEVICE_SIGNATURE"

    old_map = store.get_device_map(sig)
    param = next((p for p in old_map["params"] if p.get("name") == "PARAM_NAME"), None)

    samples = param.get("samples", [])
    xy_pairs = [(s["value"], s["display_num"]) for s in samples
                if s.get("value") is not None and s.get("display_num") is not None]

    # CRITICAL: Add boundary points
    xy_pairs.append((0.0, MIN_DISPLAY))
    xy_pairs.append((1.0, MAX_DISPLAY))

    xy_pairs = sorted(set(xy_pairs), key=lambda p: p[0])

    xs = [p[0] for p in xy_pairs]
    ys = [p[1] for p in xy_pairs]

    a, b, r2, y_pred = fit_exp(xs, ys)

    print(f"Exponential fit: y = {a:.10f} * exp({b:.10f} * x)")
    print(f"R² = {r2:.10f}")

    # VERIFY at boundaries
    y_at_0 = a * math.exp(b * 0.0)
    y_at_1 = a * math.exp(b * 1.0)
    print(f"At x=0.0: predicted={y_at_0:.3f}, expected={MIN_DISPLAY}")
    print(f"At x=1.0: predicted={y_at_1:.3f}, expected={MAX_DISPLAY}")

    # TEST INVERSION (this is what server does)
    for test_y in [MIN_DISPLAY, 100, 1000, MAX_DISPLAY]:
        test_x = math.log(test_y / a) / b if (a != 0 and b != 0 and test_y > 0) else 0.0
        verify_y = a * math.exp(b * test_x)
        print(f"y={test_y} -> x={test_x:.6f} -> verify_y={verify_y:.3f}")

    # Update Firestore
    from google.cloud import firestore
    client = firestore.Client(database="dev-display-value")
    doc_ref = client.collection("device_mappings").document(sig)
    doc = doc_ref.get()
    data = doc.to_dict()
    params_meta = data.get("params_meta", [])

    for param in params_meta:
        if param.get("name") == "PARAM_NAME":
            param["fit"] = {
                "type": "exp",
                "coeffs": {"a": a, "b": b},
                "r2": r2
            }
            param["confidence"] = r2
            param["min_display"] = MIN_DISPLAY
            param["max_display"] = MAX_DISPLAY
            break

    doc_ref.update({"params_meta": params_meta})
    print("✓ Saved to Firestore")

if __name__ == "__main__":
    sys.exit(main())
```

**Key Points:**
1. **ALWAYS add boundary points** - presets may not cover full range
2. **Verify at boundaries** - predicted vs expected must match
3. **Test inversion** - this is what server does when user sets value
4. **Check R²** - should be > 0.999 for good fit

### 3.3 Batch Fit All Continuous Parameters

Use `fit_params_from_presets.py`:
```bash
# Fit all continuous params at once
python3 scripts/fit_params_from_presets.py --signature <SIG> --import
```

This will:
- Auto-detect fit type (linear/exp) for each param
- Fit all continuous params
- Import to Firestore

**BUT**: You'll need to manually add boundaries afterwards for any params where presets didn't cover full range.

---

## Phase 5: Verify and Test Mappings (1 hour)

### 5.1 Verify params_meta Completeness

**NOTE:** params_meta was already created in Phase 2 and updated with fits in Phase 4.
Now verify all fields are complete:

**Binary parameter:**
```json
{
  "name": "Chorus On",
  "index": 17,
  "control_type": "binary",
  "labels": ["off", "on"]
}
```

**Quantized parameter:**
```json
{
  "name": "Density",
  "index": 29,
  "control_type": "quantized",
  "labels": ["Sparse", "Low", "Mid", "High"],
  "label_map": {
    "Sparse": 0.0,
    "Low": 1.0,
    "Mid": 2.0,
    "High": 3.0
  }
}
```

**Continuous parameter:**
```json
{
  "name": "Decay Time",
  "index": 20,
  "control_type": "continuous",
  "fit": {
    "type": "exp",
    "coeffs": {
      "a": 200.0734297468,
      "b": 5.7032621663
    },
    "r2": 0.9999999776
  },
  "confidence": 0.9999999776,
  "min_display": 200.0,
  "max_display": 60000.0
}
```

**Piecewise parameter:**
```json
{
  "name": "Reflect Level",
  "index": 30,
  "control_type": "continuous",
  "fit": {
    "type": "piecewise",
    "points": [
      {"x": 0.0, "y": -30.0},
      {"x": 0.025, "y": -22.0},
      ...
      {"x": 1.0, "y": 6.0}
    ],
    "r2": 1.0
  },
  "confidence": 1.0,
  "min_display": -30.0,
  "max_display": 6.0
}
```

### 4.2 Add All Parameters

Script to create complete params_meta:
```python
#!/usr/bin/env python3
"""Create complete params_meta for device."""
import sys, os
os.environ["FIRESTORE_DATABASE_ID"] = "dev-display-value"
sys.path.insert(0, '/Users/sunils/ai-projects/fadebender')

from google.cloud import firestore

sig = "YOUR_DEVICE_SIGNATURE"
client = firestore.Client(database="dev-display-value")
doc_ref = client.collection("device_mappings").document(sig)

# Get existing data
doc = doc_ref.get()
data = doc.to_dict()
params_meta = data.get("params_meta", [])

# Ensure all parameters are present with correct metadata
# (Binary, quantized, continuous with fits and ranges)

# Update Firestore
doc_ref.update({"params_meta": params_meta})
print(f"✓ Updated params_meta with {len(params_meta)} parameters")
```

### 4.3 Verify Completeness

Check all parameters have required fields:
```python
# All continuous must have:
- control_type: "continuous"
- fit: {type, coeffs or points, r2}
- confidence: <r2 value>
- min_display: <float>
- max_display: <float>

# All binary must have:
- control_type: "binary"
- labels: ["off", "on"]

# All quantized must have:
- control_type: "quantized"
- labels: [...]
- label_map: {label: value}
```

---

## Phase 6: Testing & Validation (1 hour)

### 5.1 Test Each Parameter Type

**Binary:**
```bash
curl -X POST http://127.0.0.1:8722/op/return/param_by_name \
  -H "Content-Type: application/json" \
  -d '{"return_ref": "0", "device_ref": "DEVICE", "param_ref": "chorus on", "target_display": "on"}'
# Verify: applied.display = "1.0"

curl -X POST http://127.0.0.1:8722/op/return/param_by_name \
  -H "Content-Type: application/json" \
  -d '{"return_ref": "0", "device_ref": "DEVICE", "param_ref": "chorus on", "target_display": "off"}'
# Verify: applied.display = "0.0"
```

**Quantized:**
```bash
# Test each label
curl -X POST http://127.0.0.1:8722/op/return/param_by_name \
  -H "Content-Type: application/json" \
  -d '{"return_ref": "0", "device_ref": "DEVICE", "param_ref": "density", "target_display": "Low"}'
# Verify: applied.value matches label_map["Low"]
```

**Continuous:**
```bash
# Test at boundaries
curl -X POST http://127.0.0.1:8722/op/return/param_by_name \
  -H "Content-Type: application/json" \
  -d '{"return_ref": "0", "device_ref": "DEVICE", "param_ref": "decay", "target_display": "200"}'
# Verify: applied.display ≈ 200 (min)

curl -X POST http://127.0.0.1:8722/op/return/param_by_name \
  -H "Content-Type: application/json" \
  -d '{"return_ref": "0", "device_ref": "DEVICE", "param_ref": "decay", "target_display": "60000"}'
# Verify: applied.display ≈ 60000 (max)

# Test at mid-points
curl -X POST http://127.0.0.1:8722/op/return/param_by_name \
  -H "Content-Type: application/json" \
  -d '{"return_ref": "0", "device_ref": "DEVICE", "param_ref": "decay", "target_display": "1000"}'
# Verify: applied.display ≈ 1000
```

### 5.2 Common Issues & Fixes

#### Issue: Inverted Fit
**Symptom:** Setting min value gives max, setting max value gives min

**Cause:** Fit was done in wrong direction (y→x instead of x→y)

**Fix:** Refit with boundary points in correct order:
```python
xy_pairs.append((0.0, MIN_DISPLAY))  # x=0 should give MIN
xy_pairs.append((1.0, MAX_DISPLAY))  # x=1 should give MAX
```

#### Issue: Wrong Fit Type
**Symptom:** Low R² (< 0.99), or accurate at boundaries but wrong in middle

**Cause:** Used linear fit for exponential data, or vice versa

**Fix:**
- Try other fit type
- Or use piecewise linear (always works but slower)

#### Issue: Boundary Mismatch
**Symptom:** Setting to min/max gives value slightly off

**Cause:** Boundary points not included in fit

**Fix:** Always explicitly add boundary points before fitting

#### Issue: Missing Parameters
**Symptom:** Some params not in params_meta

**Cause:** Device On often excluded, or params added during fitting script runs

**Fix:** Manually add missing params to params_meta

---

## Phase 7: Audio Knowledge Curation (30-60 min)

### 7.1 Research All Parameters

Use the research-based audio knowledge curation approach (see `docs/methodology/AUDIO_KNOWLEDGE_CURATION.md`).

**Create device audio knowledge JSON:**

```bash
# Create data/audio_knowledge/<device>_accurate.json
```

**Structure:**

```json
{
  "device_name": "<Device Name>",
  "device_signature": "<firestore_doc_id>",
  "source": "Researched from Ableton forums, official docs, technical DSP knowledge",
  "last_updated": "YYYY-MM-DD",
  "parameters": {
    "<Param Name>": {
      "audio_function": "Brief technical description of what parameter controls",
      "sonic_effect": {
        "increasing": "Precise description when increasing",
        "decreasing": "Precise description when decreasing"
      },
      "technical_detail": "DSP/algorithm details (optional)",
      "use_cases": [
        "When and why to use this parameter",
        "Production scenarios"
      ],
      "typical_values": {
        "label": "Value range with context"
      }
    }
  }
}
```

### 7.2 Research Sources

For each parameter, gather information from:

**Primary Sources (Best):**

- Official Ableton documentation
- Ableton forum discussions with staff/experts
- Technical audio DSP textbooks

**Secondary Sources (Good):**

- Reputable production blogs (Sound on Sound, Beat Production, etc.)
- Expert tutorials and courses
- Industry-standard algorithm references

**Avoid:**

- Generic LLM generation without research
- Unverified forum speculation
- Marketing copy without technical substance

### 7.3 Quality Guidelines

**✅ Good Audio Knowledge:**

- Technically accurate (describes actual DSP/algorithm behavior)
- Specific (uses precise terms: modulation, filtering, compression ratio)
- Contextual (explains *why* and *when* to use parameter)
- Measurable (includes numeric ranges, units, typical values)

**❌ Poor Audio Knowledge:**

- Vague ("Makes it sound better/worse")
- Metaphorical without substance ("Spinning," "warming," "opening up")
- Generic (could apply to any parameter)
- Misleading (uses wrong technical terms)

### 7.4 Apply Audio Knowledge to Firestore

```bash
# Preview changes (dry run)
python3 scripts/apply_audio_knowledge.py data/audio_knowledge/<device>_accurate.json --dry-run

# Apply all parameters
python3 scripts/apply_audio_knowledge.py data/audio_knowledge/<device>_accurate.json

# Apply single parameter
python3 scripts/apply_audio_knowledge.py data/audio_knowledge/<device>_accurate.json --param "<Param Name>"
```

### 7.5 Verify in WebUI

- Check tooltips show accurate information
- Test chat responses reference correct knowledge
- Verify parameter descriptions are helpful

---

## Phase 8: Documentation & Backup (30 min)

### 8.1 Backup to Git

```bash
# Backup the mapping
make backup-firestore SIG=<signature> OUT=backups/device_$(date +%Y%m%d_%H%M%S).json

# Commit device mapping
git add backups/device_*.json
git commit -m "feat(devices): complete mapping for <Device Name>

- 33 parameters: 10 binary, 3 quantized, 20 continuous
- All continuous params have fits (9 exp, 9 linear, 2 piecewise)
- All tested and verified working
- Signature: <signature>"

# Commit audio knowledge
git add data/audio_knowledge/<device>_accurate.json
git commit -m "feat(audio-knowledge): add research-based knowledge for <Device Name>

- Curated knowledge for all <N> parameters
- Sources: Ableton docs, forums, technical DSP knowledge
- Applied to dev-display-value database"
```

### 8.2 Document Special Cases

Create docs entry if device has:
- Non-standard parameter interactions
- Parameters that require special handling
- Auto-enable dependencies (e.g., ER Spin Rate requires ER Spin On)
- Parameters with unusual ranges or behaviors

---

## Common Pitfalls & Solutions

### Pitfall 0: Using Manual Parameter Names Without Reconciliation (CRITICAL)
**Result:** Hours wasted on incorrect grouping, "parameter not found" errors, wrong dependencies

**What happened with Reverb:**
- Manual documentation had different parameter names than Live API
- Spent significant time trying to map dependencies with wrong names
- Example: Manual "Early Refl Spin" vs Live API "ER Spin On"
- Caused confusion in initial grouping and master/dependent relationships

**Solution:**
- ALWAYS get actual parameter names from Live first: `GET /return/device/params`
- Create reconciliation table between manual names and Live API names
- Update KB documentation with corrected names BEFORE any grouping work
- 15 minutes of reconciliation saves 2-4 hours of debugging

### Pitfall 1: Not Adding Boundary Points
**Result:** Fits work in middle range but fail at extremes

**Solution:** ALWAYS add (0.0, min_display) and (1.0, max_display) to samples before fitting

### Pitfall 2: Trusting Preset Ranges
**Result:** Boundaries incorrect because presets don't use full parameter range

**Solution:** Manually verify min/max by setting param to 0.0 and 1.0 in Live

### Pitfall 3: Wrong Fit Type
**Result:** Low R² or inaccurate mid-range values

**Solution:**
- Plot the data first (look at samples)
- Frequencies/times usually exponential
- Percentages/gains usually linear
- dB values use piecewise

### Pitfall 4: Not Testing Inversion
**Result:** Fit looks good but server can't invert it correctly

**Solution:** Always test inversion in your fitting script:
```python
# Given display value, compute normalized value, verify round-trip
test_x = invert_fit(test_y)
verify_y = apply_fit(test_x)
assert abs(verify_y - test_y) < 0.01
```

### Pitfall 5: Replacing params_meta Instead of Merging
**Result:** Data loss - other params disappear

**Solution:** Always read existing params_meta, update specific params, write back entire array:
```python
params_meta = data.get("params_meta", [])
for param in params_meta:
    if param.get("name") == TARGET_NAME:
        param.update(new_data)  # Merge, don't replace
doc_ref.update({"params_meta": params_meta})
```

---

## Time Budget (5-6 hours total)

0. **Knowledge Base Reconciliation** (15 min) - IF manual documentation available
   - Get actual param names from Live
   - Create reconciliation table
   - Update KB document with correct names
   - **CRITICAL**: Do this BEFORE any grouping/dependency work

1. **Device Learning & Preset Capture** (30 min)
   - Load device, learn structure
   - Capture all factory presets + screenshots
   - Gather device documentation
   - Verify we have good sample coverage

2. **Initialize Device Structure** (30-45 min) - **NEW**
   - Run initialization script with device docs
   - Review proposed sections, grouping, params_meta
   - Confirm or correct structure (units, grouping, labels)
   - Apply confirmed structure to Firestore

3. **Parameter Classification & Boundary Detection** (30 min)
   - Verify auto-classified parameters
   - Detect boundaries for continuous params
   - Probe Live for missing boundaries

4. **Fit Continuous Parameters** (2 hours)
   - Choose fit types
   - Run fitting scripts with boundary points
   - Verify R² > 0.999
   - Test inversions

5. **Verify and Test Mappings** (1 hour)
   - Verify params_meta completeness
   - Test each parameter type
   - Test boundaries and mid-points
   - Fix any issues

6. **Testing & Validation** (1 hour)
   - Test all parameters (binary/quantized/continuous)
   - Verify all params work correctly
   - Fix any edge cases

7. **Audio Knowledge Curation** (30-60 min) - **NEW**
   - Research all parameters from authoritative sources
   - Create audio_knowledge JSON
   - Apply to Firestore
   - Verify in WebUI

8. **Documentation & Backup** (30 min)
   - Backup to git
   - Commit device mapping
   - Commit audio knowledge
   - Document special cases

**Total: 5.5-6.5 hours**  (includes new structure initialization + audio knowledge phases)

**Note**: Phase 0 saves 2-4 hours of debugging time later. Phases 2 and 7 are new but streamline the overall process.

---

## Scripts & Tools

### Key Scripts

**NEW - Device Structure:**

- `scripts/initialize_device_structure.py` - **NEW** - Convert learn_device output to complete Reverb-style format (sections, grouping, params_meta)

**NEW - Audio Knowledge:**

- `scripts/apply_audio_knowledge.py` - **NEW** - Apply curated audio knowledge from JSON to Firestore
- `scripts/update_audio_knowledge.py` - Experimental LLM-assisted research tool

**Existing - Parameter Fitting:**

- `scripts/fit_params_from_presets.py` - Auto-fit all continuous params
- `scripts/export_signature_digest.py` - Export mapping for analysis
- `scripts/import_mapping_analysis.py` - Import corrected mapping
- `scripts/backup_firestore_mapping.py` - Backup device mapping

### Key Make Targets
```bash
make backup-firestore SIG=<sig> OUT=<file>  # Backup mapping
make export-digest SIG=<sig> OUT=<file>     # Export for analysis
make import-mapping FILE=<file>             # Import mapping
make fit-from-presets-apply SIG=<sig>       # Fit and import
```

### Key API Endpoints
```bash
POST /return/learn_device                   # Learn device structure
POST /return/auto_capture_presets          # Capture all presets
GET  /return/device/mapping_status         # Check mapping status
POST /op/return/param_by_name              # Set param by display value
GET  /return/device/params                 # Get all params from Live
```

---

## Success Criteria

A device mapping is complete when:

✅ **Structure** - Complete Reverb-style format:
  - `sections` with descriptions, sonic_focus, technical_notes
  - `grouping` with masters, dependents, dependent_master_values, apply_order
  - `params_meta` array in main document (not subcollection)

✅ **Parameters** - All params in params_meta (33 for Reverb):
  - All binary params have labels
  - All quantized params have label_map
  - All continuous params have fit, confidence, min_display, max_display
  - All units confirmed and correct

✅ **Fitting** - All continuous params:
  - fit (type, coeffs/points, r2)
  - confidence > 0.999
  - min_display and max_display

✅ **Testing** - All parameters tested:
  - All parameters tested at min/mid/max values
  - All test results within 1% of target
  - No missing or incorrectly classified params

✅ **Audio Knowledge** - All params have accurate knowledge:
  - audio_function (technical description)
  - sonic_effect (increasing/decreasing)
  - technical_detail, use_cases, typical_values (when applicable)
  - Researched from authoritative sources

✅ **Documentation** - Complete backup and commits:
  - Mapping backed up to git
  - Device mapping committed
  - Audio knowledge JSON committed
  - Special cases documented

---

## Example: Quick Mapping Workflow

```bash
# 1. Learn device (5 min)
curl -X POST http://127.0.0.1:8722/return/learn_device \
  -d '{"return_index": 0, "device_index": 0}'

# 2. Capture presets (10 min)
curl -X POST http://127.0.0.1:8722/return/auto_capture_presets \
  -d '{"return_index": 0, "device_index": 0}'

# 3. Check status
curl http://127.0.0.1:8722/return/device/mapping_status?index=0&device=0

# 4. Get device signature from response, export for analysis
make export-digest SIG=<signature> OUT=/tmp/device.json

# 5. Review /tmp/device.json, classify all params

# 6. Fit all continuous params
make fit-from-presets-apply SIG=<signature>

# 7. Add boundaries manually where needed (create script)
python3 /tmp/fix_boundaries.py

# 8. Add binary/quantized manually (create script)
python3 /tmp/add_binary_quantized.py

# 9. Test all params (create test script)
python3 /tmp/test_all_params.py

# 10. Backup
make backup-firestore SIG=<signature> OUT=backups/device_$(date +%Y%m%d).json

# 11. Commit
git add backups/ && git commit -m "feat(devices): complete <Device> mapping"
```

---

## Next Steps

After completing a device:
1. Update device count in project docs
2. Share learnings about unusual parameter types
3. Improve auto-fitting scripts based on issues encountered
4. Consider automating more of the classification step
