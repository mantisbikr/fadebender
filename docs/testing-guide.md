# Testing Guide for FadeBender NLP System

## Quick Start

**Run all pan tests (recommended after any pan-related changes):**
```bash
bash scripts/run_all_pan_tests.sh
```

**Run comprehensive NLP tests:**
```bash
python3 scripts/test_nlp_comprehensive.py

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

---

## Refactoring Validation Testing

This section covers testing for architectural refactoring work. Use this when making structural changes to the codebase.

### Overview: When to Run Each Test

| Test Type | Before Refactor | During Work | After Phase | Before Commit |
|-----------|----------------|-------------|-------------|---------------|
| **Functional Tests** | ✓ Baseline | - | ✓ Regression | ✓ Always |
| **API Contracts** | ✓ Snapshot | - | ✓ Verify | - |
| **Performance** | ✓ Baseline | - | ✓ Compare | - |
| **Health/Ready** | - | - | ✓ Verify | ✓ If changed |
| **Error DTOs** | - | - | ✓ Verify | ✓ If changed |
| **Import/Startup** | ✓ Baseline | ✓ Frequent | ✓ Verify | ✓ Always |

---

### BEFORE Starting Refactoring (One Time Setup)

**Run once before beginning any refactoring work.**

#### 1. Establish Functional Test Baseline

```bash
# Run all functional tests and save baseline
bash scripts/run_all_pan_tests.sh > baselines/tests_baseline.txt
python3 scripts/test_nlp_comprehensive.py >> baselines/tests_baseline.txt
python3 scripts/test_nlp_get_comprehensive.py >> baselines/tests_baseline.txt
python3 scripts/test_webui_validation.py >> baselines/tests_baseline.txt

# Check exit codes - all should be 0
echo "All tests baseline: $?"
```

**Document:** Number of passing tests, any known failures

#### 2. Capture API Contract Baseline

```bash
# Snapshot OpenAPI spec
curl -s http://localhost:8722/openapi.json | python3 -m json.tool > baselines/openapi_baseline.json

# Document all endpoint URLs and methods
echo "=== API Endpoints Baseline ===" > baselines/api_endpoints_baseline.txt
curl -s http://localhost:8722/openapi.json | \
  python3 -c "import sys,json; paths=json.load(sys.stdin)['paths']; \
  [print(f'{m.upper()} {p}') for p,ms in paths.items() for m in ms.keys()]" \
  >> baselines/api_endpoints_baseline.txt
```

**Why:** Ensures refactoring doesn't break API contracts

#### 3. Measure Performance Baseline

```bash
# Create baselines directory
mkdir -p baselines

# Capture performance metrics
echo "=== Performance Baseline ===" > baselines/performance_baseline.txt
date >> baselines/performance_baseline.txt

# Device timing
bash scripts/test_device_relative_timing.sh >> baselines/performance_baseline.txt

# Typo learning timing
bash scripts/test_typo_learning_timing.sh >> baselines/performance_baseline.txt

# Note p50/p95/p99 values for key operations
```

**Why:** Track that refactoring doesn't degrade performance

#### 4. Test Import and Startup Time

```bash
# Test clean import
echo "Testing import..." > baselines/startup_baseline.txt
python3 -c "from server.app import app; print('✓ Import successful')" 2>&1 >> baselines/startup_baseline.txt

# Measure startup time
echo "Measuring startup..." >> baselines/startup_baseline.txt
time python3 -c "from server.app import app; print('Done')" 2>&1 >> baselines/startup_baseline.txt
```

**Why:** Catch circular imports or startup regressions early

#### 5. Document Current State

```bash
# Create refactoring log
cat > REFACTORING_LOG.md <<EOF
# Refactoring Progress Log

## Baseline Established: $(date)

### Test Results Baseline
- Pan tests: [PASS/FAIL count from baselines/tests_baseline.txt]
- NLP comprehensive: [PASS/FAIL count]
- Get operations: [PASS/FAIL count]
- Web UI validation: [PASS/FAIL count]

### Known Issues
- [Document any pre-existing test failures]

### Performance Baselines
- Device relative changes (regex): [X ms]
- Device relative changes (LLM): [X ms]
- Typo correction (cached): [X ms]

### Acceptable Thresholds
- Test regression: 0 new failures
- Performance degradation: <10%
- Startup time: <5 seconds
- API contract changes: None (unless documented)

## Phase Progress
EOF
```

**Baseline setup complete!** Proceed to Phase 0a.

---

### DURING Phase 0a: Foundation & Quick Wins

**Run frequently as you make changes.**

#### While Working: Quick Validation

```bash
# After each small change, verify import still works
python3 -c "from server.app import app; print('✓ OK')"

# Exit code 0 = good, proceed
# Exit code 1 = fix import error before continuing
```

**When:** After modifying imports, moving files, or changing module structure

#### After Implementing Health Endpoints

```bash
# Test health endpoint
curl -s http://localhost:8722/health
# Expected: {"status": "ok"} or similar

# Test readiness endpoint (with Ableton Live running)
curl -s http://localhost:8722/ready
# Expected: 200 OK when connected

# Test readiness endpoint (with Ableton Live stopped)
# Stop Live, then:
curl -s http://localhost:8722/ready
# Expected: 503 Service Unavailable

# Restart Live for remaining tests
```

**When:** Immediately after implementing `/health` and `/ready` endpoints

#### After Implementing Error DTO Middleware

```bash
# Test error responses have standard format
# Trigger a known error (e.g., invalid track)
curl -s http://localhost:8722/op/mixer \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"target":"track", "track_num":999, "param":"volume", "value":0.5}' \
  | python3 -m json.tool

# Expected format:
# {
#   "ok": false,
#   "code": "track_not_found" (or similar),
#   "message": "...",
#   "detail": {...}
# }

# Test a few different error cases
# - Invalid intent
# - Missing parameters
# - Out of range values
```

**When:** After adding error middleware

#### After Implementing Feature Flags

```bash
# Test feature flag toggles behavior
# Example: if you added USE_NEW_VALUE_REGISTRY flag

# With flag OFF (or default)
# [Run test that uses old behavior]

# With flag ON
export USE_NEW_VALUE_REGISTRY=true
# [Run same test, verify new behavior]
unset USE_NEW_VALUE_REGISTRY

# Verify no errors in either mode
```

**When:** After adding each feature flag

---

### END of Phase 0a: Complete Validation

**Run this full validation before marking Phase 0a complete.**

#### 1. All Functional Tests Pass

```bash
# Full regression test
bash scripts/run_all_pan_tests.sh
python3 scripts/test_nlp_comprehensive.py
python3 scripts/test_nlp_get_comprehensive.py
python3 scripts/test_webui_validation.py

# All must pass (exit code 0)
# If any fail, debug before proceeding
```

**Must:** Zero new test failures compared to baseline

#### 2. API Contracts Unchanged

```bash
# Compare OpenAPI spec
curl -s http://localhost:8722/openapi.json | python3 -m json.tool > openapi_current.json
diff baselines/openapi_baseline.json openapi_current.json

# Should show: No differences (or only documented additions)
```

**Must:** No breaking changes to API

#### 3. Performance Acceptable

```bash
# Run performance tests
bash scripts/test_device_relative_timing.sh > perf_phase0a.txt
bash scripts/test_typo_learning_timing.sh >> perf_phase0a.txt

# Compare with baselines/performance_baseline.txt
# Verify <10% regression
```

**Must:** Performance within 10% of baseline

#### 4. Health Checks Working

```bash
# Health endpoint
curl -f http://localhost:8722/health || echo "FAIL: Health check"

# Ready endpoint (Live running)
curl -f http://localhost:8722/ready || echo "FAIL: Ready check"
```

**Must:** Both endpoints return 200 OK

#### 5. Import/Startup Clean

```bash
# Clean import
python3 -c "from server.app import app; print('✓ OK')"

# Startup time
time python3 -c "from server.app import app"
# Should complete in <5 seconds
```

**Must:** No import errors, reasonable startup time

#### 6. Update Refactoring Log

```bash
# Add to REFACTORING_LOG.md
cat >> REFACTORING_LOG.md <<EOF

### Phase 0a Complete: $(date)

**Changes Made:**
- Health and readiness endpoints added
- Error DTO middleware implemented
- Feature flags system added
- [Other changes...]

**Validation Results:**
- Functional tests: ✓ All passing
- API contracts: ✓ No breaking changes
- Performance: ✓ Within 10% baseline
- Health checks: ✓ Working
- Import/startup: ✓ Clean

**Ready for Phase 1**
EOF
```

**Phase 0a complete!** Proceed to Phase 1.

---

### DURING Phase 1: App/Config Structure

**Run frequently as you refactor app.py and config.**

#### While Working: Import Validation

```bash
# After moving code or changing imports
python3 -c "from server.app import app; print('✓ OK')"
python3 -c "from server.bootstrap import *; print('✓ OK')"
python3 -c "from server.config.helpers import *; print('✓ OK')"
python3 -c "from server.models.requests import *; print('✓ OK')"

# All should succeed
```

**When:** After each major file restructuring

#### After Creating Shared Models

```bash
# Test that routers can import shared models
python3 -c "from server.models.requests import VolumeDbBody; print('✓ OK')"
python3 -c "from server.api.ops import *; print('✓ OK')"

# Grep for duplicate model definitions (should find none)
grep -r "class VolumeDbBody" server/
# Should only appear in server/models/requests.py

grep -r "class IntentParseBody" server/
# Should only appear in server/models/requests.py
```

**When:** After consolidating request models

#### After ValueRegistry Façade

```bash
# Test dependency injection works
# Start server and test an operation that uses ValueRegistry
curl -s http://localhost:8722/op/mixer \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"target":"track", "track_num":1, "param":"volume", "value":0.5}' \
  | python3 -m json.tool

# Should work normally
```

**When:** After implementing ValueRegistry façade and DI

#### After Events.publish() Helper

```bash
# Test that events still publish
# Make a change (e.g., volume) and watch browser/client for SSE updates
# Or check server logs for event publishing

# Should see normal event flow
```

**When:** After implementing Events.publish() helper

---

### END of Phase 1: Complete Validation

**Run before marking Phase 1 complete.**

#### 1. All Functional Tests Pass

```bash
bash scripts/run_all_pan_tests.sh
python3 scripts/test_nlp_comprehensive.py
python3 scripts/test_nlp_get_comprehensive.py
python3 scripts/test_webui_validation.py

# All must pass
```

**Must:** Zero regression

#### 2. API Contracts Unchanged

```bash
curl -s http://localhost:8722/openapi.json | python3 -m json.tool > openapi_phase1.json
diff baselines/openapi_baseline.json openapi_phase1.json

# No breaking changes
```

**Must:** API stability maintained

#### 3. Performance Check

```bash
bash scripts/test_device_relative_timing.sh > perf_phase1.txt

# Compare with baseline
# Should be within 10%
```

**Must:** No performance regression

#### 4. Code Quality Checks

```bash
# No duplicate model definitions
echo "Checking for duplicates..."
grep -r "class VolumeDbBody" server/ | wc -l
# Should be 1

grep -r "class IntentParseBody" server/ | wc -l
# Should be 1

# No direct ValueRegistry access in routers (should use façade)
grep -r "get_value_registry()" server/api/*.py | wc -l
# Should be 0 (or minimal)

# app.py is smaller
wc -l server/app.py
# Should be <300 lines (down from ~1594)
```

**Must:** Code cleanup goals achieved

#### 5. Update Log

```bash
cat >> REFACTORING_LOG.md <<EOF

### Phase 1 Complete: $(date)

**Changes Made:**
- App bootstrap split into separate files
- Shared models consolidated
- ValueRegistry façade + DI implemented
- Events.publish() helper added
- Error handling middleware enhanced

**Validation Results:**
- Functional tests: ✓ All passing
- API contracts: ✓ Unchanged
- Performance: ✓ Within baseline
- Code quality: ✓ Goals achieved
- app.py size: [X lines] (down from 1594)

**Ready for Phase 2**
EOF
```

**Phase 1 complete!** Proceed to Phase 2.

---

### DURING Phase 2: Router Decomposition

**Run as you split large routers.**

#### While Working: Router Import Checks

```bash
# After splitting a router, test imports
python3 -c "from server.api.overview_status import *; print('✓ OK')"
python3 -c "from server.api.overview_devices import *; print('✓ OK')"
python3 -c "from server.api.overview_cache import *; print('✓ OK')"

# Test app still mounts all routers
python3 -c "from server.app import app; print('✓ OK')"
```

**When:** After each router split

#### After Extracting Services

```bash
# Test service imports
python3 -c "from server.services.mixer_readers import *; print('✓ OK')"
python3 -c "from server.services.device_readers import *; print('✓ OK')"

# Test related endpoints still work
curl -s http://localhost:8722/overview | python3 -m json.tool
# Should return normal data
```

**When:** After extracting service modules

---

### END of Phase 2: Complete Validation

**Run before marking Phase 2 complete.**

#### 1. All Functional Tests Pass

```bash
bash scripts/run_all_pan_tests.sh
python3 scripts/test_nlp_comprehensive.py
python3 scripts/test_nlp_get_comprehensive.py
python3 scripts/test_webui_validation.py

# All must pass
```

**Must:** Zero regression

#### 2. API Contracts Unchanged

```bash
curl -s http://localhost:8722/openapi.json | python3 -m json.tool > openapi_phase2.json
diff baselines/openapi_baseline.json openapi_phase2.json
```

**Must:** API stability

#### 3. Performance Check

```bash
bash scripts/test_device_relative_timing.sh > perf_phase2.txt
```

**Must:** Within 10% baseline

#### 4. Router Size Checks

```bash
# Check router file sizes
echo "Router sizes:"
wc -l server/api/overview*.py
wc -l server/api/device_mapping.py
wc -l server/api/returns.py
wc -l server/api/tracks.py

# All should be <400 lines each
```

**Must:** Code cleanup goals achieved

#### 5. Update Log

```bash
cat >> REFACTORING_LOG.md <<EOF

### Phase 2 Complete: $(date)

**Changes Made:**
- Split overview.py into 3 routers
- Extracted device_mapping_io service
- Created mixer_readers and device_readers services
- Consolidated cap_utils

**Validation Results:**
- Functional tests: ✓ All passing
- API contracts: ✓ Unchanged
- Performance: ✓ Within baseline
- Router sizes: ✓ All <400 lines

**Ready for Phase 3**
EOF
```

**Phase 2 complete!** Continue with remaining phases using same pattern.

---

### GENERAL: Before Every Commit

**Quick validation before committing any refactoring work.**

```bash
# 1. Import check (fast)
python3 -c "from server.app import app; print('✓ OK')" || exit 1

# 2. Core functional tests (2-3 minutes)
bash scripts/run_all_pan_tests.sh || exit 1
python3 scripts/test_nlp_comprehensive.py || exit 1

# 3. If all pass, commit is safe
git add .
git commit -m "refactor: [your change description]"
```

---

### When Tests Fail During Refactoring

#### If Import Fails

```bash
# Check for circular imports
python3 -c "from server.app import app"

# Common issues:
# - Moved file but didn't update imports
# - Circular dependency created
# - Missing __init__.py
```

**Fix:** Review recent file moves and import changes

#### If Functional Tests Fail

```bash
# Identify which test failed
# Run tests individually to isolate

# Common issues:
# - Changed function signature
# - Broke dependency injection
# - Registry or event publishing broken
```

**Fix:** Review code changes related to failed test area

#### If API Contract Changed

```bash
# Review OpenAPI diff
diff baselines/openapi_baseline.json openapi_current.json

# If intentional change:
# - Document in REFACTORING_LOG.md
# - Update baseline: cp openapi_current.json baselines/openapi_baseline.json

# If unintentional:
# - Revert breaking change
```

**Fix:** Ensure backward compatibility

#### If Performance Regressed

```bash
# Identify slow operation
# Run timing tests with verbose output

# Common issues:
# - Added unnecessary database call
# - Broke caching
# - N+1 query problem
```

**Fix:** Profile and optimize hot path

---

### Test Scripts To Create

**These scripts don't exist yet - create them as part of Phase 0a:**

#### `scripts/run_all_tests.sh`

```bash
#!/bin/bash
# Master test runner for baseline and validation

set -e

echo "=== Running All Tests ==="
echo ""

echo "1. Pan Commands..."
bash scripts/run_all_pan_tests.sh

echo "2. NLP Comprehensive..."
python3 scripts/test_nlp_comprehensive.py

echo "3. Get Operations..."
python3 scripts/test_nlp_get_comprehensive.py

echo "4. Web UI Validation..."
python3 scripts/test_webui_validation.py

echo ""
echo "=== All Tests Complete ==="
```

#### `scripts/validate_refactor_phase.sh`

```bash
#!/bin/bash
# Validates refactoring phase completion

set -e

PHASE=$1

echo "=== Validating Phase: $PHASE ==="

echo "1. Functional tests..."
bash scripts/run_all_tests.sh || exit 1

echo "2. API contracts..."
curl -s http://localhost:8722/openapi.json > openapi_current.json
diff baselines/openapi_baseline.json openapi_current.json || {
  echo "WARNING: API contract changed"
  exit 1
}

echo "3. Performance..."
bash scripts/test_device_relative_timing.sh > perf_current.txt
# TODO: Add performance comparison logic

echo "4. Import/Startup..."
python3 -c "from server.app import app; print('OK')" || exit 1

echo ""
echo "=== Phase $PHASE Validated ==="
```

Create these scripts in Phase 0a.
