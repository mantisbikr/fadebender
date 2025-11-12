# Layered NLP Architecture Design

## Overview

This document describes the 5-layer modular architecture for Fadebender's NLP system. Each layer is independently testable, has a single responsibility, and can leverage LLM assistance minimally where needed.

## Design Principles

1. **Modularity**: Each layer has ONE clear responsibility
2. **Testability**: Each layer can be tested in isolation
3. **Error Isolation**: Failures are traceable to specific layers
4. **Minimal LLM**: Use regex first, LLM only for corner cases
5. **No Hardcoding**: Configuration-driven where possible
6. **Progressive Enhancement**: Core layers work with canonical syntax; Layer 0 adds alternate phrasings later

---

## Architecture Diagram

```
┌──────────────────────────────────────────────────────────┐
│ Input: "increase volume on return A by 2 dB"            │
└────────────────────┬─────────────────────────────────────┘
                     │
                     ▼
          ┌──────────────────────┐
          │  LAYER 0:            │
          │  Text Normalization  │  ← BUILD LATER (optional enhancement)
          │  (Word Order)        │     Adds alternate phrasing support
          └────────────┬─────────┘
                       │ "increase return A volume by 2 dB"
                       │
          ┌────────────┴─────────┐
          │                      │
          ▼                      ▼
┌──────────────────┐  ┌──────────────────┐
│  LAYER 1:        │  │  LAYER 2:        │
│  Action Parser   │  │  Track/Return    │
├──────────────────┤  │  Parser          │
│ Extracts:        │  └────────┬─────────┘
│ - intent_type    │           │
│ - operation      │           │ domain: "return"
│ - value          │           │ index: 0
│ - unit           │           │
└────────┬─────────┘           │
         │                     │
         │ intent_type: "set_parameter"
         │ operation: "relative"
         │ value: 2
         │ unit: "dB"
         │
         └──────────┬──────────┘
                    │
                    ▼
          ┌──────────────────┐
          │  LAYER 3:        │
          │  Device/Param    │
          │  Parser          │
          │  (parse_index)   │
          └────────┬─────────┘
                   │
                   │ device: "mixer" (no device name found)
                   │ param: "volume"
                   │
                   ▼
          ┌──────────────────┐
          │  LAYER 4:        │
          │  Intent Builder  │
          │  & Router        │  ← ROUTES: mixer vs device vs transport
          └────────┬─────────┘
                   │
                   ▼
┌──────────────────────────────────────────────────────────┐
│ Output: raw_intent (mixer parameter)                     │
│ {                                                        │
│   "intent": "set_parameter",                            │
│   "targets": [{                                         │
│     "track": "Return A",                                │
│     "plugin": null,          ← NULL = mixer             │
│     "parameter": "volume"                               │
│   }],                                                   │
│   "operation": {                                        │
│     "type": "relative",                                 │
│     "value": 2.0,                                       │
│     "unit": "dB"                                        │
│   }                                                     │
│ }                                                       │
└──────────────────────────────────────────────────────────┘
```

---

## Layer 0: Text Normalization (BUILD LATER)

### Responsibility
Normalize word order from alternate phrasings to canonical form.

### Status
**DEFERRED** - Build after Layers 1-4 are working. This is an optional enhancement that adds support for alternate command phrasings.

### Input
- Alternate word order: "set volume to -3db on track 1"
- Alternate word order: "increase reverb decay on return A by 1 second"

### Output
- Canonical word order: "set track 1 volume to -3db"
- Canonical word order: "increase return A reverb decay by 1 second"

### Transformation Patterns

#### Pattern 1: "set X to Y on TRACK" → "set TRACK X to Y"
```python
# Before: "set volume to -3db on track 1"
# After:  "set track 1 volume to -3db"

# Before: "set reverb predelay to 200 on return A"
# After:  "set return A reverb predelay to 200"
```

#### Pattern 2: "increase/decrease X on TRACK by Y" → "increase/decrease TRACK X by Y"
```python
# Before: "increase volume on return A by 3db"
# After:  "increase return A volume by 3db"

# Before: "decrease reverb decay on return B by 1 second"
# After:  "decrease return B reverb decay by 1 second"
```

#### Pattern 3: Navigation/Transport commands
```python
# Keep as-is (already canonical)
"open track 1"
"list tracks"
"loop on"
"set tempo to 130"
```

### Implementation Location
`server/services/nlp/text_normalizer.py`

### Testing
Test file: `scripts/test_text_normalizer.py`

**Test cases:**
- "set X on track Y" → "set track Y X"
- "increase X on return Y by Z" → "increase return Y X by Z"
- Navigation commands pass through unchanged
- Edge cases: multiple "on" keywords, nested commands

---

## Layer 1: Action/Value/Unit Parser

### Responsibility
Extract **intent type**, **operation type**, **value**, and **unit** from text.

### Input
- Raw text command (after typo correction)

### Output
```python
@dataclass
class ActionMatch:
    intent_type: str        # "set_parameter", "transport", "open_capabilities"
    operation: str | None   # "absolute", "relative", None (for non-param intents)
    value: float | str | None  # Numeric value, label string, or None
    unit: str | None        # "dB", "%", "s", "ms", "hz", "display", None
    confidence: float       # 0.0-1.0
    method: str            # "regex", "llm_fallback"
```

### Patterns to Extract

#### Absolute Changes
- "set ... to X UNIT" → `{operation: "absolute", value: X, unit: UNIT}`
- "set ... at X UNIT" → `{operation: "absolute", value: X, unit: UNIT}`

#### Relative Changes
- "increase ... by X UNIT" → `{operation: "relative", value: +X, unit: UNIT}`
- "decrease ... by X UNIT" → `{operation: "relative", value: -X, unit: UNIT}`
- "raise ... by X UNIT" → `{operation: "relative", value: +X, unit: UNIT}`
- "lower ... by X UNIT" → `{operation: "relative", value: -X, unit: UNIT}`

#### Label Changes
- "set ... to LABEL" → `{operation: "absolute", value: "LABEL", unit: "display"}`
- "set ... mode to Hall" → `{operation: "absolute", value: "Hall", unit: "display"}`

#### Toggle Operations
- "mute ..." → `{operation: "absolute", value: True, unit: None}`
- "solo ..." → `{operation: "absolute", value: True, unit: None}`

#### Transport
- "loop on" → `{intent_type: "transport", operation: "absolute", value: True}`
- "set tempo to 130" → `{intent_type: "transport", operation: "absolute", value: 130}`

#### Navigation
- "open ..." → `{intent_type: "open_capabilities", operation: None, value: None}`
- "list ..." → `{intent_type: "list_capabilities", operation: None, value: None}`

### Unit Normalization
- `db`, `dB` → `"dB"`
- `%`, `percent` → `"%"`
- `ms`, `millisecond`, `milliseconds` → `"ms"`
- `s`, `sec`, `second`, `seconds` → `"s"`
- `hz` → `"hz"`
- `khz` → `"khz"`
- `degree`, `degrees`, `deg`, `°` → `"degrees"`

### Implementation Location
`server/services/nlp/action_parser.py`

### Testing
Test file: `scripts/test_action_parser.py`

**Test cases:**
- Absolute value extraction: "set ... to 20 dB"
- Relative value extraction: "increase ... by 5%"
- Unit normalization: "dB" vs "db"
- Label extraction: "set mode to Hall"
- Transport commands: "loop on", "set tempo to 130"
- Navigation commands: "open track 1"

---

## Layer 2: Track/Return Parser

### Responsibility
Extract **domain** (track/return/master) and **index** from text.

### Input
- Raw text command

### Output
```python
@dataclass
class TrackMatch:
    domain: str         # "track", "return", "master"
    index: int | None   # Track number (0-indexed) or Return index (0=A, 1=B, etc.)
    reference: str      # Original reference ("Track 1", "Return A", "Master")
    confidence: float   # 0.0-1.0
    method: str        # "regex", "llm_fallback"
```

### Patterns to Extract

#### Track References
- "track 1" → `{domain: "track", index: 0, reference: "Track 1"}`
- "track 2" → `{domain: "track", index: 1, reference: "Track 2"}`

#### Return References
- "return a" → `{domain: "return", index: 0, reference: "Return A"}`
- "return b" → `{domain: "return", index: 1, reference: "Return B"}`
- "return c" → `{domain: "return", index: 2, reference: "Return C"}`
- "return d" → `{domain: "return", index: 3, reference: "Return D"}`

#### Master Reference
- "master" → `{domain: "master", index: None, reference: "Master"}`

### Implementation Location
`server/services/nlp/track_parser.py`

### Reuse Existing Code
Refactor patterns from:
- `nlp-service/parsers/mixer_parser.py` (track/return extraction)
- `nlp-service/parsers/transport_parser.py` (handles master)

### Testing
Test file: `scripts/test_track_parser.py`

**Test cases:**
- Track references: "track 1", "track 12"
- Return references: "return A", "return D"
- Master reference: "master"
- Case insensitivity: "TRACK 1", "Return a"

---

## Layer 3: Device/Param Parser (parse_index)

### Responsibility
Extract **device name** and **parameter name** with fuzzy matching and typo correction.

### Input
- Raw text command (after typo correction)
- Parse index (device/param vocabulary)

### Output
```python
@dataclass
class DeviceParamMatch:
    device: str | None     # Device name ("reverb", "delay") or "mixer"
    param: str | None      # Parameter name ("Decay", "Dry/Wet")
    device_ordinal: int | None  # Ordinal reference (1, 2, etc.)
    raw_param: str         # Original parameter text from user
    confidence: float      # 0.0-1.0
    method: str           # "exact", "fuzzy", "typo_corrected", etc.
```

### Patterns to Extract

#### Mixer Parameters
- "volume" → `{device: "mixer", param: "volume"}`
- "pan" → `{device: "mixer", param: "pan"}`
- "send a" → `{device: "mixer", param: "send a"}`
- "mute" → `{device: "mixer", param: "mute"}`
- "solo" → `{device: "mixer", param: "solo"}`

#### Device Parameters
- "reverb decay" → `{device: "reverb", param: "Decay"}`
- "reverb dry wet" → `{device: "reverb", param: "Dry/Wet"}` (special char handling)
- "delay time" → `{device: "delay", param: "Time"}`

#### Device Ordinal References
- "device 0" → `{device: "device", device_ordinal: 0}`
- "device 1" → `{device: "device", device_ordinal: 1}`

#### Typo Correction
- "reverb decya" → `{device: "reverb", param: "Decay", method: "typo_corrected"}`
- "pan" (typo: "pna") → `{device: "mixer", param: "pan", method: "typo_corrected"}`

### Implementation Location
`server/services/parse_index/` (already exists)

### Current Issues to Fix
1. **Mixer params not recognized**: "pan", "send a" return `device=None`
2. **Typo handling loses context**: Corrects param but loses device

### Testing
Test file: `scripts/test_parse_index_comprehensive.py` (already exists)

---

## Layer 4: Intent Builder

### Responsibility
Combine outputs from Layers 1-3 into final `raw_intent` structure.

### Input
- `ActionMatch` from Layer 1
- `TrackMatch` from Layer 2
- `DeviceParamMatch` from Layer 3

### Output
```python
raw_intent = {
    "intent": "set_parameter",  # or "transport", "open_capabilities"
    "targets": [{
        "track": "Return A",     # From Layer 2
        "plugin": "reverb",      # From Layer 3 (or None for mixer)
        "parameter": "Decay",    # From Layer 3
        "device_ordinal": 1      # From Layer 3 (optional)
    }],
    "operation": {
        "type": "relative",      # From Layer 1
        "value": 2.0,           # From Layer 1
        "unit": "s"             # From Layer 1
    },
    "meta": {
        "utterance": "original text",
        "confidence": 0.95,
        "pipeline": "regex",     # or "llm_fallback"
        "layer_methods": {
            "action": "regex",
            "track": "regex",
            "device_param": "fuzzy"
        }
    }
}
```

### Combining Rules

#### Rule 1: Control Intent (set_parameter)
- **Requires**: ActionMatch (operation != None) + TrackMatch + DeviceParamMatch
- **Output**: Intent with targets, operation

#### Rule 2: Transport Intent
- **Requires**: ActionMatch (intent_type="transport")
- **Output**: Intent with action, value (no targets)

#### Rule 3: Navigation Intent
- **Requires**: ActionMatch (intent_type="open_capabilities") + TrackMatch
- **Optional**: DeviceParamMatch (for device-specific navigation)
- **Output**: Intent with target reference

#### Rule 4: Mixer vs Device
- If `DeviceParamMatch.device == "mixer"`: `plugin=None`
- Otherwise: `plugin=DeviceParamMatch.device`

### Routing Logic (Determines Intent Type)

**Layer 4 routes based on Layer 1 intent_type and Layer 3 device field:**

```python
def build_intent(action: ActionMatch, track: TrackMatch, device_param: DeviceParamMatch):
    # Route 1: Transport intents (no targets)
    if action.intent_type == "transport":
        return build_transport_intent(action)

    # Route 2: Navigation intents (open/list)
    if action.intent_type in ("open_capabilities", "list_capabilities"):
        return build_navigation_intent(action, track, device_param)

    # Route 3: Parameter intents (mixer or device)
    if action.intent_type == "set_parameter":
        # Sub-route based on device field
        if device_param.device == "mixer":
            return build_mixer_intent(action, track, device_param, plugin=None)
        elif device_param.device:
            return build_device_intent(action, track, device_param, plugin=device_param.device)
        else:
            return None  # Ambiguous - fallback to LLM

    return None  # Unknown intent type - fallback to LLM
```

**Decision Tree:**
```
Layer 1 intent_type?
├─ "transport" → build_transport_intent() (no targets)
├─ "open_capabilities" → build_navigation_intent() (track + optional device)
├─ "list_capabilities" → build_navigation_intent() (track + optional device)
└─ "set_parameter" → Check Layer 3 device field:
   ├─ device="mixer" → build_mixer_intent() with plugin=null
   ├─ device="reverb" → build_device_intent() with plugin="reverb"
   └─ device=None → FALLBACK TO LLM (ambiguous)
```

### Implementation Location
`server/services/nlp/intent_builder.py`

### Testing
Test file: `scripts/test_intent_builder.py`

**Test cases:**
- Control intent: Combine all 3 layers
- Transport intent: Layer 1 only
- Navigation intent: Layer 1 + 2 (+ optional Layer 3)
- Mixer vs Device: Proper plugin field handling
- Missing layers: Graceful degradation

---

## Pipeline Integration

### Main NLP Coordinator

**Location**: `server/services/nlp/nlp_coordinator.py` (NEW)

**Flow**:
```python
def parse_command(text: str) -> Dict[str, Any]:
    """
    Main entry point for NLP parsing.

    1. Typo correction (existing)
    2. Try regex pipeline (4 layers)
    3. If regex fails, try LLM fallback
    4. Return raw_intent
    """

    # Typo correction
    corrected_text = apply_typo_corrections(text)

    # Layer 1: Action/Value/Unit
    action_match = parse_action(corrected_text)
    if not action_match or action_match.confidence < 0.5:
        return llm_fallback(text)

    # Layer 2: Track/Return (if needed)
    track_match = None
    if action_match.intent_type in ("set_parameter", "open_capabilities"):
        track_match = parse_track_reference(corrected_text)
        if not track_match or track_match.confidence < 0.5:
            return llm_fallback(text)

    # Layer 3: Device/Param (if control intent)
    device_param_match = None
    if action_match.intent_type == "set_parameter":
        device_param_match = parse_device_param(corrected_text, parse_index)
        if not device_param_match or device_param_match.confidence < 0.5:
            return llm_fallback(text)

    # Layer 4: Build Intent
    raw_intent = build_intent(
        action=action_match,
        track=track_match,
        device_param=device_param_match,
        original_text=text
    )

    return raw_intent
```

### Replacing Existing Code

**Current**: `nlp-service/parsers/device_parser.py` (monolithic regex)

**New**: 4-layer pipeline (modular)

**Migration Strategy**:
1. Build all 4 layers independently
2. Test each layer in isolation
3. Build integration tests for full pipeline
4. Replace calls to `device_parser.py` with `nlp_coordinator.py`
5. Keep LLM fallback as-is (no changes to LLM system)
6. Keep mixer/transport regex as-is initially (can refactor later)

---

## Testing Strategy

### Unit Tests (Per Layer)

**Layer 1: Action Parser**
- Test all action patterns independently
- Test unit normalization
- Test edge cases (missing units, typos in actions)

**Layer 2: Track Parser**
- Test all track/return/master patterns
- Test case insensitivity
- Test edge cases (invalid track numbers)

**Layer 3: Device/Param Parser**
- Test device+param extraction
- Test mixer parameter recognition
- Test typo correction
- Test special character handling
- Test device ordinal references

**Layer 4: Intent Builder**
- Test intent assembly from layer outputs
- Test missing layer handling
- Test confidence aggregation
- Test meta field population

### Integration Tests

**Full Pipeline Tests**
- Test commands that require all layers
- Test commands with partial layer usage (transport, navigation)
- Test typo correction flow
- Test LLM fallback trigger conditions

**Regression Tests**
- All existing test cases from `test_comprehensive_intents.py`
- All mixer, device, transport patterns
- Typo handling patterns
- Special character patterns

### Performance Tests
- Measure latency per layer
- Compare regex vs LLM fallback costs
- Ensure >80% commands use regex pipeline

---

## Configuration

### Action Patterns Config
`server/config/action_patterns.json`

```json
{
  "absolute_verbs": ["set", "change", "adjust"],
  "relative_verbs": {
    "increase": 1,
    "decrease": -1,
    "raise": 1,
    "lower": -1
  },
  "units": {
    "dB": ["db", "dB"],
    "%": ["%", "percent"],
    "s": ["s", "sec", "second", "seconds"],
    "ms": ["ms", "millisecond", "milliseconds"],
    "hz": ["hz"],
    "khz": ["khz"],
    "degrees": ["degree", "degrees", "deg", "°"]
  }
}
```

### Track Reference Patterns
Already in `server/config/app_config.json` (reuse existing)

### Device/Param Patterns
Already in Firestore + `parse_index` (no changes needed)

---

## LLM Integration Points

Each layer can use LLM as fallback when regex confidence is low:

1. **Layer 1**: If action pattern doesn't match cleanly
2. **Layer 2**: If track reference is ambiguous
3. **Layer 3**: Already has LLM fallback in parse_index
4. **Layer 4**: If intent assembly fails

**Goal**: Keep LLM usage <20% (currently at target)

---

## Success Metrics

1. **All layers independently testable**: ✓ (when complete)
2. **100% test coverage per layer**: Target
3. **Failures traceable to specific layer**: ✓ (by design)
4. **No hardcoded patterns**: ✓ (config-driven)
5. **LLM usage <20%**: Target (maintain current)
6. **Latency <10ms per layer**: Target

---

## Implementation Order

1. **Phase 1**: Layer 1 (Action Parser) + Unit tests
2. **Phase 2**: Layer 2 (Track Parser) + Unit tests
3. **Phase 3**: Fix Layer 3 (Device/Param Parser) + Unit tests
4. **Phase 4**: Layer 4 (Intent Builder) + Unit tests
5. **Phase 5**: Integration tests (full pipeline)
6. **Phase 6**: Replace device_parser.py with nlp_coordinator.py
7. **Phase 7**: End-to-end testing + TESTING_GUIDE.md update

---

## Open Questions

1. **Device ordinal handling**: Should Layer 3 extract "device 1" or should Layer 1 handle it?
   - **Decision**: Layer 3 (device context-aware)

2. **Typo correction placement**: Before or after layer parsing?
   - **Decision**: Before (as currently implemented)

3. **LLM fallback per layer or full command?**
   - **Decision**: Try per-layer first, full command fallback if any layer fails

4. **Mixer vs Device decision logic**: Who decides plugin=None?
   - **Decision**: Layer 4 (Intent Builder) based on Layer 3 device field

---

## Next Steps

1. Create `server/services/nlp/` directory
2. Implement Layer 1 (Action Parser)
3. Write unit tests for Layer 1
4. Proceed to Layer 2, 3, 4 sequentially
