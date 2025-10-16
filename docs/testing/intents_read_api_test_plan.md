# Intents Read API Test Plan

**Date:** 2025-10-15 (Updated with Letter-Based API)
**Tester:** _____________
**Live Version:** _____________
**Status:** Ready for testing

Goal: Validate `/intent/read` returns accurate current values to enable reliable relative edits and UI previews.

## 🆕 NEW: Letter-Based API

**This test plan uses the improved letter-based API for sends and returns!**

- ✅ **Tracks:** Use `track_index: 1` for Track 1 (1-based, matches Live UI)
- ✅ **Sends:** Use `send_ref: "A"` for Send A (instead of `send_index: 0`)
- ✅ **Returns:** Use `return_ref: "A"` for Return A (instead of `return_index: 0`)

**Legacy numeric API still works** but letter-based is preferred.

## Setup Requirements
- [ ] Ableton Live running
- [ ] Server running on port 8722 (`cd server && make dev-returns`)
- [ ] At least 3 audio tracks in Live set
- [ ] At least 2 return tracks (Return A, Return B)
- [ ] Return A has a Reverb device at device_index 0

## Test Format
- **Expected Values:** Verify the returned JSON contains correct `normalized_value`, `display_value`, and `unit` fields
- **Pass Criteria:** Mark `y` if JSON response matches expected format, `n` if wrong, `skip` if cannot test
- **Notes:** Add any observations in the Notes column

## Conventions
- Use `jq` to pretty-print JSON
- All responses should have `ok: true`
- Verify `normalized_value` is between 0.0 and 1.0
- Check that `display_value` matches Live's display
- Verify `unit` field matches expected unit from mapping

---

## PART 1: DEVICE PARAM READ (RETURN DEVICE) - Letter-Based

**Note:** Using letter-based `return_ref` instead of numeric `return_index`

| # | Curl Command | Expected Result | Pass (y/n/skip) | Notes |
|---|--------------|-----------------|-----------------|-------|
| 1 | `curl -s -X POST http://127.0.0.1:8722/intent/read -H "Content-Type: application/json" -d '{"domain":"device","return_ref":"A","device_index":0,"param_ref":"Decay"}' \| jq` | ok:true, display_value like "X.XX s", unit:"s", normalized_value 0-1 | | |
| 2 | `curl -s -X POST http://127.0.0.1:8722/intent/read -H "Content-Type: application/json" -d '{"domain":"device","return_ref":"A","device_index":0,"param_ref":"Predelay"}' \| jq` | ok:true, display_value like "XX ms", unit:"ms", normalized_value 0-1 | | |
| 3 | `curl -s -X POST http://127.0.0.1:8722/intent/read -H "Content-Type: application/json" -d '{"domain":"device","return_ref":"A","device_index":0,"param_ref":"Dry/Wet"}' \| jq` | ok:true, display_value like "XX %", unit:"%", normalized_value 0-1 | | |

---

## PART 2: DEVICE PARAM READ WITH NUMERIC INDEX

**Note:** Testing param_index for direct parameter access

| # | Curl Command | Expected Result | Pass (y/n/skip) | Notes |
|---|--------------|-----------------|-----------------|-------|
| 4 | `curl -s -X POST http://127.0.0.1:8722/intent/read -H "Content-Type: application/json" -d '{"domain":"device","return_ref":"A","device_index":0,"param_index":0}' \| jq` | ok:true, min/max present, normalized_value 0-1, display_value string | | |
| 5 | `curl -s -X POST http://127.0.0.1:8722/intent/read -H "Content-Type: application/json" -d '{"domain":"device","track_index":1,"device_index":0,"param_index":0}' \| jq` | ok:true (if track 1 has device), normalized_value 0-1 | | |

---

## PART 3: TRACK MIXER READ

| # | Curl Command | Expected Result | Pass (y/n/skip) | Notes |
|---|--------------|-----------------|-----------------|-------|
| 6 | `curl -s -X POST http://127.0.0.1:8722/intent/read -H "Content-Type: application/json" -d '{"domain":"track","track_index":1,"field":"volume"}' \| jq` | ok:true, display_value like "X.X dB", unit:"dB", normalized_value 0-1 | | |
| 7 | `curl -s -X POST http://127.0.0.1:8722/intent/read -H "Content-Type: application/json" -d '{"domain":"track","track_index":1,"field":"pan"}' \| jq` | ok:true, display_value like "XXL"/"XXR"/"C", normalized_value 0-1 | | |
| 8 | `curl -s -X POST http://127.0.0.1:8722/intent/read -H "Content-Type: application/json" -d '{"domain":"track","track_index":2,"field":"volume"}' \| jq` | ok:true, display_value in dB format | | |
| 9 | `curl -s -X POST http://127.0.0.1:8722/intent/read -H "Content-Type: application/json" -d '{"domain":"track","track_index":1,"field":"mute"}' \| jq` | ok:true, normalized_value 0.0 or 1.0 | | |
| 10 | `curl -s -X POST http://127.0.0.1:8722/intent/read -H "Content-Type: application/json" -d '{"domain":"track","track_index":1,"field":"solo"}' \| jq` | ok:true, normalized_value 0.0 or 1.0 | | |

---

## PART 4: TRACK SEND READ - Letter-Based

**Note:** Using `send_ref:"A"` instead of `send_index:0`

| # | Curl Command | Expected Result | Pass (y/n/skip) | Notes |
|---|--------------|-----------------|-----------------|-------|
| 11 | `curl -s -X POST http://127.0.0.1:8722/intent/read -H "Content-Type: application/json" -d '{"domain":"track","track_index":1,"field":"send","send_ref":"A"}' \| jq` | ok:true, display_value like "X.X dB", unit:"dB", normalized_value 0-1 | | |
| 12 | `curl -s -X POST http://127.0.0.1:8722/intent/read -H "Content-Type: application/json" -d '{"domain":"track","track_index":1,"field":"send","send_ref":"B"}' \| jq` | ok:true, display_value in dB format | | |
| 13 | `curl -s -X POST http://127.0.0.1:8722/intent/read -H "Content-Type: application/json" -d '{"domain":"track","track_index":2,"field":"send","send_ref":"A"}' \| jq` | ok:true, normalized_value 0-1 | | |

---

## PART 5: RETURN MIXER READ - Letter-Based

**Note:** Using `return_ref:"A"` instead of `return_index:0`

| # | Curl Command | Expected Result | Pass (y/n/skip) | Notes |
|---|--------------|-----------------|-----------------|-------|
| 14 | `curl -s -X POST http://127.0.0.1:8722/intent/read -H "Content-Type: application/json" -d '{"domain":"return","return_ref":"A","field":"volume"}' \| jq` | ok:true, display_value like "X.X dB", unit:"dB", normalized_value 0-1 | | |
| 15 | `curl -s -X POST http://127.0.0.1:8722/intent/read -H "Content-Type: application/json" -d '{"domain":"return","return_ref":"A","field":"pan"}' \| jq` | ok:true, display_value like "XXL"/"XXR"/"C", normalized_value 0-1 | | |
| 16 | `curl -s -X POST http://127.0.0.1:8722/intent/read -H "Content-Type: application/json" -d '{"domain":"return","return_ref":"B","field":"volume"}' \| jq` | ok:true, display_value in dB format | | |
| 17 | `curl -s -X POST http://127.0.0.1:8722/intent/read -H "Content-Type: application/json" -d '{"domain":"return","return_ref":"A","field":"mute"}' \| jq` | ok:true, normalized_value 0.0 or 1.0 | | |
| 18 | `curl -s -X POST http://127.0.0.1:8722/intent/read -H "Content-Type: application/json" -d '{"domain":"return","return_ref":"A","field":"solo"}' \| jq` | ok:true, normalized_value 0.0 or 1.0 | | |

---

## PART 6: RETURN SEND READ - Letter-Based

**Note:** Return tracks can send to other return tracks

| # | Curl Command | Expected Result | Pass (y/n/skip) | Notes |
|---|--------------|-----------------|-----------------|-------|
| 19 | `curl -s -X POST http://127.0.0.1:8722/intent/read -H "Content-Type: application/json" -d '{"domain":"return","return_ref":"A","field":"send","send_ref":"B"}' \| jq` | ok:true, display_value like "X.X dB", unit:"dB", normalized_value 0-1 | | |
| 20 | `curl -s -X POST http://127.0.0.1:8722/intent/read -H "Content-Type: application/json" -d '{"domain":"return","return_ref":"B","field":"send","send_ref":"A"}' \| jq` | ok:true, display_value in dB format | | |

---

## PART 7: MASTER MIXER READ

| # | Curl Command | Expected Result | Pass (y/n/skip) | Notes |
|---|--------------|-----------------|-----------------|-------|
| 21 | `curl -s -X POST http://127.0.0.1:8722/intent/read -H "Content-Type: application/json" -d '{"domain":"master","field":"volume"}' \| jq` | ok:true, display_value like "X.X dB", unit:"dB", normalized_value 0-1 | | |
| 22 | `curl -s -X POST http://127.0.0.1:8722/intent/read -H "Content-Type: application/json" -d '{"domain":"master","field":"pan"}' \| jq` | ok:true, display_value like "XXL"/"XXR"/"C", normalized_value 0-1 | | |

---

## PART 8: REVERB BASIC PARAMETERS READ

**Prerequisites:** Return A must have a Reverb device at device_index 0

| # | Curl Command | Expected Result | Pass (y/n/skip) | Notes |
|---|--------------|-----------------|-----------------|-------|
| 23 | `curl -s -X POST http://127.0.0.1:8722/intent/read -H "Content-Type: application/json" -d '{"domain":"device","return_ref":"A","device_index":0,"param_ref":"Decay"}' \| jq` | ok:true, display_value in ms or s format, unit:"ms" or "s", normalized_value 0-1 | | |
| 24 | `curl -s -X POST http://127.0.0.1:8722/intent/read -H "Content-Type: application/json" -d '{"domain":"device","return_ref":"A","device_index":0,"param_ref":"Predelay"}' \| jq` | ok:true, display_value like "XX ms", unit:"ms", normalized_value 0-1 | | |
| 25 | `curl -s -X POST http://127.0.0.1:8722/intent/read -H "Content-Type: application/json" -d '{"domain":"device","return_ref":"A","device_index":0,"param_ref":"Dry/Wet"}' \| jq` | ok:true, display_value like "XX %", unit:"%", normalized_value 0-1 | | |
| 26 | `curl -s -X POST http://127.0.0.1:8722/intent/read -H "Content-Type: application/json" -d '{"domain":"device","return_ref":"A","device_index":0,"param_ref":"In Filter Freq"}' \| jq` | ok:true, display_value like "XXXX Hz" or "X.X kHz", unit:"Hz", normalized_value 0-1 | | |

---

## PART 9: REVERB UNITLESS PARAMETERS READ (Including Diffuse & Reflect)

**Note:** These parameters are unitless (0.0-1.0 range) and should return display_value as numeric strings

| # | Curl Command | Expected Result | Pass (y/n/skip) | Notes |
|---|--------------|-----------------|-----------------|-------|
| 27 | `curl -s -X POST http://127.0.0.1:8722/intent/read -H "Content-Type: application/json" -d '{"domain":"device","return_ref":"A","device_index":0,"param_ref":"Room Size"}' \| jq` | ok:true, display_value like "0.XX" (unitless), normalized_value 0-1 | | |
| 28 | `curl -s -X POST http://127.0.0.1:8722/intent/read -H "Content-Type: application/json" -d '{"domain":"device","return_ref":"A","device_index":0,"param_ref":"Stereo Image"}' \| jq` | ok:true, display_value unitless numeric, normalized_value 0-1 | | |
| 29 | `curl -s -X POST http://127.0.0.1:8722/intent/read -H "Content-Type: application/json" -d '{"domain":"device","return_ref":"A","device_index":0,"param_ref":"Reflect"}' \| jq` | ok:true, display_value unitless numeric (Reflect Level), normalized_value 0-1 | | |
| 30 | `curl -s -X POST http://127.0.0.1:8722/intent/read -H "Content-Type: application/json" -d '{"domain":"device","return_ref":"A","device_index":0,"param_ref":"Diffuse"}' \| jq` | ok:true, display_value unitless numeric (Diffuse Level), normalized_value 0-1 | | |

---

## PART 10: REVERB QUANTIZED PARAMETERS READ (Label-Based)

**Note:** These parameters return label strings, not numeric values

| # | Curl Command | Expected Result | Pass (y/n/skip) | Notes |
|---|--------------|-----------------|-----------------|-------|
| 31 | `curl -s -X POST http://127.0.0.1:8722/intent/read -H "Content-Type: application/json" -d '{"domain":"device","return_ref":"A","device_index":0,"param_ref":"HiFilter Type"}' \| jq` | ok:true, display_value:"Low-pass" or "Shelving", normalized_value matches label_map | | |
| 32 | `curl -s -X POST http://127.0.0.1:8722/intent/read -H "Content-Type: application/json" -d '{"domain":"device","return_ref":"A","device_index":0,"param_ref":"Size Smoothing"}' \| jq` | ok:true, display_value:"None"/"Slow"/"Fast", normalized_value matches label_map | | |
| 33 | `curl -s -X POST http://127.0.0.1:8722/intent/read -H "Content-Type: application/json" -d '{"domain":"device","return_ref":"A","device_index":0,"param_ref":"Density"}' \| jq` | ok:true, display_value:"Sparse"/"Low"/"Mid"/"High", normalized_value matches label_map | | |

---

## PART 11: REVERB DEPENDENT PARAMETERS READ

**Note:** These parameters have master toggles (e.g., "Chorus On", "ER Spin On")

| # | Curl Command | Expected Result | Pass (y/n/skip) | Notes |
|---|--------------|-----------------|-----------------|-------|
| 34 | `curl -s -X POST http://127.0.0.1:8722/intent/read -H "Content-Type: application/json" -d '{"domain":"device","return_ref":"A","device_index":0,"param_ref":"Chorus On"}' \| jq` | ok:true, normalized_value 0.0 or 1.0 (toggle) | | |
| 35 | `curl -s -X POST http://127.0.0.1:8722/intent/read -H "Content-Type: application/json" -d '{"domain":"device","return_ref":"A","device_index":0,"param_ref":"Chorus Amount"}' \| jq` | ok:true, display_value like "XX %", unit:"%", normalized_value 0-1 | | |
| 36 | `curl -s -X POST http://127.0.0.1:8722/intent/read -H "Content-Type: application/json" -d '{"domain":"device","return_ref":"A","device_index":0,"param_ref":"Chorus Rate"}' \| jq` | ok:true, display_value like "X.X Hz", unit:"Hz", normalized_value 0-1 | | |
| 37 | `curl -s -X POST http://127.0.0.1:8722/intent/read -H "Content-Type: application/json" -d '{"domain":"device","return_ref":"A","device_index":0,"param_ref":"ER Spin On"}' \| jq` | ok:true, normalized_value 0.0 or 1.0 (toggle) | | |
| 38 | `curl -s -X POST http://127.0.0.1:8722/intent/read -H "Content-Type: application/json" -d '{"domain":"device","return_ref":"A","device_index":0,"param_ref":"ER Spin Amount"}' \| jq` | ok:true, display_value like "XX %", unit:"%", normalized_value 0-1 | | |
| 39 | `curl -s -X POST http://127.0.0.1:8722/intent/read -H "Content-Type: application/json" -d '{"domain":"device","return_ref":"A","device_index":0,"param_ref":"ER Spin Rate"}' \| jq` | ok:true, display_value like "X.X Hz", unit:"Hz", normalized_value 0-1 | | |

---

## PART 12: REVERB TAIL SHELVES & FILTERS READ

| # | Curl Command | Expected Result | Pass (y/n/skip) | Notes |
|---|--------------|-----------------|-----------------|-------|
| 40 | `curl -s -X POST http://127.0.0.1:8722/intent/read -H "Content-Type: application/json" -d '{"domain":"device","return_ref":"A","device_index":0,"param_ref":"LowShelf On"}' \| jq` | ok:true, normalized_value 0.0 or 1.0 (toggle) | | |
| 41 | `curl -s -X POST http://127.0.0.1:8722/intent/read -H "Content-Type: application/json" -d '{"domain":"device","return_ref":"A","device_index":0,"param_ref":"LowShelf Freq"}' \| jq` | ok:true, display_value like "XXX Hz", unit:"Hz", normalized_value 0-1 | | |
| 42 | `curl -s -X POST http://127.0.0.1:8722/intent/read -H "Content-Type: application/json" -d '{"domain":"device","return_ref":"A","device_index":0,"param_ref":"LowShelf Gain"}' \| jq` | ok:true, display_value unitless "0.X", normalized_value 0-1 | | |
| 43 | `curl -s -X POST http://127.0.0.1:8722/intent/read -H "Content-Type: application/json" -d '{"domain":"device","return_ref":"A","device_index":0,"param_ref":"HiFilter On"}' \| jq` | ok:true, normalized_value 0.0 or 1.0 (toggle) | | |
| 44 | `curl -s -X POST http://127.0.0.1:8722/intent/read -H "Content-Type: application/json" -d '{"domain":"device","return_ref":"A","device_index":0,"param_ref":"HiFilter Freq"}' \| jq` | ok:true, display_value like "XXXX Hz" or "X.X kHz", unit:"Hz", normalized_value 0-1 | | |
| 45 | `curl -s -X POST http://127.0.0.1:8722/intent/read -H "Content-Type: application/json" -d '{"domain":"device","return_ref":"A","device_index":0,"param_ref":"HiShelf Gain"}' \| jq` | ok:true, display_value unitless "0.X", normalized_value 0-1 | | |

---

## PART 13: REVERB INDEPENDENT TOGGLES READ

| # | Curl Command | Expected Result | Pass (y/n/skip) | Notes |
|---|--------------|-----------------|-----------------|-------|
| 46 | `curl -s -X POST http://127.0.0.1:8722/intent/read -H "Content-Type: application/json" -d '{"domain":"device","return_ref":"A","device_index":0,"param_ref":"Freeze On"}' \| jq` | ok:true, normalized_value 0.0 or 1.0 (independent toggle) | | |
| 47 | `curl -s -X POST http://127.0.0.1:8722/intent/read -H "Content-Type: application/json" -d '{"domain":"device","return_ref":"A","device_index":0,"param_ref":"Flat On"}' \| jq` | ok:true, normalized_value 0.0 or 1.0 (independent toggle) | | |

---

## Summary

**Total Tests:** 47
- **Part 1-2:** Device parameter reads (5 tests)
- **Part 3-7:** Mixer controls - tracks, returns, sends, master (17 tests)
- **Part 8:** Reverb basic parameters (4 tests)
- **Part 9:** Reverb unitless parameters including Diffuse & Reflect (4 tests)
- **Part 10:** Reverb quantized/label parameters (3 tests)
- **Part 11:** Reverb dependent parameters with master toggles (6 tests)
- **Part 12:** Reverb tail shelves & filters (6 tests)
- **Part 13:** Reverb independent toggles (2 tests)

---

## Notes
- Read API should return current values that match what's displayed in Live
- All responses should include `ok:true`, `normalized_value` (0.0-1.0), and `display_value`
- For parameters with units (dB, Hz, ms, %, etc.), verify the `unit` field is present
- For quantized parameters with labels, display_value should match the label string
- Relative execution workflow: `read` first → compute deltas in display units → align to params_meta.unit → write
- Display values from read should be suitable for use in execute with `display` parameter
