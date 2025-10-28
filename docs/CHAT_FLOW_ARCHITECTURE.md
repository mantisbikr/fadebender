# Chat Service Architecture

## Single Processing Path

**One source of truth: All commands go through the same unified NLP → Intent → Execution pipeline.**

This ensures WebUI and command-line tests behave identically.

---

## Flow Diagram

```
User Input: "set track 1 volme to -12 dB"
    ↓
Chat Service (/chat endpoint)
    ↓
    ┌─────────────────────────────────────────┐
    │ Step 1: NLP Service                     │
    │   - LLM First (Gemini Flash-Lite)       │
    │   - Handles typos: "volme" → "volume"   │
    │   - Natural language understanding      │
    │   - Regex fallback if LLM fails         │
    └─────────────────────────────────────────┘
    ↓
Intent (structured JSON)
    ↓
    ┌─────────────────────────────────────────┐
    │ Step 2: Intent Mapper                   │
    │   - Transforms to canonical format      │
    │   - Validates intent structure          │
    └─────────────────────────────────────────┘
    ↓
Canonical Intent
    ↓
    ┌─────────────────────────────────────────┐
    │ Step 3: Intent Executor                 │
    │   - Executes Ableton Live API calls     │
    │   - Fetches audio engineering context   │
    │   - Returns result with metadata        │
    └─────────────────────────────────────────┘
    ↓
Result with Audio Knowledge
```

**Latency:** ~1732ms (Gemini Flash-Lite)
**Typo Handling:** ✓ Native in LLM
**Accuracy:** 100% (tested with typos)
**Consistency:** WebUI = Command Line = Tests

---

## Inside NLP Service (llm_first mode)

The NLP service uses a two-tier approach:

```
┌──────────────────────────────────────────────────────┐
│ NLP Service (llm_first mode)                         │
│                                                       │
│  Tier 1: LLM (Gemini 2.5 Flash-Lite)                │
│    - Model: gemini-2.5-flash-lite                    │
│    - Latency: ~1732ms                                │
│    - Handles: typos, complex queries, NL             │
│    - Configured in: models.intent_parsing            │
│                                                       │
│  Tier 2: Regex Fallback (if LLM fails)              │
│    - Fast patterns (mixer_parser, device_parser)     │
│    - Latency: <10ms                                  │
│    - Handles: exact syntax patterns                  │
│    - Returns: intent with fallback=true              │
│                                                       │
└──────────────────────────────────────────────────────┘
```

**Priority:** LLM First → Regex Fallback

This is configured in `app_config.py`:
```json
{
  "nlp": {
    "mode": "llm_first"
  }
}
```

---

## Model Configuration

Models are configured per operation type in `app_config.py`:

```json
{
  "models": {
    "intent_parsing": "gemini-2.5-flash-lite",
    "audio_analysis": "gemini-2.5-flash",
    "context_analysis": "gemini-2.5-flash",
    "default": "gemini-2.5-flash"
  }
}
```

**Why Flash-Lite for intent parsing?**
- 1.55x faster than Flash (1732ms vs 2676ms)
- Same accuracy (100% with typos)
- 33% lower cost ($0.10 vs $0.15 per 1M tokens)

See `scripts/test_llama_vs_gemini.py` for benchmark results.

---

## Code Location

**Main handler:** `server/services/chat_service.py::handle_chat()`

```python
def handle_chat(body: ChatBody) -> Dict[str, Any]:
    """
    Handle chat commands through unified NLP → Intent → Execution path.

    This is the single source of truth for all command processing.
    Both WebUI and command-line tests use this same path.
    """
    # Step 1: Parse with NLP service
    intent = interpret_daw_command(text, model_preference=body.model)

    # Step 2: Transform to canonical format
    canonical, errors = map_llm_to_canonical(intent)

    # Step 3: Execute canonical intent
    result = execute_intent(canonical_intent)

    return result
```

**Total lines:** ~117 (simplified from 400+ in legacy version)

---

## Benefits

✅ **Single Source of Truth**
   - WebUI and CLI use identical path
   - Tests match production behavior exactly

✅ **Natural Typo Correction**
   - "volme", "vilme", "revreb" all work
   - No special typo dictionaries needed

✅ **Consistent Behavior**
   - All commands processed the same way
   - Predictable latency and accuracy

✅ **Maintainable**
   - No duplicate logic
   - Easy to debug (one path)
   - Clear code structure

✅ **Audio Knowledge Always Included**
   - Parameter capabilities from Firestore
   - Audio engineering context
   - Professional guidance

✅ **Future-Proof**
   - Easy to swap models (per operation)
   - Can add new intent types easily
   - Extensible architecture

---

## Example: Typo Handling

### Input: "set track 1 volme to -12 dB"

**Processing:**
```
1. Chat service receives command
2. NLP service (llm_first):
   - LLM (Gemini Flash-Lite) parses
   - Recognizes "volme" as typo
   - Returns: {intent: "set_parameter", parameter: "volume", value: -12}
3. Intent mapper transforms to canonical format
4. Executor sets volume, fetches audio context
5. Returns success with audio knowledge
```

**Result:**
```json
{
  "ok": true,
  "summary": "Set Track 1 volume to -12 dB",
  "data": {
    "capabilities": {
      "audio_knowledge": "Reduces perceived loudness; creates headroom...",
      "range": "-inf to 6.0 dB",
      "unit": "dB"
    }
  }
}
```

---

## Testing

All tests use the same path as production:

### Command Line Tests
```bash
python3 scripts/test_nlp_get_comprehensive.py
```

### Benchmark Tests
```bash
python3 scripts/test_llama_vs_gemini.py
```

### Integration Tests
WebUI `/chat` endpoint uses `handle_chat()` directly.

**Result:** Command line tests = WebUI behavior ✓

---

## Performance

From `test_llama_vs_gemini.py` results:

| Metric | Gemini Flash | Flash-Lite |
|--------|--------------|------------|
| Avg Latency | 2676ms | 1732ms |
| Speedup | 1.0x | **1.55x** |
| Success Rate | 100% | 100% |
| Cost/1M input | $0.15 | **$0.10** |

**Recommendation:** Use Flash-Lite for intent parsing (default)

---

## Configuration

### Verify Current Config

```bash
python3 scripts/verify_model_config.py
```

Shows:
- Model for each operation type
- Environment variable overrides
- Effective model being used

### Change Models

Edit `configs/app_config.json`:
```json
{
  "models": {
    "intent_parsing": "gemini-2.5-flash-lite",  // Fast
    "audio_analysis": "gemini-2.5-pro",          // Accurate
    "default": "gemini-2.5-flash"                // Balanced
  }
}
```

Or set environment variable (overrides config):
```bash
export VERTEX_MODEL=gemini-2.5-flash
```

---

## Troubleshooting

### Commands are slow

**Check which model is being used:**
```bash
python3 scripts/verify_model_config.py
```

Should show: `intent_parsing → gemini-2.5-flash-lite`

If using Flash instead of Flash-Lite, update config.

### Commands don't execute

**Check NLP mode:**
```python
from config.nlp_config import get_nlp_mode
print(get_nlp_mode())  # Should be: NLPMode.LLM_FIRST
```

**Check logs for errors:**
```bash
tail -f server.log
```

### Typos not handled

**This should never happen** - LLM handles all typos.

If it does:
1. Check that request reached NLP service
2. Verify LLM_PROJECT_ID is set
3. Check GCP credentials are valid

---

## Migration from Legacy Code

The legacy regex-based handler has been removed. If you have old code references:

**Old (removed):**
```python
# Legacy regex patterns in chat_service.py
m = re.search(r"set\s+track\s+(\d+)\s+(?:send\s+)?...", text)
```

**New (single path):**
```python
# Unified NLP path
intent = interpret_daw_command(text)
canonical = map_llm_to_canonical(intent)
result = execute_intent(canonical)
```

**Benefits of migration:**
- Typo handling works automatically
- No regex maintenance
- Consistent with tests

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────┐
│                     User Input                          │
│                  "set track 1 volme..."                 │
└────────────────────┬────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────────┐
│              Chat Service (handle_chat)                 │
│           Single source of truth - one path             │
└────────────────────┬────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────────┐
│                  NLP Service                            │
│  ┌───────────────────────────────────────────────────┐ │
│  │ Tier 1: LLM (Gemini 2.5 Flash-Lite)               │ │
│  │  - Typo correction                                │ │
│  │  - Natural language understanding                 │ │
│  │  - ~1732ms latency                                │ │
│  └───────────────────────────────────────────────────┘ │
│  ┌───────────────────────────────────────────────────┐ │
│  │ Tier 2: Regex Fallback (if LLM fails)            │ │
│  │  - Fast pattern matching                          │ │
│  │  - <10ms latency                                  │ │
│  └───────────────────────────────────────────────────┘ │
└────────────────────┬────────────────────────────────────┘
                     │
                     ↓
              Intent (JSON)
                     │
                     ↓
┌─────────────────────────────────────────────────────────┐
│              Intent Mapper                              │
│         Transform to canonical format                   │
└────────────────────┬────────────────────────────────────┘
                     │
                     ↓
           Canonical Intent
                     │
                     ↓
┌─────────────────────────────────────────────────────────┐
│             Intent Executor                             │
│  - Execute Ableton Live API                            │
│  - Fetch audio engineering context (Firestore)         │
│  - Add capabilities metadata                           │
└────────────────────┬────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────────┐
│          Result with Audio Knowledge                    │
│  {                                                      │
│    "ok": true,                                          │
│    "summary": "Set Track 1 volume to -12 dB",          │
│    "data": {                                            │
│      "capabilities": {                                  │
│        "audio_knowledge": "..."                         │
│      }                                                  │
│    }                                                    │
│  }                                                      │
└─────────────────────────────────────────────────────────┘
```

---

## Related Documentation

- **Model Configuration:** `docs/MODEL_CONFIGURATION.md`
- **Benchmark Results:** `scripts/test_llama_vs_gemini.py`
- **Model Verification:** `scripts/verify_model_config.py`
- **Intent System:** `docs/INTENT_SYSTEM.md`
