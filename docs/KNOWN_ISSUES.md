# Known Issues

**Last Updated:** 2025-10-15

This document tracks known issues, incomplete features, and technical debt in the fadebender project.

---

## 🚧 Incomplete Features

### 1. Routing Intents - NOT WORKING CORRECTLY

**Status:** ⚠️ Code exists but has bugs/issues

**Issue:**
The `/intent/execute` and `/intent/read` endpoints include routing support for tracks and returns. Both the server API code and remote scripts are implemented, but the feature is not working correctly.

**Implemented Code (current architecture):**
- `server/services/intents/routing_service.py` – track/return routing execute/read

**Remote Scripts (Implemented):**
- `ableton_remote/Fadebender/lom_ops.py`:
  - `get_track_routing` (line 1205) ✅ EXISTS
  - `set_track_routing` (line 1287) ✅ EXISTS
  - `get_return_routing` (line 1350) ✅ EXISTS
  - `set_return_routing` (line 1399) ✅ EXISTS

**Routing Features Included (but non-functional):**
- Track routing:
  - `monitor_state` (In/Auto/Off)
  - `audio_from_type`, `audio_from_channel` (input routing)
  - `audio_to_type`, `audio_to_channel` (output routing)
  - `midi_from_type`, `midi_from_channel` (MIDI input)
- Return routing:
  - `audio_to_type`, `audio_to_channel` (output routing)
  - `sends_mode` (PreFader/PostFader/etc)

**Current Issues:**
- Routing operations may timeout or return incorrect data
- Validation logic exists but behavior needs verification
- Unknown what specific bugs are present (needs debugging/testing)

**To Fix:**
1. Debug why routing operations aren't working correctly
2. Test against Live API to verify routing reads/writes
3. Check if dispatcher is routing requests correctly
4. Verify option validation logic matches Live's available options
5. Add routing tests to test suite once working

**Priority:** Medium (feature is implemented but broken, should be fixed or removed)

**Next Steps:**
1. Investigate why routing operations fail
2. Add debug logging to track request/response flow
3. Test with simple routing changes (e.g., monitor state)
4. Consider if Live API limitations are causing issues

**Related Code:**
- Server: `server/services/intents/routing_service.py` (routing intent handlers; API delegates here)
- Remote: `ableton_remote/Fadebender/lom_ops.py` (routing operations)
- Both exist; investigate connection/logic issues

---

## ✅ Recently Fixed Issues

### Read API Implementation (FIXED 2025-10-15)

**Issue:** `/intent/read` endpoint had limited implementation
- Return domain reads missing
- Send reads missing
- Mute/solo returning null
- display_value formatting missing

**Fixed in:** Commit `39c9309`
- ✅ Full return domain support with letter-based API
- ✅ Send reads for tracks and returns
- ✅ Mute/solo boolean fixes (0.0/1.0 instead of null)
- ✅ display_value formatting for all mixer controls
- ✅ 47/47 tests passing

---

## 📋 Technical Debt

### 1. Test Coverage Gaps

**Areas needing tests:**
- Routing intents (once remote scripts implemented)
- Error handling edge cases
- Timeout scenarios
- Invalid parameter combinations

### 2. Documentation Gaps

**Missing documentation:**
- API reference for routing intents (once implemented)
- Remote script development guide
- Firestore schema documentation
- Device mapping creation guide

### 3. Code Quality Items

**Improvement opportunities:**
- Routing validation logic could be abstracted into shared helper
- Error messages could be more descriptive for routing failures
- Consider adding request/response logging for debugging

---

## 🔮 Future Enhancements

### 1. Routing Control (when remote scripts ready)
- Full track/return I/O routing control
- MIDI routing support
- Monitor state control
- Send mode control (pre/post fader)

### 2. Additional Domains
- Clip control (launch, stop, record)
- Scene control
- Transport control (play, stop, tempo)
- Arrangement view control

### 3. Performance Optimizations
- Batch intent execution
- Request coalescing
- Response caching where appropriate

---

## 📝 Notes for Developers

**Before implementing new intent features:**
1. Ensure corresponding remote script operations exist
2. Add tests to test plan documents
3. Update API documentation
4. Consider error cases and timeouts

**Testing routing when implemented:**
1. Use `dry_run: true` to preview changes
2. Test with actual Live set to verify options match
3. Validate against Live's routing constraints
4. Document any Live version differences

---

**Reporting Issues:**
If you discover additional issues, please update this document with:
- Clear description of the issue
- Steps to reproduce
- Expected vs actual behavior
- Related code locations
- Suggested fixes (if known)
