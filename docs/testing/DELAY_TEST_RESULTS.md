# Delay Device Parameter Testing Results

**Date:** 2025-10-01
**Device:** Delay on Return B (index 1, device 0)
**Mapping Signature:** 6b18c71542233be7280030531890ec10de53daab
**Quick Learn:** 21 parameters mapped successfully

## Test Summary

| Test | Parameter | Target | Expected | Actual | Status | Notes |
|------|-----------|--------|----------|--------|--------|-------|
| 1 | L Time | "250 ms" | ~250 ms | 245.0 ms | ✓ | Within 2% tolerance (5ms off) |
| 2 | R 16th | "5" | 5.0 with R Sync On | 5.0 with R Sync Off | ⚠️ | Value correct but R Sync not auto-enabled |
| 3 | Feedback | +3 relative | 24.0 (from 21.0) | 24.0 | ✓ | Relative increase works |
| 3b | Feedback | -3 relative | 21.0 (back to original) | 21.0 | ✓ | Relative decrease works |
| 4 | Filter On | "On" | 1.0 | 1.0 | ✓ | Response shows 0.0 but actual is 1.0 |
| 4b | Filter Freq | "1200 Hz" | ~1200 Hz | 1200.0 Hz | ✓ | Exact match |
| 5 | Filter Width | +1 relative | 9.0 (from 8.0) | 9.0 | ✓ | Relative works |
| 6 | Dry/Wet | "20%" | 20% | 20.0 | ✓ | Exact match |
| 7 | Link | "On" / 1.0 | 1.0 | 0.0 | ✗ | Toggle not working |
| 8 | Ping Pong | 1.0 | 1.0 | 0.0 | ✗ | Toggle not working |

## Issues Found

### 1. Master Auto-Enable Not Working for Sync Parameters
**Severity:** Medium
**Affected:** R 16th, L 16th (likely), R Time, L Time

**Expected Behavior:**
- Setting R 16th should auto-enable R Sync to 1.0 (per config `dependent_master_values`)
- Setting L Time should auto-enable L Sync to 0.0 (per config)

**Actual Behavior:**
- R 16th sets correctly to 5.0 but R Sync remains at 0.0
- L Time works because L Sync was already at 0.0

**Config Reference (param_learn.json lines 62-67):**
```json
"dependent_master_values": {
  "L Time": 0.0,
  "L 16th": 1.0,
  "R Time": 0.0,
  "R 16th": 1.0
}
```

**Root Cause Hypothesis:**
The code in `server/app.py` around line 1323-1354 reads `dependent_master_values` from config but may have:
1. Case-sensitivity issue in matching device name or param name
2. Logic error in applying the desired_val
3. Issue with config key matching

### 2. Binary/Toggle Parameters Not Setting Correctly
**Severity:** High
**Affected:** Link, Ping Pong (possibly others)

**Expected Behavior:**
- Setting value to 1.0 or target_display "On" should set parameter to 1.0
- Label map shows: `{"1.0": 1.0, "0.0": 0.0}`

**Actual Behavior:**
- API returns value 0.99609375 with display "0.0"
- Actual device parameter stays at 0.0
- Both "On" text and 1.0 numeric value fail

**Root Cause Hypothesis:**
1. Label matching may require exact "1.0" or "0.0" strings, not "On"/"Off"
2. The 0.996 value suggests it's being treated as continuous instead of binary
3. Quick learn may have incorrectly classified these as continuous (see map_summary: control_type="continuous" for toggles)

### 3. Filter On Response Discrepancy
**Severity:** Low (cosmetic)
**Affected:** Filter On

**Actual Behavior:**
- API response shows `{"value": 0.0, "display": "0.0"}`
- But actual device parameter is correctly at 1.0
- This is just a response formatting issue, actual control works

## Recommendations

### Priority 1: Fix Binary Parameter Classification
The quick learn incorrectly classified binary toggles as "continuous". Check:
- `_classify_control_type()` function
- Should detect when label_map has only 2 entries and classify as binary/enum
- Binary params should use exact value matching from label_map

### Priority 2: Fix Master Auto-Enable Logic
The config-driven master enabling (`dependent_master_values`) is not working:
1. Debug device name matching in `_group_role_for_device()` at line ~133
2. Verify config lookup returns correct match_key for "Delay"
3. Check that desired_val is being applied correctly at line ~1349
4. Add logging to trace the execution path

### Priority 3: Improve Toggle Parameter Handling
Need better support for "On"/"Off" text matching:
1. When label_map exists, check for text alternatives (On→1.0, Off→0.0)
2. Add fuzzy matching for common toggle terms
3. Consider "1.0"/"0.0" display strings as binary indicators

## Successful Features

✓ Continuous parameter accuracy (within 1-2% tolerance)
✓ Relative value adjustments
✓ Frequency/time parameter mapping with fit models
✓ Config-driven grouping structure (masters/dependents detected)
✓ Filter dependency detection (Filter Freq/Width depend on Filter On)

## Next Steps

1. Fix binary parameter classification in quick_learn
2. Debug and fix master auto-enable for dependent_master_values
3. Add toggle text matching ("On"/"Off" → 1.0/0.0)
4. Re-test with fixes
5. Consider exhaustive learn for better binary detection
