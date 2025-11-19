# RAG Feature Flags & Configuration

**Created:** 2025-11-19
**Status:** ✅ Implemented

## Overview

The `/help` endpoint now supports **feature-flagged RAG** with automatic fallback. You can toggle between Vertex AI Search (RAG) and LLM-only mode without changing code.

---

## Configuration File

**Location:** `configs/rag_config.json`

### Key Configuration Options

```json
{
  "rag": {
    "enabled": true,  // Master switch for RAG system

    "vertex_ai_search": {
      "enabled": true,              // Enable/disable Vertex AI Search
      "project_id": "487213218407",
      "location": "global",
      "engine_id": "fadebender-search",
      "data_store_id": "fadebender-knowledge",
      "serving_config": "default_search",
      "fallback_on_error": true,    // Auto-fallback if RAG fails
      "max_results": 5,              // Max search results to retrieve
      "min_relevance_score": 0.3     // Min relevance threshold
    }
  }
}
```

---

## How It Works

### Architecture

```
┌─────────────────┐
│  /help endpoint │
└────────┬────────┘
         │
         ▼
    ┌─────────┐
    │ Router  │ ◄─── Checks: rag.enabled & vertex_ai_search.enabled
    └────┬────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
┌─────────┐ ┌──────────┐
│ RAG Mode│ │ Fallback │
└─────────┘ └──────────┘
    │             │
    ▼             ▼
┌─────────┐   ┌──────┐
│ Vertex  │   │ LLM  │
│ Search  │   │ Only │
└─────────┘   └──────┘
```

### Mode Selection Logic

1. **Check `rag.enabled`**
   - `false` → Use Fallback Mode
   - `true` → Continue

2. **Check `vertex_ai_search.enabled`**
   - `false` → Use Fallback Mode
   - `true` → Use RAG Mode

3. **RAG Mode with Error Handling**
   - Try Vertex AI Search
   - If error + `fallback_on_error: true` → Use Fallback Mode
   - If error + `fallback_on_error: false` → Return error

---

## Usage Examples

### Example 1: RAG Enabled (Default)

**Config:**
```json
{
  "rag": {
    "enabled": true,
    "vertex_ai_search": {
      "enabled": true,
      "fallback_on_error": true
    }
  }
}
```

**Behavior:**
- Searches Vertex AI Search for relevant documents
- Generates response using LLM + search results
- Falls back to LLM-only if search fails

**Response:**
```json
{
  "response": "To set track volume in Fadebender...",
  "model_used": "gemini-1.5-flash",
  "mode": "rag",
  "sources": [
    {
      "title": "Mixer Controls",
      "snippet": "Set track volume using..."
    }
  ]
}
```

---

### Example 2: RAG Disabled (Fallback Mode)

**Config:**
```json
{
  "rag": {
    "enabled": true,
    "vertex_ai_search": {
      "enabled": false  // ◄── RAG disabled
    }
  }
}
```

**Behavior:**
- Skips Vertex AI Search entirely
- Generates response using LLM with basic prompt
- No knowledge base retrieval

**Response:**
```json
{
  "response": "To set track volume in Fadebender...",
  "model_used": "gemini-1.5-flash",
  "mode": "fallback",
  "sources": null
}
```

---

### Example 3: RAG with No Fallback (Strict Mode)

**Config:**
```json
{
  "rag": {
    "enabled": true,
    "vertex_ai_search": {
      "enabled": true,
      "fallback_on_error": false  // ◄── No fallback
    }
  }
}
```

**Behavior:**
- Attempts Vertex AI Search
- If search fails → Returns error (no fallback)
- Use this for debugging/testing RAG performance

---

## Testing Both Modes

### Test RAG Mode

```bash
# Enable RAG
# Edit configs/rag_config.json: vertex_ai_search.enabled = true

# Start emulator
cd functions
firebase emulators:start

# Test query
curl -X POST http://localhost:5001/fadebender/us-central1/help \
  -H "Content-Type: application/json" \
  -d '{"query": "how do I set track volume?"}'

# Check logs for:
# - "Using RAG help generator (Vertex AI Search)"
# - "mode": "rag"
# - "sources": [...]
```

### Test Fallback Mode

```bash
# Disable RAG
# Edit configs/rag_config.json: vertex_ai_search.enabled = false

# Restart emulator
firebase emulators:start

# Test query
curl -X POST http://localhost:5001/fadebender/us-central1/help \
  -H "Content-Type: application/json" \
  -d '{"query": "how do I set track volume?"}'

# Check logs for:
# - "Using fallback help generator (no RAG)"
# - "mode": "fallback"
# - "sources": null
```

---

## Code Structure

### New Files Created

1. **`functions/src/vertex-search.ts`**
   - Vertex AI Search API integration
   - Handles authentication, API calls, result parsing
   - `isVertexSearchEnabled()` - Feature flag check
   - `searchVertexAI(query)` - Main search function

2. **`functions/src/help-rag.ts`**
   - RAG mode implementation
   - Retrieves documents from Vertex AI Search
   - Builds context-enhanced prompts
   - `generateRAGHelp(query)` - RAG response generation

3. **`functions/src/help-fallback.ts`**
   - Fallback mode implementation
   - LLM-only responses (no RAG)
   - Basic prompt without knowledge base
   - `generateFallbackHelp(query)` - Fallback response generation

4. **`functions/src/help.ts` (Modified)**
   - Main router with feature flag logic
   - Routes between RAG and fallback modes
   - Error handling with automatic fallback
   - HTTP endpoint configuration

---

## Toggling Modes

### Quick Toggle Commands

**Enable RAG:**
```bash
# Edit configs/rag_config.json
sed -i '' 's/"enabled": false/"enabled": true/' configs/rag_config.json
```

**Disable RAG:**
```bash
# Edit configs/rag_config.json
sed -i '' 's/"enabled": true/"enabled": false/' configs/rag_config.json
```

**Restart is required after config changes:**
```bash
firebase emulators:start
```

---

## Monitoring & Debugging

### Check Which Mode Is Active

Look for these log messages:

**RAG Mode:**
```
Help mode selected: { useRAG: true, ... }
Using RAG help generator (Vertex AI Search)
Vertex AI Search results: { resultCount: 5, ... }
```

**Fallback Mode:**
```
Help mode selected: { useRAG: false, ... }
Using fallback help generator (no RAG)
```

**Fallback After Error:**
```
RAG help generation failed: { error: "...", willFallback: true }
Falling back to non-RAG help
Using fallback help generator (no RAG)
```

---

## Performance Comparison

| Mode | Latency | Cost | Quality (Relevance) |
|------|---------|------|---------------------|
| **RAG Mode** | ~1-2s | Higher (search + LLM) | ⭐⭐⭐⭐⭐ High |
| **Fallback Mode** | ~0.5-1s | Lower (LLM only) | ⭐⭐⭐ Medium |

---

## Next Steps

1. **Wait for Vertex AI Search indexing** to complete (~5-10 min)
2. **Test RAG mode** with various queries
3. **Compare results** between RAG and fallback modes
4. **Adjust configuration** based on results:
   - `max_results` - If responses are too broad/narrow
   - `min_relevance_score` - If results are not relevant enough
   - `fallback_on_error` - Enable/disable auto-fallback

---

## Related Documentation

- `docs/roadmap/vertex-ai-search-setup-complete.md` - Vertex AI Search setup details
- `docs/architecture/rag-firebase-studio-architecture.md` - Full RAG architecture
- `configs/rag_config.json` - Configuration file
