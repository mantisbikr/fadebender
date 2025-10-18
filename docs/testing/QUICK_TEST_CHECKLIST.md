# Quick Test Checklist - New Web UI Features

**Quick reference for manual testing the latest UI updates**

---

## Setup (2 minutes)

1. ✅ Ableton Live running with remote script connected
2. ✅ At least one return track with an effect (e.g., Return A → Reverb)
3. ✅ Server running: `cd server && make dev-returns`
4. ✅ Web UI running: `cd clients/web-chat && npm run dev`
5. ✅ Open http://localhost:5173

---

## Critical Path Tests (5 minutes)

### 1. Device Command Shows Accordion ⚡
**Type:** `set return A reverb decay to 2 seconds`

**✅ Pass if:**
- Command executes successfully
- Accordion appears below success message
- Shows "Parameters • Reverb"
- Can expand groups and see parameter chips

---

### 2. Click Parameter Reads Value ⚡⚡
**Action:** Click any parameter chip in accordion (e.g., "Dry/Wet")

**✅ Pass if:**
- Info message appears: "Current value for Dry/Wet on Return A device 0 is 100%"
- Three suggested intents appear (25%, 50%, 75%)
- Response is instant (<1 second)

---

### 3. Execute Suggested Intent ⚡
**Action:** Click one of the suggested chips (e.g., "50%")

**✅ Pass if:**
- Command executes
- Parameter value changes in Live
- New success message appears
- New accordion appears

---

### 4. Context-Aware Help ⚡
**After doing #1, type:** `what parameters can I control`

**✅ Pass if:**
- Lists parameters for the device you just controlled
- Shows device name (e.g., "Return A • Reverb")
- No errors

---

### 5. Clean Chat UI ⚡
**Check:** Review chat messages from tests above

**✅ Pass if:**
- No JSON dropdowns visible
- User messages right-aligned
- Bot messages left-aligned
- Clean, readable, chat-like interface

---

## Extended Tests (10 minutes)

### 6. Multiple Parameters
**Action:** Click 3-5 different parameters in accordion

**✅ Pass if:**
- Each shows current value
- Suggested intents update
- No lag or errors

---

### 7. Generic Help
**Type:** `how do I control sends?`

**✅ Pass if:**
- Help response with explanation
- Suggested intents appear as clickable chips
- Clean formatting

---

### 8. Snapshot API
**Browser Console:**
```javascript
fetch('http://127.0.0.1:8722/snapshot')
  .then(r => r.json())
  .then(console.log);
```

**✅ Pass if:**
- Returns tracks, returns, device lists
- Counts match your Live project
- Response < 2 seconds

---

### 9. Capabilities API
**Browser Console:**
```javascript
fetch('http://127.0.0.1:8722/return/device/capabilities?index=0&device=0')
  .then(r => r.json())
  .then(console.log);
```

**✅ Pass if:**
- Returns groups (or ungrouped fallback)
- Shows current values
- Device name correct

---

### 10. Error Handling
**Type:** `set return A device 99 reverb decay to 2 seconds`

**✅ Pass if:**
- Clear error message
- Lists available devices
- No crash or console errors

---

## Regression Tests (5 minutes)

### 11. Basic Volume Control
**Type:** `set track 1 volume to -6 dB`

**✅ Pass if:**
- Still works as before
- Clean success message

---

### 12. Mute/Solo
**Type:** `mute track 1`

**✅ Pass if:**
- Track mutes in Live
- Success message

---

### 13. Send Control
**Type:** `set track 1 send A to -12 dB`

**✅ Pass if:**
- Send level changes
- Works normally

---

## Performance Check

### 14. No Console Errors
**Action:** Open DevTools → Console tab

**✅ Pass if:**
- No red errors during any test
- Warnings are acceptable (if not critical)

---

### 15. Network Performance
**Action:** Open DevTools → Network tab, execute commands

**✅ Pass if:**
- `/intent/parse` < 2 seconds
- `/intent/execute` < 2 seconds
- `/return/device/capabilities` < 2 seconds
- `/intent/read` < 1 second

---

## Visual Check

### 16. Layout
**✅ Pass if:**
- Messages don't overflow
- Accordions render cleanly
- Chips wrap properly
- Timestamps visible

---

### 17. Interactivity
**✅ Pass if:**
- Chips clickable with hover effect
- Accordions expand/collapse smoothly
- No UI freezing

---

## Quick Debugging Commands

### Check Config
```javascript
fetch('http://127.0.0.1:8722/config')
  .then(r => r.json())
  .then(c => console.log('Config:', c.features));
```

### Check Health
```bash
curl http://127.0.0.1:8722/health
```

### Check Network Tab
- Filter: "XHR"
- Look for: `/intent/parse`, `/intent/execute`, `/return/device/capabilities`, `/intent/read`

---

## Pass/Fail Summary

**Date:** _______________
**Tester:** _______________

| # | Test | Pass | Fail | Notes |
|---|------|------|------|-------|
| 1 | Device Accordion | ☐ | ☐ | |
| 2 | Click Parameter | ☐ | ☐ | |
| 3 | Execute Suggested | ☐ | ☐ | |
| 4 | Context Help | ☐ | ☐ | |
| 5 | Clean UI | ☐ | ☐ | |
| 6 | Multiple Params | ☐ | ☐ | |
| 7 | Generic Help | ☐ | ☐ | |
| 8 | Snapshot API | ☐ | ☐ | |
| 9 | Capabilities API | ☐ | ☐ | |
| 10 | Error Handling | ☐ | ☐ | |
| 11 | Volume Control | ☐ | ☐ | |
| 12 | Mute/Solo | ☐ | ☐ | |
| 13 | Send Control | ☐ | ☐ | |
| 14 | No Errors | ☐ | ☐ | |
| 15 | Performance | ☐ | ☐ | |
| 16 | Layout | ☐ | ☐ | |
| 17 | Interactivity | ☐ | ☐ | |

**Overall:** ☐ PASS  ☐ FAIL

---

## Critical Issues Found

_List any blocking issues here_

---

## Notes

_Additional observations_
