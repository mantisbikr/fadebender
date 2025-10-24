# Intents API Test Plan

## Overview

This document outlines the comprehensive test plan for the Intents API (`server/api/intents.py`). The API layer is a thin dispatcher that delegates to service modules in `server/services/intents/*` for execution.

## Test Coverage Summary

| Category | Tests | Description |
|----------|-------|-------------|
| Track Mixer | 6 | Volume (dB/%), pan (normalized/%), mute, solo |
| Return Mixer | 3 | Volume, pan, mute on return tracks |
| Master Mixer | 2 | Master volume (dB), pan |
| Track Sends | 2 | Send levels (normalized, percent) |
| Return Sends | 1 | Return send chains |
| Device Params (Index) | 2 | Direct parameter access by index |
| Device Params (Name) | 3 | Fuzzy name matching, ambiguous names, not found |
| Display Values | 2 | Linear fit conversion, label mapping |
| Auto-Enable | 2 | Master toggle auto-enable, already-enabled check |
| Dry-Run Mode | 2 | Preview mode for track/device operations |
| Error Handling | 5 | Missing fields, timeouts, unsupported ops |
| Clamping | 2 | Value clamping enabled/disabled |
| Track Devices | 2 | Track device parameter control |
| Edge Cases | 3 | Zero dB, extreme negative dB, hard panning |
| Integration | 1 | Multi-operation mixing scenario |

**Total: 38 comprehensive tests**

## Key Features Tested

### 1. Multiple Unit Systems
- **dB**: Logarithmic volume representation
- **Percent**: 0-100% linear scaling
- **Normalized**: Direct 0-1 values

### 2. Parameter Resolution
- **By Index**: Direct access (fastest)
- **By Name**: Fuzzy matching for natural language
- **Ambiguity Detection**: Prevents accidental parameter changes

### 3. Display-Value Transformations
- **Linear Fit**: `y = ax + b`
- **Log Fit**: `y = a*ln(x) + b`
- **Exp Fit**: `y = a*exp(bx)`
- **Piecewise**: Linear interpolation between points
- **Label Maps**: Discrete choices (e.g., "Shelving", "Low-pass")

### 4. Smart Dependencies
- **Auto-enable master toggles**: When setting a dependent parameter (e.g., "Chorus Amount"), automatically enable the section toggle (e.g., "Chorus On")
- **Skip if already enabled**: Avoid redundant operations
- **Heuristic-based**: Name pattern matching

### 5. Dry-Run Mode
- **Preview operations** without sending to Live
- **Validate intents** before execution
- **Test transformations** without side effects

## Test Scenarios

### Scenario 1: Basic Mixing
```json
// Set track 1 volume to -6dB
{
  "domain": "track",
  "action": "set",
  "track_index": 1,
  "field": "volume",
  "value": -6.0,
  "unit": "dB"
}
```

**Expected**: Volume converted from -6dB to the correct normalized value per mixer mapping and applied via mixer service.

### Scenario 2: Natural Language Parameter
```json
// Set reverb decay time by name
{
  "domain": "device",
  "action": "set",
  "return_index": 0,
  "device_index": 0,
  "param_ref": "decay",  // Matches "Decay Time"
  "value": 0.7
}
```

**Expected**: Fuzzy match finds "Decay Time" parameter

### Scenario 3: Display-Value Control
```json
// Set predelay to 50ms using display value
{
  "domain": "device",
  "action": "set",
  "return_index": 0,
  "device_index": 0,
  "param_ref": "predelay",
  "display": "50 ms"
}
```

**Expected**:
1. Fetch device mapping with fit coefficients
2. Invert linear fit: 50ms → 0.5 (normalized)
3. Set parameter to 0.5

### Scenario 4: Label-Based Control
```json
// Set HiFilter Type to Low-pass
{
  "domain": "device",
  "action": "set",
  "return_index": 0,
  "device_index": 0,
  "param_ref": "hifilter type",
  "display": "Low-pass"
}
```

**Expected**:
1. Lookup label_map in params_meta
2. Find "Low-pass" → 1.0
3. Set parameter to 1.0

### Scenario 5: Auto-Enable Master
```json
// Set Chorus Amount (Chorus On is off)
{
  "domain": "device",
  "action": "set",
  "return_index": 0,
  "device_index": 0,
  "param_ref": "chorus amount",
  "value": 0.8
}
```

**Expected**:
1. Detect "Chorus Amount" needs "Chorus On"
2. Auto-enable "Chorus On" → 1.0
3. Set "Chorus Amount" → 0.8

### Scenario 6: Dry-Run Preview
```json
// Preview track volume change
{
  "domain": "track",
  "action": "set",
  "track_index": 0,
  "field": "volume",
  "value": -6.0,
  "unit": "dB",
  "dry_run": true
}
```

**Expected**:
```json
{
  "ok": true,
  "preview": {
    "op": "set_mixer",
    "track_index": 0,
    "field": "volume",
    "value": 0.501
  }
}
```

## Error Conditions Tested

| Error | HTTP Code | Scenario |
|-------|-----------|----------|
| Missing track_index | 400 | Track operation without target |
| Missing param selector | 400 | Device param without index/name |
| Param not found | 404 | Invalid parameter name/index |
| Param ambiguous | 409 | Name matches multiple params |
| Device not found | 404 | Empty params list |
| No Live response | 504 | UDP timeout |
| Unsupported intent | 400 | Invalid domain/action combo |

## Running Specific Test Suites

### By Category
```bash
# Track operations
pytest tests/test_intents.py::test_track_volume_db -v
pytest tests/test_intents.py::test_track_pan_percent -v

# Device parameters
pytest tests/test_intents.py::test_return_device_param_by_index -v
pytest tests/test_intents.py::test_return_device_param_by_name -v

# Display values
pytest tests/test_intents.py::test_device_param_display_linear_fit -v
pytest tests/test_intents.py::test_device_param_display_label_map -v

# Auto-enable
pytest tests/test_intents.py::test_auto_enable_chorus_on -v

# Errors
pytest tests/test_intents.py::test_param_not_found -v
pytest tests/test_intents.py::test_param_ambiguous -v
```

### By Pattern
```bash
# All track tests
pytest tests/test_intents.py -k "track" -v

# All device tests
pytest tests/test_intents.py -k "device" -v

# All error tests
pytest tests/test_intents.py -k "error or missing or not_found" -v
```

## Manual Testing Checklist

For end-to-end testing with actual Ableton Live:

- [ ] **Track Volume**: Set using dB, verify in Live
- [ ] **Track Pan**: Set using %, verify centered vs hard L/R
- [ ] **Track Mute/Solo**: Toggle, verify visual feedback
- [ ] **Send Levels**: Set track → return send, hear effect
- [ ] **Device Param (Index)**: Set known parameter, verify display
- [ ] **Device Param (Name)**: Use fuzzy name, verify correct param
- [ ] **Display Value**: Set "50 ms" predelay, verify in Live
- [ ] **Label Value**: Set "Low-pass", verify filter type change
- [ ] **Auto-Enable**: Set dependent param with master off, verify auto-enable
- [ ] **Dry-Run**: Preview operation, verify nothing changes in Live

## Future Test Enhancements

1. **Parametric Tests**: Use `pytest.mark.parametrize` for value ranges
2. **Property-Based Testing**: Use `hypothesis` for random value testing
3. **Performance Tests**: Measure response times for various operations
4. **Concurrency Tests**: Multiple simultaneous intent executions
5. **Real Live Integration**: Optional tests against running Live instance
6. **Regression Tests**: Pin specific bug scenarios

## CI/CD Integration

Add to GitHub Actions:
```yaml
- name: Run Intent API Tests
  run: |
    cd server
    pytest tests/test_intents.py \
      --cov=server.api.intents \
      --cov=server.services.intents.mixer_service \
      --cov=server.services.intents.param_service \
      --cov=server.services.intents.routing_service \
      --cov-fail-under=90
```

## Coverage Goals

- **Line Coverage**: ≥90%
- **Branch Coverage**: ≥85%
- **Function Coverage**: 100%

Current coverage can be checked with:
```bash
pytest tests/test_intents.py \
  --cov=server.api.intents \
  --cov=server.services.intents.mixer_service \
  --cov=server.services.intents.param_service \
  --cov=server.services.intents.routing_service \
  --cov-report=html
open htmlcov/index.html
```
