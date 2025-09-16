# Logic Pro Compression and EQ Fundamentals

## Compression Principles and Settings

### Audio Engineering Fundamentals
**What Compression Does:**
- Reduces dynamic range between loudest and quietest parts
- Adds sustain and consistency to audio
- Can add punch and energy when used correctly
- Controls peaks to prevent clipping

**Key Parameters:**
- **Threshold**: Level where compression begins (-20dB to -6dB typical)
- **Ratio**: Amount of compression (2:1 to 6:1 for vocals, 4:1 to 10:1 for drums)
- **Attack**: How quickly compression engages (fast for transient control, slow to preserve attack)
- **Release**: How quickly compression stops (fast for transparency, slow for smoothness)

### Logic Pro Compressor Settings

**Vocal Compression:**
- Ratio: 3:1 to 6:1
- Attack: Medium (3-10ms) to preserve natural onset
- Release: Fast to medium (30-100ms) for transparency
- Threshold: Set for 3-6dB of gain reduction

**Drum Compression:**
- **Kick**: Fast attack (0.1-1ms), medium release, 4:1 ratio
- **Snare**: Medium attack (1-3ms), fast release, 3:1 ratio
- **Toms**: Slow attack (5-10ms), medium release, 2:1 ratio

**Commands:**
- "compress track X"
- "add compression to track X"
- "increase compression on track X"

## EQ Principles and Frequency Ranges

### Frequency Spectrum Knowledge
**Sub-Bass (20-60Hz):**
- Kick drum fundamentals, bass guitar low end
- High-pass other instruments to avoid muddiness
- Use sparingly - felt more than heard

**Bass (60-200Hz):**
- Bass guitar and kick drum body
- Too much creates boomy, muddy mix
- Cut here to tighten low end

**Low-Mids (200-500Hz):**
- Vocal and instrument body/warmth
- Problem area for muddiness
- Often needs cutting in dense mixes

**Mids (500Hz-2kHz):**
- Vocal presence and intelligibility
- Guitar power chord fundamentals
- Boost for forward, present sound

**High-Mids (2-8kHz):**
- Vocal consonants and clarity
- Instrument attack and definition
- Boost for brightness and presence

**Highs (8kHz+):**
- Air, sparkle, and shimmer
- Gentle boosts add openness
- Over-boosting creates harshness

### Logic Pro Channel EQ Techniques

**Vocal EQ:**
- High-pass at 80-100Hz (remove rumble)
- Slight cut at 200-400Hz (reduce muddiness)
- Boost at 2-5kHz (presence and clarity)
- Gentle boost at 10-12kHz (air and sparkle)

**Drum EQ:**
- **Kick**: Boost 60-80Hz (power), 2-5kHz (attack)
- **Snare**: Cut 200-400Hz (boxiness), boost 3-5kHz (crack)
- **Hi-hats**: High-pass at 300Hz, boost 8-12kHz (sparkle)

**Commands:**
- "boost track X highs by 3dB"
- "cut track X at 400Hz"
- "add presence to track X"
- "high-pass track X at 100Hz"

## Advanced Processing Techniques

### Multipressor (Multiband Compression)
**Frequency-Specific Control:**
- Low band: Control bass frequencies independently
- Mid band: Manage vocal presence without affecting highs
- High band: Control brightness and air

**Vocal Multipressor:**
- Low (80-500Hz): Light compression to control body
- Mid (500Hz-3kHz): Medium compression for consistency
- High (3kHz+): Light compression to control sibilance

### Vintage EQ Modeling
**Analog Console Emulation:**
- Musical, smooth frequency response
- Harmonic saturation for character
- Wide, gentle curves for natural sound

**When to Use:**
- Adding warmth and character to vocals
- Smoothing harsh digital recordings
- Creating vintage, analog-style mixes

**Commands:**
- "add warmth to track X"
- "make track X sound vintage"
- "smooth track X harshness"

## EQ and Compression Order

### Signal Chain Considerations
**EQ Before Compression:**
- Shape tone before dynamics processing
- Remove problem frequencies before compression amplifies them
- Standard approach for most situations

**Compression Before EQ:**
- Control dynamics first, then shape tone
- Useful when compression adds desirable coloration
- Common in vintage-style processing

**Commands:**
- "process track X with EQ then compression"
- "compress then EQ track X"