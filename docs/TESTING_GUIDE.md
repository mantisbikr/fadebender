# Fadebender Testing Guide

## Overview

This guide explains how to test the Fadebender NLP system after making changes to the parser, intent mapper, or NLP pipeline.

## Prerequisites

1. **Server must be running:**
   ```bash
   npm run server
   ```

2. **Ableton Live must be connected** with a valid preset loaded

---

## Comprehensive Intent Test Suite

### Quick Test (Recommended)

Run this after **any** parser or NLP changes:

```bash
python3 scripts/test_comprehensive_intents.py
```

This test covers:
- ✅ **Mixer commands** (volume, pan, send, mute, solo)
- ✅ **Device parameters** (absolute + relative changes)
- ✅ **Transport commands** (loop, tempo, playhead, time signature)
- ✅ **Navigation commands** (open track/return/device)
- ✅ **Typo handling** (common typos)
- ✅ **Special characters** (/, <, >, &, -)

**Expected result:** All tests passing (0 failures)

---

## Specialized Test Suites

### 1. Device-Context Parsing Tests

Tests fuzzy matching and device-scoped parameter resolution:

```bash
python3 scripts/test_special_characters.py
```

Covers:
- Parameters with `/` (e.g., "Dry/Wet")
- Parameters with `<` / `>` (e.g., "Dly < Mod")
- Device name hyphens (e.g., "Gentle-Kneeless")

### 2. Mixer Functional Tests

Tests mixer commands still work after parser changes:

```bash
python3 scripts/test_mixer_functional.py
```

Covers:
- Track volume/pan/send/mute/solo
- Return controls
- Minimal dependencies (only needs one return track)

### 3. Relative Intent Tests

Tests increase/decrease commands:

```bash
python3 scripts/test_relative_intents.py
```

Covers:
- Relative mixer changes (volume, pan, send)
- Relative device changes (dry/wet, feedback, decay)
- Edge cases (missing amounts)

---

## Manual Testing Checklist

When doing exploratory testing, verify these scenarios:

### Core Functionality
- [ ] Absolute changes: "set track 1 volume to -10db"
- [ ] Relative changes: "increase track volume by 3db"
- [ ] Device parameters: "set return a reverb decay to 5 seconds"
- [ ] Transport: "set tempo to 130", "loop on"
- [ ] Navigation: "open track 1", "open return a"

### Song-Level Operations
- [ ] Undo/Redo: "undo", "redo", "undo last change"
- [ ] Song info: "what's the song name", "show song info"
- [ ] Song length: "what is the song length", "how long is the song"
- [ ] Playhead: "where is the playhead", "where am I"
- [ ] List locators: "list locators", "show locators"
- [ ] Jump to locator: "jump to locator 2", "go to intro"
- [ ] Rename locator: "rename locator 1 to intro", "call locator 2 verse"

### Device Loading
- [ ] Load device: "load reverb on track 2", "add compressor to track 1"
- [ ] Load on return: "put limiter on return A", "insert delay on return B"
- [ ] Load with preset (explicit): "load reverb preset cathedral on track 2"
- [ ] Load with preset (implicit): "load analog lush pad on track 3"
- [ ] Multi-word devices: "load auto filter on track 3", "add eq eight to track 1"
- [ ] Case-insensitive: "load reverb" / "load REVERB" / "load Reverb"
- [ ] Verify device appears in track/return device chain
- [ ] Requires: device_map.json configured and Live browser accessible

### Device Deletion
- [ ] Delete by name: "delete reverb from track 2", "remove compressor from track 1"
- [ ] Delete by index: "delete device 0 from track 2"
- [ ] Delete by ordinal: "delete first reverb from track 2", "remove second compressor from track 1"
- [ ] Delete from return: "delete reverb from return A", "remove delay from return B"
- [ ] Case-insensitive matching: "delete REVERB from track 2"
- [ ] Verify device is removed from device chain
- [ ] Error handling: "delete nonexistent from track 2" (should fail gracefully)
- [ ] Multiple devices: Load 2 reverbs, then "delete first reverb from track 2" (should keep second)

### Typo Handling
- [ ] Common typos work: "set track volum to -20" (volum → volume)
- [ ] Multiple typos: "incrase track volumz by 5db"
- [ ] Typos don't break legitimate words

### Edge Cases
- [ ] Missing context prompts clarification: "increase reverb dry/wet by 10%"
- [ ] Special characters: "set return a reverb dry wet to 50%" (dry wet → Dry/Wet)
- [ ] Device ordinals: "set return b device 0 dry/wet to 30%"

---

## Test After Changes To:

### Parser Changes
Run: `test_comprehensive_intents.py` + `test_special_characters.py`

### Intent Mapper Changes
Run: `test_comprehensive_intents.py`

### Typo Correction Config
Run: `test_comprehensive_intents.py` (section 7: Typo Handling)

### New Device Mappings
Run: `test_special_characters.py`

---

## Debugging Failed Tests

### 1. Check Server Logs
Look for errors in server console output

### 2. Test Single Command
```bash
curl -s http://127.0.0.1:8722/intent/parse -X POST \
  -H "Content-Type: application/json" \
  -d '{"text":"your command here"}' | python3 -m json.tool
```

### 3. Check Pipeline
Look for `"pipeline"` field in response:
- `"regex"` - Using fast regex matcher
- `"llm_fallback"` - Using LLM (slower, more expensive)
- `"failed"` - Parse failed

### 4. Check Learned Typos
If typo correction is involved, check:
```json
"learned_typos": {
  "volum": "volume"
}
```

---

## Performance Benchmarks

### Target Latencies
- **Regex pipeline:** < 10ms
- **LLM fallback (cached):** < 100ms
- **LLM fallback (uncached):** 1-3 seconds

### Check Pipeline Usage
After running tests, review console output for pipeline distribution:
- **Goal:** >80% using regex pipeline
- **Current:** TBD (after parser integration)

---

## Regression Testing

### Before Committing Parser Changes

1. Run comprehensive test suite:
   ```bash
   python3 scripts/test_comprehensive_intents.py
   ```

2. Verify 100% pass rate

3. Check no new LLM fallbacks introduced (if parser is integrated)

### Before Releasing

1. Run all test suites
2. Manual exploratory testing (15 minutes)
3. Check performance hasn't regressed

---

## Adding New Tests

When adding a new intent type:

1. Add test case to `test_comprehensive_intents.py`
2. Add to appropriate category (Mixer, Device, Transport, etc.)
3. Run test to verify it passes
4. Document any special setup needed

---

## Known Issues

### Issue: Tests fail with "Server not responding"
**Solution:** Start server with `npm run server`

### Issue: Tests fail with "missing_or_invalid_track"
**Solution:** Load a preset in Ableton Live with tracks/returns

### Issue: Typo tests failing
**Check:** Firestore nlp_config/typo_corrections document matches app_config.json

---

## Questions?

See:
- `CLAUDE.md` - Project instructions
- `server/services/parse_index/` - Parser implementation
- `nlp-service/` - LLM fallback system
