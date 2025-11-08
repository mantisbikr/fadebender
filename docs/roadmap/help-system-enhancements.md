# Help System Enhancement Roadmap

## Current State (v1.0)
- ✅ LLM-powered help using Gemini 2.5 Flash Lite
- ✅ Comprehensive Ableton Live 12 manual (525 markdown files)
- ✅ Audio engineering knowledge base
- ✅ Fadebender user guide integration
- ✅ Concise, formatted responses (max 200 words)

## Critical Fix Needed
- ❌ **Remove voice control references**: Fadebender uses TEXT commands, NOT voice control
  - Update help_generator.py prompt to clarify this
  - Update user-guide.md to emphasize text-based commands
  - Review all generated responses to ensure accuracy

## Priority 1: Conversational Capability

### Goal
Enable multi-turn conversations where the help assistant remembers context and can answer follow-up questions.

### Requirements
- Conversation history management
- Session-based context storage
- Follow-up question detection
- Reference to previous answers

### Implementation Considerations
```python
# Example structure
{
  "session_id": "uuid",
  "conversation_history": [
    {"role": "user", "content": "how do I use reverb?"},
    {"role": "assistant", "content": "..."},
    {"role": "user", "content": "what about on drums?"},  # Follow-up
  ]
}
```

### Technical Approach
- Add session management to `/help` endpoint
- Store conversation history (in-memory or Redis)
- Pass last 3-5 exchanges as context to LLM
- Implement session timeout (e.g., 30 minutes)

---

## Priority 2: Firestore Preset Integration

### Goal
Enable the LLM to recommend specific presets based on user descriptions of desired sonic effects.

### Requirements
1. **Extract Presets from Firestore**
   - Query all device presets from Firestore
   - Generate JSON files with preset metadata
   - Include: device_type, preset_name, description, tags, parameters

2. **Preset Knowledge Base Structure**
   ```json
   {
     "device_type": "reverb",
     "presets": [
       {
         "name": "Cathedral",
         "description": "Large, spacious reverb with long decay",
         "tags": ["spacious", "long-decay", "ambient", "hall"],
         "parameters": {
           "decay": "4.5s",
           "predelay": "50ms",
           "dry_wet": "30%"
         },
         "use_cases": ["vocals", "synths", "ambient-pads"]
       },
       {
         "name": "Small Room",
         "description": "Tight, natural room ambience",
         "tags": ["tight", "natural", "short-decay"],
         "parameters": {
           "decay": "0.8s",
           "predelay": "10ms",
           "dry_wet": "20%"
         },
         "use_cases": ["drums", "percussion", "acoustic-guitar"]
       }
     ]
   }
   ```

3. **Integration with Help System**
   - Add preset database to knowledge search
   - Enable semantic matching: "spacious reverb" → "Cathedral"
   - LLM can recommend: "Use the Cathedral reverb preset for that spacious vocal sound"

### Implementation Steps
1. Create script: `scripts/export_firestore_presets.py`
2. Generate: `knowledge/presets/reverb.json`, `delay.json`, etc.
3. Update `search_knowledge()` to include preset search
4. Update LLM prompt to reference available presets

---

## Priority 3: Live Set Context Awareness

### Goal
Provide customized advice based on the current Live set snapshot (tracks, devices, routing).

### Requirements
1. **Snapshot Integration**
   - Pass current Live set state to help endpoint
   - Include: tracks, devices on each track, routing, sends/returns

2. **Context-Aware Responses**
   - "You have a reverb on Return A - try increasing the send from Track 1"
   - "I see you have EQ Eight on Track 2 - you can boost the highs..."
   - "To add compression to vocals (Track 1), use: `add compressor to track 1`"

3. **Available Device Suggestions**
   - Check what devices are in Live's browser
   - Suggest loadable devices: "You can add a Delay device using: `add delay to track 1`"

### API Structure
```python
POST /help
{
  "query": "how do I make my vocals sound wider?",
  "live_set_context": {
    "tracks": [
      {
        "index": 1,
        "name": "Vocals",
        "devices": ["EQ Eight", "Compressor"],
        "sends": {"A": -12.0, "B": -inf}
      }
    ],
    "returns": [
      {
        "name": "A",
        "devices": ["Reverb"]
      }
    ],
    "available_devices": ["Chorus", "Delay", "Flanger", ...]
  }
}
```

### LLM Prompt Enhancement
```
**Current Live Set**:
- Track 1 (Vocals): EQ Eight, Compressor
  - Send A: -12 dB → Return A (Reverb)
- Return A: Reverb

**Available devices to load**: Chorus, Delay, Flanger, ...

**User Question**: {query}

Provide advice customized to this Live set. Reference specific tracks and devices where relevant.
Suggest Fadebender commands to implement your advice.
```

---

## Priority 4: Precise Fadebender Command Instructions

### Goal
Help users learn and use Fadebender commands correctly.

### Requirements
1. **Command Reference Integration**
   - Document all supported commands in structured format
   - Categories: Mixer, Device, Transport, Routing, Topology

2. **Command Knowledge Base**
   Create `knowledge/fadebender/commands/` with files like:

   **mixer-commands.md**:
   ```markdown
   # Mixer Commands

   ## Volume Control
   - Absolute: `set track 1 volume to -6 dB`
   - Relative: `increase track 2 volume by 3 dB`
   - Compact pan: `set track 1 pan to 25R` (25% right)

   ## Mute/Solo
   - `mute track 3`
   - `solo track 1`
   - `unmute track 3`
   ```

   **device-commands.md**:
   ```markdown
   # Device Commands

   ## Return Device Parameters
   - `set return A reverb decay to 2 s`
   - `set return B delay feedback to 35%`
   - `what is return A reverb decay?`

   ## Device Ordinals (multiple devices)
   - `set return B reverb 2 decay to 1.5 s`
   ```

   **get-commands.md**:
   ```markdown
   # Query Commands

   ## Parameter Values
   - `what is track 1 volume?`
   - `what is return A pan?`

   ## State Bundles
   - `what is track 1 state` (volume, pan, mute, solo + routing)
   - `what is return A state`

   ## Topology
   - `what are return A devices`
   - `who sends to return A`
   - `what does track 1 send A affect`
   ```

3. **LLM Prompt Updates**
   - Add command examples to LLM context
   - Format: "To {action}, use: `{command}`"
   - Emphasize TEXT-based commands (NOT voice)

### Implementation
1. Create structured command documentation
2. Add to knowledge base search
3. Update help_generator.py prompt:
   ```python
   **Important**:
   - Fadebender uses TEXT commands (NOT voice control)
   - Provide exact command syntax using backticks: `command here`
   - Commands are case-insensitive
   ```

---

## Priority 5: Enhanced Response Quality

### Improvements
1. **Code examples**: Show actual Fadebender commands
2. **Step-by-step instructions**: Break down complex workflows
3. **Visual references**: Point to UI elements when relevant
4. **Common mistakes**: Address typical errors
5. **Related topics**: Suggest follow-up questions

### Example Enhanced Response Format
```markdown
**How to add reverb to vocals:**

1. Create a reverb send:
   - The reverb is already on Return A in your set

2. Increase the send from your vocal track:
   ```
   set track 1 send A to -12 dB
   ```

3. Adjust reverb parameters:
   ```
   set return A reverb decay to 2.5 s
   set return A reverb predelay to 30 ms
   ```

4. Fine-tune the amount:
   ```
   increase track 1 send A by 2 dB
   ```

**Tip**: Start with -12 dB send and adjust to taste.

**Related topics**:
- How do I use parallel compression?
- What are the different reverb types?
```

---

## Technical Debt & Improvements

### Knowledge Base
- [ ] Add semantic search (embeddings) for better retrieval
- [ ] Implement relevance scoring improvements
- [ ] Add caching for frequently asked questions
- [ ] Version control for knowledge base updates
- [ ] **Migrate to GCS for cloud deployment**
  - Current: Knowledge files stored locally in `knowledge/` directory
  - Target: Store markdown files in Google Cloud Storage bucket
  - Benefits:
    - Enables serverless deployment (Cloud Run, Cloud Functions)
    - Reduces container image size (~550 markdown files = significant bloat)
    - Allows independent updates without redeployment
    - Supports CDN caching for faster access
    - Enables versioning and rollback via GCS object versioning
  - Implementation:
    - Create `fadebender-knowledge` GCS bucket
    - Upload knowledge base with organized folder structure
    - Update `knowledge.py` to use GCS client instead of local filesystem
    - Add environment variable: `KNOWLEDGE_SOURCE=gcs|local` (default: local for dev)
    - Cache downloaded files locally with TTL to reduce GCS API calls
  - Migration path:
    - Phase 1: Support both local and GCS (configurable)
    - Phase 2: Default to GCS in production
    - Phase 3: Remove local file dependencies for cloud deployments

### Performance
- [ ] Cache LLM responses for identical queries
- [ ] Optimize knowledge search (currently scans all files)
- [ ] Consider vector database (Pinecone, Chroma, Weaviate)
- [ ] Implement query expansion/synonyms

### Monitoring
- [ ] Track query types and patterns
- [ ] Measure response quality (user feedback)
- [ ] Log failed queries for improvement
- [ ] A/B test different prompts

---

## Future Considerations

### Advanced Features
1. **Interactive tutorials**: Step-by-step guided workflows
2. **Audio examples**: Link to reference tracks/sounds
3. **Video integration**: Embed Ableton tutorial videos
4. **Community knowledge**: User-contributed tips and tricks
5. **Multi-language support**: Translate help content

### Integration Opportunities
1. **Ableton Live documentation**: Direct links to official docs
2. **Plugin manufacturer docs**: Link to third-party device manuals
3. **YouTube tutorials**: Curated video recommendations
4. **Forum discussions**: Link to relevant community threads

---

## Migration Path

### Phase 1 (Current)
- ✅ Basic LLM-powered help
- ✅ Comprehensive manual integration
- ⏳ Fix voice control references

### Phase 2 (Next Sprint)
- [ ] Conversational capability
- [ ] Fadebender command reference integration
- [ ] Fix voice control messaging

### Phase 3
- [ ] Firestore preset integration
- [ ] Live set context awareness

### Phase 4
- [ ] Enhanced response quality
- [ ] Performance optimizations
- [ ] Monitoring and analytics

---

## Notes
- Keep responses concise (current 200-word limit is good)
- Maintain markdown formatting for readability
- Balance technical accuracy with accessibility
- Test with real user queries regularly
- Gather feedback and iterate
