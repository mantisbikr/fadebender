# Device Parameter Relative Change Optimization Plan

## Objective

Add regex-based parsers for device parameter relative changes to achieve **1-10ms latency** instead of **300-400ms LLM fallback**.

**Target Coverage:** 80% of device relative change commands handled by regex
**Expected Impact:** Instant feedback on common commands like "increase reverb decay by 20%"

---

## Phase 1: Core Relative Change Parsers

### 1.1 Return Device Param Relative

**Target commands:**
- "increase return A reverb decay by 20%"
- "decrease return A delay feedback by 10 percent"
- "increase return A reverb predelay by 5 ms"

**Implementation:**

```python
def parse_return_device_param_relative(q: str, query: str, error_msg: str, model_preference: str | None) -> Dict[str, Any] | None:
    """Parse: increase return A reverb decay by 20%

    Handles relative changes to device parameters on return tracks.
    Supports: increase/decrease verbs, numeric amounts, units (%, dB, ms, s, hz, etc.)
    """
    # Get verbs from config
    increase_verbs, decrease_verbs = get_relative_change_verbs()
    all_verbs = increase_verbs + decrease_verbs

    # Quick check for relative verb
    if not any(word in q for word in all_verbs):
        return None

    try:
        # Get device pattern
        dev_pat = _get_device_pattern()

        # Pattern: "increase return A reverb decay by 20 percent"
        # Captures: return_ref, device_name, (optional ordinal), parameter, amount, unit
        pattern = rf"\b(?:{'|'.join(all_verbs)})\s+return\s+([a-d])\s+({dev_pat})(?:\s+(\d+))?\s+(.+?)\s+by\s+(-?\d+(?:\.\d+)?)(?:\s*({UNITS_PAT}))?\b"

        m = re.search(pattern, q, re.IGNORECASE)
        if m:
            return_ref = m.group(1).upper()
            device_raw = m.group(2)
            device_ord = m.group(3)
            pname = m.group(4).strip()
            value = float(m.group(5))
            unit_raw = m.group(6)

            # Device name must be present
            if not device_raw:
                return None

            # Apply direction based on verb
            if any(word in q for word in decrease_verbs):
                value = -abs(value)
            else:
                value = abs(value)

            dev_norm = _normalize_device_name(device_raw)
            param_ref = _normalize_param_name(pname)
            unit_out = _normalize_unit(unit_raw) or "display"  # Default to display if no unit

            out = {
                'intent': 'relative_change',
                'targets': [{'track': f'Return {return_ref}', 'plugin': dev_norm, 'parameter': param_ref}],
                'operation': {'type': 'relative', 'value': value, 'unit': unit_out},
                'meta': {'utterance': query, 'fallback': True, 'error': error_msg, 'model_selected': _safe_model_name(model_preference)}
            }

            if device_ord:
                try:
                    out['targets'][0]['device_ordinal'] = int(device_ord)
                except Exception:
                    pass

            return out

    except Exception:
        pass

    return None
```

**Test cases:**
```python
# Should match
"increase return A reverb decay by 20%"
"decrease return A reverb decay by 20 percent"
"increase return A delay feedback by 10%"
"decrease return B reverb predelay by 5 ms"
"increase return A reverb 2 decay by 15%"  # With ordinal

# Should not match (fall through to next parser or LLM)
"increase return A volume by 3 dB"  # Mixer command, not device
"set return A reverb decay to 2 s"  # Absolute, not relative
```

### 1.2 Track Device Param Relative

**Target commands:**
- "increase track 1 reverb decay by 20%"
- "decrease track 2 delay feedback by 10%"

**Implementation:** Same pattern as 1.1, but with `track\s+(\d+)` instead of `return\s+([a-d])`

```python
def parse_track_device_param_relative(q: str, query: str, error_msg: str, model_preference: str | None) -> Dict[str, Any] | None:
    """Parse: increase track 1 reverb decay by 20%"""
    increase_verbs, decrease_verbs = get_relative_change_verbs()
    all_verbs = increase_verbs + decrease_verbs

    if not any(word in q for word in all_verbs):
        return None

    try:
        dev_pat = _get_device_pattern()

        # Pattern: "increase track 1 reverb decay by 20 percent"
        pattern = rf"\b(?:{'|'.join(all_verbs)})\s+track\s+(\d+)\s+({dev_pat})(?:\s+(\d+))?\s+(.+?)\s+by\s+(-?\d+(?:\.\d+)?)(?:\s*({UNITS_PAT}))?\b"

        m = re.search(pattern, q, re.IGNORECASE)
        if m:
            track_num = int(m.group(1))
            device_raw = m.group(2)
            device_ord = m.group(3)
            pname = m.group(4).strip()
            value = float(m.group(5))
            unit_raw = m.group(6)

            if not device_raw:
                return None

            if any(word in q for word in decrease_verbs):
                value = -abs(value)
            else:
                value = abs(value)

            dev_norm = _normalize_device_name(device_raw)
            param_ref = _normalize_param_name(pname)
            unit_out = _normalize_unit(unit_raw) or "display"

            out = {
                'intent': 'relative_change',
                'targets': [{'track': f'Track {track_num}', 'plugin': dev_norm, 'parameter': param_ref}],
                'operation': {'type': 'relative', 'value': value, 'unit': unit_out},
                'meta': {'utterance': query, 'fallback': True, 'error': error_msg, 'model_selected': _safe_model_name(model_preference)}
            }

            if device_ord:
                try:
                    out['targets'][0]['device_ordinal'] = int(device_ord)
                except Exception:
                    pass

            return out

    except Exception:
        pass

    return None
```

### 1.3 Device Ordinal Relative (Fallback)

**Target commands:**
- "increase return A device 1 dry wet by 20 percent"
- "decrease track 1 device 2 gain by 3 dB"

**Implementation:** For when device name is not recognized, use ordinal reference

```python
def parse_return_device_ordinal_relative(q: str, query: str, error_msg: str, model_preference: str | None) -> Dict[str, Any] | None:
    """Parse: increase return A device 1 decay by 20%"""
    increase_verbs, decrease_verbs = get_relative_change_verbs()
    all_verbs = increase_verbs + decrease_verbs

    if not any(word in q for word in all_verbs):
        return None

    try:
        # Pattern: "increase return A device 1 decay by 20 percent"
        pattern = rf"\b(?:{'|'.join(all_verbs)})\s+return\s+([a-d])\s+device\s+(\d+)\s+(.+?)\s+by\s+(-?\d+(?:\.\d+)?)(?:\s*({UNITS_PAT}))?\b"

        m = re.search(pattern, q, re.IGNORECASE)
        if m:
            return_ref = m.group(1).upper()
            device_index = int(m.group(2)) - 1  # Convert to 0-indexed
            pname = m.group(3).strip()
            value = float(m.group(4))
            unit_raw = m.group(5)

            if any(word in q for word in decrease_verbs):
                value = -abs(value)
            else:
                value = abs(value)

            param_ref = _normalize_param_name(pname)
            unit_out = _normalize_unit(unit_raw) or "display"

            return {
                'intent': 'relative_change',
                'targets': [{'track': f'Return {return_ref}', 'plugin': None, 'parameter': param_ref, 'device_index': device_index}],
                'operation': {'type': 'relative', 'value': value, 'unit': unit_out},
                'meta': {'utterance': query, 'fallback': True, 'error': error_msg, 'model_selected': _safe_model_name(model_preference)}
            }

    except Exception:
        pass

    return None
```

**Corresponding track version:**
```python
def parse_track_device_ordinal_relative(q: str, query: str, error_msg: str, model_preference: str | None) -> Dict[str, Any] | None:
    """Parse: increase track 1 device 2 gain by 3 dB"""
    # Same as above but with track\s+(\d+) pattern
    ...
```

---

## Phase 2: Integration and Testing

### 2.1 Add to DEVICE_PARSERS List

**File:** `nlp-service/parsers/device_parser.py`

**Current order:**
```python
DEVICE_PARSERS = [
    parse_track_device_param,           # Absolute
    parse_return_device_param,          # Absolute
    parse_return_device_label,          # Label selection
    parse_track_device_label,           # Label selection
    parse_return_device_ordinal,        # Ordinal absolute
    parse_track_device_ordinal,         # Ordinal absolute
    parse_return_device_label_arbitrary,    # JIT resolution
    parse_return_device_numeric_arbitrary,  # JIT resolution
    parse_track_device_numeric_arbitrary,   # JIT resolution
]
```

**New order (add relative parsers BEFORE absolute parsers):**
```python
DEVICE_PARSERS = [
    # Relative changes (check these FIRST - more specific patterns)
    parse_return_device_param_relative,      # NEW: "increase return A reverb decay by 20%"
    parse_track_device_param_relative,       # NEW: "increase track 1 reverb decay by 20%"
    parse_return_device_ordinal_relative,    # NEW: "increase return A device 1 decay by 20%"
    parse_track_device_ordinal_relative,     # NEW: "increase track 1 device 2 gain by 3 dB"

    # Absolute operations
    parse_track_device_param,
    parse_return_device_param,
    parse_return_device_label,
    parse_track_device_label,
    parse_return_device_ordinal,
    parse_track_device_ordinal,

    # JIT resolution fallbacks
    parse_return_device_label_arbitrary,
    parse_return_device_numeric_arbitrary,
    parse_track_device_numeric_arbitrary,
]
```

**Rationale:** Check relative patterns first because they're more specific (contain "by" keyword).

### 2.2 Create Comprehensive Test Suite

**File:** `scripts/test_device_relative_regex.py`

```python
#!/usr/bin/env python3
"""
Test regex parsers for device parameter relative changes.

Validates that common device relative change commands are handled by regex
instead of falling back to LLM (300-400ms → 1-10ms).
"""

import sys
import time
import os

# Add nlp-service to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'nlp-service'))

from execution.regex_executor import try_regex_parse

# ANSI colors
GREEN = "\\033[92m"
RED = "\\033[91m"
RESET = "\\033[0m"

# Test cases: (query, should_match_regex)
TEST_CASES = [
    # Return device param relative
    ("increase return A reverb decay by 20%", True),
    ("decrease return A reverb decay by 20 percent", True),
    ("increase return A delay feedback by 10%", True),
    ("decrease return B reverb predelay by 5 ms", True),
    ("increase return A reverb 2 decay by 15%", True),  # With ordinal

    # Track device param relative
    ("increase track 1 reverb decay by 20%", True),
    ("decrease track 2 delay feedback by 10%", True),
    ("increase track 1 reverb predelay by 5 ms", True),

    # Device ordinal relative
    ("increase return A device 1 dry wet by 20 percent", True),
    ("decrease track 1 device 2 gain by 3 dB", True),

    # Should NOT match (absolute commands - use different parser)
    ("set return A reverb decay to 2 s", True),  # Absolute - different parser
    ("set track 1 delay feedback to 50%", True),  # Absolute - different parser

    # Should NOT match (mixer commands - use mixer parser)
    ("increase return A volume by 3 dB", True),  # Mixer command
    ("decrease track 1 volume by 2 dB", True),  # Mixer command
]

def test_regex_coverage():
    """Test that device relative commands are handled by regex."""
    print("=" * 80)
    print("Device Relative Change Regex Parser Tests")
    print("=" * 80)
    print()

    passed = 0
    failed = 0

    for query, should_match in TEST_CASES:
        start = time.perf_counter()
        result, suspected_typos = try_regex_parse(query, "", "gemini-2.5-flash")
        latency_ms = (time.perf_counter() - start) * 1000

        matched = result is not None

        if matched == should_match:
            status = f"{GREEN}✓ PASS{RESET}"
            passed += 1
        else:
            status = f"{RED}✗ FAIL{RESET}"
            failed += 1

        print(f"{status} [{latency_ms:6.2f}ms] {query}")

        if matched and result:
            intent = result.get('intent')
            pipeline = result.get('meta', {}).get('pipeline', 'unknown')
            print(f"          → Intent: {intent}, Pipeline: {pipeline}")
        elif not matched and should_match:
            print(f"          → Expected regex match but got None (suspected typos: {suspected_typos})")

    print()
    print("=" * 80)
    print(f"SUMMARY: {passed} passed, {failed} failed out of {len(TEST_CASES)} tests")
    print("=" * 80)

    return failed == 0

if __name__ == "__main__":
    success = test_regex_coverage()
    sys.exit(0 if success else 1)
```

### 2.3 Benchmark Performance Impact

**Extend:** `scripts/benchmark_nlp_modes.py`

Add device relative change test queries:

```python
TEST_QUERIES = [
    # ... existing mixer queries ...

    # Device relative changes (NEW - should be fast with regex)
    "increase return A reverb decay by 20%",
    "decrease return A delay feedback by 10%",
    "increase return A reverb predelay by 5 ms",
    "increase track 1 reverb decay by 15%",
    "decrease track 2 delay feedback by 20%",
    "increase return A device 1 dry wet by 20 percent",
]
```

**Expected results:**
- **Before:** Device relative avg latency = 350ms (all LLM)
- **After:** Device relative avg latency = 3ms (regex)
- **Improvement:** 117x faster

---

## Phase 3: Edge Cases and Enhancements

### 3.1 Handle Implicit Units

**Problem:** User says "increase decay by 20" without specifying unit

**Solution:** Default to "display" unit, let `intent_mapper.py` determine proper unit based on parameter metadata

```python
# Already handled in Phase 1:
unit_out = _normalize_unit(unit_raw) or "display"  # Default to display if no unit
```

### 3.2 Handle Negative Deltas

**Problem:** User says "increase decay by -20%" (confusing but valid)

**Solution:** Normalize direction based on verb, ignore sign in query

```python
# Apply direction based on verb (ignore sign in query)
if any(word in q for word in decrease_verbs):
    value = -abs(value)  # Force negative
else:
    value = abs(value)   # Force positive
```

### 3.3 Handle Alternative Phrasing

**Target commands:**
- "add 20% to return A reverb decay"
- "subtract 10% from delay feedback"

**Solution:** Add alternative patterns for "add X to" and "subtract X from"

```python
def parse_return_device_param_relative_alt(q: str, query: str, error_msg: str, model_preference: str | None) -> Dict[str, Any] | None:
    """Parse: add 20% to return A reverb decay"""
    try:
        dev_pat = _get_device_pattern()

        # Pattern: "add 20 percent to return A reverb decay"
        add_pattern = rf"\badd\s+(-?\d+(?:\.\d+)?)(?:\s*({UNITS_PAT}))?\s+to\s+return\s+([a-d])\s+({dev_pat})(?:\s+(\d+))?\s+(.+)\b"

        m = re.search(add_pattern, q, re.IGNORECASE)
        if m:
            value = float(m.group(1))  # Positive for add
            unit_raw = m.group(2)
            return_ref = m.group(3).upper()
            device_raw = m.group(4)
            device_ord = m.group(5)
            pname = m.group(6).strip()

            # ... build intent (same as above)

        # Pattern: "subtract 10 percent from return A reverb decay"
        sub_pattern = rf"\bsubtract\s+(-?\d+(?:\.\d+)?)(?:\s*({UNITS_PAT}))?\s+from\s+return\s+([a-d])\s+({dev_pat})(?:\s+(\d+))?\s+(.+)\b"

        m = re.search(sub_pattern, q, re.IGNORECASE)
        if m:
            value = -float(m.group(1))  # Negative for subtract
            # ... build intent

    except Exception:
        pass

    return None
```

**Add to DEVICE_PARSERS after primary relative parsers.**

---

## Phase 4: Documentation and Rollout

### 4.1 Update Documentation

**Files to update:**
1. `docs/nlp-performance-optimization.md` - Update coverage stats
2. `nlp-service/parsers/device_parser.py` - Add docstrings
3. `README.md` - Add note about regex-first optimization

### 4.2 Monitoring and Metrics

**Add telemetry to track:**
- Regex hit rate for device relative commands
- Average latency for device relative commands
- LLM fallback rate

**Implementation:**

```python
# In regex_executor.py
def try_regex_parse(query: str, error_msg: str, model_preference: str | None):
    # ... existing code ...

    result = parse_device_command(q, query, error_msg, model_preference)
    if result:
        # Track successful regex hit
        if result.get('intent') == 'relative_change':
            print(f"[REGEX HIT] Device relative: {query} (intent: {result['intent']})")
        return result, []

    # Track regex miss
    print(f"[REGEX MISS] Query fell through to LLM: {query}")
    suspected_typos = _extract_suspected_typos(query)
    return None, suspected_typos
```

### 4.3 Gradual Rollout

**Option 1: Feature flag**
```python
# In app_config.json
"features": {
    "device_relative_regex": true  # Enable device relative regex parsers
}
```

**Option 2: A/B test**
- 50% of users: Use device relative regex parsers
- 50% of users: Fall back to LLM
- Compare latency, accuracy, user satisfaction

---

## Expected Outcomes

### Performance Improvements

| Command Type | Before (LLM) | After (Regex) | Improvement |
|--------------|--------------|---------------|-------------|
| Device relative (return) | 350ms | 3ms | **117x faster** |
| Device relative (track) | 350ms | 3ms | **117x faster** |
| Device ordinal relative | 350ms | 3ms | **117x faster** |

### Coverage Improvements

| Category | Before | After | Change |
|----------|--------|-------|--------|
| Mixer absolute | 100% | 100% | - |
| Mixer relative | 100% | 100% | - |
| Device absolute | 90% | 90% | - |
| Device relative | **0%** | **80%** | **+80pp** |

### User Experience

**Typical mixing workflow:**
- User adjusts reverb decay 10 times during session
- Before: 10 × 350ms = 3.5s total waiting
- After: 10 × 3ms = 30ms total waiting
- **Savings:** 3.47s (99% faster)

**Perceived responsiveness:**
- Sub-10ms feels instant to humans
- 300ms+ feels sluggish
- Result: App feels **dramatically more responsive**

---

## Implementation Checklist

- [ ] Phase 1.1: Implement `parse_return_device_param_relative()`
- [ ] Phase 1.2: Implement `parse_track_device_param_relative()`
- [ ] Phase 1.3: Implement ordinal relative parsers
- [ ] Phase 2.1: Add to `DEVICE_PARSERS` list in correct order
- [ ] Phase 2.2: Create test suite `test_device_relative_regex.py`
- [ ] Phase 2.3: Run benchmarks before/after
- [ ] Phase 3.1: Test edge cases (implicit units, negative deltas)
- [ ] Phase 3.2: Add alternative phrasing support
- [ ] Phase 4.1: Update documentation
- [ ] Phase 4.2: Add monitoring/telemetry
- [ ] Phase 4.3: Roll out to users

---

## Risks and Mitigations

### Risk 1: False Positives

**Problem:** Regex pattern too permissive, matches unintended commands

**Mitigation:**
- Use strict word boundaries `\b`
- Require specific keywords ("increase", "decrease", "by")
- Test extensively with edge cases
- Fall back to LLM on ambiguous matches

### Risk 2: Parameter Name Variations

**Problem:** User says "dry/wet" but regex expects "dry wet"

**Mitigation:**
- Already handled by `_normalize_param_name()`
- Typo correction handles common variations
- LLM fallback catches rare variations

### Risk 3: Regex Maintenance Burden

**Problem:** Adding new patterns increases maintenance complexity

**Mitigation:**
- Follow mixer parser pattern (proven to work)
- Use config-driven verbs (easy to extend)
- Comprehensive test coverage catches regressions
- Document patterns clearly with examples

---

## Success Criteria

1. **Performance:** 80% of device relative commands execute in <10ms
2. **Accuracy:** 95% of regex matches produce correct intents (validated by tests)
3. **Coverage:** Regex handles 8/10 common device relative commands
4. **User Experience:** User feedback indicates app feels "instant" and "responsive"
5. **Maintainability:** New developers can add patterns following clear examples

**Target completion:** 1 week (20 hours implementation + testing)

**ROI:** Massive user experience improvement + modest cost savings
