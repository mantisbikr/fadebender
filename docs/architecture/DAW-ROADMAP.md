# Multi-DAW Architecture Roadmap

## Current State
- **Ableton Live**: Primary focus with devices and workflows
- **System**: Single chat interface with Ableton-focused advice

## Future Architecture Goals

### DAW Detection & Context
- **Auto-detection**: Identify connected DAW (Ableton Live, Cubase)
- **Context switching**: Provide DAW-specific advice based on active connection
- **Unified interface**: Same chat experience across all DAWs

### DAW-Specific Knowledge Bases

#### Ableton Live (✅ In Progress)
- **Reverb**: Reverb device, Echo, Corpus
- **Compression**: Multiband Dynamics, Compressor, Glue Compressor
- **Spatial**: Auto Pan, Utility (width), Reverb (freeze)
- **Workflow**: Clip launching, Session vs Arrangement view

#### Cubase (🔄 Planned)
- **Reverb**: REVerence, RoomWorks, Vintage Reverb
- **Compression**: VintageVCA, Compressor, MultibandCompressor
- **Spatial**: StereoEnhancer, MonoToStereo, VST Amp Rack
- **Workflow**: Expression Maps, Key Editor, Logical Editor

### Implementation Strategy

#### Phase 1: Knowledge Base Expansion
```
/knowledge/
├── ableton-live/
│   ├── workflows/
│   ├── devices.md
│   └── session-workflow.md
├── cubase/
│   ├── workflows/
│   ├── plugins.md
│   └── expression-maps.md
└── audio-fundamentals/
    ├── audio-engineering-principles.md
    └── cross-daw-concepts.md
```

#### Phase 2: Dynamic System Prompt
- Base audio engineering knowledge (shared)
- DAW-specific sections loaded dynamically
- Context-aware plugin and workflow suggestions

#### Phase 3: DAW Detection Integration
```python
# Future architecture
class DAWContext:
    daw_type: str  # "ableton-live", "cubase"
    version: str
    available_plugins: List[str]
    current_project: Optional[Dict]

def get_daw_specific_advice(query: str, daw_context: DAWContext):
    # Load appropriate knowledge base
    # Provide DAW-specific suggestions
    # Return unified response format
```

#### Phase 4: Execution Engine Updates
- DAW-specific command translation
- Plugin parameter mapping per DAW
- Protocol adapters (Ableton: Remote Script/UDP, Cubase: Generic Remote)

### Response Format Evolution

#### Example (DAW-aware):
```
"For vocal spaciousness:
- Ableton Live: Reverb device with Hall algorithm, Echo for pre-delay
- Cubase: REVerence convolution reverb with vocal hall impulse

You can say: 'add reverb to track 2'"
```

## Benefits of This Architecture

1. **Unified User Experience**: Same chat interface regardless of DAW
2. **Expert Knowledge**: DAW-specific plugin recommendations
3. **Consistent Commands**: Universal language that translates to each DAW
4. **Scalable**: Easy to add new DAWs or update workflows
5. **Context-Aware**: Advice tailored to user's actual setup

## Migration Strategy

1. **Ableton-First Implementation**: Build robust Ableton integration
2. **Gradual DAW Addition**: Add Cubase incrementally as needed
3. **Backward Compatibility**: N/A (Ableton-only focus initially)
4. **Feature Flags**: Enable multi-DAW features when ready

## Current Status (September 14, 2024)

### ✅ Completed
- **Directory Structure**: DAW-specific organization ready for expansion
- **Enhanced System Prompt**: AI grounded in audio engineering principles
- **Architecture Foundation**: Multi-DAW support framework established

### 🔄 Current Issues
- **Intent Execution**: Reverb and effect commands failing with 400 errors
- **Controller Service**: Parameter mapping bugs in `master-controller/src/index.ts`
- **MIDI Pipeline**: Execution chain broken between NLP parsing and MIDI output

### 📋 Next Steps
1. **Fix Execution Pipeline**: Debug and resolve 400 errors in controller service
2. **Add Ableton Live Workflows**: Create `/knowledge/ableton-live/` workflows
4. **Implement DAW Detection**: Auto-switching between DAW-specific knowledge bases

### 🧠 Knowledge Ingestion (Planned)
- **Local Manual Integration (Private)**: Allow placing extracted Ableton Live manual sections under `knowledge/references/ableton-live-manual/` (kept out of git) and include them in-app search with `KNOWLEDGE_INCLUDE_REFERENCES=1`.
- **Retriever Improvements**: Auto-scan all `knowledge/**/*.md` (done), add better ranking (headings weight, recency), and per-section summaries.
- **Ingest Helper**: Script to split large Markdown/text into chunked `.md` files by heading and save under `knowledge/references/` for indexing.
- **Curation First**: Maintain concise curated notes under `knowledge/ableton-live/` and `knowledge/audio-fundamentals/`; use references to fill gaps.

## Technical Considerations

- **Knowledge Base Storage**: File-based vs database for DAW workflows
- **Prompt Engineering**: Balance comprehensive knowledge vs token limits
- **DAW Communication**: Different protocols and connection methods
- **Plugin Availability**: Handle missing plugins gracefully
- **Version Differences**: Account for DAW version variations
