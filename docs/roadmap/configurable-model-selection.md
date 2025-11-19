# Configurable Model Selection - Enhancement

**Date:** 2025-11-18
**Status:** ✅ Complete

---

## Summary

Integrated Firebase Cloud Functions RAG system with existing `app_config.json` model configuration, enabling centralized model management across all services.

## Changes Made

### 1. Enhanced Configuration Loader

**File:** `functions/src/config.ts`

**Added:**
- `AppConfig` interface for `app_config.json` structure
- `loadAppConfig()` function to load and cache app config
- `getModelName(purpose)` function to get model name for specific purposes

**Usage:**
```typescript
const modelName = getModelName('help_assistant');
// Returns: "gemini-2.5-flash-lite" (from app_config.json)
```

### 2. Created Model Mapper

**File:** `functions/src/models.ts` [NEW]

**Purpose:** Maps model name strings to Genkit model instances

**Functions:**
- `getModel(purpose)` - Returns Genkit model instance
- `getModelDisplayName(purpose)` - Returns model name string

**Supported Models:**
- `gemini-2.5-flash` → Falls back to `gemini20FlashExp` (2.5 not yet in Genkit)
- `gemini-2.5-flash-lite` → Falls back to `gemini20FlashExp`
- `gemini-2.0-flash` → `gemini20FlashExp`
- `gemini-1.5-flash` → `gemini15Flash`
- `gemini-1.5-pro` → `gemini15Pro`

**Smart Fallback:**
- If Gemini 2.5 requested but not available → Uses Gemini 2.0 Flash Exp
- If unknown model → Falls back to Gemini 1.5 Flash
- Logs warnings for fallbacks

### 3. Updated Help Endpoint

**File:** `functions/src/help.ts`

**Changes:**
- Removed hardcoded `gemini15Flash` / `gemini15Pro` imports
- Now uses `getModel('help_assistant')` from models.ts
- Model selection driven by `app_config.json`
- Logs both configured and actual model used

**Before:**
```typescript
const model = config.useFlash ? gemini15Flash : gemini15Pro;
```

**After:**
```typescript
const model = getModel('help_assistant');
const modelName = getModelDisplayName('help_assistant');
```

---

## Configuration in app_config.json

The system now respects these model settings:

```json
{
  "models": {
    "help_assistant": "gemini-2.5-flash-lite",
    "intent_parsing": "gemini-2.5-flash-lite",
    "audio_analysis": "gemini-2.5-flash",
    "context_analysis": "gemini-2.5-flash",
    "default": "gemini-2.5-flash"
  }
}
```

### Model Purpose Mapping

| Purpose | Default Model | Use Case |
|---------|--------------|----------|
| `help_assistant` | gemini-2.5-flash-lite | /help endpoint queries |
| `intent_parsing` | gemini-2.5-flash-lite | NLP intent classification |
| `audio_analysis` | gemini-2.5-flash | Audio/mixing analysis |
| `context_analysis` | gemini-2.5-flash | Project context understanding |
| `default` | gemini-2.5-flash | Fallback for all purposes |

---

## Benefits

### 1. Centralized Configuration
- ✅ Single source of truth for all models (`app_config.json`)
- ✅ No need to change code to switch models
- ✅ Consistent across NLP service, Cloud Functions, etc.

### 2. Cost Optimization
- ✅ Use cheaper models (Flash Lite) for simple tasks
- ✅ Reserve expensive models (Pro) for complex analysis
- ✅ Easy to experiment with different models

### 3. Future-Proof
- ✅ When Gemini 2.5 becomes available in Genkit, just update the mapping
- ✅ When Gemini 3.0 releases, add to switch statement
- ✅ No code changes needed to switch models

### 4. Testing & Development
- ✅ Easy to test with different models
- ✅ Can use cheaper models in development
- ✅ Production can use best models

---

## Example Usage Scenarios

### Scenario 1: User Asks for Help

1. User: `POST /help` with query: "How do I set track volume?"
2. Cloud Function reads `app_config.json`
3. Finds `models.help_assistant = "gemini-2.5-flash-lite"`
4. `getModel('help_assistant')` returns `gemini20FlashExp` (fallback)
5. Response generated with that model
6. Logs show:
   ```
   configuredModel: "gemini-2.5-flash-lite"
   actualModel: "gemini-2.0-flash-experimental"
   ```

### Scenario 2: Switching to Expensive Model for Better Quality

**Edit `app_config.json`:**
```json
{
  "models": {
    "help_assistant": "gemini-1.5-pro"  // Changed from lite
  }
}
```

**Result:** All help queries now use Gemini 1.5 Pro (no code changes needed)

### Scenario 3: Cost Reduction

**Edit `app_config.json`:**
```json
{
  "models": {
    "help_assistant": "gemini-1.5-flash"  // Cheaper than 2.5
  }
}
```

**Result:** Immediate cost reduction (Flash is 10x cheaper than Pro)

---

## Migration Path for Future Endpoints

When adding new endpoints (e.g., `/chat`, `/intent`), use the same pattern:

```typescript
// In your new endpoint file
import { getModel, getModelDisplayName } from './models';

// For intent parsing
const intentModel = getModel('intent_parsing');

// For conversation
const chatModel = getModel('context_analysis');

// For audio analysis
const audioModel = getModel('audio_analysis');
```

---

## Model Availability Notes

### Gemini 2.5 (November 2024)
- **Status:** Announced but not yet in Genkit
- **Fallback:** System uses Gemini 2.0 Flash Exp
- **Action:** Monitor Genkit releases, update `models.ts` when 2.5 available

### Gemini 2.0 Flash
- **Status:** Available as experimental
- **Performance:** ~2x faster than 1.5 Flash
- **Cost:** Similar to 1.5 Flash

### Gemini 1.5 Flash/Pro
- **Status:** Stable, widely available
- **Reliability:** Production-ready
- **Fallback:** Used when newer models unavailable

---

## Testing

### Verify Model Selection

```bash
# Start emulator
cd functions
npm run build
firebase emulators:start

# Test help endpoint
curl -X POST http://localhost:5001/fadebender-dev/us-central1/help \
  -H "Content-Type: application/json" \
  -d '{"query": "test"}'

# Check Firebase Functions logs
# Should show:
# "configuredModel": "gemini-2.5-flash-lite"
# "actualModel": "gemini-2.0-flash-experimental"
```

### Change Model and Retest

1. Edit `configs/app_config.json`
2. Change `help_assistant` to `"gemini-1.5-flash"`
3. Restart emulator
4. Re-run curl command
5. Logs should show new model

---

## Files Changed

```
functions/src/
├── config.ts          [MODIFIED] - Added AppConfig interface and loader
├── models.ts          [NEW]      - Model mapping and selection
└── help.ts            [MODIFIED] - Uses getModel() instead of hardcoded

Total Changes:
- 1 new file
- 2 modified files
- ~120 lines added
```

---

## Next Steps

### Immediate
- [ ] Test with Firebase emulator
- [ ] Verify model selection works
- [ ] Check logs show correct model names

### Future Phases
- [ ] Add model selection to `/chat` endpoint (Phase 3)
- [ ] Add model selection to `/intent/parse` (when migrated)
- [ ] Monitor Genkit for Gemini 2.5 support
- [ ] Update `models.ts` when 2.5 available

---

## Resources

- **App Config:** `configs/app_config.json`
- **Model Mapper:** `functions/src/models.ts`
- **Config Loader:** `functions/src/config.ts`
- **Help Endpoint:** `functions/src/help.ts`
- **Genkit Models Docs:** https://firebase.google.com/docs/genkit/models

---

**Status:** ✅ Complete and ready for testing
