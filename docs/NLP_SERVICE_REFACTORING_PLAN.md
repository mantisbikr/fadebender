# NLP Service Refactoring Plan

**Target**: `nlp-service/llm_daw.py` (1,069 lines → ~150 lines)
**Goal**: Extract business logic into focused, testable modules with clear separation of concerns
**Estimated Effort**: 2-3 hours
**Risk Level**: Medium (requires careful testing of all NLP patterns)

---

## Current State Analysis

### File Structure (1,069 lines, 5 functions):

1. **`_extract_llm_hints()`** (66 lines)
   - Extracts track hints (Return A/Track N/Master)
   - Extracts device name hints from known generic devices
   - Extracts device ordinal hints (numeric: "reverb 2", word: "second reverb")

2. **`_build_daw_prompt()`** (187 lines)
   - Builds context-aware LLM prompt with mixer params and known devices
   - Contains massive hardcoded prompt template with examples
   - Helper function `_hints_text()` for injecting hints

3. **`_fetch_session_devices()`** (37 lines)
   - Fetches devices from Live session via /snapshot endpoint
   - Processes track and return devices

4. **`interpret_daw_command()`** (95 lines)
   - Main entry point for NLP interpretation
   - Orchestrates device/param fetching
   - Calls Google Gen AI SDK (Vertex AI)
   - Falls back to rule-based parser on failure

5. **`_fallback_daw_parse()`** (637 lines) ⚠️ CRITICAL BLOAT
   - 30+ regex patterns for different command types
   - Handles: track volume, return volume, device params, pan, solo/mute, sends, label selections
   - Typo correction mapping
   - Ordinal word expansion (first→1, second→2)
   - Question handling fallback

### Key Issues:

- **Poor Testability**: Can't test individual patterns in isolation
- **Difficult Maintenance**: 637-line function is unmaintainable
- **Code Duplication**: Similar patterns repeated for tracks vs returns
- **Mixed Concerns**: Parsing, validation, typo correction all intertwined
- **Hard to Extend**: Adding new patterns requires modifying massive function

---

## Proposed Module Structure

```
nlp-service/
├── llm_daw.py                 (150 lines - main orchestration only)
├── prompts/
│   ├── __init__.py
│   ├── hint_extractor.py      (80 lines - _extract_llm_hints)
│   ├── prompt_builder.py      (120 lines - _build_daw_prompt logic)
│   └── prompt_templates.py    (200 lines - prompt string templates)
├── parsers/
│   ├── __init__.py
│   ├── fallback_parser.py     (100 lines - main coordinator)
│   ├── track_parser.py        (150 lines - track patterns)
│   ├── return_parser.py       (150 lines - return patterns)
│   ├── mixer_parser.py        (120 lines - volume/pan/mute/solo/sends)
│   ├── device_parser.py       (120 lines - device param patterns)
│   └── typo_corrector.py      (60 lines - typo mapping and ordinals)
├── fetchers/
│   ├── __init__.py
│   ├── session_fetcher.py     (50 lines - _fetch_session_devices)
│   └── preset_fetcher.py      (60 lines - Firestore preset fetching)
└── models/
    ├── __init__.py
    ├── intent_types.py        (40 lines - Intent type definitions)
    └── pattern_types.py       (40 lines - Pattern match types)
```

**Total Lines**: ~1,290 lines (up from 1,069, but vastly more maintainable)
**Modules**: 15 focused files (vs 1 monolithic file)

---

## Detailed Refactoring Steps

### Phase 1: Extract Models and Types (30 mins, Low Risk)

**Files to Create:**
- `nlp-service/models/__init__.py`
- `nlp-service/models/intent_types.py`
- `nlp-service/models/pattern_types.py`

**What to Extract:**
```python
# intent_types.py - Type definitions used across the service
from typing import Dict, List, Any, TypedDict, Literal

IntentType = Literal["set_parameter", "relative_change", "get_parameter",
                     "question_response", "clarification_needed"]

class Target(TypedDict, total=False):
    track: str | None
    plugin: str | None
    parameter: str
    device_ordinal: int

class Operation(TypedDict, total=False):
    type: Literal["absolute", "relative"]
    value: float | str
    unit: str | None

class Intent(TypedDict):
    intent: IntentType
    targets: List[Target]
    operation: Operation
    meta: Dict[str, Any]

# pattern_types.py - Pattern match result types
class PatternMatch(TypedDict, total=False):
    track_num: int | None
    return_ref: str | None
    device_name: str | None
    device_ordinal: int | None
    parameter: str
    value: float | str
    unit: str | None
```

**Changes to llm_daw.py:**
- Add imports: `from nlp-service.models.intent_types import Intent, Target, Operation`
- Type hint return values: `def interpret_daw_command(...) -> Intent:`

**Testing:**
- Run existing NLP tests to ensure types don't break anything
- Run: `python -m pytest nlp-service/tests/` (if tests exist)

---

### Phase 2: Extract Hint Extractor (20 mins, Low Risk)

**Files to Create:**
- `nlp-service/prompts/__init__.py`
- `nlp-service/prompts/hint_extractor.py`

**What to Extract:**
```python
# hint_extractor.py
import re
from typing import Dict, Any

def extract_llm_hints(query: str) -> Dict[str, Any]:
    """Extract lightweight hints from user utterance to guide the LLM.

    Returns:
        dict with optional keys:
            - track_hint: "Return A" | "Track N" | "Master"
            - device_name_hint: device name (generic or arbitrary)
            - device_ordinal_hint: 1-based ordinal (from "reverb 2" or word ordinals)
    """
    # [Move entire _extract_llm_hints function body here]
    # No changes to logic, just rename from _extract_llm_hints → extract_llm_hints
```

**Changes to llm_daw.py:**
- Remove `_extract_llm_hints()` function (lines 16-82)
- Add import: `from nlp-service.prompts.hint_extractor import extract_llm_hints`
- Update call in `_build_daw_prompt()`: `hints = extract_llm_hints(q)`

**Testing:**
- Test hint extraction: `python -c "from nlp-service.prompts.hint_extractor import extract_llm_hints; print(extract_llm_hints('set return A reverb 2 decay to 2s'))"`
- Expected: `{'track_hint': 'Return A', 'device_name_hint': 'reverb', 'device_ordinal_hint': 2}`

---

### Phase 3: Extract Prompt Builder (30 mins, Low Risk)

**Files to Create:**
- `nlp-service/prompts/prompt_templates.py`
- `nlp-service/prompts/prompt_builder.py`

**What to Extract:**

```python
# prompt_templates.py - Massive prompt string constants
DAW_SYSTEM_PROMPT = """You are an expert audio engineer and Ableton Live power user..."""
# [Move entire prompt template string from lines 145-270]

CONTEXT_INSTRUCTIONS = """**CONTEXT: You understand audio engineering terminology**..."""
# etc.

# prompt_builder.py
from typing import List, Dict, Any
from nlp-service.prompts.hint_extractor import extract_llm_hints
from nlp-service.prompts.prompt_templates import DAW_SYSTEM_PROMPT
import json

def build_hints_text(query: str) -> str:
    """Build hints injection text for LLM prompt."""
    try:
        hints = extract_llm_hints(query)
    except Exception:
        hints = {}
    if not hints:
        return ""
    # [Move _hints_text logic here]

def build_mixer_context(mixer_params: List[str] | None) -> str:
    """Build mixer parameters context section."""
    # [Move mixer_context logic from lines 107-115]

def build_device_context(known_devices: List[Dict[str, str]] | None) -> str:
    """Build known devices context section."""
    # [Move device_context logic from lines 117-139]

def build_daw_prompt(query: str,
                     mixer_params: List[str] | None = None,
                     known_devices: List[Dict[str, str]] | None = None) -> str:
    """Build complete LLM prompt with context."""
    # Orchestrate all the above functions
```

**Changes to llm_daw.py:**
- Remove `_build_daw_prompt()` function (lines 85-272)
- Add import: `from nlp-service.prompts.prompt_builder import build_daw_prompt`
- Update call in `interpret_daw_command()`: `prompt = build_daw_prompt(...)`

**Testing:**
- Test prompt building: Verify prompt contains hints, mixer params, device context
- Run comprehensive NLP tests to ensure prompts still work

---

### Phase 4: Extract Session/Preset Fetchers (20 mins, Low Risk)

**Files to Create:**
- `nlp-service/fetchers/__init__.py`
- `nlp-service/fetchers/session_fetcher.py`
- `nlp-service/fetchers/preset_fetcher.py`

**What to Extract:**

```python
# session_fetcher.py
from typing import List, Dict
import requests

def fetch_session_devices() -> List[Dict[str, str]] | None:
    """Fetch all devices from current Live session snapshot."""
    # [Move _fetch_session_devices logic from lines 275-312]

# preset_fetcher.py
from typing import List, Dict
import os
import sys

def fetch_preset_devices() -> List[Dict[str, str]] | None:
    """Fetch devices from Firestore presets as fallback."""
    try:
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..', 'server'))
        from services.mapping_store import MappingStore
        store = MappingStore()
        presets = store.list_presets()
        # [Move logic from lines 333-343]
    except Exception:
        return None

def fetch_mixer_params() -> List[str] | None:
    """Fetch mixer parameter names from Firestore."""
    # [Move logic from lines 347-359]
```

**Changes to llm_daw.py:**
- Remove `_fetch_session_devices()` function
- Add imports: `from nlp-service.fetchers.session_fetcher import fetch_session_devices`
- Add imports: `from nlp-service.fetchers.preset_fetcher import fetch_preset_devices, fetch_mixer_params`
- Update calls in `interpret_daw_command()`

**Testing:**
- Test device fetching: Verify devices are fetched correctly
- Test fallback behavior: Kill Live session, verify Firestore fallback works

---

### Phase 5: Extract Typo Corrector (15 mins, Low Risk)

**Files to Create:**
- `nlp-service/parsers/__init__.py`
- `nlp-service/parsers/typo_corrector.py`

**What to Extract:**

```python
# typo_corrector.py
import re
from typing import Dict

ORDINAL_WORD_MAP = {
    'first': '1', 'second': '2', 'third': '3', 'fourth': '4', 'fifth': '5',
    'sixth': '6', 'seventh': '7', 'eighth': '8', 'ninth': '9', 'tenth': '10'
}

def get_typo_corrections() -> Dict[str, str]:
    """Get typo correction map (config-driven with fallback)."""
    try:
        from server.config.app_config import get_typo_corrections as get_config_typos
        return get_config_typos() or _get_default_typo_map()
    except Exception:
        return _get_default_typo_map()

def _get_default_typo_map() -> Dict[str, str]:
    """Default typo corrections."""
    return {
        'retrun': 'return', 'retun': 'return',
        'revreb': 'reverb', 'reverbb': 'reverb', # etc.
    }

def apply_typo_corrections(query: str) -> str:
    """Apply typo corrections and expand ordinal words."""
    q = query.lower().strip()

    # Expand ordinal words
    for word, digit in ORDINAL_WORD_MAP.items():
        q = re.sub(rf"\b{word}\b", digit, q)

    # Apply typo corrections
    for typo, correct in get_typo_corrections().items():
        q = re.sub(rf"\b{typo}\b", correct, q)

    return q
```

**Changes to llm_daw.py:**
- No direct changes yet (will be used in Phase 6)

**Testing:**
- Test typo correction: `apply_typo_corrections("set retun A revreb decay to 2s")`
- Expected: `"set return a reverb decay to 2s"`

---

### Phase 6: Extract Mixer Parser (45 mins, Medium Risk)

**Files to Create:**
- `nlp-service/parsers/mixer_parser.py`

**What to Extract:**

```python
# mixer_parser.py
import re
from typing import Dict, Any
from nlp-service.models.intent_types import Intent

def parse_track_volume_absolute(q: str, query: str, error_msg: str, model: str) -> Intent | None:
    """Parse: set track 1 volume to -6 dB"""
    # [Move logic from lines 441-464]

def parse_track_volume_relative(q: str, query: str, error_msg: str, model: str) -> Intent | None:
    """Parse: increase track 1 volume by 3 dB"""
    # [Move logic from lines 515-531]

def parse_track_pan(q: str, query: str, error_msg: str, model: str) -> Intent | None:
    """Parse: pan track 1 25L"""
    # [Move logic from lines 534-551]

def parse_track_solo_mute(q: str, query: str, error_msg: str, model: str) -> Intent | None:
    """Parse: solo track 1, mute track 2"""
    # [Move logic from lines 611-625]

def parse_track_sends(q: str, query: str, error_msg: str, model: str) -> Intent | None:
    """Parse: set track 1 send A to -12 dB"""
    # [Move logic from lines 629-683]

def parse_return_volume(q: str, query: str, error_msg: str, model: str) -> Intent | None:
    """Parse: set return A volume to -3 dB"""
    # [Move logic from lines 961-980]

def parse_return_sends(q: str, query: str, error_msg: str, model: str) -> Intent | None:
    """Parse: set return A send B to -10 dB"""
    # [Move logic from lines 903-958]

# Main mixer parser coordinator
MIXER_PARSERS = [
    parse_track_volume_absolute,
    parse_track_volume_relative,
    parse_track_pan,
    parse_track_solo_mute,
    parse_track_sends,
    parse_return_volume,
    parse_return_sends,
]

def parse_mixer_command(q: str, query: str, error_msg: str, model: str) -> Intent | None:
    """Try all mixer parsers in order."""
    for parser in MIXER_PARSERS:
        try:
            result = parser(q, query, error_msg, model)
            if result:
                return result
        except Exception:
            continue
    return None
```

**Changes to llm_daw.py:**
- Remove mixer parsing logic from `_fallback_daw_parse()`
- Add import: `from nlp-service.parsers.mixer_parser import parse_mixer_command`
- Call in `_fallback_daw_parse()`:
  ```python
  result = parse_mixer_command(q, query, error_msg, model_preference)
  if result:
      return result
  ```

**Testing:**
- Test each mixer pattern individually
- Run comprehensive NLP tests for mixer operations
- Test edge cases: typos, missing units, variant phrasings

---

### Phase 7: Extract Device Parser (45 mins, Medium Risk)

**Files to Create:**
- `nlp-service/parsers/device_parser.py`

**What to Extract:**

```python
# device_parser.py
import re
from typing import Dict, Any
from nlp-service.models.intent_types import Intent

def parse_track_device_param(q: str, query: str, error_msg: str, model: str) -> Intent | None:
    """Parse: set track 1 reverb decay to 2s"""
    # [Move logic from lines 469-511]

def parse_return_device_param(q: str, query: str, error_msg: str, model: str) -> Intent | None:
    """Parse: set return A reverb decay to 2s"""
    # [Move logic from lines 554-606]

def parse_return_device_label(q: str, query: str, error_msg: str, model: str) -> Intent | None:
    """Parse: set return A align delay mode to distance"""
    # [Move logic from lines 688-741]

def parse_return_device_arbitrary_param(q: str, query: str, error_msg: str, model: str) -> Intent | None:
    """Parse: set return A 4th bandpass feedback to 20%"""
    # [Move logic from lines 744-771]

def parse_track_device_label(q: str, query: str, error_msg: str, model: str) -> Intent | None:
    """Parse: set track 1 compressor mode to peak"""
    # [Move logic from lines 804-833]

def parse_track_device_arbitrary_param(q: str, query: str, error_msg: str, model: str) -> Intent | None:
    """Parse: set track 1 4th bandpass feedback to 20%"""
    # [Move logic from lines 774-800]

def parse_return_device_ordinal(q: str, query: str, error_msg: str, model: str) -> Intent | None:
    """Parse: set return A device 2 decay to 2s"""
    # [Move logic from lines 839-866]

def parse_track_device_ordinal(q: str, query: str, error_msg: str, model: str) -> Intent | None:
    """Parse: set track 1 device 2 decay to 2s"""
    # [Move logic from lines 870-896]

def parse_generic_return_device(q: str, query: str, error_msg: str, model: str) -> Intent | None:
    """Parse: set return A reverb <param> to <val>"""
    # [Move logic from lines 983-1026]

# Main device parser coordinator
DEVICE_PARSERS = [
    parse_track_device_param,
    parse_return_device_param,
    parse_return_device_label,
    parse_track_device_label,
    parse_track_device_arbitrary_param,
    parse_return_device_arbitrary_param,
    parse_return_device_ordinal,
    parse_track_device_ordinal,
    parse_generic_return_device,
]

def parse_device_command(q: str, query: str, error_msg: str, model: str) -> Intent | None:
    """Try all device parsers in order."""
    for parser in DEVICE_PARSERS:
        try:
            result = parser(q, query, error_msg, model)
            if result:
                return result
        except Exception:
            continue
    return None
```

**Changes to llm_daw.py:**
- Remove device parsing logic from `_fallback_daw_parse()`
- Add import: `from nlp-service.parsers.device_parser import parse_device_command`
- Call in `_fallback_daw_parse()` after mixer parser

**Testing:**
- Test each device pattern individually
- Run comprehensive NLP tests for device operations
- Test ordinals, label selections, arbitrary device names

---

### Phase 8: Extract Fallback Parser Coordinator (20 mins, Low Risk)

**Files to Create:**
- `nlp-service/parsers/fallback_parser.py`

**What to Extract:**

```python
# fallback_parser.py
from typing import Dict, Any
from nlp-service.models.intent_types import Intent
from nlp-service.parsers.typo_corrector import apply_typo_corrections
from nlp-service.parsers.mixer_parser import parse_mixer_command
from nlp-service.parsers.device_parser import parse_device_command
from config.llm_config import get_default_model_name

def parse_question(q: str, query: str, error_msg: str, model: str) -> Intent | None:
    """Handle question-style queries."""
    # [Move logic from lines 1029-1042]

def fallback_daw_parse(query: str, error_msg: str, model_preference: str | None) -> Intent:
    """Simple rule-based fallback parser for basic DAW commands."""
    q = apply_typo_corrections(query)
    model = get_default_model_name(model_preference)

    # Try mixer commands first (most common)
    result = parse_mixer_command(q, query, error_msg, model)
    if result:
        return result

    # Try device commands
    result = parse_device_command(q, query, error_msg, model)
    if result:
        return result

    # Try question handling
    result = parse_question(q, query, error_msg, model)
    if result:
        return result

    # Default: clarification needed
    return {
        "intent": "clarification_needed",
        "question": "I'm having trouble understanding your command...",
        "context": {"partial_query": query},
        "meta": {"utterance": query, "fallback": True, "error": error_msg, "model_selected": model}
    }
```

**Changes to llm_daw.py:**
- Remove `_fallback_daw_parse()` function entirely
- Add import: `from nlp-service.parsers.fallback_parser import fallback_daw_parse`
- Update call in `interpret_daw_command()`: `return fallback_daw_parse(query, str(e), model_preference)`

**Testing:**
- Run full comprehensive NLP test suite
- Test all command types: mixer, device, questions
- Verify fallback behavior when LLM unavailable

---

### Phase 9: Simplify Main Entry Point (10 mins, Low Risk)

**Changes to llm_daw.py:**

Final `llm_daw.py` should be ~150 lines:

```python
"""Lightweight LLM-backed DAW command interpreter."""
from typing import Dict, Any
import os
import json

from config.llm_config import get_llm_project_id, get_default_model_name
from nlp-service.models.intent_types import Intent
from nlp-service.prompts.prompt_builder import build_daw_prompt
from nlp-service.fetchers.session_fetcher import fetch_session_devices
from nlp-service.fetchers.preset_fetcher import fetch_preset_devices, fetch_mixer_params
from nlp-service.parsers.fallback_parser import fallback_daw_parse

def interpret_daw_command(query: str,
                          model_preference: str | None = None,
                          strict: bool | None = None) -> Intent:
    """Interpret user query into DAW commands using Vertex AI if available."""

    # Fetch context: devices and mixer params
    known_devices = fetch_session_devices()
    if not known_devices:
        known_devices = fetch_preset_devices()

    mixer_params = fetch_mixer_params()
    if not mixer_params:
        mixer_params = ["volume", "pan", "mute", "solo", "send"]

    # Try LLM interpretation
    try:
        from google import genai
        from google.genai import types

        project = get_llm_project_id()
        location = os.getenv("GCP_REGION", "us-central1")
        model_name = get_default_model_name(model_preference)

        client = genai.Client(vertexai=True, project=project, location=location)
        prompt = build_daw_prompt(query, mixer_params, known_devices)

        config = types.GenerateContentConfig(
            temperature=0.1, max_output_tokens=512, top_p=0.8, top_k=20
        )

        resp = client.models.generate_content(
            model=model_name, contents=prompt, config=config
        )

        response_text = resp.text if hasattr(resp, 'text') else None
        if not response_text:
            raise RuntimeError("Empty LLM response")

        text = response_text.strip()
        start, end = text.find("{"), text.rfind("}")
        if start < 0 or end <= start:
            raise ValueError("No JSON found in response")

        result = json.loads(text[start:end + 1])
        result.setdefault("meta", {})["model_used"] = model_name
        return result

    except Exception as e:
        if strict is None:
            strict = os.getenv("LLM_STRICT", "").lower() in ("1", "true", "yes", "on")
        if strict:
            raise
        return fallback_daw_parse(query, str(e), model_preference)

# CLI entry point
if __name__ == "__main__":
    import argparse
    import sys
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except Exception:
        pass

    parser = argparse.ArgumentParser(description="Parse a DAW command and print JSON.")
    parser.add_argument("text", help="Command text in quotes")
    parser.add_argument("--model", dest="model", default=None, help="Model preference")
    args = parser.parse_args()

    result = interpret_daw_command(args.text, model_preference=args.model)
    print(json.dumps(result, ensure_ascii=False))
    sys.exit(0)
```

**Testing:**
- Run comprehensive NLP test suite
- Test CLI entry point
- Verify all imports work correctly

---

## Testing Strategy

### Unit Tests (Create New):

```python
# nlp-service/tests/test_hint_extractor.py
def test_extract_return_hint():
    hints = extract_llm_hints("set return A reverb decay to 2s")
    assert hints["track_hint"] == "Return A"
    assert hints["device_name_hint"] == "reverb"

def test_extract_device_ordinal():
    hints = extract_llm_hints("set return B reverb 2 decay to 2s")
    assert hints["device_ordinal_hint"] == 2

# nlp-service/tests/test_mixer_parser.py
def test_track_volume_absolute():
    result = parse_track_volume_absolute("set track 1 volume to -6 db", ...)
    assert result["intent"] == "set_parameter"
    assert result["targets"][0]["parameter"] == "volume"

# nlp-service/tests/test_device_parser.py
def test_return_device_param():
    result = parse_return_device_param("set return a reverb decay to 2s", ...)
    assert result["targets"][0]["plugin"] == "reverb"
```

### Integration Tests:

- Run existing comprehensive NLP test suite (28+ tests)
- Test all command types end-to-end
- Test LLM mode and fallback mode separately
- Test typo correction, ordinal expansion

### Regression Tests:

- Before refactoring: Run full test suite, save results
- After each phase: Run full test suite, compare with baseline
- Any failures: Fix immediately before proceeding

---

## Risk Mitigation

### Medium Risk Areas:

1. **Regex Pattern Changes**: Extracting patterns might introduce bugs
   - **Mitigation**: Copy exact regex patterns, no modifications during extraction
   - Test each parser function individually before integrating

2. **Import Circular Dependencies**: New modules might create cycles
   - **Mitigation**: Models → Parsers → Main (strict dependency hierarchy)
   - Use `TYPE_CHECKING` for type hints if needed

3. **Performance Regression**: More function calls might slow down fallback
   - **Mitigation**: Profile before/after with `cProfile`
   - Fallback parser is rarely used (LLM handles 95%+ of cases)

### Rollback Plan:

- Create git branch: `refactor/nlp-service-modularization`
- Commit after each phase completes successfully
- If tests fail: `git reset --hard` to previous phase
- Keep original llm_daw.py as llm_daw_backup.py until all tests pass

---

## Success Criteria

✅ All 28+ comprehensive NLP tests pass
✅ llm_daw.py reduced to ~150 lines
✅ All functions under 150 lines
✅ Clear module boundaries with single responsibilities
✅ Unit tests exist for each parser function
✅ No performance regression (< 5% slowdown acceptable)
✅ No change to external API (server endpoints unchanged)

---

## Timeline

| Phase | Task | Time | Risk |
|-------|------|------|------|
| 1 | Extract Models/Types | 30 min | Low |
| 2 | Extract Hint Extractor | 20 min | Low |
| 3 | Extract Prompt Builder | 30 min | Low |
| 4 | Extract Fetchers | 20 min | Low |
| 5 | Extract Typo Corrector | 15 min | Low |
| 6 | Extract Mixer Parser | 45 min | Medium |
| 7 | Extract Device Parser | 45 min | Medium |
| 8 | Extract Fallback Coordinator | 20 min | Low |
| 9 | Simplify Main Entry Point | 10 min | Low |
| **Total** | | **~4 hours** | **Medium** |

**Recommendation**: Execute Phases 1-5 in one session (low risk, ~2 hours), then Phases 6-9 in a second session after tests pass.

---

## Next Steps

**Option A**: Start Phase 1 now (extract models and types)
**Option B**: Review this plan, then execute when ready
**Option C**: Adjust plan based on feedback

**Recommended**: Option B - Review plan, then execute Phases 1-5 together (~2 hours, low risk)
