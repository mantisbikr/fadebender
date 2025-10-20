# Comprehensive Device & NLP Test Plan

**Date:** 2025-01-19
**Scope:** LiveIndex, DeviceResolver, ValueRegistry, Snapshots, NLP hints, Parameter aliases
**Test Duration:** ~2-3 hours

---

## 0. Pre-Test Setup

### Start Stack
```bash
# Terminal 1: Start server
cd server
python -m uvicorn app:app --reload --port 8722

# Terminal 2: Check UDP events are running
# Should see UDP listener messages in server logs

# Terminal 3: Start web UI
cd clients/web-chat
npm start
```

### Enable Debug Logs
```bash
export FB_DEBUG_FIRESTORE=true
export FB_DEBUG_SSE=true
```

### Verify Health
- [ ] **GET** `http://127.0.0.1:8722/health`
  - Expect: `{"status": "ok"}`
- [ ] Check server logs for LiveIndex startup message
  - Expect: "Starting LiveIndex background refresh loop" or similar
  - Expect: Refresh cycle messages every ~60s

### Verify Snapshot Endpoints
- [ ] **GET** `http://127.0.0.1:8722/snapshot`
  - Expect: JSON with `data.devices.returns` and `data.devices.tracks`
  - Verify device names and indices appear
- [ ] **GET** `http://127.0.0.1:8722/snapshot/devices?domain=return&index=0`
  - Expect: Non-empty list with device names, indices, signatures

---

## A. NLP + LLM Hints (Name/Ordinal/Label Resolution)

### A1. Name-Only Resolution (Generic Device Names)

**Test Case:** Generic delay reference
**Command:** "set Return B Align Delay Mode to Distance"

- [ ] Executes without clarification
- [ ] Summary mentions "distance" or "Distance"
- [ ] Capabilities card appears in UI with parameter groups
- [ ] Verify Mode parameter shows "Distance" (value = 2)

**Verify:**
```bash
curl "http://127.0.0.1:8722/return/device/params?index=1&device=0"
# Check Mode parameter value is 2.0
```

---

### A2. Name-Only Resolution (Arbitrary Device Names)

**Setup:** Assume "4th Bandpass" exists in Return A, device index 1

**Test Case:** Arbitrary name reference
**Command:** "set Return A 4th Bandpass mode to Repitch"

- [ ] Executes without clarification (name normalization works)
- [ ] Summary shows "Repitch" or confirms mode change
- [ ] Card appears with device capabilities

**Verify:**
```bash
curl "http://127.0.0.1:8722/return/device/params?index=0&device=1"
# Check Delay Mode or equivalent parameter
```

---

### A3. Name + Ordinal (Valid)

**Setup:** Assume Return B has 2 reverb devices

**Test Case:** Target second reverb by ordinal
**Command:** "set Return B reverb 2 decay to 2 s"

- [ ] Executes without error
- [ ] `device_ordinal_hint` honored (second reverb targeted)
- [ ] Summary shows decay change
- [ ] Correct device index used (verify in response or logs)

**Verify:**
```bash
# Check which device index corresponds to "reverb 2"
curl "http://127.0.0.1:8722/snapshot/devices?domain=return&index=1"
# Then verify decay parameter on that device
```

---

### A4. Name + Ordinal (Invalid - Ordinal Out of Range)

**Setup:** Return A has only 1 "4th Bandpass" device

**Test Case:** Invalid ordinal with exact name
**Command:** "set Return A 4th Bandpass 3 mode to Repitch"

- [ ] Resolves by exact name (ignores invalid ordinal=3)
- [ ] Executes successfully on the single "4th Bandpass"
- [ ] No "ordinal out of range" error
- [ ] Summary confirms mode change

**Alternative:** If this should error, expect friendly clarification with device chips

---

### A5. Generic Ordinal (No Name)

**Setup:** Return A has multiple devices

**Test Case:** Target by ordinal only
**Command:** "set Return A device 2 decay to 2 s"

- [ ] Second device in Return A targeted (from LiveIndex cache)
- [ ] Executes parameter change
- [ ] Summary shows device name and param change

**Verify:**
```bash
curl "http://127.0.0.1:8722/snapshot/devices?domain=return&index=0"
# Confirm device at index=1 (second device) matches
```

---

## B. Fallback Parser Coverage

### B1. Label Selection Parameters

**Test Cases:** Quantized parameters with labels

| Command | Expected Behavior |
|---------|------------------|
| "set Return B Align Delay Mode to Samples" | Mode = 1 (Samples) |
| "set Return A Reverb Quality to High" | Quality = High value |
| "set Return A Delay Type to Repitch" | Type/Mode = Repitch |
| "set Return B Amp Type to Rock" | Amp Type = 3 (Rock) |

For each:
- [ ] Executes without clarification
- [ ] Correct label value set
- [ ] Capabilities card shows updated value

---

### B2. Numeric Device Parameters (with units)

**Test Cases:** Continuous parameters

| Command | Expected Behavior |
|---------|------------------|
| "set Return B Align Delay Left ms to 15 ms" | Left ms = 15 |
| "set Return A Reverb Decay to 2 s" | Decay = 2 s |
| "set track 2 align delay left ms to 15 ms" | Track 2 device param updated |

For each:
- [ ] Correct parameter targeted
- [ ] Display value matches command
- [ ] Summary shows value with unit
- [ ] Readback confirms value

**Verify:**
```bash
# For Return B example:
curl "http://127.0.0.1:8722/return/device/params?index=1&device=0"
# Check "Left ms" or equivalent parameter
```

---

## C. Typo/Variant Tolerance (Parameter Aliases)

### C1. Filter Parameter Variants

**Test:** Low Cut / LoCut / Lo Cut

| Command | Expected Match |
|---------|---------------|
| "set Return A reverb LoCut to 100 Hz" | Matches "Low Cut" param |
| "set Return A reverb Lo Cut to 100 Hz" | Matches "Low Cut" param |
| "set Return A reverb Low Cut to 100 Hz" | Matches "Low Cut" param |
| "set Return A reverb LPF to 100 Hz" | Matches "Low Cut" / "Low-pass" param |

**Test:** High Cut / HiCut / Hi Cut

| Command | Expected Match |
|---------|---------------|
| "set Return A reverb HiCut to 5 kHz" | Matches "High Cut" param |
| "set Return A reverb Hi Cut to 5 kHz" | Matches "High Cut" param |
| "set Return A reverb HPF to 5 kHz" | Matches "High Cut" / "High-pass" param |

For each:
- [ ] Resolves to correct parameter (no clarification needed if unique)
- [ ] If multiple matches, shows clarification chips
- [ ] Executes successfully

---

### C2. Other Parameter Family Aliases

**Test:** Bandwidth / BW / Resonance → Q

| Command | Expected Match |
|---------|---------------|
| "set Return A filter bandwidth to 0.7" | Matches Q or Bandwidth param |
| "set Return A filter BW to 0.7" | Matches Q or Bandwidth param |
| "set Return A filter resonance to 0.7" | Matches Q or Resonance param |

**Test:** Speed → Rate

| Command | Expected Match |
|---------|---------------|
| "set Return A LFO speed to 2 Hz" | Matches Rate param |
| "set Return A LFO rate to 2 Hz" | Matches Rate param |

**Test:** Intensity → Depth

| Command | Expected Match |
|---------|---------------|
| "set Return A effect intensity to 50%" | Matches Depth param |
| "set Return A effect depth to 50%" | Matches Depth param |

**Test:** Amount → Amt

| Command | Expected Match |
|---------|---------------|
| "set Return A LFO amount to 30%" | Matches Amount or Amt param |
| "set Return A LFO amt to 30%" | Matches Amount or Amt param |

**Test:** Feedback → Fbk

| Command | Expected Match |
|---------|---------------|
| "set Return A delay feedback to 40%" | Matches Feedback param |
| "set Return A delay fbk to 40%" | Matches Feedback param |

For each:
- [ ] Resolves correctly
- [ ] If ambiguous, shows chips with all matches
- [ ] Summary uses canonical parameter name

---

## D. Device Resolution + UI Clarification Flow

### D1. No Device Match

**Setup:** Return A has only "4th Bandpass (1)" and "Reverb (1)"

**Test Case:** Request non-existent device
**Command:** "set Return A delay 2 mode to repitch"

**Expected:**
- [ ] Friendly clarification message (not raw error)
- [ ] Chips show available devices:
  - "4th Bandpass (1)"
  - "Reverb (1)"
  - etc.
- [ ] No "device_not_found" raw error code shown to user

**Then:**
- [ ] Click "4th Bandpass (1)" chip
- [ ] Executes: "set Return A 4th Bandpass mode to repitch"
- [ ] Card appears with capabilities

---

### D2. Ordinal Out of Range

**Setup:** Return A has only 1 reverb

**Test Case:** Request ordinal 3
**Command:** "set Return A reverb 3 decay to 2s"

**Expected:**
- [ ] Friendly message (not "ordinal out of range" technical wording)
- [ ] Device list chips appear
- [ ] Click available reverb chip → executes successfully

---

### D3. Parameter Ambiguity

**Setup:** Device has multiple parameters matching query

**Test Case:** Ambiguous param
**Command:** "set Return B reverb hi filter to 10 kHz"

**Expected:**
- [ ] If multiple "hi filter" variants exist: clarification question
- [ ] Parameter chips appear (e.g., "HiFilter Freq", "HiFilter Type")
- [ ] Capabilities card shown below chips (if available)
- [ ] Click correct chip → executes

---

## E. Cards + Capabilities

### E1. Device Parameter Cards

**Test:** Execute device parameter change

**Command:** "set Return B Amp Gain to 7.5"

**Expected:**
- [ ] Execution succeeds
- [ ] Capabilities attached server-side in response
- [ ] UI renders card with:
  - All device parameters
  - Correct groupings (if groups defined)
  - Current values displayed
  - Parameter chips clickable

---

### E2. Clickable Parameter Chips (Read Current Value)

**Test:** Click parameter chip in card

**Setup:** Card is open after executing a command

**Action:**
- [ ] Click a parameter name chip (e.g., "Bass")

**Expected:**
- [ ] Payload sent: `READ_PARAM|B|1|Bass|Screamer`
- [ ] Server reads current value
- [ ] UI displays current value in response

---

### E3. Mixer Cards

**Test:** Mixer command shows mixer card

**Command:** "set Return A volume to -3 dB"

**Expected:**
- [ ] Executes mixer change
- [ ] UI fetches `/return/mixer/capabilities?index=0`
- [ ] Mixer card opens with grouped parameters:
  - Volume, Pan, Sends
  - Current values shown
  - Sliders/controls interactive

---

## F. Registry + Snapshots (Incremental Values)

### F1. Mixer Values in Snapshot

**Test:** Verify mixer write-through

**Steps:**
1. [ ] **GET** `/snapshot` → note current Return A volume
2. [ ] Execute: "set Return A volume to -6 dB"
3. [ ] **GET** `/snapshot` again

**Expected:**
- [ ] `data.mixer.returns[0].volume` updated
- [ ] Contains:
  - `normalized` value
  - `display` value (-6.0)
  - `unit` (dB)
  - `timestamp`

---

### F2. Device Params NOT in Snapshot

**Test:** Verify device params stored separately

**Steps:**
1. [ ] Execute: "set Return B Amp Gain to 8.0"
2. [ ] **GET** `/snapshot`

**Expected:**
- [ ] Device parameter NOT in `data.devices` (by design)
- [ ] Only mixer values in snapshot
- [ ] Check server logs: ValueRegistry write-through + readback logged

---

### F3. Write-Through + Readback

**Test:** Rapid parameter change shows updated value

**Steps:**
1. [ ] Execute: "set Return B Amp Gain to 5.0"
2. [ ] Immediately: **GET** `/return/device/params?index=1&device=1`

**Expected:**
- [ ] Gain shows 5.0 (write-through ensures registry updated)
- [ ] No stale cached values

---

## G. LiveIndex Freshness

### G1. Device List Refresh After Changes in Live

**Test:** Rename device in Ableton Live

**Steps:**
1. [ ] In Live: Rename "Screamer" to "Super Screamer" in Return B
2. [ ] Wait ~60 seconds (refresh cycle)
3. [ ] **GET** `/snapshot/devices?domain=return&index=1`

**Expected:**
- [ ] Device list shows "Super Screamer"
- [ ] Index unchanged

---

### G2. Resolution During Refresh Gap

**Test:** Command before refresh cycle completes

**Steps:**
1. [ ] Rename device in Live
2. [ ] Immediately (within 60s): "set Return B Screamer Gain to 6"

**Expected:**
- [ ] Resolves using normalization + contains matching
- [ ] Old name still matches
- [ ] Executes successfully (fallback to Live query if cache stale)

---

### G3. Re-order Devices

**Test:** Swap device order in Live

**Steps:**
1. [ ] In Live: Move reverb from index 0 to index 2 in Return A
2. [ ] Wait ~60s
3. [ ] **GET** `/snapshot/devices?domain=return&index=0`

**Expected:**
- [ ] Device indices updated in snapshot
- [ ] Next command uses new indices

---

## H. Performance/Resilience

### H1. Rapid Command Series

**Test:** Send 20 commands in succession

**Commands:**
```
set Return A volume to -3 dB
set Return A pan to 10% left
set Return B volume to -6 dB
set Return B Amp Gain to 7
set Return A Reverb Decay to 3 s
... (15 more similar)
```

**Expected:**
- [ ] All commands execute without noticeable lag
- [ ] No repeated clarifications for same device/param
- [ ] No server errors
- [ ] Snapshot updates incrementally

---

### H2. Server Restart Resilience

**Test:** Restart server mid-session

**Steps:**
1. [ ] Execute a few commands
2. [ ] Restart server (`Ctrl+C` and restart)
3. [ ] Wait for LiveIndex refresh (check logs)
4. [ ] Execute: "set Return B Amp Gain to 5"

**Expected:**
- [ ] Snapshot returns quickly after startup
- [ ] LiveIndex cache populated within 60s
- [ ] Command resolves correctly using fresh cache

---

## I. Error Paths (Friendly Messages)

### I1. Parameter Not Found

**Test:** Non-existent parameter

**Command:** "set Return B reverb nonexistent to 100"

**Expected:**
- [ ] Friendly message: "I couldn't find a parameter..."
- [ ] If possible, suggest similar params (optional)
- [ ] NO raw "param_not_found" error code visible

---

### I2. Parameter Ambiguous

**Test:** Multiple matches

**Command:** "set Return B reverb hi filter to 10 kHz"

**Expected:**
- [ ] Question message with parameter chips
- [ ] If capabilities available, card shown below chips
- [ ] Clicking chip executes with selected param

---

### I3. Device Not Found

**Test:** Non-existent device

**Command:** "set Return A nonexistent delay mode to fade"

**Expected:**
- [ ] Friendly message with available device chips
- [ ] NO "device_not_found_for_hint" raw error
- [ ] Chips show actual device names

---

### I4. Invalid Value

**Test:** Out-of-range value

**Command:** "set Return B Amp Gain to 999"

**Expected:**
- [ ] Clamped to max (10.0) OR friendly error
- [ ] Summary explains clamping/limit
- [ ] NO raw exception visible

---

## J. API Direct Tests (curl/Postman)

### J1. Intent Parse

```bash
curl -X POST "http://127.0.0.1:8722/intent/parse" \
  -H "Content-Type: application/json" \
  -d '{"utterance": "set Return A reverb decay to 2 s"}'
```

**Expected:**
- [ ] `raw_intent` with LLM interpretation
- [ ] `canonical_intent` with domain/return_index/param_ref/display

---

### J2. Intent Execute - Return Device

```bash
curl -X POST "http://127.0.0.1:8722/intent/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "domain": "device",
    "return_index": 1,
    "device_index": 1,
    "param_ref": "Gain",
    "display": "7.5"
  }'
```

**Expected:**
- [ ] `ok: true`
- [ ] `summary` describes change
- [ ] `data.capabilities` present

---

### J3. Intent Execute - Track Mixer

```bash
curl -X POST "http://127.0.0.1:8722/intent/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "domain": "track",
    "track_index": 0,
    "field": "volume",
    "display": "-6",
    "unit": "dB"
  }'
```

**Expected:**
- [ ] `ok: true`
- [ ] `summary` with "decreasing" or similar
- [ ] Track volume updated

---

### J4. Intent Execute - Return Mixer

```bash
curl -X POST "http://127.0.0.1:8722/intent/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "domain": "return",
    "return_index": 0,
    "field": "volume",
    "display": "-3",
    "unit": "dB"
  }'
```

**Expected:**
- [ ] `ok: true`
- [ ] `/snapshot` shows updated return volume

---

### J5. Snapshot Endpoints

```bash
# Full snapshot
curl "http://127.0.0.1:8722/snapshot"

# Device list
curl "http://127.0.0.1:8722/snapshot/devices?domain=return&index=0"
curl "http://127.0.0.1:8722/snapshot/devices?domain=track&index=1"
```

**Expected:**
- [ ] JSON structure with devices, mixer values, timestamps
- [ ] Device lists non-empty

---

### J6. Intent Read - Mixer

```bash
curl -X POST "http://127.0.0.1:8722/intent/read" \
  -H "Content-Type: application/json" \
  -d '{
    "domain": "return",
    "return_index": 0,
    "field": "volume"
  }'
```

**Expected:**
- [ ] Current volume value with display conversion
- [ ] Normalized and display values present

---

## K. Acceptance Criteria (Summary Checklist)

- [ ] **Device selection by name** works for generic names (reverb, delay) and arbitrary names (4th Bandpass)
- [ ] **Invalid ordinals ignored** when exact device name exists
- [ ] **Clarification chips** always appear for device/param mismatches
- [ ] **Clicking chips** executes the command successfully
- [ ] **Cards render consistently** after device param changes (capabilities attached or fetched)
- [ ] **Parameter chips clickable** to read current values
- [ ] **/snapshot** returns valid structure with mixer values
- [ ] **Mixer write-through** visible within one operation
- [ ] **No regressions** on existing mixer/send flows
- [ ] **Summaries use display-aware** language (increasing/decreasing)
- [ ] **Alias matching works** for all documented variants (LoCut, BW, speed, etc.)
- [ ] **LiveIndex refreshes** every ~60s and updates device lists
- [ ] **Friendly error messages** - no raw error codes visible to users

---

## L. Optional Automation

### L1. Python Test Script

Create `/scripts/test_nlp_integration.py`:

```python
#!/usr/bin/env python3
"""Automated integration tests for NLP + device resolution."""
import requests
import time

BASE_URL = "http://127.0.0.1:8722"

test_cases = [
    {
        "name": "Return device by name",
        "utterance": "set Return B Align Delay Mode to Distance",
        "expect_ok": True,
        "expect_summary_contains": "distance"
    },
    {
        "name": "Arbitrary device name",
        "utterance": "set Return A 4th Bandpass mode to Repitch",
        "expect_ok": True
    },
    {
        "name": "Alias: LoCut → Low Cut",
        "utterance": "set Return A reverb LoCut to 100 Hz",
        "expect_ok": True
    },
    # Add more cases...
]

def run_tests():
    passed = 0
    failed = 0

    for test in test_cases:
        print(f"\nTesting: {test['name']}")
        resp = requests.post(
            f"{BASE_URL}/intent/parse",
            json={"utterance": test["utterance"]},
            timeout=10
        )

        if resp.status_code == 200:
            data = resp.json()
            ok = data.get("ok", False)

            if test.get("expect_ok") and ok:
                summary = data.get("summary", "")
                if test.get("expect_summary_contains"):
                    if test["expect_summary_contains"].lower() in summary.lower():
                        print(f"  ✓ PASS")
                        passed += 1
                    else:
                        print(f"  ✗ FAIL - summary doesn't contain '{test['expect_summary_contains']}'")
                        failed += 1
                else:
                    print(f"  ✓ PASS")
                    passed += 1
            else:
                print(f"  ✗ FAIL - ok={ok}")
                failed += 1
        else:
            print(f"  ✗ FAIL - HTTP {resp.status_code}")
            failed += 1

    print(f"\n{'='*50}")
    print(f"Results: {passed} passed, {failed} failed")
    return failed == 0

if __name__ == "__main__":
    import sys
    sys.exit(0 if run_tests() else 1)
```

Run with:
```bash
python3 scripts/test_nlp_integration.py
```

---

### L2. Snapshot Diff Script

Create `/scripts/test_snapshot_diff.py`:

```python
#!/usr/bin/env python3
"""Test mixer write-through by comparing snapshots."""
import requests
import json

BASE_URL = "http://127.0.0.1:8722"

def get_snapshot():
    resp = requests.get(f"{BASE_URL}/snapshot")
    return resp.json()

def test_mixer_write_through():
    # Get baseline
    before = get_snapshot()
    before_volume = before.get("data", {}).get("mixer", {}).get("returns", [{}])[0].get("volume", {})

    print(f"Before: Return A volume = {before_volume.get('display')}")

    # Execute change
    requests.post(
        f"{BASE_URL}/intent/execute",
        json={
            "domain": "return",
            "return_index": 0,
            "field": "volume",
            "display": "-6",
            "unit": "dB"
        }
    )

    # Get after
    after = get_snapshot()
    after_volume = after.get("data", {}).get("mixer", {}).get("returns", [{}])[0].get("volume", {})

    print(f"After: Return A volume = {after_volume.get('display')}")

    if float(after_volume.get("display", 0)) == -6.0:
        print("✓ PASS - Volume updated in snapshot")
        return True
    else:
        print("✗ FAIL - Volume not updated")
        return False

if __name__ == "__main__":
    import sys
    sys.exit(0 if test_mixer_write_through() else 1)
```

---

## M. Test Execution Tracking

Use this checklist to track progress:

| Section | Test Count | Passed | Failed | Notes |
|---------|-----------|--------|--------|-------|
| A. NLP Hints | 5 | | | |
| B. Fallback Parser | 8 | | | |
| C. Aliases | 15+ | | | |
| D. Device Resolution | 3 | | | |
| E. Cards | 3 | | | |
| F. Registry | 3 | | | |
| G. LiveIndex | 3 | | | |
| H. Performance | 2 | | | |
| I. Error Paths | 4 | | | |
| J. API Tests | 6 | | | |
| K. Acceptance | 13 | | | |

---

## N. Known Issues / Edge Cases to Watch

1. **LiveIndex refresh timing**: Commands during 60s gap may use stale cache
2. **Device name changes**: Old names should still resolve temporarily
3. **Multiple devices same name**: Ordinal becomes critical
4. **Parameter ambiguity**: Some devices have similar param names
5. **Unit conversion edge cases**: ms/s, Hz/kHz conversions
6. **Snapshot size**: Large device counts may impact performance

---

## O. Post-Test Actions

After completing all tests:

1. [ ] Document any failures in GitHub issues
2. [ ] Update this test plan with new findings
3. [ ] Add regression tests for fixed bugs
4. [ ] Consider adding to CI/CD pipeline
5. [ ] Update user documentation with new capabilities

---

**END OF TEST PLAN**
