# Testing Guide for FadeBender NLP System

## Quick Start

**Run all pan tests (recommended after any pan-related changes):**
```bash
bash scripts/run_all_pan_tests.sh
```

**Run comprehensive NLP tests:**
```bash
python3 scripts/test_nlp_comprehensive.py
python3 scripts/test_nlp_get_comprehensive.py
python3 scripts/test_webui_validation.py

```

---

## Test Categories

### 1. Pan Command Tests (NEW!)

Tests the preprocessing normalization (30L → -30, 30R → 30) and pan parsers.

#### Individual Tests:
```bash
# Master pan (8 test cases)
bash scripts/test_master_pan.sh

# Return pan (10 test cases)
bash scripts/test_return_pan.sh

# Track pan (8 test cases)
bash scripts/test_track_pan.sh
```

#### Combined Runner:
```bash
bash scripts/run_all_pan_tests.sh
```

**What it tests:**
- Compact format: "pan master to 30L" → -30
- Compact format: "pan return A to 25R" → 25
- Word-based: "pan track 1 to 30 left" → -30
- Numeric: "pan master to -20" → -20
- Multiple targets: Master, Returns (A-D), Tracks (1-9)

**When to run:**
- After changes to preprocessing (`typo_corrector.py`)
- After changes to pan parsers (`mixer_parser.py`)
- Before committing pan-related features

---

### 2. Comprehensive NLP Tests

Tests all NLP command types (mixer, device, get operations).

#### Set/Relative Operations:
```bash
# All mixer + device operations
python3 scripts/test_nlp_comprehensive.py
```

**What it tests:**
- Track volume/pan/solo/mute/sends
- Return volume/pan/solo/sends
- Master volume/cue/pan
- Device parameters (reverb, delay, eq, etc.)
- Typo correction
- Relative changes ("increase by X")

#### Get Operations:
```bash
# Query operations (what is X?)
python3 scripts/test_nlp_get_comprehensive.py
```

**What it tests:**
- "what is track 1 volume?"
- "show me return A reverb decay"
- "get all track 1 send levels"
- Wildcard queries ("all parameters")

**When to run:**
- Before every commit (comprehensive validation)
- After parser changes
- After prompt template changes

---

### 3. Performance Tests

#### Device Relative Changes Timing:
```bash
bash scripts/test_device_relative_timing.sh
```

**What it tests:**
- Latency of device relative changes
- Regex vs LLM fallback performance
- Expected: <10ms for regex hits, 300-400ms for LLM

#### Typo Learning Timing:
```bash
bash scripts/test_typo_learning_timing.sh
```

**What it tests:**
- Self-learning typo correction system
- Firestore cache performance
- First hit (LLM) vs subsequent hits (cached)

**When to run:**
- After optimization changes
- When investigating performance issues
- Before/after regex parser additions

---

### 4. Backend Integration Tests

#### Device Parameter Backend:
```bash
python3 scripts/test_device_relative_backend.py
```

**What it tests:**
- Device parameter reads from Ableton
- Relative change calculations
- Parameter range validation

#### Preset Cache:
```bash
python3 scripts/test_preset_cache.py
```

**What it tests:**
- Firestore preset loading
- Device type filtering (amp/delay/reverb)
- Alias generation from presets

**When to run:**
- After Ableton API changes
- When debugging device parameter issues
- After preset cache modifications

---

### 5. Web UI Validation

```bash
python3 scripts/test_webui_validation.py
```

**What it tests:**
- Chat endpoint responses
- Intent parsing via HTTP API
- Error handling
- Response formatting

**When to run:**
- Before deploying to production
- After server endpoint changes
- When debugging UI issues

---

## Recommended Testing Workflow

### Before Every Commit:
```bash
# 1. Run pan tests (if you changed pan-related code)
bash scripts/run_all_pan_tests.sh

# 2. Run comprehensive NLP tests
python3 scripts/test_nlp_comprehensive.py

# 3. Run get operations tests
python3 scripts/test_nlp_get_comprehensive.py
```

### After Parser Changes:
```bash
# Verify regex performance is maintained
bash scripts/test_device_relative_timing.sh
```

### After Prompt Changes:
```bash
# Ensure LLM fallback still works
python3 scripts/test_nlp_comprehensive.py
```

### Before Production Deploy:
```bash
# All validation tests
bash scripts/run_all_pan_tests.sh
python3 scripts/test_nlp_comprehensive.py
python3 scripts/test_nlp_get_comprehensive.py
python3 scripts/test_webui_validation.py
```

---

## Test Output Format

All tests follow a consistent format:

```
Testing: 'command text'
  ✓ PASS - Description of success
    "value": expected_value

  ✗ FAIL - Description of failure
    Result: {actual output}

======================================
SUMMARY: X passed, Y failed
======================================
```

**Exit codes:**
- `0` = All tests passed
- `1` = Some tests failed

---

## Adding New Tests

### For new mixer operations:
1. Add test cases to relevant script (`test_master_pan.sh`, etc.)
2. Update `run_all_pan_tests.sh` if needed

### For new device operations:
1. Add test cases to `test_nlp_comprehensive.py`
2. Consider adding to `test_device_relative_timing.sh` for performance

### For new query operations:
1. Add test cases to `test_nlp_get_comprehensive.py`

---

## Troubleshooting

**Tests fail with "Connection refused":**
- Ensure server is running: `python3 server/app.py`
- Check server port: default is 8722

**Tests timeout:**
- Check if Ableton Live is running
- Verify Live Control Surface script is loaded
- Check firewall/network settings

**Performance tests show slow times:**
- Verify regex patterns are correct
- Check typo cache is populated
- Review prompt template length (shorter = faster)

---

## CI/CD Integration

**Quick validation (fast):**
```bash
bash scripts/run_all_pan_tests.sh && \
python3 scripts/test_nlp_comprehensive.py
```

**Full validation (comprehensive):**
```bash
bash scripts/run_all_pan_tests.sh && \
python3 scripts/test_nlp_comprehensive.py && \
python3 scripts/test_nlp_get_comprehensive.py && \
python3 scripts/test_webui_validation.py
```

---

## Test Coverage Summary

| Category | Tests | Coverage |
|----------|-------|----------|
| **Pan Commands** | 26 | Master/Return/Track pan (all formats) |
| **Mixer Operations** | ~100 | Volume/pan/solo/mute/sends |
| **Device Operations** | ~50 | Reverb/delay/eq/amp parameters |
| **Get Operations** | ~30 | Query/read operations |
| **Performance** | 10 | Latency benchmarks |
| **Backend** | 20 | Ableton integration |
| **Web UI** | 15 | HTTP API endpoints |

**Total: ~250+ automated tests**
