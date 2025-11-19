# RAG + Firebase Studio Architecture for Fadebender

**Status:** 🟡 In Planning
**Last Updated:** 2025-11-18
**Owner:** Architecture Team

---

## Executive Summary

Fadebender will implement an intelligent help and conversational assistant system using Firebase Studio RAG (Retrieval Augmented Generation) combined with Genkit for serverless AI flows. This architecture supports:

- **Semantic knowledge retrieval** from curated documentation
- **Project-aware assistance** with live Ableton state injection
- **Multi-turn conversations** with state management
- **Device/preset discovery** with incremental knowledge building
- **Serverless-first** for cost efficiency and auto-scaling

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Technology Stack](#technology-stack)
3. [Data Architecture](#data-architecture)
4. [RAG Strategy](#rag-strategy)
5. [Conversation Flow](#conversation-flow)
6. [Project Context Injection](#project-context-injection)
7. [Device Knowledge Integration](#device-knowledge-integration)
8. [Serverless Architecture](#serverless-architecture)
9. [Implementation Phases](#implementation-phases)
10. [Configuration Management](#configuration-management)
11. [Cost Analysis](#cost-analysis)
12. [Risks and Mitigations](#risks-and-mitigations)

---

## Architecture Overview

### High-Level System Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                      User's Browser                         │
│                   (React Chat Interface)                    │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│              Cloud Functions (Serverless)                   │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────────┐  │
│  │ /intent/parse│  │    /chat     │  │  /help (simple) │  │
│  │              │  │              │  │                 │  │
│  │  Regex/LLM   │  │  Genkit +    │  │  Firebase Studio│  │
│  │              │  │  Conversation│  │  RAG Only       │  │
│  └──────────────┘  └──────────────┘  └─────────────────┘  │
│                           │                                 │
│                           ▼                                 │
│         ┌──────────────────────────────────────┐           │
│         │     Firebase Studio RAG Engine       │           │
│         │  - Vector embeddings                 │           │
│         │  - Semantic retrieval                │           │
│         │  - Auto-reindexing                   │           │
│         └──────────────────────────────────────┘           │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                  Firestore Database                         │
│                                                             │
│  Collections:                                               │
│  - conversations/{userId}/sessions/{sessionId}              │
│  - device_mappings/{device_signature}                       │
│  - presets/{preset_id}                                      │
│  - user_projects/{userId}/snapshots/{snapshot_id}           │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│          Firebase Realtime Database (Command Queue)         │
│                                                             │
│  Real-time bidirectional communication:                     │
│  - Cloud → Local: Commands to execute                       │
│  - Local → Cloud: Project state updates                     │
└───────────────────────┬─────────────────────────────────────┘
                        │ (listener)
                        ▼
┌─────────────────────────────────────────────────────────────┐
│            Local Server :8722 (User's Machine)              │
│                                                             │
│  - Listens to Firebase Realtime DB                          │
│  - Executes commands against Ableton Live                   │
│  - Pushes project state snapshots to Firestore              │
│  - Streams real-time parameter changes                      │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│              Ableton Live + Remote Script                   │
└─────────────────────────────────────────────────────────────┘
```

---

## Technology Stack

### Core Technologies

| Component | Technology | Purpose |
|-----------|-----------|---------|
| RAG Engine | Firebase Studio | Vector embeddings, semantic retrieval |
| AI Flows | Genkit | Serverless AI orchestration, conversation mgmt |
| Serverless Compute | Cloud Functions (2nd gen) | Intent parsing, chat, help endpoints |
| Database | Firestore | Conversation state, device mappings, presets |
| Real-time Sync | Firebase Realtime DB | Command queue, project state streaming |
| LLM | Gemini 1.5 Pro/Flash | Response generation, intent classification |
| Embeddings | Google text-embedding-004 | Semantic search via Firebase Studio |

### Development Tools

| Tool | Purpose |
|------|---------|
| Firebase CLI | Deployment, emulator, testing |
| Genkit CLI | Flow development, testing |
| TypeScript | Type-safe cloud functions |
| Vitest | Testing framework |

---

## Data Architecture

### Firebase Studio Knowledge Base Structure

```
knowledge/
├── fadebender/
│   ├── user-guide.md                    [✓ Exists]
│   ├── device-catalog.md                [⏳ To Generate]
│   └── preset-catalog.md                [⏳ To Generate]
├── ableton-live/
│   ├── live-concepts.md                 [✓ Exists]
│   ├── routing-fundamentals.md          [✓ Exists]
│   └── session-vs-arrangement.md        [✓ Exists]
└── audio-fundamentals/
    ├── mixing-basics.md                 [✓ Exists]
    ├── compression-guide.md             [✓ Exists]
    ├── eq-fundamentals.md               [✓ Exists]
    └── reverb-and-delay.md              [✓ Exists]
```

**Status Key:**
- ✓ Exists and ready for RAG indexing
- ⏳ To be generated from Firestore data
- ⏹ Not yet created

### Firestore Schema

#### Conversations Collection

```typescript
conversations/{userId}/sessions/{sessionId}
{
  session_id: string,
  user_id: string,
  created_at: Timestamp,
  last_updated: Timestamp,
  status: 'active' | 'completed' | 'waiting_user_input',

  // Multi-turn conversation history
  conversation_history: [
    {
      role: 'user' | 'assistant',
      content: string,
      timestamp: Timestamp,
      context_used?: {
        knowledge_chunks: string[],  // RAG doc IDs
        project_scope: string,        // 'minimal' | 'single_track' | 'full_project'
        tracks_analyzed?: number[]
      }
    }
  ],

  // Cached project analysis (persists across turns)
  project_analysis?: {
    last_snapshot: Timestamp,
    routing_graph: object,
    identified_issues: object[],
    full_details_loaded: boolean,
    detailed_tracks: number[]
  },

  // Pending intents awaiting confirmation
  pending_intents: [
    {
      type: string,
      action: string,
      targets: string[],
      reasoning: string
    }
  ]
}
```

#### Device Mappings Collection (Enhanced for RAG)

```typescript
device_mappings/{device_signature}
{
  device_name: string,
  device_signature: string,
  device_type: string,

  // Structured data (existing)
  parameters: {
    [param_name]: {
      min: number,
      max: number,
      unit: string,
      type: string
    }
  },
  parameter_groups: object,

  // RAG-friendly metadata (NEW)
  description: string,
  sonic_character: string,
  use_cases: string[],
  key_parameters: {
    [param_name]: {
      description: string,
      typical_range: string
    }
  },
  tips: string[],

  // RAG management
  include_in_rag: boolean,
  last_rag_sync: Timestamp
}
```

#### Presets Collection (Enhanced for RAG)

```typescript
presets/{preset_id}
{
  preset_name: string,
  device: string,
  device_signature: string,
  structure_signature: string,

  // Exact parameter values (existing)
  values: {
    [param_name]: number
  },

  // RAG-friendly metadata (NEW)
  description: string,
  use_case: string,
  genre_tags: string[],
  characteristics: string[],
  parameter_summary: string,  // High-level description

  // Preset management
  created_by: string,
  is_public: boolean,
  include_in_rag: boolean,
  last_rag_sync: Timestamp
}
```

#### Project Snapshots (for Context Injection)

```typescript
user_projects/{userId}/snapshots/{snapshot_id}
{
  snapshot_id: string,
  timestamp: Timestamp,

  // Lightweight summary (always cached)
  summary: {
    track_count: number,
    scene_count: number,
    return_count: number,
    track_names: string[],
    track_types: ('audio' | 'midi')[]
  },

  // Device structure (cached)
  device_structure: {
    [track_index]: {
      devices: string[],  // Device names
      device_signatures: string[]
    }
  },

  // Routing graph (cached)
  routing_graph: {
    [track_id]: {
      sends_to: string[],
      receives_from: string[]
    }
  },

  // Full parameter details (stored in Cloud Storage, linked)
  full_details_uri?: string  // gs://bucket/user_id/snapshot_id.json
}
```

---

## RAG Strategy

### Two-Tier Retrieval Architecture

#### Tier 1: Semantic Retrieval (Firebase Studio RAG)

**Purpose:** Discover relevant concepts, devices, techniques, workflows

**Data Sources:**
- Static knowledge markdown files
- Device catalog (high-level capabilities)
- Preset catalog (use cases and characteristics)
- Audio fundamentals
- Ableton Live concepts

**Query Examples:**
- "How do I make my mix less muddy?"
- "What devices are good for vocal compression?"
- "Explain send routing in Ableton"

**Retrieval Process:**
```typescript
const ragDocs = await firebaseStudio.retrieve(query, {
  sources: [
    'knowledge/fadebender/**/*.md',
    'knowledge/ableton-live/**/*.md',
    'knowledge/audio-fundamentals/**/*.md'
  ],
  topK: 5,
  minRelevanceScore: 0.7
});
```

#### Tier 2: Structured Lookup (Firestore Direct Query)

**Purpose:** Get exact parameter values, device structures, preset details

**Data Sources:**
- device_mappings collection (exact parameter specs)
- presets collection (exact values)
- user_projects snapshots (current project state)

**Query Examples:**
- "Load warm vocal reverb" → Lookup preset exact values
- "What parameters does Glue Compressor have?" → Lookup device mapping

**Retrieval Process:**
```typescript
// Detect entities needing exact lookup
const entities = extractEntities(query);

if (entities.preset) {
  const preset = await firestore
    .collection('presets')
    .where('preset_name', '==', entities.preset)
    .get();
}
```

### Hybrid Query Strategy

Most queries use **both tiers**:

```typescript
const handleQuery = async (query, userId) => {
  // Parallel retrieval
  const [ragDocs, exactData] = await Promise.all([
    // Tier 1: Semantic understanding
    firebaseStudio.retrieve(query),

    // Tier 2: Exact data (if entities detected)
    getExactData(query, userId)
  ]);

  // Combine in prompt
  const prompt = buildPrompt({
    knowledge: ragDocs,
    exact: exactData,
    projectContext: await getProjectContext(userId, query)
  });

  return await llm.generate(prompt);
};
```

---

## Conversation Flow

### Genkit Conversation Flow Implementation

```typescript
import { defineFlow } from '@genkit-ai/flow';
import { onFlow } from '@genkit-ai/firebase/functions';
import { gemini15Pro } from '@genkit-ai/googleai';

export const chatFlow = onFlow(
  {
    name: 'fadebenderChat',
    inputSchema: z.object({
      userId: z.string(),
      sessionId: z.string().optional(),
      message: z.string()
    }),
    outputSchema: z.object({
      response: z.string(),
      sessionId: z.string(),
      needsClarification: z.boolean(),
      suggestedIntents: z.array(z.any()).optional(),
      projectAnalysis: z.any().optional()
    })
  },
  async ({ userId, sessionId, message }) => {
    // 1. Load or create session
    const session = sessionId
      ? await loadSession(userId, sessionId)
      : await createSession(userId);

    // 2. Determine analysis scope
    const analysisScope = await determineScope(message, session);

    // 3. Parallel context retrieval
    const [ragDocs, projectContext] = await Promise.all([
      retrieveKnowledge(message),        // Firebase Studio
      getProjectContext(userId, analysisScope) // Firestore + Realtime DB
    ]);

    // 4. Project analysis (if needed)
    let projectAnalysis = session.project_analysis;
    if (analysisScope.needsAnalysis && !projectAnalysis) {
      projectAnalysis = await analyzeProject(projectContext);
      session.project_analysis = projectAnalysis; // Cache for next turn
    }

    // 5. Build conversational prompt
    const prompt = buildConversationalPrompt({
      knowledge: ragDocs,
      projectContext,
      projectAnalysis,
      conversationHistory: session.conversation_history,
      currentMessage: message
    });

    // 6. Generate response
    const response = await generate({
      model: gemini15Pro,
      prompt,
      config: { temperature: 0.7, maxOutputTokens: 2048 }
    });

    // 7. Parse for intents/clarifications
    const parsed = await parseAssistantResponse(response.text);

    // 8. Update session
    session.conversation_history.push(
      { role: 'user', content: message, timestamp: new Date() },
      {
        role: 'assistant',
        content: response.text,
        timestamp: new Date(),
        context_used: {
          knowledge_chunks: ragDocs.map(d => d.id),
          project_scope: analysisScope.depth
        }
      }
    );

    if (parsed.suggestedIntents) {
      session.pending_intents = parsed.suggestedIntents;
    }

    await saveSession(session);

    return {
      response: response.text,
      sessionId: session.session_id,
      needsClarification: parsed.needsClarification,
      suggestedIntents: parsed.suggestedIntents,
      projectAnalysis: projectAnalysis
    };
  }
);
```

---

## Project Context Injection

### Progressive Loading Strategy

**Principle:** Don't load entire project upfront. Load based on query needs.

```typescript
const determineScope = async (query: string, session: Session) => {
  // Quick intent classification
  const intent = await classifyIntent(query);

  return {
    depth: intent.analysisDepth,
    // 'minimal' | 'single_track' | 'routing_chain' | 'full_project'

    needsAnalysis: intent.requiresProjectAnalysis,
    targetTracks: intent.targetTracks,
    targetDevices: intent.targetDevices
  };
};

const getProjectContext = async (userId: string, scope: Scope) => {
  switch (scope.depth) {
    case 'minimal':
      // Just current selection
      return {
        current_track: await getCurrentTrack(userId),
        scope: 'minimal'
      };

    case 'single_track':
      // One track with devices
      return {
        track: await getTrackDetails(userId, scope.targetTracks[0]),
        routing: await getTrackRouting(userId, scope.targetTracks[0]),
        scope: 'single_track'
      };

    case 'routing_chain':
      // Follow the signal flow
      return {
        source_tracks: await getTracks(userId, scope.targetTracks),
        return_tracks: await getReturns(userId),
        routing_graph: await buildRoutingGraph(userId),
        scope: 'routing_chain'
      };

    case 'full_project':
      // Everything (expensive, cached aggressively)
      const snapshot = await getOrCreateSnapshot(userId);
      return {
        summary: snapshot.summary,
        device_structure: snapshot.device_structure,
        routing_graph: snapshot.routing_graph,
        // Full details only if really needed
        full_details: scope.needsFullDetails
          ? await loadFullDetails(snapshot.full_details_uri)
          : null,
        scope: 'full_project'
      };
  }
};
```

### Context Size Management

**Problem:** Large projects = huge context = high LLM costs + latency

**Solution:** Smart filtering and summarization

```typescript
const optimizeContext = (projectContext: any, query: string) => {
  // Only include relevant parts
  const filtered = {
    ...projectContext,

    // Summarize track list if > 10 tracks
    tracks: projectContext.tracks.length > 10
      ? summarizeTracks(projectContext.tracks)
      : projectContext.tracks,

    // Only include device details for mentioned devices
    devices: filterRelevantDevices(projectContext.devices, query),

    // Compress parameter values (ranges instead of exact)
    parameters: compressParameters(projectContext.parameters)
  };

  return filtered;
};
```

---

## Device Knowledge Integration

### Incremental Knowledge Building

**Status Tracking in configs/rag_config.json:**

```json
{
  "rag": {
    "enabled": true,
    "firebase_studio": {
      "project_id": "fadebender",
      "data_sources": {
        "knowledge_base": "knowledge/**/*.md",
        "device_catalog": "knowledge/fadebender/device-catalog.md",
        "preset_catalog": "knowledge/fadebender/preset-catalog.md"
      }
    },

    "device_signatures": {
      "enabled_for_rag": [
        "AudioEffectGroupDevice:Reverb"
      ],
      "in_progress": [
        "AudioEffectGroupDevice:Compressor",
        "AudioEffectGroupDevice:EQ Eight"
      ],
      "planned": [
        "AudioEffectGroupDevice:Glue Compressor",
        "AudioEffectGroupDevice:Delay"
      ]
    },

    "structure_signatures": {
      "enabled_for_rag": [
        "reverb_v1"
      ],
      "in_progress": [],
      "planned": [
        "compressor_v1",
        "eq_eight_v1"
      ]
    },

    "auto_generation": {
      "device_catalog": {
        "enabled": true,
        "sources": ["device_mappings"],
        "output": "knowledge/fadebender/device-catalog.md"
      },
      "preset_catalog": {
        "enabled": true,
        "sources": ["presets"],
        "filter": {
          "is_public": true,
          "include_in_rag": true
        },
        "output": "knowledge/fadebender/preset-catalog.md"
      }
    }
  }
}
```

### Device Catalog Generation Script

**Status:** ⏳ To Be Created

**Location:** `scripts/generate-rag-catalogs.ts`

```typescript
import { firestore } from './firebase-admin';
import fs from 'fs';
import { loadConfig } from './config-loader';

const generateDeviceCatalog = async () => {
  const config = await loadConfig('configs/rag_config.json');
  const enabledSignatures = config.rag.device_signatures.enabled_for_rag;

  let markdown = '# Fadebender Device Catalog\n\n';
  markdown += 'Comprehensive guide to supported Ableton Live devices.\n\n';
  markdown += `**Last Generated:** ${new Date().toISOString()}\n\n`;
  markdown += '---\n\n';

  for (const signature of enabledSignatures) {
    const deviceDoc = await firestore
      .collection('device_mappings')
      .doc(signature)
      .get();

    if (!deviceDoc.exists) continue;

    const device = deviceDoc.data();

    markdown += `## ${device.device_name}\n\n`;
    markdown += `**Device Signature:** \`${signature}\`\n\n`;

    if (device.description) {
      markdown += `**Description:** ${device.description}\n\n`;
    }

    if (device.sonic_character) {
      markdown += `**Sonic Character:** ${device.sonic_character}\n\n`;
    }

    if (device.use_cases?.length) {
      markdown += `**Common Use Cases:**\n`;
      device.use_cases.forEach(useCase => {
        markdown += `- ${useCase}\n`;
      });
      markdown += '\n';
    }

    if (device.key_parameters) {
      markdown += `**Key Parameters:**\n\n`;
      Object.entries(device.key_parameters).forEach(([param, info]) => {
        markdown += `### ${param}\n`;
        markdown += `${info.description}\n\n`;
        if (info.typical_range) {
          markdown += `**Typical Range:** ${info.typical_range}\n\n`;
        }
      });
    }

    if (device.tips?.length) {
      markdown += `**Tips & Tricks:**\n`;
      device.tips.forEach(tip => {
        markdown += `- ${tip}\n`;
      });
      markdown += '\n';
    }

    markdown += '---\n\n';
  }

  fs.writeFileSync(config.rag.auto_generation.device_catalog.output, markdown);
  console.log(`✓ Device catalog generated with ${enabledSignatures.length} devices`);
};

const generatePresetCatalog = async () => {
  // Similar implementation for presets
  // Groups by device, includes descriptions and use cases
};

// Main execution
if (require.main === module) {
  generateDeviceCatalog().then(() => generatePresetCatalog());
}
```

### Workflow: Adding New Device to RAG

1. **Complete device mapping in Firestore**
   - Add parameter structure
   - Add RAG metadata (description, use_cases, tips)

2. **Update rag_config.json**
   ```json
   "device_signatures": {
     "enabled_for_rag": [
       "AudioEffectGroupDevice:Reverb",
       "AudioEffectGroupDevice:Compressor"  // ← Add here
     ]
   }
   ```

3. **Generate device catalog**
   ```bash
   npm run generate:rag-catalogs
   ```

4. **Firebase Studio auto-reindexes**
   - Watches knowledge/ directory
   - Detects new device-catalog.md content
   - Generates embeddings
   - Ready for retrieval

5. **Test in /help or /chat**
   ```
   User: "What's good for compression?"
   → RAG retrieves Compressor device info
   → Returns description, use cases, tips
   ```

---

## Serverless Architecture

### Why Serverless for Fadebender

**Usage Pattern:**
- Intermittent commands (not constant streaming)
- Bursty traffic (user sends command → idle → next command)
- Variable user activity
- Perfect for serverless cost model

### Cloud Functions Endpoints

```typescript
// functions/src/index.ts

// Simple help (RAG only, no conversation state)
export const help = onRequest(async (req, res) => {
  const { query } = req.body;

  const ragDocs = await firebaseStudio.retrieve(query);
  const response = await llm.generate({
    prompt: buildHelpPrompt(ragDocs, query)
  });

  res.json({ response });
});

// Intent parsing (existing, serverless migration)
export const parseIntent = onRequest(async (req, res) => {
  const { command } = req.body;

  // Regex-first, LLM fallback
  const intent = await intentParser.parse(command);

  res.json({ intent });
});

// Conversational chat (Genkit flow)
export const chat = onFlow(chatFlow); // Defined earlier

// Device catalog generation (scheduled)
export const generateCatalogs = onSchedule(
  'every 24 hours',
  async () => {
    await generateDeviceCatalog();
    await generatePresetCatalog();
  }
);
```

### Cost Optimization

**Estimated costs (per 1000 users/month):**

| Operation | Frequency | Cost/Op | Monthly Cost |
|-----------|-----------|---------|--------------|
| Intent Parse | 50k/month | $0.0004 | $20 |
| Help Query | 5k/month | $0.003 | $15 |
| Chat (3-turn avg) | 2k sessions | $0.015/session | $30 |
| Firestore Reads | 100k/month | $0.0006/100 | $0.60 |
| Realtime DB | Included | - | $0 (free tier) |
| **Total** | | | **~$66/month** |

For comparison, dedicated RAG infrastructure (vector DB + embeddings service) would cost ~$200-500/month minimum.

---

## Implementation Phases

### Phase 1: Foundation Setup ✅ **[FOUNDATION COMPLETE - FIREBASE SETUP PENDING]**

**Goal:** Get Firebase Studio + Genkit working with existing knowledge base

**Tasks:**
- [x] Create project structure
- [x] Set up Genkit in `functions/` directory
- [x] Create `rag_config.json`
- [x] Create `/help` endpoint scaffold
- [x] Configure knowledge base paths (494 .md files)
- [x] Documentation complete
- [ ] Create Firebase project (user action required)
- [ ] Configure Firebase Studio data sources (user action required)
- [ ] Test with sample queries (pending Firebase setup)

**Deliverables:**
- ✅ Project structure created
- ✅ RAG configuration system in place
- ✅ `/help` endpoint code ready
- ✅ Knowledge base indexed in config
- ⏳ Firebase project (next step)
- ⏳ Basic RAG retrieval working (pending Firebase)

**Timeline:** Foundation: Complete | Firebase Setup: 1-2 days

**See:** `docs/roadmap/phase1-rag-setup-complete.md` for detailed summary

---

### Phase 2: Device Knowledge Integration ⏹ **[PLANNED]**

**Goal:** Generate device/preset catalogs from Firestore, enable incremental addition

**Tasks:**
- [ ] Create `configs/rag_config.json`
- [ ] Build `scripts/generate-rag-catalogs.ts`
- [ ] Enhance Firestore schema with RAG metadata fields
- [ ] Document first device (Reverb) with RAG metadata
- [ ] Generate device-catalog.md
- [ ] Test device discovery queries

**Deliverables:**
- RAG config system operational
- Device catalog generation working
- At least 1 device fully documented

**Timeline:** 1 week

---

### Phase 3: Conversation System ⏹ **[PLANNED]**

**Goal:** Multi-turn conversations with state management

**Tasks:**
- [ ] Design conversation Firestore schema
- [ ] Implement Genkit conversation flow (`/chat` endpoint)
- [ ] Session management (create, load, save)
- [ ] Conversation history tracking
- [ ] Intent extraction from assistant responses
- [ ] Frontend chat UI updates

**Deliverables:**
- `/chat` endpoint with multi-turn support
- Conversation state persists across turns
- UI shows conversation history

**Timeline:** 2 weeks

---

### Phase 4: Project Context Injection ⏹ **[PLANNED]**

**Goal:** Project-aware responses using live Ableton state

**Tasks:**
- [ ] Project snapshot caching in Firestore
- [ ] Progressive context loading strategy
- [ ] Scope detection (minimal → full_project)
- [ ] Context optimization/filtering
- [ ] Local server → Firestore sync
- [ ] Test with live project state

**Deliverables:**
- Queries like "my mix is muddy" analyze actual project
- Context size optimized (< 10KB typical)
- Responses reference user's actual devices

**Timeline:** 2 weeks

---

### Phase 5: Project Analysis Engine ⏹ **[PLANNED]**

**Goal:** Intelligent analysis of routing, frequency conflicts, etc.

**Tasks:**
- [ ] Routing graph builder
- [ ] Frequency analysis algorithms
- [ ] Issue detection (muddy mix, harsh highs, etc.)
- [ ] Multi-track dependency analysis
- [ ] Caching analysis results in session
- [ ] Actionable suggestions with intents

**Deliverables:**
- System detects common mixing issues
- Suggests fixes with executable commands
- Analysis cached across conversation turns

**Timeline:** 3 weeks

---

### Phase 6: Production Readiness ⏹ **[PLANNED]**

**Goal:** Deploy to production, monitoring, optimization

**Tasks:**
- [ ] Cloud Functions deployment
- [ ] Firebase Studio production index
- [ ] Monitoring and alerting
- [ ] Cost tracking dashboard
- [ ] Performance optimization
- [ ] User feedback collection

**Deliverables:**
- Production deployment
- Monitoring active
- Cost tracking operational

**Timeline:** 2 weeks

---

## Configuration Management

### rag_config.json Structure

**Status:** ⏳ To Be Created
**Location:** `configs/rag_config.json`

```json
{
  "rag": {
    "enabled": true,
    "version": "1.0.0",

    "firebase_studio": {
      "project_id": "fadebender",
      "region": "us-central1",
      "data_sources": {
        "knowledge_base": "knowledge/**/*.md",
        "device_catalog": "knowledge/fadebender/device-catalog.md",
        "preset_catalog": "knowledge/fadebender/preset-catalog.md"
      },
      "indexing": {
        "auto_reindex": true,
        "watch_paths": ["knowledge/"],
        "embedding_model": "text-embedding-004"
      }
    },

    "device_signatures": {
      "enabled_for_rag": [
        "AudioEffectGroupDevice:Reverb"
      ],
      "in_progress": [],
      "planned": [
        "AudioEffectGroupDevice:Compressor",
        "AudioEffectGroupDevice:EQ Eight",
        "AudioEffectGroupDevice:Glue Compressor"
      ],
      "excluded": [
        "MidiEffectGroupDevice:*"
      ]
    },

    "structure_signatures": {
      "enabled_for_rag": [
        "reverb_v1"
      ],
      "in_progress": [],
      "planned": [
        "compressor_v1",
        "eq_eight_v1"
      ]
    },

    "auto_generation": {
      "device_catalog": {
        "enabled": true,
        "sources": ["device_mappings"],
        "filter": {
          "include_in_rag": true
        },
        "output": "knowledge/fadebender/device-catalog.md",
        "schedule": "manual"
      },
      "preset_catalog": {
        "enabled": true,
        "sources": ["presets"],
        "filter": {
          "is_public": true,
          "include_in_rag": true
        },
        "output": "knowledge/fadebender/preset-catalog.md",
        "schedule": "manual"
      }
    },

    "retrieval": {
      "top_k": 5,
      "min_relevance_score": 0.7,
      "rerank": true
    },

    "conversation": {
      "max_history_turns": 10,
      "session_timeout_minutes": 30,
      "cache_project_analysis": true,
      "cache_ttl_minutes": 15
    },

    "context_injection": {
      "max_context_size_kb": 50,
      "progressive_loading": true,
      "default_scope": "minimal"
    }
  }
}
```

### Config Usage in Code

```typescript
import { loadConfig } from './utils/config-loader';

const config = await loadConfig('configs/rag_config.json');

// Check if RAG is enabled
if (!config.rag.enabled) {
  return fallbackResponse();
}

// Get enabled device signatures
const enabledDevices = config.rag.device_signatures.enabled_for_rag;

// Retrieval settings
const topK = config.rag.retrieval.top_k;
```

---

## Cost Analysis

### Detailed Cost Breakdown

**Assumptions:**
- 1000 active users/month
- 50 commands/user/month
- 5 help queries/user/month
- 2 chat sessions/user/month (3 turns avg)

| Service | Usage | Unit Cost | Monthly Cost |
|---------|-------|-----------|--------------|
| **Cloud Functions** | | | |
| - Intent Parse (50k invocations) | 50k | $0.40/1M | $0.02 |
| - Help (5k invocations) | 5k | $0.40/1M | $0.002 |
| - Chat (6k invocations, 3 turns × 2k) | 6k | $0.40/1M | $0.002 |
| **Firestore** | | | |
| - Reads (100k reads) | 100k | $0.06/100k | $0.06 |
| - Writes (10k writes) | 10k | $0.18/100k | $0.02 |
| **Realtime Database** | | | |
| - Data transfer (10GB) | 10GB | Free tier | $0 |
| **Firebase Studio** | | | |
| - Embeddings (5k queries) | 5k | $0.0001/query | $0.50 |
| - Retrieval | 5k | Included | $0 |
| **Gemini API** | | | |
| - Intent parse (regex first, 10% LLM) | 5k | $0.002/1k | $0.01 |
| - Help (5k queries, 1k tokens avg) | 5k | $0.01/1k tokens | $50 |
| - Chat (6k turns, 2k tokens avg) | 12k tokens | $0.01/1k | $120 |
| **Storage** | | | |
| - Firestore storage (1GB) | 1GB | $0.18/GB | $0.18 |
| - Cloud Storage (snapshots, 5GB) | 5GB | $0.02/GB | $0.10 |
| **TOTAL** | | | **~$171/month** |

**Cost per user:** $0.17/month

### Cost Optimization Strategies

1. **Caching aggressive**
   - Cache project analysis in conversation sessions
   - Reuse analysis across turns (saves LLM calls)
   - Estimated savings: 40% on chat costs

2. **Progressive loading**
   - Only load needed context
   - Reduces token counts → lower LLM costs
   - Estimated savings: 30% on context-heavy queries

3. **Gemini Flash for simple queries**
   - Use Gemini Flash (10x cheaper) for help queries
   - Reserve Pro for complex chat/analysis
   - Estimated savings: 60% on help queries

4. **Batch catalog generation**
   - Generate once daily via Cloud Scheduler
   - Not per-query
   - Negligible cost

**Optimized Monthly Cost:** ~$85/month for 1000 users

---

## Risks and Mitigations

### Technical Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Firebase Studio RAG quality | High | Medium | Test extensively, use structured knowledge docs, iterate on doc quality |
| Context size exceeds limits | High | Medium | Progressive loading, smart filtering, compression |
| Conversation state drift | Medium | Low | Session validation, TTL expiry, user reset option |
| Firestore costs balloon | High | Low | Monitoring, alerts, caching strategy |
| Cold start latency | Medium | Medium | Cloud Run for latency-sensitive paths, pre-warming |

### Mitigation Details

**RAG Quality:**
- Test with diverse queries before launch
- Monitor retrieval accuracy metrics
- Iterate on knowledge doc structure
- User feedback loop for bad results

**Context Size:**
- Hard limit enforcement (50KB config)
- Progressive disclosure pattern
- Summarization for large projects
- Warning to user if project too large

**Cost Control:**
- Daily cost monitoring dashboard
- Alerts at 80% of budget
- Per-user quotas if needed
- Fallback to cheaper models

---

## Success Metrics

### Phase 1 (Foundation)

- [ ] RAG retrieval accuracy > 80% (manual eval on 100 queries)
- [ ] /help response time < 2s (p95)
- [ ] Zero Firebase Studio indexing errors

### Phase 2 (Device Knowledge)

- [ ] At least 5 devices fully documented
- [ ] Device discovery queries successful > 90%
- [ ] Catalog generation completes < 10s

### Phase 3 (Conversation)

- [ ] Multi-turn conversations work (3+ turns)
- [ ] Session state persists correctly
- [ ] Intent extraction accuracy > 85%

### Phase 4 (Project Context)

- [ ] Project-aware responses > 80% accurate
- [ ] Context size < 50KB (p95)
- [ ] Response time < 3s (p95)

### Phase 5 (Analysis)

- [ ] Issue detection accuracy > 70% (manual eval)
- [ ] Actionable suggestions > 80% helpful (user survey)

### Phase 6 (Production)

- [ ] Cost per user < $0.20/month
- [ ] Uptime > 99.5%
- [ ] User satisfaction > 4/5 stars

---

## References

### External Documentation

- [Firebase Studio Documentation](https://firebase.google.com/docs/studio)
- [Genkit Documentation](https://firebase.google.com/docs/genkit)
- [Gemini API Pricing](https://ai.google.dev/pricing)
- [Cloud Functions (2nd gen) Pricing](https://cloud.google.com/functions/pricing)

### Internal Documentation

- `docs/architecture/CHAT_FLOW_ARCHITECTURE.md` - Current chat flow
- `docs/roadmap/help-system-enhancements.md` - Original help system plan
- `docs/roadmap/layered_nlp_architecture.md` - NLP architecture
- `knowledge/fadebender/user-guide.md` - User-facing command reference

---

## Change Log

| Date | Author | Changes |
|------|--------|---------|
| 2025-11-18 | Architecture Team | Initial document created |

---

## Appendix: Quick Start Checklist

### For Developers Starting on This

**Prerequisites:**
- [ ] Firebase account with billing enabled
- [ ] Node.js 18+ installed
- [ ] Firebase CLI installed (`npm install -g firebase-tools`)
- [ ] Genkit CLI installed (`npm install -g genkit`)

**Setup Steps:**
1. [ ] Read this document fully
2. [ ] Review `knowledge/` directory structure
3. [ ] Set up Firebase project (see Phase 1)
4. [ ] Configure `rag_config.json`
5. [ ] Run `npm run generate:rag-catalogs` (after Phase 2)
6. [ ] Deploy to Firebase emulator for local testing
7. [ ] Test with sample queries
8. [ ] Deploy to production

**Questions?**
Contact the architecture team or open an issue in the repo.
