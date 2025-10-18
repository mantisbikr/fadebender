# Mixer Mappings Consolidation

**Date:** 2025-10-17
**Database:** dev-display-value
**Status:** ✅ Complete (Firestore migration done, code updates pending)

## Overview

Consolidated mixer mappings from flat parameter documents to entity-based structure with `params_meta`, matching the device_mappings pattern.

## Migration Summary

### Before (Old Structure)
```
Collection: mixer_mappings
├── volume (document)
├── send (document)
├── pan (document)
└── cue (document)
```

Each document contained:
- Large `mapping` array (20+ points) for dB/float conversion
- Duplicate `applies_to` metadata
- No control_type declaration
- No entity grouping

### After (New Structure)
```
Collection: mixer_mappings
├── track_channel (document)
├── return_channel (document)
└── master_channel (document)
```

Each document contains:
- `entity_type`: "track" | "return" | "master"
- `params_meta`: Array of parameter definitions (same structure as device_mappings)
- `sections`: Logical grouping of parameters
- Simplified `fit` formulas instead of lookup tables

## New Structure

```javascript
{
  "entity_type": "track",
  "description": "Standard audio track mixer strip",
  "params_meta": [
    {
      "index": 0,
      "name": "volume",
      "control_type": "continuous",
      "unit": "dB",
      "min": 0.0,          // normalized range
      "max": 1.0,
      "min_display": -70.0,
      "max_display": 6.0,
      "fit": {
        "type": "power",
        "coeffs": {
          "min_db": -70.0,
          "max_db": 6.0,
          "gamma": 2.1823,
          "range_db": 76.0
        }
      },
      "audio_knowledge": { ... }
    },
    // ... more params
  ],
  "sections": {
    "output": {
      "parameters": ["volume", "pan"],
      "description": "Track output controls"
    }
  }
}
```

## Simplified Fit Formulas

### Volume (Power Law)
```python
# Forward: dB → normalized
normalized = ((dB + 70.0) / 76.0) ** 2.1823

# Inverse: normalized → dB
dB = -70.0 + 76.0 * (normalized ** (1/2.1823))

# Accuracy: R² = 0.994, max_error = 0.04
```

### Send (Power Law)
```python
# Forward: dB → normalized
normalized = ((dB + 76.0) / 70.0) ** 2.7742

# Inverse: normalized → dB
dB = -76.0 + 70.0 * (normalized ** (1/2.7742))

# Accuracy: R² = 0.944, max_error = 0.15
# Note: Send max is 0.85 (not 1.0) = -6dB display
```

### Pan (Linear)
```python
# Forward: display → normalized
normalized = display_value / 50.0

# Inverse: normalized → display
display_value = normalized * 50.0

# Display format: "C", "25L", "50R"
```

### Cue (Power Law - Estimated)
```python
# Forward: dB → normalized
normalized = ((dB + 60.0) / 66.0) ** 2.2

# Inverse: normalized → dB
dB = -60.0 + 66.0 * (normalized ** (1/2.2))
```

## Parameters by Entity

### Track Channel
- **volume** (continuous, dB, -70 to +6)
- **pan** (continuous, display_value, -50 to +50)
- **mute** (binary, off/on)
- **solo** (binary, off/on)
- **sends** (send_array, dB per return, -76 to -6)

### Return Channel
- **volume** (continuous, dB, -70 to +6)
- **pan** (continuous, display_value, -50 to +50)
- **mute** (binary, off/on)
- **sends** (send_array, dB per return, -76 to -6)

### Master Channel
- **volume** (continuous, dB, -70 to +6)
- **pan** (continuous, display_value, -50 to +50)
- **cue** (continuous, dB, -60 to +6)

## Benefits

1. ✅ **Consistent with device_mappings** - Same `params_meta` structure
2. ✅ **Entity-oriented** - Tracks, Returns, Master are first-class entities
3. ✅ **UI auto-generation** - Can render controls just like device params
4. ✅ **Simplified formulas** - 3 coefficients instead of 20+ point lookup
5. ✅ **Type-safe** - `control_type` declares what control to render
6. ✅ **Better accuracy** - Power law fits with R² > 0.94
7. ✅ **Extensible** - Easy to add new params (arm, monitoring, etc.)

## Backward Compatibility

- Old documents (volume, send, pan, cue) preserved
- Code should try new format first, fall back to old
- Gradual migration path
- Can remove old format after full verification

## Code Updates Required

### Files to Update
1. `server/api/intents.py` - intent/execute and intent/read for mixer params
2. `server/api/overview.py` - snapshot endpoint may need mixer metadata
3. Client code if rendering mixer controls

### Migration Strategy
1. Update intent/execute to use new mixer params_meta
2. Update intent/read to use new mixer params_meta
3. Test with WebUI via intents
4. Evaluate sidebar controls migration
5. Remove old format once verified

## Testing Plan

1. **Volume tests:**
   - Set track volume to -6dB, 0dB, +6dB
   - Read track volume and verify display values

2. **Pan tests:**
   - Set pan to center, 25L, 50R
   - Read pan and verify display format

3. **Binary tests:**
   - Toggle mute on/off
   - Toggle solo on/off

4. **Send tests:**
   - Set send A to -12dB
   - Read send and verify

## Files Changed

**Firestore (dev-display-value):**
- Created: `mixer_mappings/track_channel`
- Created: `mixer_mappings/return_channel`
- Created: `mixer_mappings/master_channel`
- Preserved: `mixer_mappings/volume`, `send`, `pan`, `cue` (backward compat)

**Backups:**
- `/backups/database_backups/mixer_mappings_before_consolidation_20251017_204851.json`

## Next Steps

1. ⏳ Update `server/api/intents.py` for mixer params
2. ⏳ Test with WebUI
3. ⏳ Evaluate sidebar migration
4. ⏳ Document API changes
