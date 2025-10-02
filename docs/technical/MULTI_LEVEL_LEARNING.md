# Multi-Level Device Learning Strategy

## Overview

A three-tier learning system that separates device structure from parameter values, enabling fast preset loading and user customization.

## Architecture

### Level 1: Structure Learning (One-Time)
**Purpose:** Learn parameter mapping (value ↔ display) for the device type

**What's Learned:**
- Parameter structure (count, names, order)
- Fit models (LINEAR, EXPONENTIAL, PIECEWISE) for each parameter
- Control types (continuous, binary, quantized)
- Grouping (masters/dependents)
- Label maps for binary/enum parameters

**Signature:** `SHA1(param_count|param_names)` - NO device name!

**Stored As:**
```
~/.fadebender/param_maps/structures/
└── abc123def456.json  # Structure signature
    {
      "device_type": "reverb",  # Detected from params
      "param_count": 33,
      "params": [
        {
          "name": "Decay Time",
          "index": 20,
          "fit": {"model": "LINEAR", "r2": 0.998, ...},
          "control_type": "continuous",
          ...
        }
      ],
      "groups": [...],
      "learned_from": "Reverb (default)"
    }
```

### Level 2: Preset Variations (Quick Load)
**Purpose:** Capture parameter values for known presets

**What's Stored:**
- Parameter values only (not mappings)
- Preset metadata (name, category, use-case)
- References structure signature

**Stored As:**
```
~/.fadebender/param_maps/presets/reverb/
├── arena_tail.json
├── vocal_hall.json
├── plate.json
└── bright_chamber.json

# Example: arena_tail.json
{
  "name": "Arena Tail",
  "structure_signature": "abc123def456",
  "category": "reverb",
  "use_case": ["vocals", "large_space"],
  "parameter_values": {
    "Decay Time": 3.5,
    "Predelay": 25,
    "Dry/Wet": 0.3,
    ...
  }
}
```

### Level 3: User-Defined Settings
**Purpose:** Save user modifications

**Stored As:**
```
~/.fadebender/param_maps/presets/reverb/user/
├── my_vocal_reverb.json
├── tight_drum_room.json
└── arena_tail_modified.json

# Created when user:
# 1. Loads "Arena Tail"
# 2. Tweaks Decay Time or other params
# 3. Saves as new preset
```

## Workflows

### Initial Setup (Developer/Power User)

**1. Learn Structure Once:**
```bash
# Learn any Ableton Reverb (e.g., default "Reverb")
POST /return/device/learn_quick {"return_index":0,"device_index":0}
→ Creates structure signature abc123...
→ Saves to structures/abc123.json
```

**2. Capture All Presets:**
```bash
# For each Ableton Reverb preset:
# 1. Load preset in Live (e.g., "Arena Tail")
# 2. Capture parameter values
POST /return/device/capture_preset {"return_index":0,"device_index":0,"preset_name":"Arena Tail"}
→ Reads all parameter values
→ Saves to presets/reverb/arena_tail.json
→ Links to structure abc123...
```

**3. Package for Users:**
```
fadebender/presets/
├── structures/
│   └── reverb_ableton.json  # Renamed from abc123... for clarity
└── reverb/
    ├── arena_tail.json
    ├── vocal_hall.json
    ├── plate.json
    └── ...
```

### End-User Experience

**Using Presets (No Learning Required):**
```bash
# User loads "Arena Tail" preset
POST /return/device/apply_preset {
  "return_index": 0,
  "device_index": 0,
  "preset_name": "arena_tail"
}

# System:
# 1. Checks device signature → matches reverb structure ✅
# 2. Loads arena_tail.json parameter values
# 3. Applies using existing structure mapping
# 4. Done in <1 second!
```

**Creating Custom Presets:**
```bash
# User tweaks and saves
POST /return/device/save_preset {
  "return_index": 0,
  "device_index": 0,
  "preset_name": "My Vocal Hall",
  "category": "user"
}
→ Saves to presets/reverb/user/my_vocal_hall.json
```

## Third-Party Plugin Safety

### Collision Detection & Validation

**When signature matches existing structure:**
```python
def validate_device_compatibility(structure_sig: str, device_params: list) -> bool:
    """Test if device is truly compatible with learned structure"""

    # 1. Quick test: Set & read back 3-5 critical parameters
    test_params = ["Decay Time", "Predelay", "Dry/Wet"]

    for param in test_params:
        # Set to known value
        set_value = 0.5
        set_device_param(param, set_value)

        # Read back
        actual = get_device_param(param)

        # Use learned fit to predict display
        expected_display = predict_from_fit(set_value)
        actual_display = actual["display_value"]

        # Check if display values match
        if not values_match(expected_display, actual_display, tolerance=0.05):
            return False  # Different device!

    return True  # Compatible ✅
```

**Workflow:**
```bash
# User adds "Valhalla VintageVerb" (hypothetically same 33 params)
GET /return/device/map?index=0&device=0
→ Signature matches Ableton Reverb! (collision)
→ Auto-triggers validation test
→ Sets Decay Time, Predelay, Dry/Wet
→ Compares display values
→ Different! → Mark as new device, trigger full learn

# User adds another Ableton Reverb preset
→ Signature matches
→ Validation passes ✅
→ Reuses structure, no learning needed
```

## API Endpoints

### New Endpoints Needed:

```python
# Capture preset values (no learning)
POST /return/device/capture_preset
{
  "return_index": 0,
  "device_index": 0,
  "preset_name": "Arena Tail",
  "category": "stock"  # stock | user
}

# Apply preset values
POST /return/device/apply_preset
{
  "return_index": 0,
  "device_index": 0,
  "preset_name": "arena_tail"
}

# List available presets for device
GET /return/device/presets?signature=abc123...
→ Returns all presets compatible with this structure

# Validate device compatibility
POST /return/device/validate
{
  "return_index": 0,
  "device_index": 0,
  "structure_signature": "abc123..."
}
→ Returns {"compatible": true/false, "confidence": 0.95}
```

### Modified Endpoints:

```python
# Updated signature (no name)
def _make_device_signature(params: list[dict]) -> str:
    param_names = ",".join([str(p.get("name", "")) for p in params])
    base = f"{len(params)}|{param_names}"
    return hashlib.sha1(base.encode("utf-8")).hexdigest()

# Detect device type from params
def _detect_device_type(params: list[dict]) -> str:
    param_set = set(p.get("name") for p in params)

    # Reverb signature params
    if {"ER Spin On", "Freeze On", "Chorus On", "Diffusion"}.issubset(param_set):
        return "reverb"

    # Delay signature params
    if {"L Time", "R Time", "Ping Pong", "Feedback"}.issubset(param_set):
        return "delay"

    # Compressor signature params
    if {"Threshold", "Ratio", "Attack", "Release"}.issubset(param_set):
        return "compressor"

    return "unknown"
```

## Benefits

### For Developers:
- ✅ Learn all Ableton presets once
- ✅ Package preset library with app
- ✅ Users never need to learn stock devices

### For End Users:
- ✅ Instant preset loading (no 30s learning)
- ✅ Save custom presets
- ✅ Share presets with others
- ✅ Safe third-party plugin handling

### Storage Savings:
- ✅ One structure (100KB) vs 50 presets × 100KB (5MB)
- ✅ Preset files tiny (2-5KB each, just values)

### Collision Safety:
- ✅ Auto-validation prevents wrong mappings
- ✅ Graceful fallback to full learn if incompatible

## Implementation Phases

**Phase A: Structure-Only Signatures** (Current)
- Remove device name from signature
- All Ableton Reverbs share one signature ✅

**Phase B: Preset Capture** (Next)
- Add `/capture_preset` endpoint
- Store preset value snapshots
- Link to structure signature

**Phase C: Preset Application** (Then)
- Add `/apply_preset` endpoint
- Quick preset loading (no learning)

**Phase D: Validation System** (Finally)
- Auto-detect third-party collisions
- Test-based validation
- Fallback to full learn if incompatible

## Risk Mitigation

**Q: What if third-party plugin has identical params?**
**A:** Validation test detects incompatibility → triggers full learn

**Q: What if user modifies stock preset, breaks mapping?**
**A:** Mapping is per-structure, not per-preset → still works

**Q: What if Ableton updates Reverb, adds params?**
**A:** New param count → different signature → new structure learn

**Q: How to handle preset name conflicts?**
**A:** Namespace by category: `stock/arena_tail` vs `user/arena_tail`

---

See [DEVICE_RECOGNITION.md](DEVICE_RECOGNITION.md) for signature system details.
