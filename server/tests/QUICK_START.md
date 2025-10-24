# Intents API Tests - Quick Start Guide

## TL;DR

```bash
cd /Users/sunils/ai-projects/fadebender/server
pytest tests/test_intents.py -v
```

**Result**: ✅ 39/39 tests passing in < 2 seconds

---

## What Gets Tested?

### Core Functionality
- ✅ Track/Return/Master mixer controls (volume, pan, mute, solo)
- ✅ Send level control (track → return, return → return)
- ✅ Device parameters (by index and by fuzzy name)
- ✅ Display-value conversions ("50 ms", "Low-pass")
- ✅ Auto-enable master toggles (smart dependencies)
- ✅ Dry-run mode (preview without executing)

### Quality Assurance
- ✅ All unit conversions (dB, percent, normalized)
- ✅ Error handling (missing fields, timeouts, not found)
- ✅ Edge cases (extreme values, hard panning)
- ✅ Clamping behavior (enabled/disabled)

---

## Running Tests

### All tests (default)
```bash
pytest tests/test_intents.py -v
```

### Specific categories
```bash
# Track operations only
pytest tests/test_intents.py -k "track" -v

# Device parameters only
pytest tests/test_intents.py -k "device" -v

# Display-value conversions
pytest tests/test_intents.py -k "display" -v

# Error handling
pytest tests/test_intents.py -k "error or missing or not_found" -v
```

### Single test
```bash
pytest tests/test_intents.py::test_track_volume_db -v
```

### With detailed output
```bash
pytest tests/test_intents.py -v -s
```

---

## Test Results Summary

| Category | Tests | Status |
|----------|-------|--------|
| Track Mixer | 7 | ✅ All Pass |
| Return Mixer | 3 | ✅ All Pass |
| Master Mixer | 2 | ✅ All Pass |
| Sends | 3 | ✅ All Pass |
| Device Params | 7 | ✅ All Pass |
| Display Values | 2 | ✅ All Pass |
| Auto-Enable | 2 | ✅ All Pass |
| Dry-Run | 2 | ✅ All Pass |
| Error Handling | 5 | ✅ All Pass |
| Clamping | 2 | ✅ All Pass |
| Edge Cases | 3 | ✅ All Pass |
| Integration | 1 | ✅ All Pass |
| **TOTAL** | **39** | **✅ 100% Pass** |

---

## Key Test Examples

### Track Volume (dB)
```python
POST /intent/execute
{
  "domain": "track",
  "track_index": 1,
  "field": "volume",
  "value": -6.0,
  "unit": "dB"
}
# Expected: -6dB converted per mixer mapping and applied via service ✅
```

### Device Parameter (by name)
```python
POST /intent/execute
{
  "domain": "device",
  "return_index": 0,
  "device_index": 0,
  "param_ref": "decay",  # Fuzzy match
  "value": 0.75
}
# Expected: Matches "Decay Time" parameter ✅
```

### Display-Value Conversion
```python
POST /intent/execute
{
  "domain": "device",
  "return_index": 0,
  "device_index": 0,
  "param_ref": "predelay",
  "display": "50 ms"
}
# Expected: "50 ms" → 0.5 via linear fit ✅
```

### Auto-Enable Master Toggle
```python
POST /intent/execute
{
  "domain": "device",
  "return_index": 0,
  "device_index": 0,
  "param_ref": "chorus amount",
  "value": 0.8
}
# Expected: Auto-enables "Chorus On" first ✅
```

---

## Test Files

| File | Purpose |
|------|---------|
| `test_intents.py` | Main test suite (39 tests) |
| `TEST_REPORT.md` | Detailed test report with analysis |
| `TEST_PLAN.md` | Comprehensive test plan and scenarios |
| `README.md` | Test documentation and coverage goals |
| `run_tests.sh` | Convenient test runner script |

---

## No Live Connection Required

All tests use **mocking** - no Ableton Live connection needed!

- Fast execution (< 2 seconds)
- Reliable (no external dependencies)
- Runnable in CI/CD environments

---

## Dependencies

```bash
# Already installed in your environment
pytest==8.4.2
httpx  # For FastAPI TestClient
```

---

## CI/CD Integration

Add to `.github/workflows/test.yml`:

```yaml
name: Tests
on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  intents:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.10'
      - name: Install deps
        run: |
          python -m pip install --upgrade pip
          pip install -r server/requirements.txt || true
          pip install pytest pytest-cov httpx
      - name: Run Intent API Tests with coverage
        working-directory: server
        run: |
          pytest tests/test_intents.py -v --tb=short \
            --cov=server.api.intents \
            --cov=server.services.intents.mixer_service \
            --cov=server.services.intents.param_service \
            --cov=server.services.intents.routing_service \
            --cov-report=term-missing
```

---

## Quick Reference

### Test a specific intent type:
```bash
pytest tests/test_intents.py -k "volume" -v    # All volume tests
pytest tests/test_intents.py -k "pan" -v       # All pan tests
pytest tests/test_intents.py -k "send" -v      # All send tests
pytest tests/test_intents.py -k "param" -v     # All device param tests
```

### Test error conditions:
```bash
pytest tests/test_intents.py -k "error or missing or not_found" -v
```

### Test dry-run mode:
```bash
pytest tests/test_intents.py -k "dry_run" -v
```

---

## Understanding Test Output

### ✅ Success
```
tests/test_intents.py::test_track_volume_db PASSED [2%]
```
- Test passed
- All assertions validated
- Expected behavior confirmed

### ❌ Failure (example)
```
tests/test_intents.py::test_track_volume_db FAILED [2%]
AssertionError: assert 0.7 < 0.55
```
- Test failed
- Assertion not met
- Check expected vs actual values

---

## Common Issues

### Import Errors
```bash
# If you see ModuleNotFoundError
cd /Users/sunils/ai-projects/fadebender/server
export PYTHONPATH=/Users/sunils/ai-projects/fadebender/server:$PYTHONPATH
pytest tests/test_intents.py -v
```

### Pytest Not Found
```bash
pip install pytest httpx
```

---

## Next Steps

1. ✅ Tests are passing - you're good to go!
2. 📋 Add new tests when adding new features
3. 📋 Run tests before committing changes
4. 📋 Consider adding to CI/CD pipeline

---

## Questions?

- **What's tested?** See `TEST_PLAN.md`
- **Detailed results?** See `TEST_REPORT.md`
- **How to run?** See `README.md`
- **Coverage goals?** See `README.md`

**Happy testing!** 🎉
