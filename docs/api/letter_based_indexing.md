# Letter-Based Indexing for Sends and Returns

**Date:** 2025-10-15
**Status:** ✅ Implemented and Tested

## Summary

The Intents API now supports letter-based references for sends and returns, making the API more intuitive and aligned with how Ableton Live displays these elements to users.

## Motivation

Ableton Live uses **inconsistent indexing** in its API:
- **Tracks:** 1-based (Track 1 = index 1, Track 2 = index 2)
- **Sends:** 0-based (Send A = index 0, Send B = index 1)
- **Returns:** 0-based (Return A = index 0, Return B = index 1)

This creates confusion for users because:
- Live's UI shows "Send A", "Return A" (letters)
- But the API requires numeric indices starting at 0
- Users must mentally translate "A" → 0, "B" → 1, etc.

## Solution: Letter-Based References

We now accept **letter references** alongside numeric indices:

| User Sees | Old API (Numeric) | New API (Letter-Based) |
|-----------|------------------|------------------------|
| Send A | `send_index: 0` | `send_ref: "A"` ✨ |
| Send B | `send_index: 1` | `send_ref: "B"` ✨ |
| Return A | `return_index: 0` | `return_ref: "A"` ✨ |
| Return B | `return_index: 1` | `return_ref: "B"` ✨ |

## API Examples

### Track Sends

**Old (numeric):**
```json
{
  "domain": "track",
  "track_index": 1,
  "field": "send",
  "send_index": 0,
  "value": -12,
  "unit": "dB"
}
```

**New (letter-based) - PREFERRED:**
```json
{
  "domain": "track",
  "track_index": 1,
  "field": "send",
  "send_ref": "A",
  "value": -12,
  "unit": "dB"
}
```

### Return Track Mixer

**Old (numeric):**
```json
{
  "domain": "return",
  "return_index": 0,
  "field": "volume",
  "value": -6,
  "unit": "dB"
}
```

**New (letter-based) - PREFERRED:**
```json
{
  "domain": "return",
  "return_ref": "A",
  "field": "volume",
  "value": -6,
  "unit": "dB"
}
```

### Return Sends

**Old (numeric):**
```json
{
  "domain": "return",
  "return_index": 0,
  "field": "send",
  "send_index": 1,
  "value": -10,
  "unit": "dB"
}
```

**New (letter-based) - PREFERRED:**
```json
{
  "domain": "return",
  "return_ref": "A",
  "field": "send",
  "send_ref": "B",
  "value": -10,
  "unit": "dB"
}
```

## Implementation Details

### CanonicalIntent Support

```python
# Implemented in `server/models/intents_api.py`:
# `CanonicalIntent` supports both numeric indices and letter refs
# for returns (`return_index` or `return_ref`) and sends (`send_index` or `send_ref`).
```

### Resolution Functions

```python
Implemented in `server/services/intents/utils/refs.py`:

```python
def _letter_to_index(letter: str) -> int: ...
def _resolve_return_index(return_index: Optional[int] = None, return_ref: Optional[str] = None) -> int: ...
def _resolve_send_index(send_index: Optional[int] = None, send_ref: Optional[str] = None) -> int: ...
```
```

## Backwards Compatibility

✅ **Both formats are supported**
- Letter-based references are **preferred** for new code
- Numeric indices still work for backwards compatibility
- No breaking changes to existing API consumers

## Benefits for NLP/Voice Control

Letter-based references are perfect for natural language:

```
"Set send A on track 1 to -12 dB"
→ {"domain":"track","track_index":1,"field":"send","send_ref":"A","value":-12,"unit":"dB"}

"Pan return A to center"
→ {"domain":"return","return_ref":"A","field":"pan","display":"center"}

"Mute return B"
→ {"domain":"return","return_ref":"B","field":"mute","value":1}
```

## Consistency Summary

After this change, the API indexing is consistent with user expectations:

| Element | User Sees | API Format | Internal Index | Live API Index |
|---------|-----------|------------|----------------|----------------|
| Track 1 | "Track 1" | `track_index: 1` | 1 | 1 (1-based) |
| Send A | "Send A" | `send_ref: "A"` | 0 | 0 (0-based) |
| Send B | "Send B" | `send_ref: "B"` | 1 | 1 (0-based) |
| Return A | "Return A" | `return_ref: "A"` | 0 | 0 (0-based) |
| Return B | "Return B" | `return_ref: "B"` | 1 | 1 (0-based) |

## Testing

✅ **Tested Commands:**
```bash
# Track Send A with letter reference
curl -X POST http://127.0.0.1:8722/intent/execute \
  -H "Content-Type: application/json" \
  -d '{"domain":"track","track_index":1,"field":"send","send_ref":"A","value":-12,"unit":"dB"}'
# Result: {"ok":true,"op":"set_send"}

# Return A volume with letter reference
curl -X POST http://127.0.0.1:8722/intent/execute \
  -H "Content-Type: application/json" \
  -d '{"domain":"return","return_ref":"A","field":"volume","value":-6,"unit":"dB"}'
# Result: {"ok":true,"op":"set_return_mixer"}
```

## Files Modified

1. **server/models/intents_api.py**
   - `CanonicalIntent` includes `return_ref` and `send_ref`
2. **server/services/intents/utils/refs.py**
   - `_letter_to_index()`, `_resolve_return_index()`, `_resolve_send_index()`
3. **server/api/intents.py**
   - Delegates to services; no inline resolver logic

2. **docs/testing/intents_api_test_plan.md**
   - Updated all test cases to use letter-based references
   - Added explanation section at top

3. **docs/testing/intents_api_letter_examples.md**
   - Comprehensive examples document
   - Shows both old and new formats
   - Natural language examples

4. **docs/api/letter_based_indexing.md** (this file)
   - Technical documentation
   - Implementation details
   - Migration guide

## Migration Guide

No migration required! Both formats work. To adopt letter-based format:

1. Replace `send_index: 0` with `send_ref: "A"`
2. Replace `send_index: 1` with `send_ref: "B"`
3. Replace `return_index: 0` with `return_ref: "A"`
4. Replace `return_index: 1` with `return_ref: "B"`

## Future Enhancements

Potential improvements:
- Support ranges: `send_ref: "A-C"` for bulk operations
- Support wildcards: `send_ref: "*"` for all sends
- Auto-complete suggestions in web UI based on letter format
