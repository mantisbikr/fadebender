# Next Features & Enhancements

**Priority Order:** Step 6 Intents → Phase 4 Knowledge → Smart Learning

---

## 🎯 Step 6: Intent Improvements (In Progress)

### Relative Volume via UDP Readback
**Status:** ⏳ Pending
**Goal:** Support "increase volume by 3dB" with current value readback

**Implementation:**
1. Read current volume from UDP before applying relative change
2. Calculate new value with bounds checking
3. Apply and verify

**Endpoint:** Extend `/op/mixer` with readback support

### Basic Sends Auto-Execution
**Status:** ⏳ Pending
**Goal:** Enable send control in auto-execute mode

**Implementation:**
1. Add sends intent parsing
2. Support "Send A to Drums" style commands
3. Add to auto-executable intent list

**Endpoint:** Extend `/intent/parse` and `/op/send`

---

## 📚 Phase 4: Knowledge + Aliasing (Planned)

### Knowledge Files for LLM Context
**Goal:** Provide device-specific parameter context to LLM

**Implementation:**
1. Create knowledge files per device (e.g., `knowledge/delay.md`)
2. Include parameter descriptions, typical values, use cases
3. Inject into LLM context when device mentioned
4. Use Ableton Live manual + audio engineering notes

**Files to Create:**
- `knowledge/delay.md`
- `knowledge/reverb.md`
- `knowledge/compressor.md`
- `knowledge/eq_eight.md`

**Example Content:**
```markdown
# Delay Device Parameters

## Feedback (0-100%)
Controls how many times the delay repeats.
- Low (0-30%): Subtle echo
- Medium (30-60%): Multiple repeats
- High (60-100%): Infinite sustain (use with caution)

Typical uses:
- Vocal delay: 20-40%
- Dub delays: 60-80%
```

### Parameter Aliasing
**Goal:** Map natural language to parameter names

**Implementation:**
1. Create alias mapping config (e.g., `configs/param_aliases.json`)
2. Support multi-word aliases ("wet signal" → "Dry/Wet")
3. Device-specific aliases (Reverb "room size" → "DecayTime")

**Example Config:**
```json
{
  "global": {
    "wet": "Dry/Wet",
    "dry": "Dry/Wet",
    "mix": "Dry/Wet"
  },
  "Delay": {
    "repeats": "Feedback",
    "echo time": "L Time"
  }
}
```

**Endpoint:** Modify `/op/return/param_by_name` to resolve aliases first

---

## 🧠 Smart Learning Enhancements (Future)

### Template-Based Learning
**Goal:** Use known device patterns to speed up learning

**Concept:**
- Store device "templates" with common parameter patterns
- For known devices, use template + verification instead of full learn
- Dramatically reduce learn time (5s vs 30s)

**Implementation:**
1. Build template library from learned devices
2. Match by device name/signature
3. Quick verification scan (3-5 key parameters)
4. Fall back to full learn if mismatch

### Binary State Exploration
**Goal:** Always explore both states of binary parameters

**Current Issue:**
- If parameter is always Off during learn, On state unknown
- Causes incomplete mappings for toggles

**Solution:**
1. Detect binary parameters (label_map with 2 entries)
2. Force toggle to opposite state during learning
3. Sample both On and Off states
4. Restore original state after learning

**Files to Modify:**
- `server/app.py` - `learn_return_device_quick()` function

### Iterative Value Refinement
**Goal:** Multi-pass refinement for exact display value targeting

**Current:** Single-shot inversion with 1-2 nudges
**Proposed:** Bisection search for exact targets

**Implementation:**
1. Set initial value via fit inversion
2. Read actual display value
3. If error > threshold, bisect toward target
4. Repeat up to 5 iterations or within 0.5% tolerance

**Already Implemented:** Basic bisection exists in `set_return_param_by_name()`
**Enhancement:** Tune bisection parameters, add adaptive step sizing

---

## 🔍 Additional Device Testing

### Priority Devices to Test
1. **Reverb** - Already has grouping rules, verify all params
2. **Compressor** - Test threshold, ratio, attack, release
3. **EQ Eight** - Test frequency bands, gain, Q
4. **Saturator** - Test drive, dry/wet, color

### Test Plan Template
For each device:
1. Run quick learn
2. Verify map_summary (groups, roles)
3. Test 5-10 key parameters (continuous, binary, relative)
4. Document results in `testing/DEVICE_TEST_RESULTS.md`
5. Update config if grouping needed

---

## 📊 Priority Matrix

| Feature | Impact | Effort | Priority |
|---------|--------|--------|----------|
| Relative volume readback | High | Low | 🔥 P0 |
| Sends auto-exec | Medium | Low | 🔥 P0 |
| Parameter aliases | High | Medium | ⭐ P1 |
| Knowledge files | Medium | Medium | ⭐ P1 |
| Binary state exploration | Medium | Medium | ⭐ P1 |
| Template learning | High | High | 💡 P2 |
| Additional device testing | Medium | Medium | 💡 P2 |

---

## 🚀 Quick Wins (< 1 hour each)

1. **Add sends intent parsing** - Extend existing mixer logic
2. **Create first knowledge file** - Start with Delay device
3. **Test Reverb device** - Use existing test plan template

---

See [STATUS.md](../STATUS.md) for overall project status.
