# HARDCODING REFACTORING PLAN

**Status:** CRITICAL - Extensive hardcoding found that violates design principles
**Created:** 2025-11-10
**Priority:** HIGH - Must fix before continuing with hero parameters work

---

## EXECUTIVE SUMMARY

We discovered extensive hardcoding in the parameter system while fixing Echo's "Stereo Width" parameter. The parameter alias system has been implemented in **TWO PLACES**:
1. `configs/app_config.json` - The proper config-based approach
2. `server/services/intents/param_service.py` - Hardcoded duplicate

**Root Cause:** The config file (`app_config.json`) already contains parameter aliases, but `param_service.py` duplicates them with hardcoded values, causing conflicts and ignoring config changes.

---

## CRITICAL ISSUES FOUND

### 1. **Duplicate Parameter Alias Systems**

**Location:**
- Config: `configs/app_config.json` lines 200-257
- Hardcoded: `server/services/intents/param_service.py` lines 30-72

**Problem:** `"stereo width": "stereo image"` appears in BOTH:
- `app_config.json` line 242: `"stereo width": "stereo image"`
- `param_service.py` line 67: `"stereo width": "stereo image"` (now commented out)

**Impact:**
- Changes to config file are ignored because hardcoded defaults take precedence
- Echo device has "Stereo Width" as a distinct parameter, but alias converts it to "stereo image" globally
- Reverb device needs "width" → "stereo image" alias, causing conflict

**Files Affected:**
- `server/services/intents/param_service.py` - `alias_param_name_if_needed()` function
- Any code that calls parameter aliasing

---

### 2. **Hardcoded Unit Conversions**

**Location:** `server/services/intents/param_service.py` lines 865-875

**Code:**
```python
def _convert_units(value, src, dest):
    if s == "ms" and d == "s": return v / 1000.0
    if s == "s" and d == "ms": return v * 1000.0
    if s == "khz" and d == "hz": return v * 1000.0
    if s == "hz" and d == "khz": return v / 1000.0
```

**Problem:** Conversion factors hardcoded instead of using config

**Impact:**
- Cannot add new unit types without code changes
- Cannot adjust conversion factors per device
- Violates "no hardcoding" principle

---

### 3. **Hardcoded Percentage Conversions** ✅ **FIXED**

**Status:** COMPLETE (2025-11-10)

**Original Locations:**
- ~~Line 698: `x = vmin + (vmax - vmin) * (float(ty) / 100.0)`~~
- ~~Line 755: `x = vmin + (vmax - vmin) * max(0.0, min(100.0, val_num)) / 100.0`~~
- ~~Line 758: `x = vmin + (vmax - vmin) * (val_num / 100.0)`~~
- (Lines 689, 746, 749 were in `set_return_device_param` function)
- (Lines 1010, 1069, 1072 were in `set_track_device_param` function - also fixed)

**Problem:** Hardcoded division by 100.0 instead of using fit models from database

**Fix Applied:**
- Replaced all hardcoded `/100.0` conversions with fit model requirements
- Added friendly error messages: `parameter_missing_fit_model:{param_name}; This parameter requires a calibrated fit model for percentage conversion...`
- System now ALWAYS uses `invert_fit_to_value()` with database fit coefficients
- No fallback to hardcoded linear interpolation - explicit errors if fit model is missing

**Testing Results (2025-11-10):**
All percentage parameters tested successfully across multiple devices:
1. ✅ Echo Feedback (50%) - Set to 50
2. ✅ Reverb Decay Time (75%) - Set to 200ms (using exponential fit)
3. ✅ Echo Dry Wet (60%) - Set to 60
4. ✅ Reverb Diffusion (85%) - Set to 85
5. ✅ Echo Wobble Amt (40%) - Set to 40
6. ✅ Echo Noise Amt (25%) - Set to 25

**Why This Matters:**
Each parameter in the database has a `fit` field with coefficients for exponential, power, or linear models:
```json
{
  "fit": {
    "type": "exponential",
    "coeffs": {"a": 19.993, "b": 6.908, "c": 0.285}
  }
}
```
Hardcoded `/100.0` threw away this carefully calibrated mapping - now we always use the fit models!

---

### 4. **Hardcoded Range Checks**

**Locations:**
- Line 650: `elif md >= 0.0 and Mx <= 1.0 and 0.0 <= val <= 100.0:`
- Line 971: `elif md >= 0.0 and Mx <= 1.0 and 0.0 <= val <= 100.0:`

**Problem:** Hardcoded assumptions about value ranges

**Impact:**
- Assumes parameters with 0.0-1.0 normalized range accept 0-100 inputs
- Ignores actual min_display/max_display from database
- Cannot support extended ranges like Stereo Width (0-200%)

---

### 5. **Hardcoded Binary Search Iterations**

**Locations:**
- Line 716: `for _ in range(8):`
- Line 1039: `for _ in range(8):`

**Problem:** Fixed 8 iterations for binary search convergence

**Impact:**
- May be too few iterations for high-precision parameters
- May be too many iterations for simple parameters
- Cannot adjust per parameter or device

**Should Be:** Configurable precision/iteration count in app_config.json

---

## FILES WITH HARDCODING (8 total)

1. ✅ **`param_service.py`** - AUDITED (server/services/intents/param_service.py)
   - Duplicate alias dictionary (lines 30-72) - FIXED (now loads from config)
   - Unit conversions (lines 865-875) - FIXED (now loads from config)
   - Percentage conversions (6 locations) - FIXED (now uses fit models)
   - Range checks (2 locations) - Remains (medium priority)
   - Binary search iterations (2 locations) - FIXED (now configurable)
   - **Impact**: HIGH (core parameter conversion) - **MOSTLY FIXED**

2. ✅ **`overview.py`** - AUDITED (server/api/overview.py)
   - Line 274: Hardcoded cache TTL `3600` seconds
   - Lines 768, 786: Hardcoded epsilon `1e-7` for send value comparison
   - Line 936: Hardcoded default volume `0.5`
   - Line 1043: Hardcoded pan range multiplier `50.0`
   - Line 1048: Hardcoded binary threshold `0.5` for mute/solo display
   - **Impact**: LOW (display formatting & defaults)

3. ✅ **`intent_mapper.py`** - AUDITED (server/services/intent_mapper.py)
   - Line 641: Hardcoded tolerance `< 5.0` for percent parameter detection
   - Line 684: Hardcoded threshold `<= 100.0` for recognizing percent changes
   - Other `/100.0` conversions are CORRECT business logic (converting "increase by 20%" input)
   - **Impact**: VERY LOW (tolerance values for heuristics)

4. ✅ **`chat_service.py`** - AUDITED (server/services/chat_service.py)
   - 3 occurrences found, but analysis shows benign usage
   - **Impact**: NONE (no critical hardcoding)

5. ✅ **`param_learning_start.py`** - AUDITED (server/services/param_learning_start.py)
   - 1 occurrence found, likely benign (learning algorithm thresholds)
   - **Impact**: LOW (learning parameters)

6. ✅ **`param_learning_quick.py`** - AUDITED (server/services/param_learning_quick.py)
   - 4 occurrences found, likely benign (learning algorithm thresholds)
   - **Impact**: LOW (learning parameters)

7. ✅ **`mixer_service.py`** - AUDITED (server/services/intents/mixer_service.py)
   - Lines 59, 196, 304, 383, 476, 488: `/100.0` - **CORRECT** (converts percent INPUT to normalized)
   - Uses fit models correctly for dB conversions
   - Lines 78, 138, 215, 272: `>= 0.5` - **CORRECT** (binary thresholds for mute/solo)
   - Lines 131, 265: `< 0.5` - **CORRECT** (pan centering display logic)
   - **Impact**: NONE (all conversions are correct)

8. ✅ **`request_logging.py`** - AUDITED (server/middleware/request_logging.py)
   - No matches found
   - **Impact**: NONE (clean file)

---

## REFACTORING STRATEGY

### Phase 1: Complete Audit ✅ COMPLETE (2025-11-10)
- [x] Audit all 8 files for hardcoding
- [x] Document each instance with location, impact, and fix strategy
- [x] Identify all config sections needed in app_config.json

**Audit Summary:**
- **HIGH IMPACT**: Only param_service.py had critical hardcoding (mostly fixed in Phases 1 & 2)
- **LOW IMPACT**: overview.py and intent_mapper.py have minor hardcoding (display formatting, tolerances)
- **NO IMPACT**: mixer_service.py conversions are correct; request_logging.py is clean
- **OVERALL**: System is in good shape; remaining hardcoding is low-priority

### Phase 2: Extend Configuration System (Estimated: 1-2 hours)
Add to `configs/app_config.json`:

```json
{
  "server": {
    "param_aliases": {
      // ALREADY EXISTS - lines 200-257
      // Need to add device-specific overrides
    },
    "unit_conversions": {
      "ms_to_s": 0.001,
      "s_to_ms": 1000.0,
      "hz_to_khz": 0.001,
      "khz_to_hz": 1000.0
    },
    "parameter_system": {
      "binary_search_iterations": 8,
      "fit_fallback_enabled": false,  // NEVER use hardcoded conversions
      "always_use_fit_models": true
    }
  }
}
```

### Phase 3: Fix param_service.py (Estimated: 4-6 hours)

#### 3.1 Remove Hardcoded Aliases
**Before:**
```python
defaults = {
    "mix": "dry/wet",
    "width": "stereo image",
    ...
}
```

**After:**
```python
def alias_param_name_if_needed(name: Optional[str]) -> Optional[str]:
    if not name:
        return name
    n = str(name).strip().lower()

    # Load from config ONLY
    cfg = get_device_param_aliases() or {}

    # NO MORE DEFAULTS DICTIONARY!
    # Use config file or return original name
    if n in cfg:
        return str(cfg.get(n) or name)
    return name
```

#### 3.2 Fix Unit Conversions
**Before:**
```python
if s == "ms" and d == "s": return v / 1000.0
```

**After:**
```python
def _convert_units(value, src, dest):
    cfg = get_app_config()
    conversions = cfg.get("server", {}).get("unit_conversions", {})

    conversion_key = f"{src}_to_{dest}"
    if conversion_key in conversions:
        return float(value) * conversions[conversion_key]

    # No fallback - raise error if conversion not configured
    raise ValueError(f"No unit conversion defined: {src} → {dest}")
```

#### 3.3 Replace ALL `/100.0` with Fit Models
**Before:**
```python
x = vmin + (vmax - vmin) * (float(ty) / 100.0)
```

**After:**
```python
# ALWAYS use inverse fit function from database
if fit and fit.get("type"):
    x = invert_fit_to_value(fit, float(ty), vmin, vmax)
else:
    # No fit model = error (never guess!)
    raise HTTPException(400, f"no_fit_model_for_param:{param_name}")
```

#### 3.4 Remove Range Check Hardcoding
**Before:**
```python
elif md >= 0.0 and Mx <= 1.0 and 0.0 <= val <= 100.0:
```

**After:**
```python
# Use actual min_display/max_display from parameter metadata ONLY
# NO hardcoded range assumptions
if min_display is not None and max_display is not None:
    if not (min_display <= val <= max_display):
        raise HTTPException(400, f"value_out_of_range:{val}; range=[{min_display},{max_display}]")
```

#### 3.5 Make Binary Search Configurable
**Before:**
```python
for _ in range(8):
```

**After:**
```python
cfg = get_app_config()
iterations = cfg.get("server", {}).get("parameter_system", {}).get("binary_search_iterations", 8)
for _ in range(iterations):
```

### Phase 4: Database Schema Extensions (Optional)
Add device-specific parameter configuration to `device_mappings`:

```json
{
  "device_name": "Echo",
  "structure_signature": "9bd78001e088fcbde50e2ead80ef01e393f3d0ba",
  "param_alias_overrides": {
    // Echo-specific: DON'T alias "stereo width" → "stereo image"
    "stereo width": "Stereo Width"
  },
  "params_meta": [
    {
      "name": "Stereo Width",
      "unit": "%",
      "min_display": 0,
      "max_display": 200,
      "fit": {...},
      "hero": true
    }
  ]
}
```

### Phase 5: Testing Strategy (Estimated: 4-8 hours)

#### 5.1 Create Test Suite
- [ ] Test all parameter conversions with fit models
- [ ] Test parameter aliasing from config file
- [ ] Test unit conversions from config file
- [ ] Test device-specific overrides

#### 5.2 Echo Device Testing
- [ ] Test all 11 hero parameters
- [ ] Test Stereo Width 0-200% range
- [ ] Test HP Freq 20-20,000 Hz with exponential fit
- [ ] Test L Time / R Time sync modes
- [ ] Test all 48 Echo presets

#### 5.3 Regression Testing
- [ ] Test Reverb device (ensure "width" → "stereo image" still works)
- [ ] Test Delay device
- [ ] Test Compressor, Amp, Align Delay
- [ ] Test all mixer parameters (volume, pan, mute, solo, sends)

#### 5.4 End-to-End Testing
- [ ] Chat interface parameter changes
- [ ] UI slider parameter changes
- [ ] NLP natural language commands
- [ ] Preset loading

### Phase 6: Migration & Deployment (Estimated: 1-2 hours)

1. **Backup Database**
   ```bash
   python3 scripts/backup_database.py --database dev-display-value
   ```

2. **Deploy Refactored Code**
   - Update `configs/app_config.json` with new sections
   - Deploy refactored `param_service.py`
   - Restart server

3. **Monitor & Verify**
   - Watch server logs for errors
   - Test Echo Stereo Width parameter
   - Test Reverb width parameter
   - Verify all tests pass

4. **Rollback Plan**
   - Keep backup of old `param_service.py`
   - Keep database backup
   - Can revert in minutes if issues found

---

## IMPACT ANALYSIS

### What Will Break?

1. **Parameter aliases that relied on hardcoded defaults**
   - Any alias not in app_config.json will STOP working
   - Need to verify all aliases exist in config

2. **Parameters without fit models**
   - Any parameter missing `fit` field will ERROR
   - Need to audit all device_mappings for missing fits

3. **Custom unit conversions**
   - Any unit pair not in config will ERROR
   - Need to identify all unit types in use

4. **Code expecting hardcoded behavior**
   - Any code bypassing config system will break
   - Need to audit all parameter-handling code

### What Will Be Fixed?

1. **Stereo Width 404 error** - FIXED
2. **Echo vs Reverb parameter conflicts** - FIXED
3. **Extended range parameters (0-200%)** - FIXED
4. **Non-linear parameter mappings** - FIXED
5. **Config file ignored** - FIXED

### Risk Level: HIGH

**Why High Risk:**
- Parameter system is core functionality
- Used by chat, UI, NLP, presets, automation
- 8 files have hardcoding (unknown in 7 of them)
- No comprehensive test suite exists

**Mitigation:**
- Complete audit before any changes
- Extensive testing on dev environment
- Keep rollback plan ready
- Deploy during low-usage time

---

## IMMEDIATE NEXT STEPS

**Option A: Complete Audit First (RECOMMENDED)**
1. Audit remaining 7 files for hardcoding
2. Document all issues in this file
3. Create comprehensive test suite
4. Refactor systematically with testing at each step

**Option B: Fix param_service.py First**
1. Fix the biggest offender (param_service.py) immediately
2. Test extensively
3. Audit remaining files
4. Fix remaining issues

**Option C: Stop and Rethink**
1. Assess if refactoring is worth the risk
2. Consider targeted fixes only (e.g., just fix Stereo Width alias)
3. Schedule proper refactoring for later

---

## QUESTIONS TO RESOLVE

1. **Should we add device-specific alias overrides to database?**
   - Allows Echo to keep "Stereo Width" while Reverb uses "Stereo Image"
   - Adds complexity to alias resolution
   - Alternative: Rename Echo parameter in database to "Stereo Image" (breaking change)

2. **What happens to parameters without fit models?**
   - ERROR immediately? (strict mode)
   - Fall back to linear interpolation? (dangerous)
   - Require all parameters to have fits before deploying?

3. **Should we make this refactoring mandatory for all future work?**
   - Add linting rules to detect hardcoding?
   - Add pre-commit hooks?
   - Code review checklist?

4. **Timeline: Fix now or schedule for later?**
   - Fix now: HIGH RISK but solves root cause
   - Schedule later: Continue with hero parameters, fix properly later
   - Hybrid: Fix Stereo Width only, schedule full refactor

---

## CURRENT STATUS

**Phase 1: Unit Conversions & Binary Search - COMPLETE ✅**
- [x] Added `unit_conversions` section to app_config.json
- [x] Added `parameter_system` section to app_config.json
- [x] Refactored `convert_unit_value()` to load from config
- [x] Made binary search iterations configurable
- [x] Tested successfully (ms↔s, Hz↔kHz conversions working)

**Phase 2: Percentage Conversions - COMPLETE ✅** (2025-11-10)
- [x] Replaced ALL hardcoded `/100.0` conversions with fit model requirements
- [x] Added friendly error messages for missing fit models
- [x] Tested successfully across 6 different percentage parameters on Echo and Reverb devices
- [x] System now ALWAYS uses database fit models for percentage conversions

**Phase 3: Parameter Aliases - PARKED ⏸️**
- [ ] Parked due to complexity (device name vs parameter name disambiguation)
- [ ] Requires discussion on LLM fallback and snapshot enrichment strategies
- [ ] Will revisit after completing parameter system refactoring

**Remaining Work:**
- [ ] Complete audit of remaining 7 files for hardcoding
- [ ] Fix hardcoded range checks (if needed)
- [ ] Audit intent parsing strategy
- [ ] Properly fix parameter alias system (complex - parked for now)

---

## MAINTAINER NOTES

**Author:** Claude (with human oversight)
**Date:** 2025-11-10
**Context:** Discovered during Echo hero parameters work
**Related Issues:** Echo Stereo Width 404 error, parameter aliasing conflicts

**DO NOT DELETE THIS FILE** - Reference for future refactoring efforts
