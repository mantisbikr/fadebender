# Fadebender Knowledge Base

This directory contains comprehensive audio engineering knowledge, DAW-specific documentation, and architectural plans for the Fadebender AI system.

## Structure

### 📁 **DAW-Specific Knowledge**
- **`logic-pro/`** - Logic Pro workflows, plugins, and techniques (✅ Implemented)
  - `workflows/` - Vocal processing, drum mixing, spatial effects, compression/EQ
  - `plugins.md` - Complete Logic Pro plugin reference
- **`ableton-live/`** - Ableton Live devices and workflows (🔄 Planned)
- **`cubase/`** - Cubase plugins and workflows (🔄 Planned)

### 📁 **Universal Knowledge**
- **`shared/`** - Cross-DAW audio engineering principles
  - `audio-engineering-principles.md` - Frequency spectrum, compression, EQ fundamentals
  - `versioning-integration.md` - Chat interface for version control and history

### 📋 **Architecture Documentation**
- **`DAW-ROADMAP.md`** - Multi-DAW support strategy and implementation phases
- **`VERSIONING-ARCHITECTURE.md`** - Complete undo/redo and snapshot system design

### 📚 **Reference Materials**
- **`logic-pro-mac-user-guide.pdf`** - Official Logic Pro documentation (49MB)

## Current Implementation Status

### ✅ **Completed**
- **Logic Pro Knowledge Base**: Comprehensive workflows and plugin documentation
- **Audio Engineering Principles**: Professional frequency spectrum and compression knowledge
- **Enhanced System Prompt**: Grounded expert advice with specific Logic Pro recommendations
- **Multi-DAW Architecture**: Foundation ready for Ableton Live and Cubase expansion
- **Versioning System Design**: Complete specification for change tracking and snapshots

### 🔄 **Planned Features**
- **Ableton Live Integration**: Device-specific workflows and Live techniques
- **Cubase Integration**: Plugin mappings and Cubase-specific workflows
- **Version Control Implementation**: Undo/redo system with chat interface
- **DAW Auto-Detection**: Automatic workflow switching based on connected DAW
- **Snapshot Management**: Save/restore project states with natural language

## Key Features

### 🎯 **Expert Audio Engineering Advice**
The system provides professional-grade mixing advice:

```
User: "I want spaciousness to my vocals"
AI: "For vocal spaciousness in Logic Pro, try ChromaVerb's Synth Hall preset
(15-25% wet), Space Designer Vocal Hall impulse, and gentle high-frequency
boost at 10-12kHz for air. You can say: 'add reverb to track 2'"
```

### 🎛️ **DAW-Specific Recommendations**
- **Logic Pro**: ChromaVerb, Multipressor, Space Designer, Direction Mixer
- **Future - Ableton Live**: Reverb device, Multiband Dynamics, Auto Pan
- **Future - Cubase**: REVerence, VintageVCA, StereoEnhancer

### 📈 **Version Control Integration**
```
User: "Go back to how track 2 sounded 5 minutes ago"
AI: "Restoring Track 2 to state from 2:25 PM:
- Volume: -3dB (was -6dB)
- Reverb: 15% (was 25%)
- Compression: Off (was On)"
```

### 🧠 **Learning and Patterns**
```
User: "How do I get that vocal sound from yesterday?"
AI: "Yesterday you achieved great vocal sound with:
- ChromaVerb Vocal Hall (25% wet)
- Gentle compression (3:1 ratio)
- High boost at 10kHz (+2dB)
Would you like me to apply these settings to the current vocal track?"
```

## Knowledge Integration

### System Prompt Enhancement
The NLP service (`nlp-service/intents/parser.py`) integrates this knowledge to provide:
- **Grounded Advice**: Based on professional audio engineering principles
- **Logic Pro Specificity**: Exact plugin names and preset recommendations
- **Actionable Commands**: Every suggestion includes executable commands
- **Frequency Knowledge**: Professional understanding of spectrum management

### Future Multi-DAW Support
```python
# Future architecture example
def get_daw_specific_advice(query: str, daw_context: DAWContext):
    if daw_context.daw_type == "logic-pro":
        return load_logic_pro_workflows()
    elif daw_context.daw_type == "ableton-live":
        return load_ableton_live_workflows()
    elif daw_context.daw_type == "cubase":
        return load_cubase_workflows()
```

## Contributing to Knowledge Base

### Adding New Workflows
1. Create workflow files in appropriate DAW directory
2. Follow established format with Description, Techniques, Commands sections
3. Update system prompt in `nlp-service/intents/parser.py`
4. Test with chat interface

### Expanding DAW Support
1. Create new DAW directory structure
2. Document DAW-specific plugins and workflows
3. Add DAW detection logic to controller service
4. Update system prompt with conditional DAW knowledge

### Audio Engineering Principles
1. Add to `shared/audio-engineering-principles.md`
2. Ensure cross-DAW applicability
3. Include frequency ranges, ratios, and professional standards
4. Reference in DAW-specific implementations

## Usage by AI System

This knowledge base powers the Fadebender AI to provide expert-level mixing advice that is:
- **Technically Accurate**: Based on professional audio engineering standards
- **DAW-Specific**: Tailored to the user's actual tools and plugins
- **Immediately Actionable**: Every suggestion includes specific commands
- **Context-Aware**: References user's mixing history and patterns
- **Continuously Learning**: Improves based on user feedback and outcomes

The system transforms natural language requests into professional mixing workflows, making advanced audio engineering techniques accessible through conversation.