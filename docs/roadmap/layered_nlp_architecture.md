# Layered NLP Architecture

**Status**: ✅ **COMPLETE & INTEGRATED**
**Date**: 2025-11-16

## Overview

Fadebender uses a 4-layer modular NLP architecture for parsing natural language commands. Each layer is independently testable, has a single responsibility, and uses regex-first with LLM fallback.

## Integration Status

### How to Enable

**Environment Variables:**
- `USE_LAYERED_PARSER=true` - Routes `/intent/parse` through layered parser
- `USE_LAYERED_CHAT=true` - Routes `/chat` through layered parser

**Production Endpoints:**
- ✅ `/intent/parse` - Supports layered mode via `USE_LAYERED_PARSER`
- ✅ `/chat` - Supports layered mode via `USE_LAYERED_CHAT`
- ✅ WebUI - Uses `/intent/parse` for all commands

**Files Modified:**
- `server/api/nlp.py` - Added layered parser routing and parse index cache
- `server/services/chat_service.py` - Added layered parser support with fallback
- `clients/web-chat/src/components/ChatMessage.jsx` - Renders list/open capabilities

---

## Architecture Diagram

```
┌──────────────────────────────────────────────────────────┐
│ Input: "increase return A volume by 2 dB"               │
└────────────────────┬─────────────────────────────────────┘
                     │
          ┌──────────┴─────────┐
          │                    │
          ▼                    ▼
┌──────────────────┐  ┌──────────────────┐
│  LAYER 1:        │  │  LAYER 2:        │
│  Action Parser   │  │  Track Parser    │
│                  │  │                  │
│  File:           │  │  File:           │
│  action_parser   │  │  track_parser    │
├──────────────────┤  └────────┬─────────┘
│ Extracts:        │           │
│ - intent_type    │           │ domain: "return"
│ - operation      │           │ index: 0
│ - value          │           │ reference: "Return A"
│ - unit           │           │
└────────┬─────────┘           │
         │                     │
         │ intent_type: "set_parameter"
         │ operation: "relative"
         │ value: 2.0
         │ unit: "dB"
         │
         └──────────┬──────────┘
                    │
                    ▼
          ┌──────────────────┐
          │  LAYER 3:        │
          │  Device/Param    │
          │  Parser          │
          │                  │
          │  Files:          │
          │  device_param    │
          │  _parser         │
          │  parse_index/    │
          │  *                │
          └────────┬─────────┘
                   │
                   │ device: "mixer"
                   │ param: "volume"
                   │
                   ▼
          ┌──────────────────┐
          │  LAYER 4:        │
          │  Intent Builder  │
          │  & Router        │
          │                  │
          │  File:           │
          │  intent_builder  │
          └────────┬─────────┘
                   │
                   ▼
┌──────────────────────────────────────────────────────────┐
│ Output: raw_intent                                       │
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

## Layer 1: Action Parser ✅ COMPLETE

**File**: `server/services/nlp/action_parser.py`

### Responsibility
Extract **intent type**, **operation type**, **value**, and **unit** from text.

### Output Structure
```python
@dataclass
class ActionMatch:
    intent_type: str          # "set_parameter", "get_parameter", "transport",
                              # "open_capabilities", "list_capabilities"
    operation: Optional[str]  # "absolute", "relative", None
    value: Optional[float | str | bool]
    unit: Optional[str]       # "dB", "%", "s", "ms", "hz", "degrees", "display", None
    confidence: float         # 0.0-1.0
    method: str              # "regex", "llm_fallback"
    raw_text: str            # Original matched text
```

### Patterns Implemented

**SET Operations:**
- `parse_absolute_change()` - "set X to Y"
- `parse_relative_change()` - "increase/decrease X by Y"
- `parse_toggle_operation()` - "mute/solo/unmute/unsolo"

**GET Operations:**
- `parse_get_query()` - "what is", "how many", "show", "tell", "get", "check"

**Transport:**
- `parse_transport_command()` - "play/stop", "loop on/off", "set tempo to X"

**Navigation:**
- `parse_navigation_command()` - "open/close/pin/unpin/view"

### Key Features
- ✅ Fuzzy matching for action words (handles typos like "incrase" → "increase")
- ✅ Unit normalization (db → dB, percent → %)
- ✅ Enhanced vocabulary (81 action words)

---

## Layer 2: Track Parser ✅ COMPLETE

**File**: `server/services/nlp/track_parser.py`

### Responsibility
Extract **domain** (track/return/master) and **index** from text.

### Output Structure
```python
@dataclass
class TrackMatch:
    domain: str                  # "track", "return", "master"
    index: Optional[int]         # 0-indexed track/return, None for master or collections
    reference: str               # "Track 1", "Return A", "Master", "tracks", "returns"
    confidence: float            # 0.0-1.0
    method: str                 # "regex", "llm_fallback"
    filter: Optional[str] = None # "audio", "midi" for collection queries
```

### Patterns Implemented

**Specific References:**
- `parse_track_reference()` - "track 1", "track 12"
- `parse_return_reference()` - "return A/B/C/D"
- `parse_master_reference()` - "master"

**Collection References (for list commands):**
- `parse_track_collection()` - "tracks", "audio tracks", "midi tracks"
- `parse_return_collection()` - "returns", "return tracks"

### Key Features
- ✅ Case insensitive matching
- ✅ 0-indexed output (Track 1 → index=0)
- ✅ Letter to index conversion (Return A → index=0)
- ✅ Filter support for audio/midi track lists

---

## Layer 3: Device/Param Parser ✅ COMPLETE

**Files**:
- `server/services/nlp/device_param_parser.py` - Main parser logic
- `server/services/parse_index/device_context_parser.py` - Parse index utilities
- `server/services/parse_index/parse_index_builder.py` - Index builder

### Responsibility
Extract **device name** and **parameter name** with fuzzy matching and typo correction.

### Output Structure
```python
@dataclass
class DeviceParamMatch:
    device: Optional[str]         # "reverb", "delay", "mixer", None
    param: Optional[str]          # "Decay", "Dry/Wet", "volume"
    device_ordinal: Optional[int] # For "device 1", "device 2"
    raw_param: str                # Original user input
    confidence: float             # 0.0-1.0
    method: str                  # "exact", "fuzzy", "typo_corrected"
```

### Patterns Implemented

**Mixer Parameters:**
- Volume, pan, mute, solo
- Sends (send A/B/C/D)

**Device Parameters:**
- Device name + parameter (e.g., "reverb decay")
- Special character handling (e.g., "dry wet" → "Dry/Wet")
- Device ordinal references (e.g., "device 0", "device 1")

**Parse Index:**
- Built from Live set snapshot
- Caches device vocabulary and parameters
- Enables device-aware parsing without hardcoding

### Key Features
- ✅ Fuzzy matching using Damerau-Levenshtein distance
- ✅ Typo correction for parameters
- ✅ Special character normalization (/, <, >, &)
- ✅ Dynamic vocabulary from Live set

---

## Layer 4: Intent Builder ✅ COMPLETE

**File**: `server/services/nlp/intent_builder.py`

### Responsibility
Combine outputs from Layers 1-3 into final `raw_intent` structure.

### Main Functions

**Intent Builders:**
- `build_raw_intent()` - Main coordinator and router
- `_build_transport_intent()` - Transport commands
- `_build_navigation_intent()` - Open/list capabilities
- `_build_mixer_intent()` - Mixer SET/relative operations
- `_build_device_intent()` - Device SET/relative operations
- `_build_get_mixer_intent()` - Mixer GET queries
- `_build_get_device_intent()` - Device GET queries

**Special Pattern Handlers:**
- `_try_special_get_patterns()` - Complex GET queries (topology, state bundles, etc.)

### Routing Logic

```python
# Route based on intent_type from Layer 1
if action.intent_type == "transport":
    → build_transport_intent()

elif action.intent_type in ("open_capabilities", "list_capabilities"):
    → build_navigation_intent()

elif action.intent_type == "set_parameter":
    if device_param.device == "mixer":
        → build_mixer_intent(plugin=None)
    elif device_param.device:
        → build_device_intent(plugin=device_param.device)

elif action.intent_type == "get_parameter":
    if device_param.device == "mixer":
        → build_get_mixer_intent()
    elif device_param.device:
        → build_get_device_intent()
```

### Output Structure
```python
{
    "intent": "set_parameter" | "get_parameter" | "transport" |
              "open_capabilities" | "list_capabilities",
    "targets": [{
        "track": "Track 1" | "Return A" | "Master",
        "plugin": "reverb" | None,      # None = mixer param
        "parameter": "volume" | "Decay",
        "device_ordinal": 1              # Optional
    }],
    "operation": {                       # Only for SET operations
        "type": "absolute" | "relative",
        "value": 2.0,
        "unit": "dB"
    },
    "meta": {
        "utterance": "original text",
        "confidence": 0.95,
        "pipeline": "regex",
        "layer_methods": {
            "action": "regex",
            "track": "regex",
            "device_param": "fuzzy"
        },
        "filter": "audio"                # Optional, for list queries
    }
}
```

### Key Features
- ✅ Handles all intent types (SET, GET, transport, navigation, list)
- ✅ Mixer vs device routing based on Layer 3 device field
- ✅ Special GET patterns (topology, state bundles, device lists, counts)
- ✅ Project-level lists (audio_tracks_list, midi_tracks_list, return_tracks_list)
- ✅ Structured navigation targets (mixer, device, drawer)
- ✅ Confidence aggregation from all layers

---

## Integration & Pipeline

### Entry Point

**File**: `server/services/nlp/intent_builder.py`

**Function**: `parse_command_layered(text: str, parse_index: Dict) -> Optional[Dict]`

### Execution Flow

```python
def parse_command_layered(text: str, parse_index: Dict):
    # 1. Apply typo corrections (from nlp-service)
    text_corrected = apply_typo_corrections(text)

    # 2. Apply fuzzy action word corrections
    text_fuzzy = apply_fuzzy_action_corrections(text_corrected)

    # 3. Parse all layers in parallel
    action = parse_action(text_lower)           # Layer 1
    track = parse_track(text_lower)             # Layer 2
    device_param = parse_device_param(          # Layer 3
        text_lower, parse_index
    )

    # 4. Build intent from layer outputs
    raw_intent = build_raw_intent(              # Layer 4
        text, action, track, device_param
    )

    # 5. Fallback to special GET patterns if needed
    if not raw_intent:
        raw_intent = _try_special_get_patterns(text_fuzzy, text)

    return raw_intent
```

### Parse Index

**Location**: `server/api/nlp.py` (module-level cache)

**Builder**: `server/services/parse_index/parse_index_builder.py`

**Built From**: Live set device snapshot

**Contents**:
- Device names in current Live set
- Parameter names for each device (from Firestore)
- Device type index
- Parameter → device type mappings
- Mixer parameter vocabulary
- Typo correction map

---

## Testing

### Test Files

**Layer 1 (Action Parser):**
- `scripts/test_action_parser.py`

**Layer 2 (Track Parser):**
- `scripts/test_track_parser.py`

**Layer 3 (Device/Param Parser):**
- `scripts/test_device_param_parser.py`
- `scripts/test_device_context_parser.py`
- `scripts/test_parse_index_simple.py`

**Layer 4 (Intent Builder):**
- `scripts/test_layered_intent_builder.py`

**Integration:**
- `scripts/test_comprehensive_intents.py` - Full command testing
- `scripts/test_mixer_functional.py` - Mixer operations
- `scripts/test_relative_intents.py` - Relative change operations

**Typo Handling:**
- `scripts/test_typo_correction.py`
- `scripts/test_typo_systematic.py`
- `scripts/test_no_typos_baseline.py`

---

## Success Metrics

- ✅ **Modular**: Each layer is independently testable
- ✅ **No Hardcoding**: Uses configuration and parse_index
- ✅ **Error Isolation**: Failures traceable to specific layers
- ✅ **Integrated**: Working in production via flags
- ✅ **Fallback**: LLM fallback when regex confidence is low
- ✅ **Complete**: All intent types supported (SET, GET, transport, navigation, list)

---

## Migration from Old Parser

### Old System (deprecated)
- `nlp-service/execution/regex_executor.py` - Monolithic regex parser
- `nlp-service/parsers/mixer_parser.py` - Mixed concerns
- `nlp-service/parsers/device_parser.py` - Mixed concerns
- `nlp-service/parsers/transport_parser.py` - Transport only

### New System (current)
- `server/services/nlp/action_parser.py` - Layer 1
- `server/services/nlp/track_parser.py` - Layer 2
- `server/services/nlp/device_param_parser.py` - Layer 3
- `server/services/nlp/intent_builder.py` - Layer 4

### Advantages
1. **Testable**: Each layer has focused unit tests
2. **Maintainable**: Adding patterns doesn't require touching multiple files
3. **Debuggable**: Can trace failures to specific layer
4. **Configurable**: No hardcoded patterns, uses parse_index
5. **Extensible**: Easy to add new intent types or patterns
