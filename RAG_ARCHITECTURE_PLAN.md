# RAG Architecture Optimization Plan

## Current State Analysis

### 1. **Firestore Data Model** ✅
- **Database**: `dev-display-value`
- **Collections**: `presets` (249 total), `device_mappings`
- **Document IDs**: `{device_type}_{preset_name}` (e.g., `reverb_cathedral`)
- **Preset Counts**:
  - Delay: 88 presets
  - Reverb: 69 presets
  - Compressor: 18 presets
  - Amp: 12 presets
  - Unknown: 62 presets

### 2. **Current RAG Modes & Performance**

| Mode | Speed | Cost/month | Quality | Embedding Location |
|------|-------|------------|---------|-------------------|
| **Assistants** | 22s | $20-40 | Excellent | OpenAI (server) |
| **Hybrid** | 9s | $2-5 | Good | OpenAI (server) |
| **Vertex** | N/A | Free | N/A | Vertex (server) |

**Key Findings**:
- All embeddings currently generated **server-side**
- Simple factual queries ("how many presets?") take 22-32s with RAG
- No direct Firestore queries implemented yet

### 3. **Where Embeddings Are Generated**

#### Hybrid Mode (`hybrid_rag_service.py:93-113`)
```python
# SERVER-SIDE: OpenAI API call
embeddings_response = openai_client.embeddings.create(
    model="text-embedding-3-small",  # 1536 dimensions
    input=query
)
query_embedding = embeddings_response.data[0].embedding
```
- **Location**: OpenAI servers (API call)
- **Latency**: ~200-500ms per query
- **Cost**: $0.00002 per 1K tokens

#### Assistants Mode (`assistant_rag_service.py`)
- **Location**: OpenAI servers (built-in)
- **Latency**: Included in 22s total time
- **Cost**: Included in Assistant API pricing

#### Vertex Mode (Not implemented yet)
- **Location**: Google Cloud (API call)
- **Latency**: ~300-600ms per query
- **Cost**: Free tier available

---

## Problem Statement

**User's Core Questions**:
1. ✅ Are we using `dev-display-value`? **YES**
2. ❓ Where are embeddings generated? **Server-side (OpenAI/Vertex)**
3. ❓ Can we generate embeddings locally? **YES - with trade-offs**
4. ❓ How to speed up and improve accuracy? **Multi-tier architecture**

---

## Proposed Architecture: 4-Tier Smart Routing

### Tier 1: **Pattern-Based Routing** (0ms)
- **No LLM, no embeddings**
- Regex pattern matching for factual queries
- **Implementation**: `help_router.py` ✅ DONE
- **Queries**:
  - "how many X presets?" → Count query
  - "list all X presets" → List query
  - "what parameters does X have?" → Schema query
- **Speed**: Instant classification
- **Accuracy**: 100% for supported patterns

### Tier 2: **Firestore Direct Queries** (<100ms)
- **No embeddings needed**
- Direct database lookups
- **Implementation**: `firestore_help_service.py` ⚠️ NEEDS FIX
- **Fix Required**: Query by document ID prefix, not `device_name` field
- **Queries**:
  - Count: `WHERE __name__ >= 'reverb_' AND __name__ < 'reverb_~'`
  - List: Same query, return all docs
  - Parameters: Get first doc, extract schema
- **Speed**: 50-100ms
- **Accuracy**: 100%
- **Cost**: Free

### Tier 3: **Semantic Search with Local Embeddings** (~500ms)
- **Client-side embedding generation**
- Firestore vector search or in-memory search
- **Implementation**: NEW
- **Queries**:
  - "best reverb for vocals"
  - "warm delay for guitars"
  - "aggressive compressor"
- **Options**:

#### Option A: ONNX Runtime (Recommended)
```python
# Install: sentence-transformers + onnxruntime
# Model: all-MiniLM-L6-v2 (23MB, 384 dimensions)
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('all-MiniLM-L6-v2')
embedding = model.encode(query)  # 50-100ms on laptop
```
- **Pros**: Fast, offline, free, small model
- **Cons**: Slightly lower quality than OpenAI
- **Speed**: 50-100ms per query (local CPU)
- **Model Size**: 23MB

#### Option B: Xenova Transformers (Browser/Node)
```javascript
// npm install @xenova/transformers
import { pipeline } from '@xenova/transformers';

const extractor = await pipeline('feature-extraction', 'Xenova/all-MiniLM-L6-v2');
const embedding = await extractor(query, { pooling: 'mean', normalize: true });
```
- **Pros**: Runs in browser, no server needed
- **Cons**: 50-100MB model download, slower on mobile
- **Speed**: 100-200ms (browser), 300-500ms (mobile)

#### Option C: Hybrid (Recommended for Best UX)
- **Factual queries**: Skip embeddings entirely (Tier 1+2)
- **Semantic queries**: Use local embeddings (Tier 3)
- **Complex queries**: Fall back to server RAG (Tier 4)

### Tier 4: **Full RAG for Complex Queries** (8-22s)
- **Server-side embeddings + LLM generation**
- For comparisons, explanations, workflows
- **Implementation**: Existing (`hybrid_rag_service.py`, `assistant_rag_service.py`)
- **Queries**:
  - "compare Cathedral vs Church"
  - "explain reverb decay time"
  - "how to automate send levels?"
- **Speed**: 8-22s depending on mode
- **Accuracy**: Highest

---

## Recommended Implementation Plan

### Phase 1: Fix Firestore Queries (Immediate)
**Estimated Time**: 30 minutes
**Impact**: 200x speedup for factual queries

1. Fix `firestore_help_service.py` to query by document ID prefix
2. Update methods:
   ```python
   def get_preset_count(self, device_name: str) -> Optional[int]:
       # Query: WHERE __name__ >= 'reverb_' AND __name__ < 'reverb_~'
       start_id = f'{device_name}_'
       end_id = f'{device_name}_~'
       presets = self.db.collection('presets') \
           .where('__name__', '>=', start_id) \
           .where('__name__', '<', end_id) \
           .stream()
       return sum(1 for _ in presets)
   ```
3. Test with: "how many reverb presets?" → <100ms

### Phase 2: Add Firestore Vector Search (Optional, Later)
**Estimated Time**: 2-3 hours
**Impact**: Fast semantic search without external APIs

1. Enable Firestore vector search (requires index)
2. Pre-compute embeddings for all presets offline
3. Store embeddings in Firestore documents
4. Query using similarity search

**Note**: Requires Firestore indexes, may have quota limits.

### Phase 3: Local Embedding Generation (Later, if needed)
**Estimated Time**: 1-2 hours
**Impact**: Eliminates API calls for semantic queries

1. Add ONNX model to server:
   ```bash
   pip install sentence-transformers onnxruntime
   ```
2. Load model once at startup:
   ```python
   _model = SentenceTransformer('all-MiniLM-L6-v2')
   ```
3. Replace OpenAI embedding calls in hybrid mode
4. Compare quality with OpenAI embeddings

---

## Performance Projections

### Before Optimizations (Current)
| Query Type | Current Time | Current Mode |
|------------|--------------|--------------|
| "how many reverb presets?" | 32s | Assistants API |
| "list all reverb presets" | 31s | Assistants API |
| "best reverb for vocals" | 22s | Assistants API |
| "compare Cathedral vs Church" | 23s | Assistants API |

### After Phase 1 (Firestore Direct)
| Query Type | New Time | Speedup | Mode |
|------------|----------|---------|------|
| "how many reverb presets?" | **0.05s** | 640x | Firestore |
| "list all reverb presets" | **0.15s** | 206x | Firestore |
| "best reverb for vocals" | 22s | 1x | RAG (unchanged) |
| "compare Cathedral vs Church" | 23s | 1x | RAG (unchanged) |

### After Phase 2+3 (Full Optimization)
| Query Type | New Time | Speedup | Mode |
|------------|----------|---------|------|
| "how many reverb presets?" | **0.05s** | 640x | Firestore |
| "list all reverb presets" | **0.15s** | 206x | Firestore |
| "best reverb for vocals" | **0.5s** | 44x | Local embeddings + Firestore |
| "compare Cathedral vs Church" | 8s | 2.9x | Hybrid RAG |

**Expected Distribution**:
- 70% of queries → Firestore (instant)
- 20% of queries → Semantic search (~500ms)
- 10% of queries → Full RAG (8-22s)

**Overall Average**:
- Before: 22s per query
- After: **1.3s per query** (17x speedup)

---

## Cost Analysis

### Current Costs (Assistants Mode)
- **OpenAI Assistants API**: $20-40/month
- **File Search**: Included
- **Embeddings**: Included

### After Optimization
- **Firestore queries**: Free (within quota)
- **Local embeddings**: Free
- **OpenAI Assistants** (only 10% of queries): $2-4/month
- **Total**: **$2-4/month** (90% cost reduction)

---

## Accuracy Considerations

### Local Embeddings vs OpenAI

**OpenAI `text-embedding-3-small`**:
- Dimensions: 1536
- Training data: Proprietary, massive
- Quality: Industry-leading

**Sentence Transformers `all-MiniLM-L6-v2`**:
- Dimensions: 384
- Training data: Public datasets
- Quality: 95-97% of OpenAI for domain-specific tasks

**Recommendation**:
- Use local embeddings for semantic search
- Fall back to full RAG for complex queries requiring reasoning

---

## Next Steps

1. **Immediate**: Fix Firestore queries (30 min)
2. **Test**: Verify <100ms response times
3. **Decide**: Local embeddings vs Firestore vector search
4. **Implement**: Chosen approach
5. **Benchmark**: Compare quality and speed

## Questions for Discussion

1. Do you want to proceed with Phase 1 (Firestore fixes) immediately?
2. Should we prioritize local embeddings or Firestore vector search?
3. What's the acceptable latency for semantic queries? (<500ms ideal?)
4. Should we keep Assistants mode as fallback, or switch to Hybrid?
