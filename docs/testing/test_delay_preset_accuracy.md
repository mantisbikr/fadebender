# Test Plan: Verify delay_delay Preset Accuracy

## Issue
The `delay_delay` preset shows discrepancy between stored Firestore values and actual Live state:
- **Firestore**: L Sync=0.0 (OFF), R Sync=1.0 (ON)
- **Live UI**: Left=TIME 245ms, Right=TIME 245ms (suggests BOTH syncs OFF)

## Test Procedure

### Step 1: Capture Current State
1. In Ableton Live, load a Delay device on Return A
2. Set it to your current state (both TIME mode, 245ms each)
3. Note the exact parameter values:
   ```
   L Sync: [  ] (checkbox state)
   L Time: 245 ms
   L 16th: [value if visible]
   R Sync: [  ] (checkbox state)
   R Time: 245 ms
   R 16th: [value if visible]
   ```

### Step 2: Load Stored Preset
Run this command to load the `delay_delay` preset:
```bash
curl -X POST http://127.0.0.1:8722/api/return/0/device/0/preset/delay_delay
```

### Step 3: Read Actual Loaded State
After loading, check the Live UI and note:
```
L Sync: [  ] (checkbox state)
L Time: [value] ms
L 16th: [value] 16ths (if Sync is ON)
R Sync: [  ] (checkbox state)
R Time: [value] ms
R 16th: [value] 16ths (if Sync is ON)
```

Also run this to see what the server reads:
```bash
curl -s http://127.0.0.1:8722/api/return/0/device/0 | jq '.parameters[] | select(.name | test("Sync|Time|16th"; "i")) | {name, value, display}'
```

### Step 4: Analysis
Compare:
1. **Firestore stored values** (L Sync=0.0, R Sync=1.0)
2. **Actual loaded UI state** (what you see after Step 2)
3. **Server read values** (from curl command)

### Step 5: Restore Original State
Manually set the delay back to your original state from Step 1.

## Expected Findings

If Firestore values are **correct**:
- After loading, Left should be TIME mode ~120ms
- After loading, Right should be SYNC mode ~5 sixteenths

If Firestore values are **incorrect** (as suspected):
- After loading, BOTH might be in TIME mode
- Or values might be different from what's stored
- This indicates the **capture process didn't record the actual state**

## Root Cause Hypotheses

1. **Capture timing issue**: When preset was captured, Ableton might have sent old parameter values before the device fully loaded
2. **Grouping logic in capture**: The capture process might store ALL parameters even when some are inactive
3. **Normalized value confusion**: The normalized values might not correctly represent the sync state

## Next Steps Based on Results

If values mismatch:
1. Fix the capture/learning process to respect grouping rules
2. Re-capture delay_delay preset correctly
3. Update enrichment to use corrected values
4. Potentially re-capture ALL delay presets

If values match:
1. Investigate why Live UI shows different values than stored
2. Check if there's a display vs. internal value discrepancy
