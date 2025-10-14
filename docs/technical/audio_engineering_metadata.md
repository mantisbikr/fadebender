# Audio Engineering Metadata for Devices

## Purpose

Enable intelligent parameter tweaking based on audio engineering knowledge:
1. User: "Increase the predelay a bit" → System knows what sonic effect this creates
2. User: "Make it sound more spacious" → System knows which params to adjust
3. System can explain: "Increasing diffusion will make the reverb smoother and denser"

---

## Two-Level Structure

### Level 1: Parameter Audio Knowledge (in device mapping)
**Attached to each parameter in `params_meta`**
- What does changing this parameter do to the sound?
- What audio engineering principle does it implement?
- When would you increase/decrease it?

### Level 2: Preset Recipes (in preset metadata)
**Attached to each preset**
- What audio goal does this preset achieve?
- What makes it a "cathedral" vs "plate" vs "room"?
- What parameters define its character?

---

## Level 1: Parameter Audio Knowledge

**Stored in Firestore `params_meta` alongside fit data:**

```json
{
  "name": "Predelay",
  "index": 1,
  "control_type": "continuous",
  "fit": {...},
  "min_display": 0.5,
  "max_display": 250.0,
  "audio_knowledge": {
    "audio_function": "Delays the onset of reverb after the direct sound",
    "sonic_effect": {
      "increasing": "Creates separation between dry signal and reverb; sounds more spacious and clear",
      "decreasing": "Reverb blends immediately with sound; tighter, more integrated"
    },
    "audio_principle": "Mimics natural room acoustics where first reflections arrive after initial sound",
    "typical_adjustments": {
      "vocals": "20-50ms for clarity and separation",
      "drums": "0-10ms for tight, natural blend",
      "pads": "30-80ms for depth and space"
    },
    "relationships": [
      "Works with Decay Time - longer predelay + long decay = very spacious",
      "Affects perception of room size - longer predelay suggests larger space"
    ]
  }
}
```

---

## Example: Reverb Parameters with Audio Knowledge

### Core Parameters

#### Predelay (0.5-250ms)
```json
{
  "audio_function": "Time delay before reverb starts after direct sound",
  "sonic_effect": {
    "increasing": "More separation, clearer, more spacious",
    "decreasing": "Tighter blend, more immediate"
  },
  "audio_principle": "Simulates time for sound to travel to walls and back",
  "when_to_adjust": [
    "Increase for vocals/leads to keep them upfront and clear",
    "Decrease for drums/percussion for tighter integration",
    "Increase for bigger sense of space"
  ]
}
```

#### Decay Time (200-60000ms)
```json
{
  "audio_function": "How long the reverb tail persists",
  "sonic_effect": {
    "increasing": "Longer, more sustained tail; ethereal, washy",
    "decreasing": "Shorter, controlled tail; tighter, punchier"
  },
  "audio_principle": "Simulates how quickly sound energy dissipates in a space",
  "when_to_adjust": [
    "Increase for ambient pads, atmospheric sounds",
    "Decrease for drums, rhythm sections to avoid muddiness",
    "Match to tempo - shorter for fast music, longer for slow"
  ]
}
```

#### Diffusion (0.1-96)

##### Room Size (0.22-500m)
```json
{
  "audio_function": "Defines the size of the virtual acoustic space",
  "perceptual_effect": {
    "increasing": "Larger space, longer initial reflections, more diffuse sound",
    "decreasing": "Smaller space, tighter sound, more intimate"
  },
  "typical_use_cases": [
    "Small room (5-20m): Vocal booth, small studio",
    "Medium room (20-100m): Concert hall, large studio",
    "Large space (100-500m): Cathedral, arena, grand hall"
  ],
  "audio_goals": {
    "spacious_sound": {"direction": "increase", "typical_value": "100-300m"},
    "intimate_sound": {"direction": "decrease", "typical_value": "5-30m"},
    "cathedral_effect": {"direction": "increase", "typical_value": "200-500m"}
  },
  "relationships": [
    {
      "param": "Decay Time",
      "interaction": "Larger rooms typically need longer decay times to sound natural"
    },
    {
      "param": "Diffusion",
      "interaction": "Large rooms benefit from higher diffusion for realistic sound"
    }
  ]
}
```

##### Decay Time (200-60000ms)
```json
{
  "audio_function": "Controls how long reverb tail persists after initial sound",
  "perceptual_effect": {
    "increasing": "Longer, more sustained reverb tail, ethereal quality",
    "decreasing": "Shorter, tighter reverb, more controlled"
  },
  "typical_use_cases": [
    "Short decay (200-1000ms): Drums, percussion, tight mixes",
    "Medium decay (1000-4000ms): Vocals, general instruments",
    "Long decay (4000-60000ms): Pads, ambient, cinematic effects"
  ],
  "audio_goals": {
    "tight_punchy": {"direction": "decrease", "typical_value": "500-1500ms"},
    "lush_ambient": {"direction": "increase", "typical_value": "4000-15000ms"},
    "cathedral": {"direction": "increase", "typical_value": "8000-20000ms"},
    "plate_reverb": {"direction": "moderate", "typical_value": "1500-3000ms"}
  },
  "relationships": [
    {
      "param": "Dry/Wet",
      "interaction": "Longer decay needs careful wet/dry balance to avoid muddiness"
    },
    {
      "param": "Room Size",
      "interaction": "Should scale with room size for realism"
    }
  ]
}
```

#### GROUP: Early Reflections
**Purpose**: Shape the initial sound reflections that define space character

##### ER Shape (0.0-1.0)
```json
{
  "audio_function": "Morphs between different early reflection patterns",
  "perceptual_effect": {
    "low_values": "Sharp, distinct early reflections, hard surfaces",
    "high_values": "Soft, diffuse early reflections, absorptive surfaces"
  },
  "typical_use_cases": [
    "Hard surfaces (0.0-0.3): Tile, concrete, glass",
    "Mixed surfaces (0.3-0.7): Wood, carpet, mixed materials",
    "Soft surfaces (0.7-1.0): Heavy drapes, acoustic panels"
  ],
  "audio_goals": {
    "bright_reflective": {"direction": "decrease", "typical_value": "0.0-0.3"},
    "warm_natural": {"direction": "moderate", "typical_value": "0.4-0.6"},
    "diffuse_smooth": {"direction": "increase", "typical_value": "0.7-1.0"}
  }
}
```

#### GROUP: Frequency Shaping
**Purpose**: Control tonal character of reverb

##### HiFilter Freq (20-16000 Hz) + Type
```json
{
  "audio_function": "Removes or shelves high frequencies in reverb",
  "perceptual_effect": {
    "low_cutoff": "Dark, muffled reverb, distant sound",
    "high_cutoff": "Bright, airy reverb, present sound"
  },
  "typical_use_cases": [
    "Dark reverb (1000-4000 Hz): Vintage, lo-fi, distant",
    "Natural reverb (6000-10000 Hz): Realistic space simulation",
    "Bright reverb (12000-16000 Hz): Modern, pristine, crystal clear"
  ],
  "audio_goals": {
    "vintage_warm": {"cutoff": "2000-4000", "type": "low-pass"},
    "natural_space": {"cutoff": "8000-12000", "type": "shelving"},
    "modern_bright": {"cutoff": "12000-16000", "type": "shelving"}
  }
}
```

##### LowShelf Freq (20-15000 Hz) + Gain
```json
{
  "audio_function": "Boosts or cuts low frequencies in reverb",
  "perceptual_effect": {
    "boost": "Fuller, warmer reverb with more body",
    "cut": "Cleaner, tighter reverb with less mud"
  },
  "typical_use_cases": [
    "Cut lows (reduce 100-300 Hz): Vocals, keep clarity",
    "Boost lows (increase 60-150 Hz): Pads, warmth, fullness",
    "Neutral: General purpose"
  ],
  "audio_goals": {
    "clear_vocal": {"freq": "200-300", "gain": "0.2-0.4", "note": "reduce lows"},
    "warm_pad": {"freq": "80-150", "gain": "0.7-1.0", "note": "boost lows"},
    "clean_mix": {"freq": "100-200", "gain": "0.3-0.5", "note": "slight cut"}
  }
}
```

#### GROUP: Diffusion Network
**Purpose**: Control density and texture of reverb

##### Diffusion (0.1-96.0)
```json
{
  "audio_function": "Controls density of reverb reflections",
  "perceptual_effect": {
    "low": "Sparse, individual echoes audible, grainy texture",
    "high": "Dense, smooth reverb, creamy texture"
  },
  "typical_use_cases": [
    "Low diffusion (0.1-30): Special effects, rhythmic echoes",
    "Medium diffusion (30-70): Natural spaces, realistic rooms",
    "High diffusion (70-96): Smooth plates, lush ambient"
  ],
  "audio_goals": {
    "echo_chamber": {"direction": "decrease", "typical_value": "5-25"},
    "natural_room": {"direction": "moderate", "typical_value": "40-65"},
    "smooth_plate": {"direction": "increase", "typical_value": "75-96"}
  }
}
```

##### Reflect Level / Diffuse Level (-30 to 6 dB)
```json
{
  "audio_function": "Balance between early reflections and diffuse reverb tail",
  "perceptual_effect": {
    "reflect_high_diffuse_low": "Emphasize space character, more distinct reflections",
    "reflect_low_diffuse_high": "Emphasize reverb tail, smoother wash"
  },
  "typical_use_cases": [
    "Spatial clarity: Reflect -6 to 0 dB, Diffuse -12 to -6 dB",
    "Smooth ambient: Reflect -15 to -10 dB, Diffuse -3 to 0 dB",
    "Balanced: Both around -6 to -3 dB"
  ],
  "audio_goals": {
    "define_space": {"reflect": "-3 to 0", "diffuse": "-12 to -6"},
    "smooth_wash": {"reflect": "-15 to -10", "diffuse": "0 to 3"},
    "natural_balance": {"reflect": "-6 to -3", "diffuse": "-6 to -3"}
  }
}
```

#### GROUP: Mix Controls
**Purpose**: Blend reverb with dry signal

##### Dry/Wet (0-100%)
```json
{
  "audio_function": "Balance between original (dry) and reverb (wet) signal",
  "perceptual_effect": {
    "low_wet": "Subtle ambience, sound stays upfront",
    "high_wet": "Obvious reverb, sound pushed back in mix"
  },
  "typical_use_cases": [
    "Subtle space (10-25%): Vocals, lead instruments",
    "Moderate reverb (30-50%): Pads, backgrounds",
    "Heavy reverb (60-100%): Effects, ambient textures"
  ],
  "audio_goals": {
    "subtle_depth": {"value": "10-25%"},
    "present_ambience": {"value": "30-45%"},
    "reverb_effect": {"value": "50-80%"},
    "full_wet_processing": {"value": "100%"}
  }
}
```

---

## Common Audio Goals and Parameter Recipes

### Goal: Cathedral Reverb
```json
{
  "description": "Large, spacious cathedral with long, lush reverb",
  "preset_base": "Large Hall or Cathedral preset",
  "parameter_adjustments": {
    "Room Size": {"value": "250-400m", "reason": "Cathedral-sized space"},
    "Decay Time": {"value": "8000-15000ms", "reason": "Long, sustained reverb"},
    "Diffusion": {"value": "70-90", "reason": "Smooth, dense reverb"},
    "Reflect Level": {"value": "-6 to -3 dB", "reason": "Define space"},
    "Diffuse Level": {"value": "-3 to 0 dB", "reason": "Lush tail"},
    "HiFilter Freq": {"value": "8000-12000 Hz", "reason": "Natural brightness"},
    "Dry/Wet": {"value": "30-50%", "reason": "Obvious but not overwhelming"}
  }
}
```

### Goal: Tight Vocal Plate
```json
{
  "description": "Classic plate reverb for vocals - present but controlled",
  "preset_base": "Plate preset",
  "parameter_adjustments": {
    "Decay Time": {"value": "1500-2500ms", "reason": "Moderate sustain"},
    "Diffusion": {"value": "80-95", "reason": "Smooth plate character"},
    "LowShelf Freq": {"value": "200-300 Hz", "reason": "Reduce low end mud"},
    "LowShelf Gain": {"value": "0.2-0.4", "reason": "Cut low frequencies"},
    "HiFilter Freq": {"value": "10000-14000 Hz", "reason": "Bright but not harsh"},
    "Dry/Wet": {"value": "15-30%", "reason": "Subtle support"},
    "Predelay": {"value": "20-40ms", "reason": "Separation from dry signal"}
  }
}
```

### Goal: Small Room Ambience
```json
{
  "description": "Subtle room sound for dry recordings",
  "preset_base": "Small Room preset",
  "parameter_adjustments": {
    "Room Size": {"value": "5-20m", "reason": "Small space"},
    "Decay Time": {"value": "400-1000ms", "reason": "Quick decay"},
    "ER Shape": {"value": "0.3-0.6", "reason": "Natural room character"},
    "Diffusion": {"value": "40-60", "reason": "Realistic reflections"},
    "Dry/Wet": {"value": "10-20%", "reason": "Very subtle"}
  }
}
```

### Goal: Ambient Wash
```json
{
  "description": "Ethereal, long reverb for pads and atmospheres",
  "preset_base": "Large Space or Ambient preset",
  "parameter_adjustments": {
    "Decay Time": {"value": "10000-30000ms", "reason": "Very long tail"},
    "Diffusion": {"value": "85-96", "reason": "Maximum smoothness"},
    "Reflect Level": {"value": "-18 to -12 dB", "reason": "Minimize early reflections"},
    "Diffuse Level": {"value": "0 to 3 dB", "reason": "Emphasize tail"},
    "HiFilter Freq": {"value": "6000-10000 Hz", "reason": "Soften high end"},
    "Dry/Wet": {"value": "50-80%", "reason": "Heavy reverb presence"},
    "Freeze On": {"value": "optional", "reason": "Infinite sustain"}
  }
}
```

---

## Implementation Strategy

### 1. Store in Firestore
Extend device mapping with `audio_metadata`:

```json
{
  "signature": "64ccfc236b79371d0b45e913f81bf0f3a55c6db9",
  "device_name": "Reverb",
  "params_meta": [...],
  "audio_metadata": {
    "parameter_functions": {
      "Room Size": {
        "audio_function": "...",
        "perceptual_effect": {...},
        "audio_goals": {...}
      }
    },
    "parameter_groups": {
      "Room Characteristics": {
        "members": ["Room Size", "Decay Time", "Scale"],
        "group_function": "Define the virtual acoustic space"
      }
    },
    "audio_goals": {
      "cathedral": {...},
      "vocal_plate": {...},
      "small_room": {...}
    }
  }
}
```

### 2. NLP Intent Resolution
When user says: **"Make the reverb sound like a cathedral"**

1. **Extract intent**: `audio_goal = "cathedral"`
2. **Look up recipe**: Get parameter adjustments from `audio_goals.cathedral`
3. **Apply adjustments**:
   - Load base preset (if specified)
   - Apply each parameter tweak
   - Return result

### 3. LLM-Assisted Tweaking
When user says: **"Make it more spacious but tighter"**

1. **Parse request**:
   - "more spacious" → increase Room Size, maybe increase Diffusion
   - "tighter" → decrease Decay Time
2. **Check conflicts**: Spacious + Tight = increase Room Size moderately, decrease Decay Time
3. **Apply intelligent adjustments**:
   ```python
   adjustments = {
     "Room Size": "+20%",  # More spacious
     "Decay Time": "-30%",  # Tighter
     "Diffusion": "+10%"    # Support spaciousness
   }
   ```

### 4. Knowledge Base Structure
Create one metadata file per device:

```
docs/kb/audio/
  ├── reverb_audio_metadata.json
  ├── eq_eight_audio_metadata.json
  ├── compressor_audio_metadata.json
  └── ...
```

---

## Integration with Existing System

### Current Flow:
```
User: "Set reverb decay to 5 seconds"
  ↓
NLP extracts: param="decay", value="5000ms"
  ↓
Server inverts fit: 5000ms → normalized value
  ↓
Send to Live
```

### Enhanced Flow:
```
User: "Make reverb sound like a cathedral"
  ↓
NLP recognizes: audio_goal="cathedral"
  ↓
Look up audio_metadata.audio_goals.cathedral
  ↓
Get parameter recipe:
  - Room Size: 300m
  - Decay Time: 12000ms
  - Diffusion: 85
  - etc.
  ↓
For each parameter:
  - Invert fit: display → normalized
  - Send to Live
  ↓
Result: Cathedral reverb achieved
```

---

## Next Steps

1. **Create audio metadata for Reverb** (start with core parameters)
2. **Define 5-10 common audio goals** (cathedral, plate, room, etc.)
3. **Store in Firestore** alongside params_meta
4. **Extend NLP parser** to recognize audio goals
5. **Create tweaking endpoint** that applies parameter recipes
6. **Test with real audio** to validate recipes

This creates a semantic layer on top of the technical mapping, enabling intelligent parameter control based on desired audio effect!
