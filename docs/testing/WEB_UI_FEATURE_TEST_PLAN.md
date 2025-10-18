# Web UI Feature Test Plan - New Features

**Date:** 2025-10-17
**Status:** Ready for Testing
**Tester:** _______________

---

## Overview

This document covers testing for the following new features:

1. **Device Capabilities API** - Grouped parameter display with Firestore mapping
2. **Live-Set Snapshot** - Quick overview of tracks, returns, and devices
3. **Context-Aware Help** - Device-specific help responses
4. **Compact Chat UI** - Removed JSON dropdowns, cleaner messages
5. **Parameter Accordion** - Interactive device parameter exploration
6. **Direct Parameter Reads** - Fast-path for reading parameter values

---

## Prerequisites

```bash
# 1. Start Firestore emulator (if using device mappings)
cd server
make firestore-emulator  # Optional

# 2. Start server with returns support
make dev-returns

# 3. Start web UI
cd clients/web-chat
npm run dev
# Open http://localhost:5173

# 4. Ensure Ableton Live is running with remote script
# 5. Set up a return track with effects (e.g., Return A with Reverb)
```

---

## Test Suite 1: Device Capabilities API

### Test 1.1: Basic Capabilities Fetch

**Setup:**
- Return A has at least one device (e.g., Reverb, EQ Eight)

**Steps:**
1. In browser console, run:
```javascript
fetch('http://127.0.0.1:8722/return/device/capabilities?index=0&device=0')
  .then(r => r.json())
  .then(d => console.log('Capabilities:', d));
```

**Expected:**
- ✅ Response includes `ok: true`
- ✅ `data.device_name` shows device name (e.g., "Reverb")
- ✅ `data.groups` is an array (may be empty if no Firestore mapping)
- ✅ `data.ungrouped` contains parameters
- ✅ `data.values` maps parameter names to current values
- ✅ Response time < 2 seconds

**Example Response:**
```json
{
  "ok": true,
  "data": {
    "return_index": 0,
    "device_index": 0,
    "device_name": "Reverb",
    "structure_signature": "Reverb_34_params",
    "groups": [
      {
        "name": "Global",
        "params": [
          {"index": 0, "name": "Dry/Wet", "unit": "%"},
          {"index": 1, "name": "Decay Time", "unit": "s"}
        ]
      }
    ],
    "ungrouped": [],
    "values": {
      "Dry/Wet": {"value": 1.0, "display_value": "100%"},
      "Decay Time": {"value": 2.0, "display_value": "2.00 s"}
    }
  }
}
```

### Test 1.2: Capabilities with No Firestore Mapping

**Setup:**
- Device has no mapping in Firestore (or emulator not running)

**Steps:**
1. Fetch capabilities for any device

**Expected:**
- ✅ `groups` is empty array `[]`
- ✅ `ungrouped` contains all parameters from live params
- ✅ Parameters have `index` and `name` but may lack `unit`, `labels`, `role`
- ✅ Still returns current values

---

## Test Suite 2: Live-Set Snapshot

### Test 2.1: Basic Snapshot

**Steps:**
1. In browser console:
```javascript
fetch('http://127.0.0.1:8722/snapshot')
  .then(r => r.json())
  .then(d => console.log('Snapshot:', d));
```

**Expected:**
- ✅ `ok: true`
- ✅ `tracks` array with track info: `[{index, name, type}]`
- ✅ `track_count` matches actual track count
- ✅ `returns` array with return info including devices
- ✅ `return_count` matches actual return count
- ✅ `sends_per_track` equals `return_count`

**Example Response:**
```json
{
  "ok": true,
  "tracks": [
    {"index": 0, "name": "1-Audio", "type": "Audio"},
    {"index": 1, "name": "2-MIDI", "type": "MIDI"}
  ],
  "track_count": 2,
  "returns": [
    {
      "index": 0,
      "name": "A-Reverb",
      "devices": ["Audio Effect Rack", "Reverb"]
    },
    {
      "index": 1,
      "name": "B-Delay",
      "devices": ["Simple Delay"]
    }
  ],
  "return_count": 2,
  "sends_per_track": 2
}
```

### Test 2.2: Snapshot with Empty Project

**Setup:**
- Live project with no tracks or minimal tracks

**Expected:**
- ✅ Empty arrays don't cause errors
- ✅ Counts are 0 or match actual
- ✅ Response still has `ok: true`

---

## Test Suite 3: Context-Aware Help

### Test 3.1: Generic Help Query

**Steps:**
1. In web UI chat, type: **"how do I control sends?"**

**Expected:**
- ✅ Help response appears with clean formatting
- ✅ Answer explains sends control
- ✅ Suggested intents displayed as clickable chips:
  - "set track 1 send A to -12 dB"
  - "set return A send B to 25%"
  - "set track 2 send B to 15%"
- ✅ No JSON details shown

### Test 3.2: Device-Aware Parameter Listing

**Setup:**
1. First, execute a device command to establish context:
   - Type: **"set return A device 0 reverb decay to 3 seconds"**
2. Then ask: **"what parameters can I control"**

**Expected:**
- ✅ Help response lists parameters for Return A, Device 0
- ✅ Response includes device name (e.g., "Return A • Reverb")
- ✅ Parameters shown: "Dry/Wet, Decay Time, ..." (up to 40)
- ✅ Context (return_index, device_index) is used from last command

**Browser Console Debugging:**
```javascript
// Test with explicit context
fetch('http://127.0.0.1:8722/help', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    query: 'what parameters can I control',
    context: {return_index: 0, device_index: 0}
  })
}).then(r => r.json()).then(console.log);
```

### Test 3.3: Device-Aware Preset Listing

**Setup:**
- Return A has a device with presets (e.g., Compressor, EQ Eight)
- Establish context with device command

**Steps:**
1. Type: **"set return A compressor ratio to 4:1"**
2. Type: **"what presets are available"**

**Expected:**
- ✅ Lists presets for the focused device
- ✅ Shows preset names from Firestore if available
- ✅ Fallback message if no presets found

### Test 3.4: Parameter Description

**Setup:**
- Device has Firestore mapping with parameter descriptions

**Steps:**
1. Ask: **"what does decay time do?"**

**Expected:**
- ✅ Returns description from Firestore mapping
- ✅ Includes unit and range info if available
- ✅ Shows labels if it's a choice parameter

---

## Test Suite 4: Compact Chat UI

### Test 4.1: Clean User Messages

**Steps:**
1. Type: **"set track 1 volume to -6 dB"**

**Expected:**
- ✅ User message appears in right-aligned bubble
- ✅ Shows the raw command text only
- ✅ No JSON or "processed/corrections" details
- ✅ Timestamp displayed

### Test 4.2: Clean Success Messages

**Steps:**
1. Execute any successful command

**Expected:**
- ✅ Success message left-aligned
- ✅ Shows summary only (e.g., "✅ Executed")
- ✅ No JSON dropdowns for canonical_intent or raw_intent
- ✅ Green checkmark icon
- ✅ Clean, chat-like appearance

### Test 4.3: Error Messages

**Steps:**
1. Type invalid command: **"set track 999 volume to 0"**

**Expected:**
- ✅ Error message displayed clearly
- ✅ Red error icon
- ✅ Helpful error text (e.g., "Track 999 not found. Available tracks: 0-4")
- ✅ No overwhelming JSON dumps

### Test 4.4: Help Response Formatting

**Steps:**
1. Type: **"how do I boost vocals?"**

**Expected:**
- ✅ Help icon displayed
- ✅ Answer text clearly formatted
- ✅ Suggested intents shown as clickable chips below answer
- ✅ Chips have hover effects

---

## Test Suite 5: Parameter Accordion

### Test 5.1: Accordion Appears After Device Command

**Steps:**
1. Type: **"set return A reverb decay to 2 seconds"**

**Expected:**
- ✅ Success message appears
- ✅ Below success message, an accordion section displays
- ✅ Header shows: "Parameters • Reverb" (or device name)
- ✅ Groups are collapsible sections (if Firestore mapping exists)
- ✅ Each group shows parameter chips when expanded

**Visual Check:**
- Accordion has subtle borders
- Groups expand/collapse with arrow icon
- Parameters appear as small outlined chips

### Test 5.2: Grouped Parameters

**Setup:**
- Device has Firestore mapping with groups (e.g., Reverb: "Global", "Diffusion Network", "Modulation")

**Expected:**
- ✅ Groups displayed as separate accordion items
- ✅ Group names match Firestore mapping
- ✅ Parameters correctly sorted into groups
- ✅ "Other" group appears for ungrouped params

### Test 5.3: Ungrouped Parameters

**Setup:**
- Device has no Firestore mapping, all params ungrouped

**Expected:**
- ✅ Single "Other" group contains all parameters
- ✅ Parameters still clickable

### Test 5.4: Empty Accordion

**Setup:**
- Device with no parameters (edge case)

**Expected:**
- ✅ Accordion doesn't render or shows empty state
- ✅ No errors in console

---

## Test Suite 6: Direct Parameter Reads

### Test 6.1: Click Parameter Chip

**Steps:**
1. Execute device command to show accordion
2. Expand a parameter group
3. Click a parameter chip (e.g., "Decay Time")

**Expected:**
- ✅ Info message appears immediately: "Current value for Decay Time on Return A device 0 is 2.00 s"
- ✅ Three suggested intents appear as clickable chips:
  - "set Return A device 0 Decay Time to 25%"
  - "set Return A device 0 Decay Time to 50%"
  - "set Return A device 0 Decay Time to 75%"
- ✅ No delay or LLM processing (fast path)
- ✅ Value is current/accurate

**Technical Check:**
- Browser Network tab shows POST to `/intent/read`
- Request body includes `domain: 'device'`, `return_ref`, `device_index`, `param_ref`
- No call to `/intent/parse` or LLM

### Test 6.2: Execute Suggested Intent

**Steps:**
1. After clicking a parameter, click one of the suggested chips (e.g., "50%")

**Expected:**
- ✅ Chip text inserted into chat as if user typed it
- ✅ Command executes normally
- ✅ Parameter value updates in Live
- ✅ New success message + accordion appears

### Test 6.3: Read Different Parameters

**Steps:**
1. Click multiple different parameter chips in sequence

**Expected:**
- ✅ Each read returns correct current value
- ✅ Info messages stack in chat history
- ✅ Suggested intents update for each parameter
- ✅ No performance issues

### Test 6.4: Parameter with On/Off Toggle

**Steps:**
1. Find a toggle parameter (e.g., "Device On")
2. Click it

**Expected:**
- ✅ Shows current on/off state clearly
- ✅ Suggested intents may adapt (e.g., "turn on" vs "turn off")
- ✅ Display value shown accurately

---

## Test Suite 7: End-to-End Workflow

### Test 7.1: Explore and Adjust Reverb

**Complete Workflow:**
1. Type: **"set return A reverb decay to 2 seconds"**
   - ✅ Command executes
   - ✅ Accordion appears with Reverb parameters
2. Expand "Global" group (or similar)
   - ✅ See parameters: Dry/Wet, Decay Time, etc.
3. Click "Dry/Wet" chip
   - ✅ Current value displayed (e.g., "100%")
   - ✅ Suggested intents appear
4. Click "set Return A device 0 Dry/Wet to 50%"
   - ✅ Command executes
   - ✅ Dry/Wet value changes to 50% in Live
5. Ask: **"what parameters can I control"**
   - ✅ Lists all Reverb parameters
6. Ask: **"what does pre-delay do?"**
   - ✅ Returns description if in Firestore

**Success:** Entire workflow feels smooth, interactive, and informative

### Test 7.2: Multiple Devices

**Setup:**
- Return A has multiple devices (e.g., EQ Eight, Reverb)

**Steps:**
1. Type: **"set return A device 0 EQ gain to 6 dB"**
   - ✅ Accordion for device 0 appears
2. Type: **"set return A device 1 reverb decay to 3 seconds"**
   - ✅ Accordion for device 1 appears
3. Chat history shows both accordions
   - ✅ Each accordion is independent and functional

### Test 7.3: Context Switching

**Steps:**
1. Execute device command for Return A, device 0
2. Ask: **"what presets are available"**
   - ✅ Shows presets for Return A, device 0
3. Execute device command for Return B, device 1
4. Ask: **"what parameters can I control"**
   - ✅ Shows parameters for Return B, device 1 (context updated)

---

## Test Suite 8: Error Handling

### Test 8.1: Invalid Device Index

**Steps:**
1. Type: **"set return A device 99 reverb decay to 2 seconds"**

**Expected:**
- ✅ Error message: "Device 99 not found on Return A. Available devices: 0, 1"
- ✅ No accordion appears
- ✅ UI remains stable

### Test 8.2: Ambiguous Parameter Name

**Steps:**
1. In console, test parameter lookup:
```javascript
fetch('http://127.0.0.1:8722/return/device/param_lookup?index=0&device=0&param_ref=time')
  .then(r => r.json())
  .then(console.log);
```

**Expected:**
- ✅ If multiple params match "time": `match_type: 'ambiguous'`, `candidates: ["Decay Time", "Pre-Delay"]`
- ✅ If unique: `match_type: 'unique'`, param details returned

### Test 8.3: Parameter Not Found

**Steps:**
1. Click a parameter in accordion, then delete the device in Live
2. Click another parameter chip

**Expected:**
- ✅ Error message: "no response" or "parameter not found"
- ✅ UI doesn't crash
- ✅ User can continue using chat

### Test 8.4: Network Timeout

**Steps:**
1. Stop Ableton Live (remote script offline)
2. Try to click a parameter chip

**Expected:**
- ✅ Error after timeout (~1-2 seconds)
- ✅ Graceful error message
- ✅ Suggested intents may not appear

---

## Test Suite 9: Performance

### Test 9.1: Capabilities Load Time

**Steps:**
1. Measure time for capabilities fetch:
```javascript
console.time('capabilities');
fetch('http://127.0.0.1:8722/return/device/capabilities?index=0&device=0')
  .then(r => r.json())
  .then(d => {
    console.timeEnd('capabilities');
    console.log(d);
  });
```

**Expected:**
- ✅ Load time < 2000ms (2 seconds)
- ✅ Most requests < 1000ms

### Test 9.2: Parameter Read Speed

**Steps:**
1. Click multiple parameter chips rapidly

**Expected:**
- ✅ Each read completes in < 1 second
- ✅ No race conditions or stale data
- ✅ UI remains responsive

### Test 9.3: Accordion Rendering

**Steps:**
1. Device with 50+ parameters (e.g., Wavetable, Operator)

**Expected:**
- ✅ Accordion renders without lag
- ✅ Groups expand smoothly
- ✅ No excessive re-renders

---

## Test Suite 10: Browser Compatibility

### Test 10.1: Chrome/Edge

**Expected:**
- ✅ All features work
- ✅ No console errors
- ✅ Layout renders correctly

### Test 10.2: Firefox

**Expected:**
- ✅ All features work
- ✅ MUI components render properly
- ✅ Chips clickable

### Test 10.3: Safari

**Expected:**
- ✅ All features work
- ✅ Accordion animations smooth
- ✅ No layout issues

### Test 10.4: Mobile (Responsive)

**Steps:**
1. Open DevTools → Toggle device toolbar
2. Test on mobile viewport (iPhone, Android)

**Expected:**
- ✅ Chat messages stack properly
- ✅ Accordion usable on small screens
- ✅ Chips don't overflow
- ✅ Text readable

---

## Debugging Tools

### Check Feature Flags
```javascript
fetch('http://127.0.0.1:8722/config')
  .then(r => r.json())
  .then(c => console.log('Config:', c));
```

### Monitor Network Requests
1. Open DevTools → Network tab
2. Filter by "XHR" or "Fetch"
3. Execute commands and observe:
   - `/intent/parse`
   - `/intent/execute`
   - `/return/device/capabilities`
   - `/intent/read`

### Check Conversation Context
```javascript
// In React DevTools, inspect useDAWControl hook
// Look for conversationContext state:
// {return_index: 0, device_index: 0}
```

### Test API Endpoints Directly
```javascript
// Parse intent
fetch('http://127.0.0.1:8722/intent/parse', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({text: 'set return A reverb decay to 2 seconds'})
}).then(r => r.json()).then(console.log);

// Get capabilities
fetch('http://127.0.0.1:8722/return/device/capabilities?index=0&device=0')
  .then(r => r.json())
  .then(console.log);

// Get snapshot
fetch('http://127.0.0.1:8722/snapshot')
  .then(r => r.json())
  .then(console.log);

// Help with context
fetch('http://127.0.0.1:8722/help', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    query: 'what parameters can I control',
    context: {return_index: 0, device_index: 0}
  })
}).then(r => r.json()).then(console.log);
```

---

## Known Issues

### 1. Firestore Mapping Availability
- Without Firestore mappings, all params appear in "Other" group
- This is expected fallback behavior
- To test with mappings, run Firestore emulator and populate device docs

### 2. Context Persistence
- Context resets if user asks unrelated question
- Context only tracks last device interaction
- This is intentional to avoid stale context

### 3. Return-to-Return Sends
- Only available if enabled in Live Preferences
- Capabilities API will show `sends_capable: false` if not available

---

## Success Criteria

✅ **All 10 test suites pass**
✅ **No browser console errors**
✅ **UI is compact and clean (no JSON blobs)**
✅ **Accordions render and function correctly**
✅ **Parameter reads are fast (<1s)**
✅ **Context-aware help works**
✅ **Suggested intents are relevant and clickable**
✅ **Error handling is graceful**

---

## Rollback Plan

If critical issues are found:

1. **Disable feature flag:**
```bash
curl -X POST http://127.0.0.1:8722/config/update \
  -H 'Content-Type: application/json' \
  -d '{"features":{"use_intents_for_chat":false}}'
```

2. **Hide accordions (hotfix):**
- Edit `ChatMessage.jsx:192-203`, comment out `ParamAccordion` render
- Rebuild UI: `npm run build`

3. **Disable direct reads:**
- Edit `useDAWControl.js:68-94`, comment out fast path
- Rebuild UI

---

## Test Sign-Off

**Tester Name:** _______________
**Date:** _______________
**Environment:** Local Dev / Staging / Production
**Result:** ☐ PASS  ☐ FAIL  ☐ PARTIAL

**Issues Found:**

---

**Notes:**
