# Features Summary & Test Coverage

**Overview of new features and their testing documentation**

---

## New Features Overview

### 1. Device Capabilities API
**Location:** `server/api/returns.py:99-169`

**What it does:**
- Returns grouped parameters for return devices
- Fetches parameter metadata from Firestore (groups, units, labels)
- Falls back to live parameters if no Firestore mapping
- Includes current values for all parameters

**Endpoint:**
```
GET /return/device/capabilities?index=<return_index>&device=<device_index>
```

**Response:**
```json
{
  "ok": true,
  "data": {
    "return_index": 0,
    "device_index": 0,
    "device_name": "Reverb",
    "structure_signature": "Reverb_34_params",
    "groups": [...],
    "ungrouped": [...],
    "values": {...}
  }
}
```

**Test Coverage:**
- WEB_UI_FEATURE_TEST_PLAN.md: Test Suite 1
- QUICK_TEST_CHECKLIST.md: Test #9
- VISUAL_TESTING_GUIDE.md: Section 2

---

### 2. Live-Set Snapshot
**Location:** `server/api/overview.py:13-49`

**What it does:**
- Quick overview of entire Live set
- Lists all tracks with basic info
- Lists all return tracks with device names
- Provides counts for UI suggestions

**Endpoint:**
```
GET /snapshot
```

**Response:**
```json
{
  "ok": true,
  "tracks": [{index, name, type}],
  "track_count": 5,
  "returns": [{index, name, devices: [...]}],
  "return_count": 2,
  "sends_per_track": 2
}
```

**Use Cases:**
- Initial UI setup
- Autocomplete suggestions
- Context-aware validation

**Test Coverage:**
- WEB_UI_FEATURE_TEST_PLAN.md: Test Suite 2
- QUICK_TEST_CHECKLIST.md: Test #8

---

### 3. Smarter Context-Aware Help
**Location:** `server/app.py:3687-3800` (approximately)

**What it does:**
- Accepts context: `{return_index, return_ref, device_index}`
- Answers device-specific questions:
  - "what parameters can I control"
  - "what presets are available"
  - "what does <param> do"
- Provides sends/routing guidance
- Returns suggested intents relevant to context

**Endpoint:**
```
POST /help
Body: {
  "query": "what parameters can I control",
  "context": {"return_index": 0, "device_index": 0}
}
```

**Response:**
```json
{
  "ok": true,
  "answer": "Parameters on Return A • Reverb:\nDry/Wet, Decay Time, ...",
  "sources": [...],
  "suggested_intents": [...]
}
```

**Test Coverage:**
- WEB_UI_FEATURE_TEST_PLAN.md: Test Suite 3
- QUICK_TEST_CHECKLIST.md: Test #4, #7
- VISUAL_TESTING_GUIDE.md: Sections 4, 5

---

### 4. Compact Chat UI
**Location:** `clients/web-chat/src/components/ChatMessage.jsx`

**What changed:**
- Removed JSON dropdowns from intent/info messages
- User messages right-aligned
- Bot messages left-aligned
- Clean, chat-like appearance
- Only shows summary text, no technical details

**Key Changes:**
- Lines 150-177: Simplified intent card (no JSON)
- Lines 184-206: Success message without JSON details
- Lines 228-274: Info message without clutter

**Visual Impact:**
- Before: JSON blobs, technical fields, dropdowns
- After: Clean summaries, suggested intents, accordion

**Test Coverage:**
- WEB_UI_FEATURE_TEST_PLAN.md: Test Suite 4
- QUICK_TEST_CHECKLIST.md: Test #5
- VISUAL_TESTING_GUIDE.md: Sections 1, 7

---

### 5. Parameter Accordion
**Location:** `clients/web-chat/src/components/ParamAccordion.jsx`

**What it does:**
- Displays grouped parameters after device command
- Shows parameter chips (clickable)
- Expands/collapses groups
- Integrates with device capabilities API

**Component Props:**
- `capabilities`: Data from `/return/device/capabilities`
- `onParamClick`: Callback when parameter chip clicked

**Rendering Logic:**
- `ChatMessage.jsx:192-203`: Renders accordion if `message.data.capabilities` present
- Appears below success message
- Header: "Parameters • [Device Name]"

**Interaction:**
- Click parameter chip → triggers param read
- Read uses internal token `__READ_PARAM__|A|0|ParamName`
- Fast path bypasses LLM parsing

**Test Coverage:**
- WEB_UI_FEATURE_TEST_PLAN.md: Test Suite 5, 7
- QUICK_TEST_CHECKLIST.md: Tests #1, #6
- VISUAL_TESTING_GUIDE.md: Sections 2, 9

---

### 6. Direct Parameter Reads (Fast Path)
**Location:** `clients/web-chat/src/hooks/useDAWControl.js:68-94`

**What it does:**
- Bypasses LLM for parameter reads
- Uses internal directive: `__READ_PARAM__|<letter>|<device_idx>|<param_name>`
- Calls `/intent/read` directly with canonical format
- Returns current value + suggested intents instantly

**Flow:**
1. User clicks parameter chip
2. UI generates `__READ_PARAM__|A|0|Decay Time`
3. Hook detects prefix, calls `/intent/read` directly
4. Response: current value, unit, display_value
5. UI shows: "Current value for Decay Time ... is 2.00 s"
6. Suggested intents: "set ... to 25%", "... to 50%", "... to 75%"

**Performance:**
- No LLM call = < 1 second response
- Deterministic, no ambiguity
- Accurate current values

**Test Coverage:**
- WEB_UI_FEATURE_TEST_PLAN.md: Test Suite 6
- QUICK_TEST_CHECKLIST.md: Tests #2, #3
- VISUAL_TESTING_GUIDE.md: Section 3

---

### 7. Capabilities Auto-Fetch After Device Execute
**Location:** `clients/web-chat/src/hooks/useDAWControl.js:176-189`

**What it does:**
- After successful device intent execution
- Automatically fetches capabilities for that device
- Adds message with accordion to chat
- Updates conversation context for follow-up questions

**Logic:**
1. Extract context from executed intent (`return_index`, `device_index`)
2. Call `/return/device/capabilities?index=<ri>&device=<di>`
3. If successful, add message with `type: 'success'`, `data: { capabilities: ... }`
4. ChatMessage component renders ParamAccordion
5. Context stored for help queries

**Test Coverage:**
- WEB_UI_FEATURE_TEST_PLAN.md: Test Suite 7
- QUICK_TEST_CHECKLIST.md: Test #1

---

### 8. Client API Service Additions
**Location:** `clients/web-chat/src/services/api.js`

**New Methods:**

```javascript
// Execute canonical intent directly
executeCanonicalIntent(intent)

// Read intent (for fast param reads)
readIntent(body)

// Get snapshot
getSnapshot()

// Get return device capabilities
getReturnDeviceCapabilities(index, device)

// Help with context
getHelp(query, context)
```

**Usage:**
- `executeCanonicalIntent`: Used when `use_intents_for_chat` enabled
- `readIntent`: Used for `__READ_PARAM__` fast path
- `getSnapshot`: Called on UI mount (optional)
- `getReturnDeviceCapabilities`: Called after device execute
- `getHelp`: Accepts context for device-aware help

---

## Feature Integration Map

```
User Command
    ↓
[processControlCommand] useDAWControl.js:61
    ↓
[apiService.parseIntent] api.js
    ↓
[apiService.executeCanonicalIntent] api.js (if feature flag enabled)
    ↓
Success → Extract context (return_index, device_index)
    ↓
[apiService.getReturnDeviceCapabilities] api.js:176-189
    ↓
Add message with capabilities → ChatMessage.jsx:192
    ↓
Render ParamAccordion → ParamAccordion.jsx
    ↓
User clicks parameter chip
    ↓
onParamClick callback → ChatMessage.jsx:195-202
    ↓
Generate __READ_PARAM__ token → useDAWControl.js:68
    ↓
[apiService.readIntent] api.js (fast path, no LLM)
    ↓
Display current value + suggested intents
    ↓
User clicks suggested intent
    ↓
[Cycle repeats]
```

---

## Test Documentation Map

| Document | Purpose | Time to Complete |
|----------|---------|------------------|
| **WEB_UI_FEATURE_TEST_PLAN.md** | Comprehensive test plan with 10 test suites | 30-45 minutes |
| **QUICK_TEST_CHECKLIST.md** | Quick smoke tests, critical path | 5-10 minutes |
| **VISUAL_TESTING_GUIDE.md** | Visual expectations, screenshots guide | Reference |
| **INTENTS_CHAT_INTEGRATION_TEST.md** | Legacy test plan (still relevant for regression) | 20 minutes |
| **FEATURES_SUMMARY.md** | This document - feature overview | Reference |

---

## Testing Strategy

### Phase 1: Quick Smoke Tests (10 minutes)
Use: **QUICK_TEST_CHECKLIST.md**
- Tests #1-5 (critical path)
- Verify basic functionality
- Catch major regressions

### Phase 2: Comprehensive Testing (45 minutes)
Use: **WEB_UI_FEATURE_TEST_PLAN.md**
- All 10 test suites
- API verification
- Performance checks
- Error handling

### Phase 3: Visual QA (15 minutes)
Use: **VISUAL_TESTING_GUIDE.md**
- Layout verification
- Responsive design
- Browser compatibility
- Accessibility check

### Phase 4: Regression (20 minutes)
Use: **INTENTS_CHAT_INTEGRATION_TEST.md**
- Ensure old features still work
- Volume, pan, mute, sends
- Error handling
- Feature flag toggle

**Total Time:** ~90 minutes for full test cycle

---

## Feature Flags

### Current Flag: `use_intents_for_chat`
**Default:** `true`
**Location:** `configs/app_config.json`, `server/config/app_config.py`

**When enabled:**
- Web UI uses `/intent/execute` instead of `/chat`
- Canonical intents executed directly
- Faster, more deterministic

**When disabled:**
- Falls back to legacy `/chat` endpoint
- NLP service route
- Still works, but slower

**Test:** Toggle this flag and verify both paths work (see QUICK_TEST_CHECKLIST.md #10)

---

## Known Limitations

### 1. Firestore Dependency
**Impact:** Without Firestore mappings:
- All parameters appear in "Other" (ungrouped)
- No unit/label metadata
- Still functional, just less organized

**Workaround:** Run Firestore emulator and populate mappings

---

### 2. Context Persistence
**Impact:** Context only tracks last device interaction
- If user asks unrelated question, context may reset
- Intentional design to avoid stale context

**Not a bug:** Expected behavior

---

### 3. Return-to-Return Sends
**Impact:** Only available if enabled in Live Preferences
- Capabilities API shows `sends_capable: false` if disabled
- Not a bug, just a Live limitation

**Workaround:** Enable in Live → Preferences → Record/Warp/Launch

---

## API Endpoints Summary

| Endpoint | Method | Purpose | Tested In |
|----------|--------|---------|-----------|
| `/return/device/capabilities` | GET | Get grouped params + values | Suite 1, Test #9 |
| `/snapshot` | GET | Live-set overview | Suite 2, Test #8 |
| `/help` | POST | Context-aware help | Suite 3, Tests #4, #7 |
| `/intent/read` | POST | Fast param read | Suite 6, Test #2 |
| `/intent/parse` | POST | Parse to canonical | All suites |
| `/intent/execute` | POST | Execute canonical | All suites |

---

## Code Locations Reference

### Server (Python)
```
server/api/returns.py:99-169         Device capabilities endpoint
server/api/overview.py:13-49         Snapshot endpoint
server/app.py:3687-3800              Context-aware help endpoint
server/services/intent_mapper.py     Intent parsing/mapping
```

### Client (React)
```
clients/web-chat/src/components/
  ChatMessage.jsx:1-337              Message rendering, accordion integration
  ParamAccordion.jsx:1-54            Parameter accordion component

clients/web-chat/src/hooks/
  useDAWControl.js:1-346             Main business logic, fast path reads

clients/web-chat/src/services/
  api.js                             API service methods

clients/web-chat/src/utils/
  textProcessor.js                   Input processing
```

---

## Success Metrics

✅ **All critical path tests pass** (QUICK_TEST_CHECKLIST.md)
✅ **No console errors**
✅ **Parameter reads < 1 second**
✅ **Capabilities load < 2 seconds**
✅ **Clean, readable UI (no JSON blobs)**
✅ **Accordions render and function**
✅ **Context-aware help works**
✅ **Suggested intents clickable and accurate**
✅ **Error messages clear and helpful**
✅ **Responsive on mobile**

---

## Rollback Procedures

### If Critical Issues Found:

#### Option 1: Disable Feature Flag
```bash
curl -X POST http://127.0.0.1:8722/config/update \
  -H 'Content-Type: application/json' \
  -d '{"features":{"use_intents_for_chat":false}}'
```
**Impact:** Falls back to legacy `/chat` path, features still work

#### Option 2: Hide Accordions (Hotfix)
Edit `clients/web-chat/src/components/ChatMessage.jsx:192-203`
```javascript
// Comment out ParamAccordion render
// {message.data && message.data.capabilities && (
//   <ParamAccordion ... />
// )}
```
Rebuild: `npm run build`

#### Option 3: Disable Fast Path Reads
Edit `clients/web-chat/src/hooks/useDAWControl.js:68-94`
```javascript
// Comment out __READ_PARAM__ fast path
// if (rawInput && rawInput.startsWith('__READ_PARAM__|')) {
//   ...
// }
```
Rebuild: `npm run build`

---

## Next Steps After Testing

### If All Tests Pass:
1. ✅ Mark features as stable
2. ✅ Update main README with new features
3. ✅ Record demo video showing new UI
4. ✅ Consider enabling by default in production

### If Issues Found:
1. ❌ Document issues in GitHub/issue tracker
2. ❌ Prioritize fixes (critical vs nice-to-have)
3. ❌ Re-test after fixes
4. ❌ Consider partial rollback if critical

---

## Questions to Answer During Testing

- [ ] Are parameter groups intuitive?
- [ ] Is the fast read feature discoverable?
- [ ] Do suggested intents help or confuse?
- [ ] Is context switching clear to users?
- [ ] Are error messages helpful enough?
- [ ] Does the accordion improve or clutter the UI?
- [ ] Are load times acceptable?
- [ ] Does it work on all target browsers?
- [ ] Is mobile experience usable?
- [ ] Are there any unexpected edge cases?

---

**Testing Coordinator:** _______________
**Test Start Date:** _______________
**Expected Completion:** _______________
**Status:** ☐ Not Started  ☐ In Progress  ☐ Complete

---

## Feedback

After testing, please provide feedback:

**What worked well:**

**What needs improvement:**

**Bugs found:**

**Feature requests:**

**Overall impression:**
