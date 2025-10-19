# Delay Device API Testing Plan

**Date:** 2025-10-18
**Device:** Delay (on Return B)
**Tester:** _____________

## Setup Requirements
- [ ] Ableton Live running
- [ ] Server running on port 8722 (`cd server && make dev-returns`)
- [ ] Return B has a Delay device at device_index 0
- [ ] Return B Delay is set to default state (or known state)

---

## Test Format
- **Display Values:** Use human-readable values with proper units (ms, Hz, %)
- **Pass Criteria:** Mark `y` if the value in Live matches expected, `n` if wrong, `skip` if cannot test
- **Notes:** Add any observations

---

## PART 1: BINARY PARAMETERS (ON/OFF TOGGLES)

### 1.1 Device On

| # | Curl Command | Expected Result | Pass (y/n/skip) | Notes |
|---|--------------|-----------------|-----------------|-------|
| 1.1a | `curl -X POST http://127.0.0.1:8722/intent/execute -H "Content-Type: application/json" -d '{"domain":"device","action":"set","return_ref":"B","device_index":0,"param_ref":"Device On","value":1}'` | Device On button lit (enabled) | | |
| 1.1b | `curl -X POST http://127.0.0.1:8722/intent/execute -H "Content-Type: application/json" -d '{"domain":"device","action":"set","return_ref":"B","device_index":0,"param_ref":"Device On","value":0}'` | Device On button off (bypassed) | | |

### 1.2 Link (Stereo Link)

| # | Curl Command | Expected Result | Pass (y/n/skip) | Notes |
|---|--------------|-----------------|-----------------|-------|
| 1.2a | `curl -X POST http://127.0.0.1:8722/intent/execute -H "Content-Type: application/json" -d '{"domain":"device","action":"set","return_ref":"B","device_index":0,"param_ref":"Link","value":1}'` | Link button lit (L/R linked) | | |
| 1.2b | `curl -X POST http://127.0.0.1:8722/intent/execute -H "Content-Type: application/json" -d '{"domain":"device","action":"set","return_ref":"B","device_index":0,"param_ref":"Link","value":0}'` | Link button off (independent L/R) | | |

### 1.3 Ping Pong

| # | Curl Command | Expected Result | Pass (y/n/skip) | Notes |
|---|--------------|-----------------|-----------------|-------|
| 1.3a | `curl -X POST http://127.0.0.1:8722/intent/execute -H "Content-Type: application/json" -d '{"domain":"device","action":"set","return_ref":"B","device_index":0,"param_ref":"Ping Pong","value":1}'` | Ping Pong button lit (bouncing) | | |
| 1.3b | `curl -X POST http://127.0.0.1:8722/intent/execute -H "Content-Type: application/json" -d '{"domain":"device","action":"set","return_ref":"B","device_index":0,"param_ref":"Ping Pong","value":0}'` | Ping Pong button off (normal) | | |

### 1.4 L Sync

| # | Curl Command | Expected Result | Pass (y/n/skip) | Notes |
|---|--------------|-----------------|-----------------|-------|
| 1.4a | `curl -X POST http://127.0.0.1:8722/intent/execute -H "Content-Type: application/json" -d '{"domain":"device","action":"set","return_ref":"B","device_index":0,"param_ref":"L Sync","value":1}'` | L Sync lit (tempo sync mode) | | |
| 1.4b | `curl -X POST http://127.0.0.1:8722/intent/execute -H "Content-Type: application/json" -d '{"domain":"device","action":"set","return_ref":"B","device_index":0,"param_ref":"L Sync","value":0}'` | L Sync off (free time mode) | | |

### 1.5 R Sync

| # | Curl Command | Expected Result | Pass (y/n/skip) | Notes |
|---|--------------|-----------------|-----------------|-------|
| 1.5a | `curl -X POST http://127.0.0.1:8722/intent/execute -H "Content-Type: application/json" -d '{"domain":"device","action":"set","return_ref":"B","device_index":0,"param_ref":"R Sync","value":1}'` | R Sync lit (tempo sync mode) | | |
| 1.5b | `curl -X POST http://127.0.0.1:8722/intent/execute -H "Content-Type: application/json" -d '{"domain":"device","action":"set","return_ref":"B","device_index":0,"param_ref":"R Sync","value":0}'` | R Sync off (free time mode) | | |

### 1.6 Freeze

| # | Curl Command | Expected Result | Pass (y/n/skip) | Notes |
|---|--------------|-----------------|-----------------|-------|
| 1.6a | `curl -X POST http://127.0.0.1:8722/intent/execute -H "Content-Type: application/json" -d '{"domain":"device","action":"set","return_ref":"B","device_index":0,"param_ref":"Freeze","value":1}'` | Freeze lit (buffer frozen) | | |
| 1.6b | `curl -X POST http://127.0.0.1:8722/intent/execute -H "Content-Type: application/json" -d '{"domain":"device","action":"set","return_ref":"B","device_index":0,"param_ref":"Freeze","value":0}'` | Freeze off (normal operation) | | |

### 1.7 Filter On

| # | Curl Command | Expected Result | Pass (y/n/skip) | Notes |
|---|--------------|-----------------|-----------------|-------|
| 1.7a | `curl -X POST http://127.0.0.1:8722/intent/execute -H "Content-Type: application/json" -d '{"domain":"device","action":"set","return_ref":"B","device_index":0,"param_ref":"Filter On","value":1}'` | Filter On lit (filter enabled) | | |
| 1.7b | `curl -X POST http://127.0.0.1:8722/intent/execute -H "Content-Type: application/json" -d '{"domain":"device","action":"set","return_ref":"B","device_index":0,"param_ref":"Filter On","value":0}'` | Filter On off (bypassed) | | |

---

## PART 2: QUANTIZED PARAMETERS (DISCRETE VALUES)

### 2.1 Delay Mode (Repitch/Fade/Jump)

| # | Curl Command | Expected Result | Pass (y/n/skip) | Notes |
|---|--------------|-----------------|-----------------|-------|
| 2.1a | `curl -X POST http://127.0.0.1:8722/intent/execute -H "Content-Type: application/json" -d '{"domain":"device","action":"set","return_ref":"B","device_index":0,"param_ref":"Delay Mode","display":"Repitch"}'` | Delay Mode shows "Repitch" | | |
| 2.1b | `curl -X POST http://127.0.0.1:8722/intent/execute -H "Content-Type: application/json" -d '{"domain":"device","action":"set","return_ref":"B","device_index":0,"param_ref":"Delay Mode","display":"Fade"}'` | Delay Mode shows "Fade" | | |
| 2.1c | `curl -X POST http://127.0.0.1:8722/intent/execute -H "Content-Type: application/json" -d '{"domain":"device","action":"set","return_ref":"B","device_index":0,"param_ref":"Delay Mode","display":"Jump"}'` | Delay Mode shows "Jump" | | |

### 2.2 L 16th (Beat Divisions) - Requires L Sync On

**Setup:** First enable L Sync

| # | Curl Command | Expected Result | Pass (y/n/skip) | Notes |
|---|--------------|-----------------|-----------------|-------|
| 2.2a | `curl -X POST http://127.0.0.1:8722/intent/execute -H "Content-Type: application/json" -d '{"domain":"device","action":"set","return_ref":"B","device_index":0,"param_ref":"L Sync","value":1}'` | L Sync enabled (setup) | | |
| 2.2b | `curl -X POST http://127.0.0.1:8722/intent/execute -H "Content-Type: application/json" -d '{"domain":"device","action":"set","return_ref":"B","device_index":0,"param_ref":"L 16th","display":"4"}'` | L 16th shows "4" (quarter note) | | |
| 2.2c | `curl -X POST http://127.0.0.1:8722/intent/execute -H "Content-Type: application/json" -d '{"domain":"device","action":"set","return_ref":"B","device_index":0,"param_ref":"L 16th","display":"8"}'` | L 16th shows "8" (half note) | | |
| 2.2d | `curl -X POST http://127.0.0.1:8722/intent/execute -H "Content-Type: application/json" -d '{"domain":"device","action":"set","return_ref":"B","device_index":0,"param_ref":"L 16th","display":"16"}'` | L 16th shows "16" (whole note) | | |

### 2.3 R 16th (Beat Divisions) - Requires R Sync On

**Setup:** First enable R Sync

| # | Curl Command | Expected Result | Pass (y/n/skip) | Notes |
|---|--------------|-----------------|-----------------|-------|
| 2.3a | `curl -X POST http://127.0.0.1:8722/intent/execute -H "Content-Type: application/json" -d '{"domain":"device","action":"set","return_ref":"B","device_index":0,"param_ref":"R Sync","value":1}'` | R Sync enabled (setup) | | |
| 2.3b | `curl -X POST http://127.0.0.1:8722/intent/execute -H "Content-Type: application/json" -d '{"domain":"device","action":"set","return_ref":"B","device_index":0,"param_ref":"R 16th","display":"3"}'` | R 16th shows "3" (dotted 8th) | | |
| 2.3c | `curl -X POST http://127.0.0.1:8722/intent/execute -H "Content-Type: application/json" -d '{"domain":"device","action":"set","return_ref":"B","device_index":0,"param_ref":"R 16th","display":"6"}'` | R 16th shows "6" | | |

---

## PART 3: CONTINUOUS PARAMETERS (WITH UNITS)

### 3.1 L Time (Milliseconds) - Requires L Sync Off

**Setup:** Disable L Sync first

| # | Curl Command | Expected Result | Pass (y/n/skip) | Notes |
|---|--------------|-----------------|-----------------|-------|
| 3.1a | `curl -X POST http://127.0.0.1:8722/intent/execute -H "Content-Type: application/json" -d '{"domain":"device","action":"set","return_ref":"B","device_index":0,"param_ref":"L Sync","value":0}'` | L Sync off (setup) | | |
| 3.1b | `curl -X POST http://127.0.0.1:8722/intent/execute -H "Content-Type: application/json" -d '{"domain":"device","action":"set","return_ref":"B","device_index":0,"param_ref":"L Time","value":100,"unit":"ms"}'` | L Time shows ~100ms | | |
| 3.1c | `curl -X POST http://127.0.0.1:8722/intent/execute -H "Content-Type: application/json" -d '{"domain":"device","action":"set","return_ref":"B","device_index":0,"param_ref":"L Time","value":500,"unit":"ms"}'` | L Time shows ~500ms | | |
| 3.1d | `curl -X POST http://127.0.0.1:8722/intent/execute -H "Content-Type: application/json" -d '{"domain":"device","action":"set","return_ref":"B","device_index":0,"param_ref":"L Time","value":2000,"unit":"ms"}'` | L Time shows ~2000ms | | |

### 3.2 R Time (Milliseconds) - Requires R Sync Off

| # | Curl Command | Expected Result | Pass (y/n/skip) | Notes |
|---|--------------|-----------------|-----------------|-------|
| 3.2a | `curl -X POST http://127.0.0.1:8722/intent/execute -H "Content-Type: application/json" -d '{"domain":"device","action":"set","return_ref":"B","device_index":0,"param_ref":"R Sync","value":0}'` | R Sync off (setup) | | |
| 3.2b | `curl -X POST http://127.0.0.1:8722/intent/execute -H "Content-Type: application/json" -d '{"domain":"device","action":"set","return_ref":"B","device_index":0,"param_ref":"R Time","value":250,"unit":"ms"}'` | R Time shows ~250ms | | |

### 3.3 L Offset (Percent) - Requires L Sync On

| # | Curl Command | Expected Result | Pass (y/n/skip) | Notes |
|---|--------------|-----------------|-----------------|-------|
| 3.3a | `curl -X POST http://127.0.0.1:8722/intent/execute -H "Content-Type: application/json" -d '{"domain":"device","action":"set","return_ref":"B","device_index":0,"param_ref":"L Sync","value":1}'` | L Sync on (setup) | | |
| 3.3b | `curl -X POST http://127.0.0.1:8722/intent/execute -H "Content-Type: application/json" -d '{"domain":"device","action":"set","return_ref":"B","device_index":0,"param_ref":"L Offset","value":10,"unit":"%"}'` | L Offset shows ~10% | | |
| 3.3c | `curl -X POST http://127.0.0.1:8722/intent/execute -H "Content-Type: application/json" -d '{"domain":"device","action":"set","return_ref":"B","device_index":0,"param_ref":"L Offset","value":-15,"unit":"%"}'` | L Offset shows ~-15% | | |

### 3.4 Feedback (Percent)

| # | Curl Command | Expected Result | Pass (y/n/skip) | Notes |
|---|--------------|-----------------|-----------------|-------|
| 3.4a | `curl -X POST http://127.0.0.1:8722/intent/execute -H "Content-Type: application/json" -d '{"domain":"device","action":"set","return_ref":"B","device_index":0,"param_ref":"Feedback","value":50,"unit":"%"}'` | Feedback shows ~50% | | |
| 3.4b | `curl -X POST http://127.0.0.1:8722/intent/execute -H "Content-Type: application/json" -d '{"domain":"device","action":"set","return_ref":"B","device_index":0,"param_ref":"Feedback","value":75,"unit":"%"}'` | Feedback shows ~75% | | |
| 3.4c | `curl -X POST http://127.0.0.1:8722/intent/execute -H "Content-Type: application/json" -d '{"domain":"device","action":"set","return_ref":"B","device_index":0,"param_ref":"Feedback","value":90,"unit":"%"}'` | Feedback shows ~90% | | |

### 3.5 Filter Freq (Hz) - Requires Filter On

| # | Curl Command | Expected Result | Pass (y/n/skip) | Notes |
|---|--------------|-----------------|-----------------|-------|
| 3.5a | `curl -X POST http://127.0.0.1:8722/intent/execute -H "Content-Type: application/json" -d '{"domain":"device","action":"set","return_ref":"B","device_index":0,"param_ref":"Filter On","value":1}'` | Filter On (setup) | | |
| 3.5b | `curl -X POST http://127.0.0.1:8722/intent/execute -H "Content-Type: application/json" -d '{"domain":"device","action":"set","return_ref":"B","device_index":0,"param_ref":"Filter Freq","value":500,"unit":"Hz"}'` | Filter Freq shows ~500 Hz | | |
| 3.5c | `curl -X POST http://127.0.0.1:8722/intent/execute -H "Content-Type: application/json" -d '{"domain":"device","action":"set","return_ref":"B","device_index":0,"param_ref":"Filter Freq","value":2000,"unit":"Hz"}'` | Filter Freq shows ~2000 Hz | | |

### 3.6 Filter Width (Unitless)

| # | Curl Command | Expected Result | Pass (y/n/skip) | Notes |
|---|--------------|-----------------|-----------------|-------|
| 3.6a | `curl -X POST http://127.0.0.1:8722/intent/execute -H "Content-Type: application/json" -d '{"domain":"device","action":"set","return_ref":"B","device_index":0,"param_ref":"Filter Width","display":"3.0"}'` | Filter Width shows ~3.0 | | |
| 3.6b | `curl -X POST http://127.0.0.1:8722/intent/execute -H "Content-Type: application/json" -d '{"domain":"device","action":"set","return_ref":"B","device_index":0,"param_ref":"Filter Width","display":"7.0"}'` | Filter Width shows ~7.0 | | |

### 3.7 Mod Freq (Hz) - Requires Freeze Off

| # | Curl Command | Expected Result | Pass (y/n/skip) | Notes |
|---|--------------|-----------------|-----------------|-------|
| 3.7a | `curl -X POST http://127.0.0.1:8722/intent/execute -H "Content-Type: application/json" -d '{"domain":"device","action":"set","return_ref":"B","device_index":0,"param_ref":"Freeze","value":0}'` | Freeze off (setup) | | |
| 3.7b | `curl -X POST http://127.0.0.1:8722/intent/execute -H "Content-Type: application/json" -d '{"domain":"device","action":"set","return_ref":"B","device_index":0,"param_ref":"Mod Freq","value":1.0,"unit":"Hz"}'` | Mod Freq shows ~1.0 Hz | | |
| 3.7c | `curl -X POST http://127.0.0.1:8722/intent/execute -H "Content-Type: application/json" -d '{"domain":"device","action":"set","return_ref":"B","device_index":0,"param_ref":"Mod Freq","value":5.0,"unit":"Hz"}'` | Mod Freq shows ~5.0 Hz | | |

### 3.8 Dly < Mod (Time Modulation %)

| # | Curl Command | Expected Result | Pass (y/n/skip) | Notes |
|---|--------------|-----------------|-----------------|-------|
| 3.8a | `curl -X POST http://127.0.0.1:8722/intent/execute -H "Content-Type: application/json" -d '{"domain":"device","action":"set","return_ref":"B","device_index":0,"param_ref":"Dly < Mod","value":20,"unit":"%"}'` | Dly < Mod shows ~20% | | |
| 3.8b | `curl -X POST http://127.0.0.1:8722/intent/execute -H "Content-Type: application/json" -d '{"domain":"device","action":"set","return_ref":"B","device_index":0,"param_ref":"Dly < Mod","value":50,"unit":"%"}'` | Dly < Mod shows ~50% | | |

### 3.9 Filter < Mod (Filter Modulation %)

| # | Curl Command | Expected Result | Pass (y/n/skip) | Notes |
|---|--------------|-----------------|-----------------|-------|
| 3.9a | `curl -X POST http://127.0.0.1:8722/intent/execute -H "Content-Type: application/json" -d '{"domain":"device","action":"set","return_ref":"B","device_index":0,"param_ref":"Filter < Mod","value":30,"unit":"%"}'` | Filter < Mod shows ~30% | | |

### 3.10 Dry/Wet (Percent)

| # | Curl Command | Expected Result | Pass (y/n/skip) | Notes |
|---|--------------|-----------------|-----------------|-------|
| 3.10a | `curl -X POST http://127.0.0.1:8722/intent/execute -H "Content-Type: application/json" -d '{"domain":"device","action":"set","return_ref":"B","device_index":0,"param_ref":"Dry/Wet","value":50,"unit":"%"}'` | Dry/Wet shows ~50% | | |
| 3.10b | `curl -X POST http://127.0.0.1:8722/intent/execute -H "Content-Type: application/json" -d '{"domain":"device","action":"set","return_ref":"B","device_index":0,"param_ref":"Dry/Wet","value":100,"unit":"%"}'` | Dry/Wet shows 100% (wet only) | | |

---

## PART 4: DEPENDENT PARAMETERS (AUTO-ENABLE MASTERS)

### 4.1 L 16th Auto-Enables L Sync

| # | Curl Command | Expected Result | Pass (y/n/skip) | Notes |
|---|--------------|-----------------|-----------------|-------|
| 4.1a | `curl -X POST http://127.0.0.1:8722/intent/execute -H "Content-Type: application/json" -d '{"domain":"device","action":"set","return_ref":"B","device_index":0,"param_ref":"L Sync","value":0}'` | L Sync off (setup) | | |
| 4.1b | `curl -X POST http://127.0.0.1:8722/intent/execute -H "Content-Type: application/json" -d '{"domain":"device","action":"set","return_ref":"B","device_index":0,"param_ref":"L 16th","display":"4","dry_run":true}' \| jq` | Dry run shows auto_enable_master for L Sync | | |
| 4.1c | `curl -X POST http://127.0.0.1:8722/intent/execute -H "Content-Type: application/json" -d '{"domain":"device","action":"set","return_ref":"B","device_index":0,"param_ref":"L 16th","display":"4"}'` | L Sync auto-enabled, L 16th = 4 | | |

### 4.2 R 16th Auto-Enables R Sync

| # | Curl Command | Expected Result | Pass (y/n/skip) | Notes |
|---|--------------|-----------------|-----------------|-------|
| 4.2a | `curl -X POST http://127.0.0.1:8722/intent/execute -H "Content-Type: application/json" -d '{"domain":"device","action":"set","return_ref":"B","device_index":0,"param_ref":"R Sync","value":0}'` | R Sync off (setup) | | |
| 4.2b | `curl -X POST http://127.0.0.1:8722/intent/execute -H "Content-Type: application/json" -d '{"domain":"device","action":"set","return_ref":"B","device_index":0,"param_ref":"R 16th","display":"3","dry_run":true}' \| jq` | Dry run shows auto_enable_master for R Sync | | |
| 4.2c | `curl -X POST http://127.0.0.1:8722/intent/execute -H "Content-Type: application/json" -d '{"domain":"device","action":"set","return_ref":"B","device_index":0,"param_ref":"R 16th","display":"3"}'` | R Sync auto-enabled, R 16th = 3 | | |

### 4.3 Filter Freq/Width Auto-Enable Filter On

| # | Curl Command | Expected Result | Pass (y/n/skip) | Notes |
|---|--------------|-----------------|-----------------|-------|
| 4.3a | `curl -X POST http://127.0.0.1:8722/intent/execute -H "Content-Type: application/json" -d '{"domain":"device","action":"set","return_ref":"B","device_index":0,"param_ref":"Filter On","value":0}'` | Filter On off (setup) | | |
| 4.3b | `curl -X POST http://127.0.0.1:8722/intent/execute -H "Content-Type: application/json" -d '{"domain":"device","action":"set","return_ref":"B","device_index":0,"param_ref":"Filter Freq","value":1000,"unit":"Hz","dry_run":true}' \| jq` | Dry run shows auto_enable_master | | |
| 4.3c | `curl -X POST http://127.0.0.1:8722/intent/execute -H "Content-Type: application/json" -d '{"domain":"device","action":"set","return_ref":"B","device_index":0,"param_ref":"Filter Freq","value":1000,"unit":"Hz"}'` | Filter On auto-enabled, Freq ~1000 Hz | | |

---

## PART 5: FREEZE DISABLES MODULATION/FILTER

### 5.1 Freeze Disables Modulation Parameters

**Test that when Freeze is On, modulation params should be disabled**

| # | Curl Command | Expected Result | Pass (y/n/skip) | Notes |
|---|--------------|-----------------|-----------------|-------|
| 5.1a | `curl -X POST http://127.0.0.1:8722/intent/execute -H "Content-Type: application/json" -d '{"domain":"device","action":"set","return_ref":"B","device_index":0,"param_ref":"Freeze","value":1}'` | Freeze On (setup) | | |
| 5.1b | Check Mod Freq, Dly < Mod, Filter < Mod in Live UI | Should be grayed out/disabled | | Manual check |

---

## PART 6: READ OPERATIONS

### 6.1 Read All Parameters

| # | Curl Command | Expected Result | Pass (y/n/skip) | Notes |
|---|--------------|-----------------|-----------------|-------|
| 6.1a | `curl -s "http://127.0.0.1:8722/return/device/params?index=1&device=0" \| jq` | Returns all 21 Delay parameters with values | | |

### 6.2 Param Lookup (Fuzzy Matching)

| # | Curl Command | Expected Result | Pass (y/n/skip) | Notes |
|---|--------------|-----------------|-----------------|-------|
| 6.2a | `curl -s "http://127.0.0.1:8722/return/device/param_lookup?index=1&device=0&param_ref=feedback" \| jq` | Returns Feedback parameter info | | |
| 6.2b | `curl -s "http://127.0.0.1:8722/return/device/param_lookup?index=1&device=0&param_ref=delay%20mode" \| jq` | Returns Delay Mode parameter info | | |

### 6.3 Device Mapping

| # | Curl Command | Expected Result | Pass (y/n/skip) | Notes |
|---|--------------|-----------------|-----------------|-------|
| 6.3a | `curl -s "http://127.0.0.1:8722/device_mapping?index=1&device=0" \| jq` | Returns complete Delay mapping with params_meta, sections, grouping | | |

---

## PART 7: PRESET LOADING

### 7.1 Load Delay Presets

| # | Curl Command | Expected Result | Pass (y/n/skip) | Notes |
|---|--------------|-----------------|-----------------|-------|
| 7.1a | `curl -X POST http://127.0.0.1:8722/intent/execute -H "Content-Type: application/json" -d '{"domain":"preset","action":"load","return_ref":"B","device_index":0,"preset_id":"delay_16th_dub"}'` | Loads "16th Dub" preset settings | | |
| 7.1b | `curl -X POST http://127.0.0.1:8722/intent/execute -H "Content-Type: application/json" -d '{"domain":"preset","action":"load","return_ref":"B","device_index":0,"preset_id":"delay_simple_chorus"}'` | Loads "Simple Chorus" preset | | |
| 7.1c | `curl -X POST http://127.0.0.1:8722/intent/execute -H "Content-Type: application/json" -d '{"domain":"preset","action":"load","return_ref":"B","device_index":0,"preset_id":"delay_slight_slap"}'` | Loads "Slight Slap" preset | | |

---

## PART 8: EDGE CASES

### 8.1 Clamping

| # | Curl Command | Expected Result | Pass (y/n/skip) | Notes |
|---|--------------|-----------------|-----------------|-------|
| 8.1a | `curl -X POST http://127.0.0.1:8722/intent/execute -H "Content-Type: application/json" -d '{"domain":"device","action":"set","return_ref":"B","device_index":0,"param_ref":"Feedback","value":120,"unit":"%"}'` | Feedback clamped to 95% (max) | | |
| 8.1b | `curl -X POST http://127.0.0.1:8722/intent/execute -H "Content-Type: application/json" -d '{"domain":"device","action":"set","return_ref":"B","device_index":0,"param_ref":"L Time","value":-50,"unit":"ms"}'` | L Time clamped to 1ms (min) | | |
| 8.1c | `curl -X POST http://127.0.0.1:8722/intent/execute -H "Content-Type: application/json" -d '{"domain":"device","action":"set","return_ref":"B","device_index":0,"param_ref":"L Time","value":10000,"unit":"ms"}'` | L Time clamped to 5000ms (max) | | |

---

## TEST RESULTS SUMMARY

**Test Date:** __________
**Total Tests:** __________
**Passed:** __________
**Failed:** __________
**Skipped:** __________

### Results by Category:

| Part | Category | Passed | Failed | Total | Pass Rate |
|------|----------|--------|--------|-------|-----------|
| 1 | Binary Parameters | | | 14 | |
| 2 | Quantized Parameters | | | 9 | |
| 3 | Continuous Parameters | | | 23 | |
| 4 | Auto-Enable Masters | | | 9 | |
| 5 | Freeze Disables | | | 2 | |
| 6 | Read Operations | | | 3 | |
| 7 | Preset Loading | | | 3 | |
| 8 | Edge Cases | | | 3 | |

### Issues Found:

1.
2.
3.

### Notes:

- All curl commands use `http://127.0.0.1:8722` - adjust if server is on different port
- Return B index is 1 (return_index:1 for read operations, return_ref:"B" for writes)
- Delay device is at device_index:0 (first device on Return B)
