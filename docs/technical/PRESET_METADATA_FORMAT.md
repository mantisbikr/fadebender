# Preset Metadata Format

## Overview

Each preset includes metadata that combines audio engineering principles with device-specific details, enabling intelligent user guidance and natural language control.

## Metadata Schema

```json
{
  "name": "Arena Tail",
  "device_name": "Reverb",
  "manufacturer": "Ableton",
  "daw": "Ableton Live",
  "structure_signature": "abc123def456",
  "category": "reverb",
  "subcategory": "hall",
  "preset_type": "stock",

  "description": {
    "what": "Large hall reverb with extended decay and bright character",
    "when": ["lead vocals", "solo instruments", "arena/stadium effects", "dramatic builds"],
    "why": "Long decay (3.5-4.5s) creates sense of large space; bright high shelf emphasizes air and excitement; high stereo width (110-120°) maximizes spaciousness"
  },

  "audio_engineering": {
    "space_type": "hall",
    "size": "large (70-85)",
    "decay_time": "3.5-4.5s (long)",
    "predelay": "15-25ms (natural large space)",
    "frequency_character": "bright (high shelf +1 to +3dB @ 6-8kHz)",
    "stereo_width": "wide (110-120°)",
    "use_cases": [
      {
        "source": "lead vocal",
        "context": "arena rock, stadium anthems, dramatic ballads",
        "send_level": "15-25% (moderate; lets space breathe without drowning)",
        "eq_prep": "HPF @ 180-220 Hz to keep low-end clear",
        "notes": "Predelay 20-25ms maintains vocal clarity; decay creates emotional impact"
      },
      {
        "source": "electric guitar solo",
        "context": "epic moments, wide soundscapes",
        "send_level": "20-30%",
        "eq_prep": "HPF @ 150 Hz",
        "notes": "Bright character emphasizes pick attack and sustain"
      },
      {
        "source": "synth lead",
        "context": "EDM builds, cinematic moments",
        "send_level": "25-40%",
        "eq_prep": "HPF @ 200 Hz, optional LPF @ 8-10 kHz to control brightness",
        "notes": "Long tail fills gaps between notes; stereo width creates dimension"
      }
    ]
  },

  "key_parameters": {
    "predelay": {"value": "20ms", "rationale": "Natural for large spaces; maintains source clarity"},
    "size": {"value": "75", "rationale": "Large hall simulation"},
    "decay": {"value": "4.0s", "rationale": "Extended tail for dramatic effect"},
    "high_shelf": {"value": "+2dB @ 7kHz", "rationale": "Bright, exciting character"},
    "low_shelf": {"value": "-2dB @ 160Hz", "rationale": "Tightens low-end to prevent mud"},
    "stereo": {"value": "115°", "rationale": "Wide image for spaciousness"},
    "diffuse_level": {"value": "+2dB", "rationale": "Emphasizes tail over early reflections"}
  },

  "natural_language_controls": {
    "make_tighter": {
      "params": {"decay": "-0.5 to -1.0s", "size": "-10 to -15"},
      "explanation": "Shortens decay time and reduces room size for more controlled space"
    },
    "warmer": {
      "params": {"high_shelf": "-1 to -2dB"},
      "explanation": "Reduces high frequency content for warmer, less bright character"
    },
    "closer": {
      "params": {"predelay": "-5 to -10ms", "reflect_level": "+1 to +2dB"},
      "explanation": "Reduces predelay and emphasizes early reflections for closer proximity"
    },
    "wider": {
      "params": {"stereo": "+5 to +10°", "chorus_amount": "+5 to +10%"},
      "explanation": "Increases stereo width and adds subtle modulation for enhanced spaciousness"
    },
    "less_muddy": {
      "params": {"low_shelf": "-1 to -2dB", "input_hp_freq": "+20 to +40Hz"},
      "explanation": "Reduces low frequency content and raises high-pass filter to clean up low-end"
    },
    "more_dramatic": {
      "params": {"decay": "+0.5 to +1.0s", "diffuse_level": "+1 to +2dB"},
      "explanation": "Extends tail length and emphasizes diffuse field for more impact"
    }
  },

  "warnings": {
    "mono_compatibility": "Very wide stereo (115°) may collapse in mono; check mix compatibility",
    "cpu_usage": "Long decay + high density = higher CPU; reduce Density if needed",
    "mix_context": "Can overwhelm dense mixes; use sparingly or automate send levels",
    "frequency_buildup": "Bright character may emphasize sibilance; use de-esser before send if needed"
  },

  "similar_presets": ["Vocal Hall", "Cathedral", "Large Concert Hall"],
  "contrast_presets": ["Tight Room", "Drum Plate", "Small Chamber"],

  "parameter_values": {
    "Device On": 1.0,
    "Predelay": 20.0,
    "Size": 75.0,
    "Decay Time": 4.0,
    "Stereo Image": 115.0,
    "High Shelf Gain": 2.0,
    "High Shelf Freq": 7000.0,
    "Low Shelf Gain": -2.0,
    "Low Shelf Freq": 160.0,
    "Diffuse Level": 2.0,
    "Reflect Level": 0.0,
    "Dry/Wet": 100.0
  }
}
```

## Field Descriptions

### Core Identification
- **name**: Preset display name (matches Ableton preset name, e.g., "Arena Tail")
- **device_name**: Actual device name (e.g., "Reverb" for all Ableton Reverb presets)
- **manufacturer**: Device manufacturer (e.g., "Ableton", "Valhalla", "FabFilter")
- **daw**: DAW name (e.g., "Ableton Live", "Logic Pro", "Third-Party VST")
- **structure_signature**: Links to learned device structure (same for all Ableton Reverb presets)
- **category**: Device type (reverb, delay, compressor, etc.)
- **subcategory**: Preset family (hall, plate, room, chamber, etc.)
- **preset_type**: "stock" for manufacturer presets, "user" for custom presets

### Description Object
- **what**: 1-2 sentence technical description of the preset's sound
- **when**: Array of use-cases/contexts (genre, instrument, musical situation)
- **why**: Audio engineering explanation of why it works (decay times, frequency response, spatial characteristics)

### Audio Engineering Object
- **space_type**: Type of acoustic space being simulated
- **size**: Room size parameter value with qualitative descriptor
- **decay_time**: RT60 with qualitative descriptor (short/medium/long)
- **predelay**: Value with spatial context explanation
- **frequency_character**: Tonal description with key parameter values
- **stereo_width**: Width setting with qualitative descriptor
- **use_cases**: Array of detailed application scenarios with:
  - **source**: Instrument/sound type
  - **context**: Musical genre/situation
  - **send_level**: Recommended send amount with reasoning
  - **eq_prep**: Suggested pre-reverb EQ
  - **notes**: Additional tips specific to this combination

### Key Parameters Object
Maps critical parameters to their values with audio engineering rationale:
- **value**: Parameter setting
- **rationale**: Why this value was chosen (psychoacoustic/musical reasoning)

### Natural Language Controls Object
Defines how common user requests map to parameter changes:
- **params**: Dictionary of parameter adjustments (relative changes)
- **explanation**: What this adjustment does and why

Common adjustments to support:
- Tighter/looser
- Warmer/brighter
- Closer/further
- Wider/narrower
- Cleaner/muddier
- More/less dramatic
- Subtle/obvious

### Warnings Array
Potential issues users should be aware of:
- Mono compatibility concerns
- CPU usage considerations
- Mix context cautions
- Frequency buildup risks

### Related Presets
- **similar_presets**: Presets with similar character (for exploration)
- **contrast_presets**: Opposite approaches (for learning/comparison)

## Storage Location

```
~/.fadebender/param_maps/presets/reverb/stock/
├── arena_tail.json
├── vocal_hall.json
├── plate.json
├── tight_room.json
└── ...
```

## Integration Points

### 1. Preset Browser UI
Display description.what + description.when for quick understanding

### 2. LLM Context Injection
When user selects preset, inject full metadata into LLM context for intelligent suggestions

### 3. Natural Language Control
User: "Make it warmer and tighter"
→ System applies natural_language_controls["warmer"] + natural_language_controls["make_tighter"]
→ Explains what was adjusted and why

### 4. Learning/Help System
User: "When should I use Arena Tail?"
→ System surfaces audio_engineering.use_cases with context-specific guidance

### 5. Preset Recommendations
User: "I need reverb for a lead vocal in a rock ballad"
→ System searches description.when + audio_engineering.use_cases
→ Recommends Arena Tail, Vocal Hall with reasoning

## Example Natural Language Workflow

**User**: "Load Arena Tail on my vocal"
**System**:
- Applies Arena Tail preset
- Shows: "Arena Tail: Large hall reverb (4.0s decay, bright). Best for lead vocals in arena rock, dramatic ballads. Send level: 15-25%"

**User**: "Make it warmer and bring the vocal closer"
**System**:
- Applies: high_shelf -2dB, predelay -8ms, reflect_level +1.5dB
- Shows: "Reduced high shelf to warm the tail, shortened predelay and emphasized early reflections to bring vocal forward"

**User**: "Why is it muddy in the mix?"
**System**:
- Checks warnings + audio_engineering context
- Suggests: "Arena Tail has a bright character but long decay can build up low-mids. Try: (1) Reduce low shelf by -2dB, (2) Add HPF at 200Hz before the reverb send, or (3) Shorten decay to 3.0-3.5s for denser mixes"

## Benefits

1. **User Education**: Teaches audio engineering principles through use
2. **Faster Workflow**: Natural language adjustments vs manual parameter hunting
3. **Context-Aware**: Recommendations based on musical context
4. **Troubleshooting**: Built-in guidance for common issues
5. **Consistency**: Professional-grade starting points
6. **Exploration**: Similar/contrast presets guide learning
7. **LLM Grounding**: Rich context enables intelligent suggestions

## Next Steps

1. Create metadata for all Ableton Reverb stock presets
2. Implement preset browser with metadata display
3. Add LLM context injection when preset is selected
4. Build natural language control parameter adjustment logic
5. Create metadata generation tool (semi-automated from preset analysis + audio engineering rules)
