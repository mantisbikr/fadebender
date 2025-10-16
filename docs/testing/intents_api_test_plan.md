# Intents API Live Testing Plan

**Date:** 2025-10-15 (Updated with Letter-Based API)
**Tester:** _____________
**Live Version:** _____________

## 🆕 NEW: Letter-Based API

**This test plan now uses the improved letter-based API for sends and returns!**

- ✅ **Tracks:** Still use `track_index: 1` for Track 1 (1-based, matches Live UI)
- ✅ **Sends:** Use `send_ref: "A"` for Send A (instead of `send_index: 0`)
- ✅ **Returns:** Use `return_ref: "A"` for Return A (instead of `return_index: 0`)

**Why letter-based?**
- Matches how Live displays sends and returns (Send A, Return B, etc.)
- More intuitive for natural language commands
- Easier to read and understand

**Legacy numeric API still works** but letter-based is preferred.

---

## Setup Requirements
- [ ] Ableton Live running
- [ ] Server running on port 8722 (`cd server && make dev-returns`)
- [ ] At least 3 audio tracks in Live set
- [ ] At least 2 return tracks (Return A, Return B)
- [ ] Return A has a Reverb device (for device tests)

---

## Test Format
- **Display Values:** Use human-readable values (e.g., `-6` for -6dB, `20` for 20% right pan)
- **Pass Criteria:** Mark `y` if the value in Live matches expected, `n` if wrong, `skip` if cannot test
- **Notes:** Add any observations in the Notes column

---

## PART 1: TRACK VOLUME (dB)

| # | Curl Command | Expected Result | Pass (y/n/skip) | Notes |
|---|--------------|-----------------|-----------------|-------|
| 1 | `curl -X POST http://127.0.0.1:8722/intent/execute -H "Content-Type: application/json" -d '{"domain":"track","action":"set","track_index":1,"field":"volume","value":-6,"unit":"dB"}'` | Track 1 volume shows `-6.0 dB` | y | |
| 2 | `curl -X POST http://127.0.0.1:8722/intent/execute -H "Content-Type: application/json" -d '{"domain":"track","action":"set","track_index":1,"field":"volume","value":0,"unit":"dB"}'` | Track 1 volume shows `0.0 dB` (unity gain) | y | |
| 3 | `curl -X POST http://127.0.0.1:8722/intent/execute -H "Content-Type: application/json" -d '{"domain":"track","action":"set","track_index":1,"field":"volume","value":3,"unit":"dB"}'` | Track 1 volume shows `+3.0 dB` (NOT -3 dB!) | y | |
| 4 | `curl -X POST http://127.0.0.1:8722/intent/execute -H "Content-Type: application/json" -d '{"domain":"track","action":"set","track_index":1,"field":"volume","value":-12,"unit":"dB"}'` | Track 1 volume shows `-12.0 dB` | y | |
| 5 | `curl -X POST http://127.0.0.1:8722/intent/execute -H "Content-Type: application/json" -d '{"domain":"track","action":"set","track_index":2,"field":"volume","value":-3,"unit":"dB"}'` | Track 2 volume shows `-3.0 dB` | y | |
| 6 | `curl -X POST http://127.0.0.1:8722/intent/execute -H "Content-Type: application/json" -d '{"domain":"track","action":"set","track_index":1,"field":"volume","value":6,"unit":"dB"}'` | Track 1 volume shows `+6.0 dB` (maximum) | y | |
| 7 | `curl -X POST http://127.0.0.1:8722/intent/execute -H "Content-Type: application/json" -d '{"domain":"track","action":"set","track_index":1,"field":"volume","value":-60,"unit":"dB"}'` | Track 1 volume shows `-60.0 dB` (minimum) | y | |

---

## PART 2: TRACK PAN

**Note:** Pan values: `-100` = full left, `0` = center, `100` = full right

| # | Curl Command | Expected Result | Pass (y/n/skip) | Notes |
|---|--------------|-----------------|-----------------|-------|
| 8 | `curl -X POST http://127.0.0.1:8722/intent/execute -H "Content-Type: application/json" -d '{"domain":"track","action":"set","track_index":1,"field":"pan","value":-50}'` | Track 1 pan shows `50L` | y | |
| 9 | `curl -X POST http://127.0.0.1:8722/intent/execute -H "Content-Type: application/json" -d '{"domain":"track","action":"set","track_index":1,"field":"pan","value":30}'` | Track 1 pan shows `30R` | n | Got 50R when i tried 30. tried other values and they all either went to 50R or -50L if i gave -ve numbers |
| 10 | `curl -X POST http://127.0.0.1:8722/intent/execute -H "Content-Type: application/json" -d '{"domain":"track","action":"set","track_index":1,"field":"pan","value":0}'` | Track 1 pan shows `C` (center) | y | |
| 11 | `curl -X POST http://127.0.0.1:8722/intent/execute -H "Content-Type: application/json" -d '{"domain":"track","action":"set","track_index":2,"field":"pan","value":-100}'` | Track 2 pan shows `100L` (full left) | y | passed now|
| 12 | `curl -X POST http://127.0.0.1:8722/intent/execute -H "Content-Type: application/json" -d '{"domain":"track","action":"set","track_index":2,"field":"pan","value":100}'` | Track 2 pan shows `100R` (full right) | y | passed now |

---

## PART 3: TRACK MUTE/SOLO

**Note:** `1` = on/enabled, `0` = off/disabled

| # | Curl Command | Expected Result | Pass (y/n/skip) | Notes |
|---|--------------|-----------------|-----------------|-------|
| 13 | `curl -X POST http://127.0.0.1:8722/intent/execute -H "Content-Type: application/json" -d '{"domain":"track","action":"set","track_index":1,"field":"mute","value":1}'` | Track 1 mute button lit (orange) | y | |
| 14 | `curl -X POST http://127.0.0.1:8722/intent/execute -H "Content-Type: application/json" -d '{"domain":"track","action":"set","track_index":1,"field":"mute","value":0}'` | Track 1 mute button off (gray) | y | |
| 15 | `curl -X POST http://127.0.0.1:8722/intent/execute -H "Content-Type: application/json" -d '{"domain":"track","action":"set","track_index":2,"field":"solo","value":1}'` | Track 2 solo button lit (blue) | y | |
| 16 | `curl -X POST http://127.0.0.1:8722/intent/execute -H "Content-Type: application/json" -d '{"domain":"track","action":"set","track_index":2,"field":"solo","value":0}'` | Track 2 solo button off (gray) | y | |
| 17 | `curl -X POST http://127.0.0.1:8722/intent/execute -H "Content-Type: application/json" -d '{"domain":"track","action":"set","track_index":3,"field":"mute","value":1}'` | Track 3 mute button lit | y | |

---

## PART 4: TRACK SENDS (dB) - Letter-Based

**Note:** Send range is `-60 dB` to `0 dB` (sends don't go positive)
**NEW:** Use `send_ref: "A"` instead of `send_index: 0` for better readability

| # | Curl Command | Expected Result | Pass (y/n/skip) | Notes |
|---|--------------|-----------------|-----------------|-------|
| 18 | `curl -X POST http://127.0.0.1:8722/intent/execute -H "Content-Type: application/json" -d '{"domain":"track","action":"set","track_index":1,"field":"send","send_ref":"A","value":-12,"unit":"dB"}'` | Track 1 Send A shows `-12.0 dB` |y | |
| 19 | `curl -X POST http://127.0.0.1:8722/intent/execute -H "Content-Type: application/json" -d '{"domain":"track","action":"set","track_index":1,"field":"send","send_ref":"A","value":0,"unit":"dB"}'` | Track 1 Send A shows `0.0 dB` (max for sends) | y | |
| 20 | `curl -X POST http://127.0.0.1:8722/intent/execute -H "Content-Type: application/json" -d '{"domain":"track","action":"set","track_index":1,"field":"send","send_ref":"B","value":-20,"unit":"dB"}'` | Track 1 Send B shows `-20.0 dB` | y | |
| 21 | `curl -X POST http://127.0.0.1:8722/intent/execute -H "Content-Type: application/json" -d '{"domain":"track","action":"set","track_index":2,"field":"send","send_ref":"A","value":-6,"unit":"dB"}'` | Track 2 Send A shows `-6.0 dB` | y | |
| 22 | `curl -X POST http://127.0.0.1:8722/intent/execute -H "Content-Type: application/json" -d '{"domain":"track","action":"set","track_index":1,"field":"send","send_ref":"A","value":-60,"unit":"dB"}'` | Track 1 Send A shows `-60.0 dB` (minimum) | y | |

---

## PART 5: RETURN TRACK VOLUME (dB) - Letter-Based

**NEW:** Use `return_ref: "A"` instead of `return_index: 0` for better readability

| # | Curl Command | Expected Result | Pass (y/n/skip) | Notes |
|---|--------------|-----------------|-----------------|-------|
| 23 | `curl -X POST http://127.0.0.1:8722/intent/execute -H "Content-Type: application/json" -d '{"domain":"return","action":"set","return_ref":"A","field":"volume","value":-3,"unit":"dB"}'` | Return A volume shows `-3.0 dB` | y | |
| 24 | `curl -X POST http://127.0.0.1:8722/intent/execute -H "Content-Type: application/json" -d '{"domain":"return","action":"set","return_ref":"A","field":"volume","value":0,"unit":"dB"}'` | Return A volume shows `0.0 dB` | y | |
| 25 | `curl -X POST http://127.0.0.1:8722/intent/execute -H "Content-Type: application/json" -d '{"domain":"return","action":"set","return_ref":"B","field":"volume","value":-6,"unit":"dB"}'` | Return B volume shows `-6.0 dB` | y | |
| 26 | `curl -X POST http://127.0.0.1:8722/intent/execute -H "Content-Type: application/json" -d '{"domain":"return","action":"set","return_ref":"A","field":"volume","value":6,"unit":"dB"}'` | Return A volume shows `+6.0 dB` (max) | y | |

---

## PART 6: RETURN TRACK PAN - Letter-Based

| # | Curl Command | Expected Result | Pass (y/n/skip) | Notes |
|---|--------------|-----------------|-----------------|-------|
| 27 | `curl -X POST http://127.0.0.1:8722/intent/execute -H "Content-Type: application/json" -d '{"domain":"return","action":"set","return_ref":"A","field":"pan","value":-50}'` | Return A pan shows `50L` | y | |
| 28 | `curl -X POST http://127.0.0.1:8722/intent/execute -H "Content-Type: application/json" -d '{"domain":"return","action":"set","return_ref":"A","field":"pan","value":50}'` | Return A pan shows `50R` | y | |
| 29 | `curl -X POST http://127.0.0.1:8722/intent/execute -H "Content-Type: application/json" -d '{"domain":"return","action":"set","return_ref":"A","field":"pan","value":0}'` | Return A pan shows `C` | y | I tested additional values like -20, 25 etc. adn they work as well.|

---

## PART 7: RETURN TRACK MUTE/SOLO - Letter-Based

| # | Curl Command | Expected Result | Pass (y/n/skip) | Notes |
|---|--------------|-----------------|-----------------|-------|
| 30 | `curl -X POST http://127.0.0.1:8722/intent/execute -H "Content-Type: application/json" -d '{"domain":"return","action":"set","return_ref":"A","field":"mute","value":1}'` | Return A mute button lit | y | |
| 31 | `curl -X POST http://127.0.0.1:8722/intent/execute -H "Content-Type: application/json" -d '{"domain":"return","action":"set","return_ref":"A","field":"mute","value":0}'` | Return A mute button off | y | |
| 32 | `curl -X POST http://127.0.0.1:8722/intent/execute -H "Content-Type: application/json" -d '{"domain":"return","action":"set","return_ref":"B","field":"solo","value":1}'` | Return B solo button lit | y | |

---

## PART 8: RETURN SENDS (dB) - Letter-Based

**Note:** Return tracks can send to other return tracks

| # | Curl Command | Expected Result | Pass (y/n/skip) | Notes |
|---|--------------|-----------------|-----------------|-------|
| 33 | `curl -X POST http://127.0.0.1:8722/intent/execute -H "Content-Type: application/json" -d '{"domain":"return","action":"set","return_ref":"A","field":"send","send_ref":"B","value":-10,"unit":"dB"}'` | Return A Send B shows `-10.0 dB` | y | |
| 34 | `curl -X POST http://127.0.0.1:8722/intent/execute -H "Content-Type: application/json" -d '{"domain":"return","action":"set","return_ref":"B","field":"send","send_ref":"A","value":-15,"unit":"dB"}'` | Return B Send A shows `-15.0 dB` | y | |

---

## PART 9: MASTER TRACK VOLUME (dB)

| # | Curl Command | Expected Result | Pass (y/n/skip) | Notes |
|---|--------------|-----------------|-----------------|-------|
| 35 | `curl -X POST http://127.0.0.1:8722/intent/execute -H "Content-Type: application/json" -d '{"domain":"master","action":"set","field":"volume","value":-6,"unit":"dB"}'` | Master volume shows `-6.0 dB` | y | |
| 36 | `curl -X POST http://127.0.0.1:8722/intent/execute -H "Content-Type: application/json" -d '{"domain":"master","action":"set","field":"volume","value":0,"unit":"dB"}'` | Master volume shows `0.0 dB` | y | |
| 37 | `curl -X POST http://127.0.0.1:8722/intent/execute -H "Content-Type: application/json" -d '{"domain":"master","action":"set","field":"volume","value":-3,"unit":"dB"}'` | Master volume shows `-3.0 dB` | y | |

---

## PART 10: MASTER TRACK PAN

| # | Curl Command | Expected Result | Pass (y/n/skip) | Notes |
|---|--------------|-----------------|-----------------|-------|
| 38 | `curl -X POST http://127.0.0.1:8722/intent/execute -H "Content-Type: application/json" -d '{"domain":"master","action":"set","field":"pan","value":30}'` | Master pan shows `30R` | y | |
| 39 | `curl -X POST http://127.0.0.1:8722/intent/execute -H "Content-Type: application/json" -d '{"domain":"master","action":"set","field":"pan","value":-30}'` | Master pan shows `30L` | y  |  |
| 40 | `curl -X POST http://127.0.0.1:8722/intent/execute -H "Content-Type: application/json" -d '{"domain":"master","action":"set","field":"pan","value":0}'` | Master pan shows `C` | y | |

---

## PART 11: 1-BASED INDEXING VERIFICATION

**Critical Tests:** Verify that Track 1 = first track (not second)

| # | Curl Command | Expected Result | Pass (y/n/skip) | Notes |
|---|--------------|-----------------|-----------------|-------|
| 41 | `curl -X POST http://127.0.0.1:8722/intent/execute -H "Content-Type: application/json" -d '{"domain":"track","action":"set","track_index":1,"field":"volume","value":-10,"unit":"dB"}'` | **FIRST track** (Track 1) shows `-10.0 dB` | y | |
| 42 | `curl -X POST http://127.0.0.1:8722/intent/execute -H "Content-Type: application/json" -d '{"domain":"track","action":"set","track_index":2,"field":"volume","value":-15,"unit":"dB"}'` | **SECOND track** (Track 2) shows `-15.0 dB` | y | |
| 43 | `curl -X POST http://127.0.0.1:8722/intent/execute -H "Content-Type: application/json" -d '{"domain":"track","action":"set","track_index":3,"field":"volume","value":-20,"unit":"dB"}'` | **THIRD track** (Track 3) shows `-20.0 dB` | y | |

---

## PART 12: EDGE CASES - CLAMPING

**Test that values outside valid ranges are properly clamped**

| # | Curl Command | Expected Result | Pass (y/n/skip) | Notes |
|---|--------------|-----------------|-----------------|-------|
| 44 | `curl -X POST http://127.0.0.1:8722/intent/execute -H "Content-Type: application/json" -d '{"domain":"track","action":"set","track_index":1,"field":"volume","value":-100,"unit":"dB"}'` | Track 1 volume shows `-60.0 dB` (clamped to min) | y | |
| 45 | `curl -X POST http://127.0.0.1:8722/intent/execute -H "Content-Type: application/json" -d '{"domain":"track","action":"set","track_index":1,"field":"volume","value":20,"unit":"dB"}'` | Track 1 volume shows `+6.0 dB` (clamped to max) | y | |
| 46 | `curl -X POST http://127.0.0.1:8722/intent/execute -H "Content-Type: application/json" -d '{"domain":"track","action":"set","track_index":1,"field":"send","send_index":1,"value":10,"unit":"dB"}'` | Track 1 Send A shows `0.0 dB` (sends clamp at 0) | y | |

---

## PART 13: REVERB DEVICE PARAMETERS - Letter-Based

**Prerequisites:** Return A must have a Reverb device (or any device with adjustable parameters)

**Note:** These use fuzzy matching on parameter names. Uses display values with proper units from Firestore.

| # | Curl Command | Expected Result | Pass (y/n/skip) | Notes |
|---|--------------|-----------------|-----------------|-------|
| 47 | `curl -X POST http://127.0.0.1:8722/intent/execute -H "Content-Type: application/json" -d '{"domain":"device","action":"set","return_ref":"A","device_index":0,"param_ref":"decay","value":2000,"unit":"ms"}'` | Return A, Device 1, Decay Time at 2.0s | y | Decay Time in ms |
| 48 | `curl -X POST http://127.0.0.1:8722/intent/execute -H "Content-Type: application/json" -d '{"domain":"device","action":"set","return_ref":"A","device_index":0,"param_ref":"decay","value":5000,"unit":"ms"}'` | Return A, Device 1, Decay Time at 5.0s | y | Decay Time in ms |
| 49 | `curl -X POST http://127.0.0.1:8722/intent/execute -H "Content-Type: application/json" -d '{"domain":"device","action":"set","return_ref":"A","device_index":0,"param_ref":"predelay","value":20,"unit":"ms"}'` | Return A, Device 1, Predelay at 20ms | y | Predelay in ms |
| 50 | `curl -X POST http://127.0.0.1:8722/intent/execute -H "Content-Type: application/json" -d '{"domain":"device","action":"set","return_ref":"A","device_index":0,"param_ref":"dry","value":50,"unit":"%"}'` | Return A, Device 1, Dry/Wet at 50% | y | Dry/Wet in % |

---

## PART 14: REVERB DEPENDENT PARAMETERS (AUTO-ENABLE MASTERS)

These tests verify that dependent parameters (e.g., Chorus Rate/Amount, ER Spin Rate/Amount, Shelves/Filters) either:
- auto-enable their master toggle (e.g., "Chorus On") before applying the dependent, or
- in dry_run mode, preview a `pre` operation indicating auto-enable will occur.

Assumptions
- Return A (`return_ref:"A"`) has a Reverb instance at `device_index: 0`.
- Parameter names below use substring matching (`param_ref`) and may vary slightly per Live version.
- For readback verification, numeric `return_index` is 0 for Return A.

Helper: Verify current device params (readback)
- `curl -s "http://127.0.0.1:8722/return/device/params?index=0&device=0" | jq`
  - Find `"Chorus On"`, `"ER Spin On"`, `"LowShelf On"`, `"HiShelf On"`, `"HiFilter On"` and their dependents.

14.1 Chorus Group
- Dry-run dependent (should preview pre=auto_enable_master):
  - `curl -s -X POST http://127.0.0.1:8722/intent/execute -H 'Content-Type: application/json' -d '{"domain":"device","action":"set","return_ref":"A","device_index":0,"param_ref":"Chorus Amount","value":30,"unit":"percent","dry_run":true}' | jq`
  - Expect: JSON contains `preview.pre.note == "auto_enable_master"` and a pre op for `Chorus On`.
- Execute dependent (auto-enable happens):
  - `curl -s -X POST http://127.0.0.1:8722/intent/execute -H 'Content-Type: application/json' -d '{"domain":"device","action":"set","return_ref":"A","device_index":0,"param_ref":"Chorus Amount","value":30,"unit":"percent"}' | jq`
  - Verify: GET params and confirm `"Chorus On"` value ~1.0 and Chorus Amount reflects target.
- Set Chorus Rate by display:
  - `curl -s -X POST http://127.0.0.1:8722/intent/execute -H 'Content-Type: application/json' -d '{"domain":"device","action":"set","return_ref":"A","device_index":0,"param_ref":"Chorus Rate","display":"0.5 Hz"}' | jq`

14.2 ER Spin Group (Early Reflections)
- Dry-run dependent:
  - `curl -s -X POST http://127.0.0.1:8722/intent/execute -H 'Content-Type: application/json' -d '{"domain":"device","action":"set","return_ref":"A","device_index":0,"param_ref":"ER Spin Amount","value":40,"unit":"percent","dry_run":true}' | jq`
  - Expect: `preview.pre.note == "auto_enable_master"` for `ER Spin On`.
- Execute dependent (auto-enable):
  - `curl -s -X POST http://127.0.0.1:8722/intent/execute -H 'Content-Type: application/json' -d '{"domain":"device","action":"set","return_ref":"A","device_index":0,"param_ref":"ER Spin Amount","value":40,"unit":"percent"}' | jq`
  - Verify via GET params that `ER Spin On` ~1.0.
- Set ER Spin Rate by display:
  - `curl -s -X POST http://127.0.0.1:8722/intent/execute -H 'Content-Type: application/json' -d '{"domain":"device","action":"set","return_ref":"A","device_index":0,"param_ref":"ER Spin Rate","display":"0.3 Hz"}' | jq`

14.3 Tail Shelves (Low/High)
- LowShelf On + Freq/Gain
  - Dry-run dependent (LowShelf Freq):
    - `curl -s -X POST http://127.0.0.1:8722/intent/execute -H 'Content-Type: application/json' -d '{"domain":"device","action":"set","return_ref":"A","device_index":0,"param_ref":"LowShelf Freq","display":"200 Hz","dry_run":true}' | jq`
    - Expect: `preview.pre.note == "auto_enable_master"` for `LowShelf On`.
  - Execute LowShelf Freq 200 Hz:
    - `curl -s -X POST http://127.0.0.1:8722/intent/execute -H 'Content-Type: application/json' -d '{"domain":"device","action":"set","return_ref":"A","device_index":0,"param_ref":"LowShelf Freq","display":"200 Hz"}' | jq`
  - Execute LowShelf Gain 0.5 (unitless, range 0.0-1.0):
    - `curl -s -X POST http://127.0.0.1:8722/intent/execute -H 'Content-Type: application/json' -d '{"domain":"device","action":"set","return_ref":"A","device_index":0,"param_ref":"LowShelf Gain","display":"0.5"}' | jq`
- HiFilter On + Freq/Type + HiShelf Gain
  - Dry-run dependent (HiFilter Freq):
    - `curl -s -X POST http://127.0.0.1:8722/intent/execute -H 'Content-Type: application/json' -d '{"domain":"device","action":"set","return_ref":"A","device_index":0,"param_ref":"HiFilter Freq","display":"5000 Hz","dry_run":true}' | jq`
    - Expect: `preview.pre.note == "auto_enable_master"` for `HiFilter On`.
  - Execute HiFilter Freq 5000 Hz:
    - `curl -s -X POST http://127.0.0.1:8722/intent/execute -H 'Content-Type: application/json' -d '{"domain":"device","action":"set","return_ref":"A","device_index":0,"param_ref":"HiFilter Freq","display":"5000 Hz"}' | jq`
  - Execute HiShelf Gain 0.7 (unitless, range 0.0-1.0):
    - `curl -s -X POST http://127.0.0.1:8722/intent/execute -H 'Content-Type: application/json' -d '{"domain":"device","action":"set","return_ref":"A","device_index":0,"param_ref":"HiShelf Gain","display":"0.7"}' | jq`

14.4 HiFilter Type Test
- Set HiFilter Type (quantized parameter):
  - `curl -s -X POST http://127.0.0.1:8722/intent/execute -H 'Content-Type: application/json' -d '{"domain":"device","action":"set","return_ref":"A","device_index":0,"param_ref":"HiFilter Type","value":1}' | jq`

14.5 Independent Toggles (Freeze, Flat, Cut)
- Toggle Freeze On (independent):
  - `curl -s -X POST http://127.0.0.1:8722/intent/execute -H 'Content-Type: application/json' -d '{"domain":"device","action":"set","return_ref":"A","device_index":0,"param_ref":"Freeze On","value":1}' | jq`
- Toggle Flat On (independent):
  - `curl -s -X POST http://127.0.0.1:8722/intent/execute -H 'Content-Type: application/json' -d '{"domain":"device","action":"set","return_ref":"A","device_index":0,"param_ref":"Flat On","value":1}' | jq`
- Toggle Cut On (independent - use param_index due to ambiguity):
  - `curl -s -X POST http://127.0.0.1:8722/intent/execute -H 'Content-Type: application/json' -d '{"domain":"device","action":"set","return_ref":"A","device_index":0,"param_index":25,"value":1}' | jq`

**Test Results Summary:**

| # | Test | Expected Result | Pass (y/n/skip) | Notes |
|---|------|-----------------|-----------------|-------|
| 14.1a | Chorus Amount dry-run | Preview shows auto_enable_master | y | ✅ |
| 14.1b | Chorus Amount execute | Chorus On ~1.0, Amount ~30% | y | ✅ |
| 14.1c | Chorus Rate 0.5 Hz | Rate ~0.5 Hz | y | ✅ |
| 14.2a | ER Spin Amount dry-run | Preview shows auto_enable_master | y | ✅ |
| 14.2b | ER Spin Amount execute | ER Spin On ~1.0 | y | ✅ |
| 14.2c | ER Spin Rate 0.3 Hz | Rate ~0.3 Hz | y | ✅ |
| 14.3a | LowShelf Freq dry-run | Preview shows auto_enable_master | y | ✅ |
| 14.3b | LowShelf Freq 200 Hz | On ~1.0, Freq ~200 Hz | y | ✅ |
| 14.3c | LowShelf Gain 0.5 | Gain ~0.5 (unitless) | y | ✅ Fixed: removed dB unit |
| 14.3d | HiFilter Freq dry-run | Preview shows auto_enable_master | y | ✅ |
| 14.3e | HiFilter Freq 5000 Hz | On ~1.0, Freq ~5000 Hz | y | ✅ |
| 14.3f | HiShelf Gain 0.7 | Gain ~0.7 (unitless) | y | ✅ Fixed: removed dB unit |
| 14.3g | HiFilter Freq 8.0 kHz | Freq ~8000 Hz | y | ✅ Fixed: kHz→Hz conversion |
| 14.4a | HiFilter Type = 1 | Type = 1.0 | y | ✅ |
| 14.5a | Freeze On toggle | Freeze On = 1.0 | y | ✅ Independent toggle |
| 14.5b | Flat On toggle | Flat On = 1.0 | y | ✅ Independent toggle |
| 14.5c | Cut On toggle | Cut On = 1.0 | y | ✅ Using param_index |
| Bonus: 14.6a | Predelay 50 ms | Predelay ~50 ms | y | ✅ |
| Bonus: 14.6b | Decay Time 2000 ms | Decay ~2000 ms | y | ✅ |
| Bonus: 14.6c | Decay Time 5.0 s | Decay ~5000 ms | y | ✅ s→ms conversion |

**All Part 14 tests PASS (20/20 = 100%)**

Verification after each dependent write (non-dry-run)
- `curl -s "http://127.0.0.1:8722/return/device/params?index=0&device=0" | jq`
  - Confirm the relevant master toggle (e.g., "Chorus On") now has `value` near its max and the dependent reflects the target display.

Notes
- If params_meta.fit is missing for a numeric display parameter, non-dry-run will converge approximately via readback; dry_run will show an `approx_preview_no_fit` note.
- If a dependent name differs (e.g., "High Shelf" vs "HiShelf"), adjust `param_ref` substring accordingly.

---

## PART 15: REVERB ADDITIONAL CONTROLS (UNITLESS)

Treat these parameters as unitless display values; do not assume any units.
Use `display` with a numeric string (executor aligns via mapping when available).

Assumptions: Return A, Device 0 (Reverb)

| # | Curl Command | Expected Result | Pass (y/n/skip) | Notes |
|---|--------------|-----------------|-----------------|-------|
| 15.1 | `curl -s -X POST http://127.0.0.1:8722/intent/execute -H 'Content-Type: application/json' -d '{"domain":"device","action":"set","return_ref":"A","device_index":0,"param_ref":"Size Smoothing","display":"0.70"}'` | Size Smoothing ≈ 0.70 |  | |
| 15.2 | `curl -s -X POST http://127.0.0.1:8722/intent/execute -H 'Content-Type: application/json' -d '{"domain":"device","action":"set","return_ref":"A","device_index":0,"param_ref":"Room Size","display":"0.45"}'` | Room Size ≈ 0.45 |  | |
| 15.3 | `curl -s -X POST http://127.0.0.1:8722/intent/execute -H 'Content-Type: application/json' -d '{"domain":"device","action":"set","return_ref":"A","device_index":0,"param_ref":"Stereo Image","display":"0.60"}'` | Stereo Image ≈ 0.60 |  | |
| 15.4 | `curl -s -X POST http://127.0.0.1:8722/intent/execute -H 'Content-Type: application/json' -d '{"domain":"device","action":"set","return_ref":"A","device_index":0,"param_ref":"Reflect","display":"0.35"}'` | Reflect ≈ 0.35 |  | |
| 15.5 | `curl -s -X POST http://127.0.0.1:8722/intent/execute -H 'Content-Type: application/json' -d '{"domain":"device","action":"set","return_ref":"A","device_index":0,"param_ref":"Diffuse","display":"0.40"}'` | Diffuse ≈ 0.40 |  | |

Verify (optional):
- `curl -s "http://127.0.0.1:8722/return/device/param_lookup?index=0&device=0&param_ref=Size%20Smoothing" | jq`
- `curl -s "http://127.0.0.1:8722/return/device/param_lookup?index=0&device=0&param_ref=Room%20Size" | jq`
- `curl -s "http://127.0.0.1:8722/return/device/param_lookup?index=0&device=0&param_ref=Stereo%20Image" | jq`
- `curl -s "http://127.0.0.1:8722/return/device/param_lookup?index=0&device=0&param_ref=Reflect" | jq`
- `curl -s "http://127.0.0.1:8722/return/device/param_lookup?index=0&device=0&param_ref=Diffuse" | jq`

---

## PART 16: QUANTIZED PARAMETERS (LABEL-BASED)

Many device parameters are quantized (enums) and expose labels instead of numeric display values. These must be set by label using the mapping from Firestore (label_map). Do not invent labels — fetch real labels first and use them exactly (case-insensitive).

Step 0: Discover quantized params and labels

- `curl -s "http://127.0.0.1:8722/device_mapping?index=0&device=0" | jq '.mapping.params_meta[] | select(.label_map != null) | {name, label_map}'`

Pick one parameter with a non-empty `label_map` (examples on some devices: "Type", "Slope", "Quality"). Replace PARAM_NAME and A_LABEL below.

16.1 Set by exact label (case-insensitive)

```
curl -s -X POST http://127.0.0.1:8722/intent/execute \
  -H 'Content-Type: application/json' \
  -d '{
    "domain":"device",
    "action":"set",
    "return_ref":"A",
    "device_index":0,
    "param_ref":"PARAM_NAME",
    "display":"A_LABEL"
  }' | jq
```

Verify:

```
curl -s "http://127.0.0.1:8722/return/device/param_lookup?index=0&device=0&param_ref=PARAM_NAME" | jq
```

Expected: `display_value` equals `A_LABEL` (or the device’s exact casing of that label).

16.2 Set by another valid label from label_map

Repeat 16.1 using a different label from the `label_map` discovered in Step 0.

16.3 Invalid label (documentation-only)

If you send a label not present in `label_map`, the executor will not change by label (it does not invent or guess labels). Choose labels only from mapping.

Notes
- For quantized parameters, prefer `display:"<Label>"`. Numeric paths/refine are not used when labels are expected.
- If your chosen parameter does not appear with a `label_map`, pick a different one from the mapping output.

## Summary

**Total Tests:** 50
**Passed:** _____
**Failed:** _____
**Skipped:** _____

### Critical Issues Found:
_List any tests that failed with notes on what went wrong_

---

### Notes:
- All curl commands use `http://127.0.0.1:8722` - adjust if your server is on a different port
- Copy each curl command into your terminal and press Enter
- Check Live immediately after running each command
- Mark `y` for pass, `n` for fail, `skip` if you can't test it

### Quick Tips:
- **Pan values:** Use `-50` for 50L, `50` for 50R, `0` for center
- **Mute/Solo:** Use `1` for on, `0` for off
- **Sends:** Remember they max at `0 dB`, not `+6 dB`
- **1-based indexing:** Track 1 = first track, Return 1 = Return A
