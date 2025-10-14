# LLM Knowledge Architecture

## Overview
Multi-layer knowledge base for LLM-based audio assistance, enabling natural language queries from high-level ("I want airy guitars") to parameter-specific tuning.

## Knowledge Storage (All in Firestore `dev-display-value` database)

### 1. Stock Device Catalog Collection
**Location**: `stock_catalog/{device_signature}`

**Purpose**: Stage 1 device discovery - helps LLM match user's sonic goals to available devices

**Structure**:
```javascript
{
  device_name: "Reverb",
  category: "Spatial Effects",
  sonic_character: "Adds space, depth, and ambience...",
  use_cases: ["airy", "spacious", "depth", ...],
  key_capabilities: ["room simulation", "stereo width", ...],
  typical_applications: {
    vocals: "Add natural space...",
    guitars: "Create airy, spacious tones..."
  },
  sonic_descriptors: {
    airy: ["high HiFilter Freq", "wide stereo", ...],
    tight: ["short decay", "low diffusion", ...]
  },
  stock_presets: { ... },
  common_parameter_adjustments: { ... }
}
```

**Token Cost**: ~1-2KB per device (entire catalog: ~5KB, cached)

### 2. Device Mappings Collection
**Location**: `device_mappings/{device_signature}`

**Purpose**: Complete device knowledge - sections, parameters, display-values, fits

**Enhanced Structure**:
```javascript
{
  device_name: "Reverb",
  device_description: "Reverb is an audio effect that simulates...",

  // NEW: Section groupings for LLM navigation
  sections: {
    "Early Reflections": {
      description: "These are the earliest echoes...",
      parameters: ["ER Spin Amount", "ER Spin Rate", ...],
      sonic_focus: "Room character and spatial definition",
      technical_notes: [...]
    },
    ...
  },

  // ENHANCED: Parameters with multi-source knowledge
  params_meta: [
    {
      name: "Predelay",
      index: 0,

      // Your audio engineering expertise
      audio_knowledge: {
        audio_function: "Time delay before reverb starts...",
        sonic_effect: {
          increasing: "Creates separation...",
          decreasing: "Reverb blends immediately..."
        },
        typical_values: {
          vocals: "20-50ms for clarity",
          drums: "0-10ms for tight blend"
        },
        relationships: [...]
      },

      // NEW: Ableton manual context
      manual_context: {
        official_description: "Controls the delay time, in milliseconds...",
        technical_spec: "Typical values for natural sounds range from 1 ms to 25 ms",
        acoustic_principle: "One's impression of room size depends partly on this delay"
      },

      // Display-value transformation
      fit: { coefficients: [...], r2: 0.999 },
      min_display: 0.1,
      max_display: 250
    }
  ]
}
```

**Token Cost**:
- Full document: ~50KB
- Per parameter: ~200-400 tokens (when drilling down)

## LLM Interaction Flow

### Stage 1: High-Level Device Discovery
**User**: "I want my guitars to have an airy feeling"

**LLM Context**: Entire `stock_catalog` collection (~5KB, cached)

**LLM Action**:
- Search `use_cases` for "airy"
- Search `typical_applications.guitars` for matches
- Search `sonic_descriptors.airy` for parameter hints

**Response**: "Try Reverb - increase HiFilter Freq, Stereo Image, and Decay Time"

### Stage 2: Device Overview + Section Navigation
**User**: "Tell me more about Early Reflections in Reverb"

**LLM Context**: `device_mappings/{signature}.sections.Early Reflections` (~2KB)

**LLM Action**: Read section description, parameters, technical notes

**Response**: "Early Reflections define room character. Key parameters: ER Spin (adds motion), ER Shape (surface materials)..."

### Stage 3: Parameter-Specific Tuning
**User**: "How do I make the reverb brighter?"

**LLM Context**: Specific params (`HiFilter Freq`, `LowShelf Freq`) audio_knowledge + manual_context (~400 tokens)

**LLM Action**:
- Read sonic_effect.increasing/decreasing
- Check typical_values
- Review relationships

**Response**: "Increase HiFilter Freq to 12kHz+ for brighter reverb. From manual: this models high-frequency absorption in natural spaces..."

## Cost & Performance

### Firestore
- **Reads**: 1-2 per session (cached after first load)
- **Cost**: Negligible (already fetching device_mappings)
- **Latency**: No additional latency (same read)

### LLM Tokens
- **Stage 1**: ~5KB catalog (all devices)
- **Stage 2**: ~2KB section info
- **Stage 3**: ~400 tokens per parameter
- **Cost**: ~$0.001-0.002 per query
- **Latency**: +50-100ms for enhanced quality

## Future: User-Specific Catalog
See `FUTURE_USER_CATALOG.md` for:
- Per-user/per-project custom presets
- Usage analytics and recommendations
- Auto-tagging from parameter values
- Context learning from workflow

## Source Files

### Scripts
- `scripts/extract_ableton_manual.py` - Extracts manual context from Ableton docs
- `scripts/upload_stock_catalog.py` - Uploads stock catalog to Firestore
- `scripts/minimal_consolidation.py` - Merges all knowledge sources

### Source Data (for reference)
- `/tmp/reverb_ableton_manual_info.rtf` - Original Ableton manual text
- `docs/technical/reverb_audio_knowledge.json` - Your audio expertise (in repo)
- Firestore DEFAULT database - Original audio_knowledge source

### Generated Collections (in Firestore `dev-display-value`)
- `stock_catalog/` - Device discovery catalog
- `device_mappings/` - Complete device knowledge with sections + manual_context
- Future: `users/{uid}/projects/{pid}/device_catalog` - User customizations

## Verification

Check current state:
```bash
# View stock catalog
python3 -c "
from google.cloud import firestore
db = firestore.Client(database='dev-display-value')
docs = list(db.collection('stock_catalog').stream())
print(f'Stock catalog: {len(docs)} devices')
for doc in docs:
    data = doc.to_dict()
    print(f\"  {data['device_name']}: {len(data['use_cases'])} use cases\")
"

# View device mapping sections
python3 -c "
from google.cloud import firestore
db = firestore.Client(database='dev-display-value')
doc = db.collection('device_mappings').document('64ccfc236b79371d0b45e913f81bf0f3a55c6db9').get()
data = doc.to_dict()
print(f\"Sections: {len(data.get('sections', {}))}\"
for name, info in data.get('sections', {}).items():
    print(f\"  {name}: {len(info['parameters'])} params\")
"
```

## Last Updated
2025-10-13 - Initial implementation with Reverb device
