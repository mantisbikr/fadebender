# Intents Chat Integration Test Plan

**Date:** 2025-10-16
**Feature:** Web Chat UI now uses `/intent/execute` API by default
**Status:** Ready for testing

---

## What Changed

### 1. Feature Flag Enabled by Default

**Server-side:**
- `server/config/app_config.py`: Default changed from `False` to `True`
- `configs/app_config.json`: Added `"use_intents_for_chat": true`

**Client-side:**
- Web UI automatically fetches feature flags on load
- Routes chat commands through `/intent/execute` when flag is enabled
- Falls back to legacy `/chat` endpoint on error

### 2. Request Flow

**New flow (intents-based):**
1. User enters command in chat
2. Text processed and validated
3. `/intent/parse` called to get canonical intent
4. **NEW:** If `use_intents_for_chat` is true → `/intent/execute` with canonical intent
5. Success message displayed with summary

**Legacy flow (fallback):**
1-3. Same as above
4. `/chat` endpoint called (NLP service + controller)
5. Success message displayed

---

## Testing Instructions

### Prerequisites

```bash
# 1. Start server (with feature flag enabled)
cd server && make dev-returns

# 2. Start web UI
cd clients/web-chat
npm run dev
# Open http://localhost:5173

# 3. Ensure Ableton Live is running with remote script
```

### Test Cases

#### Test 1: Basic Volume Control

**Command:** "set track 1 volume to -6 dB"

**Expected:**
- ✅ Success message: "✅ Executed" or similar
- ✅ Track 1 volume moves to -6.0 dB in Live
- ✅ No errors in browser console
- ✅ Request goes to `/intent/execute` (check Network tab)

#### Test 2: Pan Control

**Command:** "pan track 2 50% left"

**Expected:**
- ✅ Success message displayed
- ✅ Track 2 pans to 50L in Live
- ✅ Uses intents API

#### Test 3: Mute/Solo

**Command:** "mute track 1"

**Expected:**
- ✅ Track 1 mute button lights up
- ✅ Success message
- ✅ Intents API used

**Command:** "unmute track 1"

**Expected:**
- ✅ Track 1 mute button turns off

#### Test 4: Send Control

**Command:** "set track 1 send A to -12 dB"

**Expected:**
- ✅ Track 1 Send A moves to -12 dB
- ✅ Success via intents

#### Test 5: Return Track Control

**Command:** "set return A volume to -3 dB"

**Expected:**
- ✅ Return A volume at -3.0 dB
- ✅ Letter-based API working

#### Test 6: Device Parameter

**Command:** "set return A reverb decay to 2 seconds"

**Expected:**
- ✅ Reverb Decay Time at 2.0s
- ✅ Display-value control working

#### Test 7: Error Handling (Invalid Command)

**Command:** "set track 999 volume to 0"

**Expected:**
- ⚠️ Error message displayed
- ⚠️ Appropriate error from intents API
- ✅ UI doesn't crash

#### Test 8: Help Query

**Command:** "how do I control sends?"

**Expected:**
- ℹ️ Help response from knowledge base
- ✅ Does NOT go through intents execute
- ✅ Routed to `/help` endpoint

#### Test 9: Clarification Needed

**Command:** "mute the track" (ambiguous)

**Expected:**
- ❓ Clarification question displayed
- ✅ User can respond with clarification
- ✅ Command executes after clarification

#### Test 10: Feature Flag Toggle

**Test disabling the flag:**

```bash
# Disable via API
curl -X POST http://127.0.0.1:8722/config/update \
  -H 'Content-Type: application/json' \
  -d '{"features":{"use_intents_for_chat":false}}'

# Reload web UI page
```

**Expected:**
- ✅ Requests now go to `/chat` endpoint (legacy)
- ✅ Commands still work (fallback path)

**Re-enable:**

```bash
curl -X POST http://127.0.0.1:8722/config/update \
  -H 'Content-Type: application/json' \
  -d '{"features":{"use_intents_for_chat":true}}'

# Reload web UI page
```

**Expected:**
- ✅ Back to using `/intent/execute`

---

## Verification Checklist

### Server Health

- [ ] `/health` returns 200 OK
- [ ] `/config` returns `use_intents_for_chat: true`
- [ ] `/intent/parse` working
- [ ] `/intent/execute` working

### Web UI Health

- [ ] Page loads without errors
- [ ] Feature flag fetched on mount
- [ ] Chat input accepts commands
- [ ] Messages display correctly
- [ ] No console errors

### Command Execution

- [ ] Simple commands work (volume, pan, mute)
- [ ] Complex commands work (sends, device params)
- [ ] Letter-based API works (return_ref:"A", send_ref:"B")
- [ ] Error handling graceful
- [ ] Success messages clear

### Integration Points

- [ ] Intent parsing works
- [ ] Canonical intent execution works
- [ ] Fallback to legacy chat on error
- [ ] Help queries routed correctly
- [ ] Clarification flow works

---

## Browser Console Debugging

### Check Feature Flag

```javascript
// In browser console
fetch('http://127.0.0.1:8722/config')
  .then(r => r.json())
  .then(c => console.log('Features:', c.features));
```

### Monitor Requests

1. Open DevTools → Network tab
2. Filter by "Fetch/XHR"
3. Enter a command
4. Look for requests to:
   - `/intent/parse` (should see canonical intent)
   - `/intent/execute` (should see execution result)
   - `/chat` (should NOT see if flag is enabled)

### Check Responses

```javascript
// Parse a test command
fetch('http://127.0.0.1:8722/intent/parse', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({text: 'set track 1 volume to -6 dB'})
}).then(r => r.json()).then(console.log);

// Execute canonical intent
fetch('http://127.0.0.1:8722/intent/execute', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    domain: 'track',
    action: 'set',
    track_index: 1,
    field: 'volume',
    value: -6,
    unit: 'dB'
  })
}).then(r => r.json()).then(console.log);
```

---

## Known Issues to Watch For

### 1. Routing Intents

- ⚠️ Routing commands may timeout (known issue - see KNOWN_ISSUES.md)
- Commands like "set track 1 monitor to in" will fail
- This is expected - routing remote scripts have bugs

### 2. Feature Flag Caching

- Web UI loads config on mount
- If you change the flag, **refresh the page**
- Or clear React state and re-mount

### 3. Error Recovery

- If intents API fails, fallback to `/chat` should trigger
- Check Network tab to verify fallback occurred

---

## Success Criteria

✅ **All 10 test cases pass**
✅ **No browser console errors**
✅ **Commands execute in Live as expected**
✅ **Feature flag toggle works**
✅ **Network requests go to correct endpoints**

---

## Troubleshooting

### Commands Not Executing

1. Check server is running: `curl http://127.0.0.1:8722/health`
2. Check Live remote script is active
3. Check browser console for errors
4. Verify feature flag: `curl http://127.0.0.1:8722/config | jq .features`

### Wrong Endpoint Being Called

1. Refresh web UI page (config loaded on mount)
2. Verify feature flag in server response
3. Check `useDAWControl.js` line 97 logic

### Errors in Execution

1. Check `/intent/parse` response for valid intent
2. Test `/intent/execute` directly (see console examples above)
3. Check server logs for errors
4. Verify Live API is responding

---

## Rollback Plan

If issues arise:

```bash
# Disable intents for chat
curl -X POST http://127.0.0.1:8722/config/update \
  -H 'Content-Type: application/json' \
  -d '{"features":{"use_intents_for_chat":false}}'

# Restart server if needed
cd server && make dev-returns
```

Web UI will automatically fall back to legacy `/chat` endpoint.

---

**Tester:** ______________
**Date Tested:** ______________
**Result:** PASS / FAIL / PARTIAL
**Notes:**
