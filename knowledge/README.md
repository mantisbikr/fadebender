# Fadebender Knowledge Base

This directory contains audio engineering knowledge and DAW device documentation for LLM grounding.

**Purpose:** Provide context to the LLM for intelligent parameter control, device understanding, and audio engineering advice.

## Structure

### 📁 **DAW-Specific Device Documentation**
- **`ableton-live/audio-effects/`** - Comprehensive Ableton Live device references (38 devices)
  - delay.md, reverb.md, compressor.md, eq-eight.md, etc.
  - Used for Phase 4: Parameter aliasing, LLM intent mapping
  - Enables knowledge-backed help system

### 📁 **Universal Audio Knowledge**
- **`audio-fundamentals/`** - Cross-DAW audio engineering principles
  - `audio-engineering-principles.md` - Frequency spectrum, compression, EQ fundamentals
  - `audio_concepts.md` - Gain staging, EQ, reverb, compression basics
  - `deep_audio_engineering_reverb.md` - Complete reverb guide (psychoacoustics, recipes, troubleshooting)
  - `deep_audio_engineering_delay.md` - Complete delay guide (types, musical use, recipes)

### 📚 **Reference Materials**
- **`references/`** - Local reference files (not committed)
  - Place copyrighted manuals here

**Note:** Architecture docs moved to `docs/architecture/` (DAW-ROADMAP.md, VERSIONING-ARCHITECTURE.md)

## Usage in Fadebender

### Current (Phase 1-3)
- ✅ **Knowledge-backed help system** - Uses device docs for intelligent responses
- ✅ **Audio engineering principles** - Grounded advice for mixing/effects
- ✅ **Device understanding** - Parameter context from device .md files

### Planned (Phase 4)
- ⏳ **Parameter aliasing** - Natural language → parameter names (e.g., "wet" → "Dry/Wet")
- ⏳ **LLM intent mapping** - Device-specific context injection for better understanding
- ⏳ **Smart suggestions** - Device-aware parameter recommendations

## Device Documentation Format

Each device .md file includes:
- **Overview** - Device purpose and common use cases
- **Parameters** - Detailed parameter descriptions with ranges
- **Techniques** - Professional mixing tips and best practices
- **Examples** - Common settings for different scenarios

**Example:** `ableton-live/audio-effects/delay.md`
- Feedback, Time, Sync parameters explained
- Echo/Dub/Slapback technique examples
- Typical wet/dry balance recommendations

## Contributing

### Adding New Device Documentation
1. Create .md file in `ableton-live/audio-effects/`
2. Follow existing format (overview, parameters, techniques, examples)
3. Include professional audio engineering context
4. Reference from index file if needed

### Updating Audio Fundamentals
1. Edit files in `audio-fundamentals/`
2. Ensure cross-DAW applicability
3. Include frequency ranges, ratios, professional standards

---

See [docs/STATUS.md](../docs/STATUS.md) for overall project status and roadmap.
