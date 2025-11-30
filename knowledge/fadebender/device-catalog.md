# Fadebender Device Catalog

**Generated**: 2025-11-29 17:30:51
**Source**: Firestore `dev-display-value` database
**Devices**: 5

This catalog contains comprehensive information about Ableton Live devices:
- Parameter ranges with units (min/max display values)
- Audio knowledge (sonic effects, use cases, typical values)
- Sections and grouping
- Master/dependent parameter relationships
- Official Ableton manual descriptions

---

## Reverb

**Device Signature**: `64ccfc236b79371d0b45e913f81bf0f3a55c6db9`
**Description**: Reverb is an audio effect that simulates the acoustic properties of audio as it echoes throughout a physical space.
**Type**: reverb
**Parameters**: 33

---

### Chorus

**Description**: The Chorus section adds a little modulation and motion to the diffusion.
**Sonic Focus**: Movement and richness in the reverb tail

**Technical Notes**:
- You can control the modulation Amount and Rate, or deactivate it altogether

---

#### Chorus Amount

**Control Type**: continuous
**Range**: 0.01 to 4

**Function**: Controls modulation depth (intensity) of diffusion network variations
**Increasing**: Deeper modulation; more pronounced shimmer and pitch variation; richer, more complex tail
**Decreasing**: Shallower modulation; subtle movement; cleaner, more focused tail
**Technical**: Sets peak deviation for diffusion network modulation. Works with Chorus Rate to determine overall modulation character.
**Use Cases**:
  - Fine-tune tail complexity
  - Balance naturalness vs special effect
  - Add depth without overwhelming signal
**Typical Values**:
  - subtle: Low values for gentle enhancement
  - moderate: Medium values for noticeable richness
  - extreme: High values for pronounced shimmer

**Ableton Manual**: Controls the amount of modulation and motion added to the diffusion
**Technical Spec**: Can be deactivated altogether
**Acoustic Principle**: Adds movement and richness through pitch variation

---

#### Chorus Rate

**Control Type**: continuous
**Range**: 0.01 to 8 Hz

**Function**: Controls modulation speed of diffusion network (reverb tail)
**Increasing**: Faster modulation; more active, shimmering reverb tail; can sound unstable at extremes
**Decreasing**: Slower modulation; subtle, gentle movement; more natural character
**Technical**: LFO rate controlling pitch/delay modulation in diffusion network. Similar to ER Spin but affects tail instead of early reflections.
**Use Cases**:
  - Add shimmer to reverb tail
  - Create evolving, organic reverb character
  - Match modulation speed to tempo or mood
**Typical Values**:
  - subtle: Low Hz for barely perceptible movement
  - fast: High Hz for obvious shimmer effect
  - moderate: 0.5-2Hz for natural complexity

**Ableton Manual**: Controls the rate of modulation and motion added to the diffusion
**Technical Spec**: Can be deactivated altogether
**Acoustic Principle**: Speed of pitch modulation in reverb tail

---

#### Chorus On

**Control Type**: binary
**Values**: off / on

**Function**: Master enable switch for diffusion network modulation
**Increasing**: Enables pitch/timing modulation in reverb tail; adds shimmer and movement
**Decreasing**: Disables modulation; static, precise reverb tail
**Use Cases**:
  - Add richness and complexity to reverb tail
  - Create lush, evolving reverb character
  - Prevent static, digital-sounding diffusion
  - Emulate natural room variations
**Typical Values**:
  - on: Use Chorus Rate and Amount to control modulation
  - off: Clean, static reverb tail

---

### Device

**Description**: Device on/off control
**Sonic Focus**: Enable or disable the entire effect

---

#### Device On

**Control Type**: binary
**Values**: off / on

**Function**: Master bypass switch for entire reverb device
**Increasing**: Enables reverb processing; adds spatial depth and ambience to signal
**Decreasing**: Bypasses all reverb processing; passes dry signal through unchanged
**Use Cases**:
  - Quick A/B comparison of dry vs processed signal
  - Automation for creative reverb drops
  - CPU conservation when reverb not needed
**Typical Values**:
  - on: Active - full reverb processing
  - off: Bypass - no reverb processing

---

### Diffusion Network

**Description**: The Diffusion Network creates the reverberant tail that follows the early reflections.
**Sonic Focus**: Reverb tail texture and frequency response

**Technical Notes**:
- High and low shelving filters provide frequency-dependent reverberation decay
- The high-frequency decay models the absorption of sound energy due to air, walls and other materials in the room (people, carpeting and so forth)
- The low shelf provides a thinner decay
- The Diffusion and Scale parameters provide additional control over the diffusion's density and coarseness
- When the room size is extremely small, have a large impact on the coloration contributed by the diffusion

---

#### Diffusion

**Control Type**: continuous
**Range**: 0.10000000149011612 to 96 %

**Function**: Controls density and complexity of reflection pattern in diffusion network
**Increasing**: Denser, smoother reverb tail; more complex reflection pattern; less discrete echoes; silkier sound
**Decreasing**: Sparser, more distinct reflections; more granular texture; potential echo artifacts; less smooth
**Technical**: Adjusts number and timing of reflections in diffusion algorithm. Higher values increase computation for smoother decay.
**Use Cases**:
  - Create smooth, lush reverb character
  - Simulate different room types (smooth vs discrete)
  - Balance CPU usage vs quality
  - Control reverb texture and density
**Typical Values**:
  - natural: 50-75% for balanced character
  - dense: 85-100% for smooth, lush reverb
  - sparse: Low % for discrete, rhythmic reflections

**Ableton Manual**: Provides control over the diffusion's density and coarseness
**Technical Spec**: When the room size is extremely small, has a large impact on the coloration contributed by the diffusion
**Acoustic Principle**: Simulates how many surfaces scatter sound and how evenly they do it

---

#### Scale

**Control Type**: continuous
**Range**: 5 to 100 %

**Function**: Adjusts reflection density in conjunction with room size and diffusion
**Increasing**: More reflections at given size; denser, more complex pattern; can increase flutter at small sizes
**Decreasing**: Fewer reflections; sparser, more open pattern; cleaner but potentially less realistic
**Technical**: Fine-tunes diffusion network complexity. Most noticeable with smaller room sizes. Can create flanger-like effects when automated with small sizes.
**Use Cases**:
  - Fine-tune reverb density
  - Create special effects (flanger-like)
  - Adjust complexity for different sources
  - Balance smoothness vs clarity
**Typical Values**:
  - balanced: 50-70% for natural density
  - dense: High % for complex, rich reverb
  - sparse: Low % for open, spacious character

**Ableton Manual**: Provides additional control over the diffusion's density and coarseness
**Technical Spec**: When the room size is extremely small, has a large impact on the coloration contributed by the diffusion
**Acoustic Principle**: Adjusts the time spacing between early reflections

---

#### HiFilter Freq

**Control Type**: continuous
**Range**: 20 to 16000 Hz

**Function**: Sets frequency point where high-frequency filtering begins in reverb tail
**Increasing**: Higher cutoff; filters less treble; brighter, more airy reverb tail
**Decreasing**: Lower cutoff; filters more treble; darker, warmer reverb tail
**Technical**: Determines frequency above which attenuation occurs. Simulates frequency-dependent absorption in real rooms.
**Use Cases**:
  - Simulate natural room absorption
  - Create vintage-style dark reverb
  - Match reverb brightness to source
  - Prevent harsh high-frequency buildup
**Typical Values**:
  - bright: 10kHz+ for minimal darkening
  - natural: 5-8kHz for balanced decay
  - dark: 2-4kHz for warm, vintage character

**Ableton Manual**: High shelving filter for frequency-dependent reverberation decay
**Technical Spec**: Models the absorption of sound energy due to air, walls and other materials in the room (people, carpeting and so forth)
**Acoustic Principle**: In nature, high frequencies absorb faster than lows in most spaces

---

#### HiFilter Type

**Control Type**: quantized

**Function**: Selects high-frequency filter algorithm (shelf or cut)
**Increasing**: Switches between filter types; different high-frequency decay characteristics
**Decreasing**: Alternative filter type with different slope and character
**Technical**: Offers different filter topologies for high-frequency attenuation in reverb tail. Shelf typically provides gentler slopes, cut provides sharper transitions.
**Use Cases**:
  - Match filter character to desired sound
  - Simulate different room absorption types
  - Fine-tune high-frequency decay curve
**Typical Values**:
  - shelf: Gentle, natural high-frequency rolloff
  - cut: Sharper, more pronounced darkening

---

#### LowShelf Freq

**Control Type**: continuous
**Range**: 20 to 15000 Hz

**Function**: Sets frequency point where low-frequency filtering begins in reverb tail
**Increasing**: Higher cutoff; filters more bass range; thinner, tighter reverb tail
**Decreasing**: Lower cutoff; filters only deep bass; fuller, warmer reverb tail
**Technical**: Determines frequency below which attenuation occurs. Controls bass energy distribution in reverb decay.
**Use Cases**:
  - Prevent low-end mud in dense mixes
  - Match reverb weight to source
  - Create space in low-frequency range
  - Simulate room bass absorption
**Typical Values**:
  - tight: 300-500Hz for thin, articulate reverb
  - balanced: 150-250Hz for natural low-end
  - full: Below 100Hz to preserve bass warmth

**Ableton Manual**: Low shelving filter for frequency-dependent reverberation decay
**Technical Spec**: Provides a thinner decay
**Acoustic Principle**: Controls low frequency content to manage clarity vs warmth

---

#### LowShelf Gain

**Control Type**: continuous
**Range**: 0.20000000298023224 to 1

**Function**: Controls amount of low-frequency attenuation in reverb tail when using shelf filter
**Increasing**: More low-frequency energy in tail; warmer, fuller, potentially muddier reverb
**Decreasing**: Less low-frequency energy; tighter, cleaner, thinner reverb tail
**Technical**: Adjusts amplitude of frequencies below LowShelf Freq. Negative values attenuate (typical), positive values boost.
**Use Cases**:
  - Balance reverb warmth vs clarity
  - Prevent low-frequency buildup
  - Match reverb weight to mix context
**Typical Values**:
  - warm: Slightly negative for controlled warmth
  - neutral: 0dB for flat response
  - tight: Negative values for clean, articulate reverb

---

#### HiFilter On

**Control Type**: binary
**Values**: off / on

**Function**: Enables high-frequency filtering in the diffusion network (reverb tail)
**Increasing**: Activates treble control; allows shaping of high-frequency decay
**Decreasing**: Bypasses filter; natural high-frequency decay
**Use Cases**:
  - Simulate absorptive materials (curtains, furniture)
  - Create darker, warmer reverb tails
  - Match reverb to room acoustic character
  - Save CPU when not needed
**Typical Values**:
  - on: Use HiFilter Type, Freq, and Gain to shape highs
  - off: Natural, bright decay

---

#### HiShelf Gain

**Control Type**: continuous
**Range**: 0.20000000298023224 to 1

**Function**: Controls amount of high-frequency attenuation in reverb tail when using shelf filter
**Increasing**: More high-frequency energy in tail; brighter, more sparkly reverb
**Decreasing**: Less high-frequency energy; darker, more damped reverb tail
**Technical**: Adjusts amplitude of frequencies above HiFilter Freq. Negative values attenuate (typical), positive values boost.
**Use Cases**:
  - Fine-tune reverb brightness
  - Simulate room absorption characteristics
  - Balance reverb tone in mix
**Typical Values**:
  - damped: Negative values for natural darkening
  - neutral: 0dB for flat response
  - boosted: Positive values for enhanced highs (rare)

---

#### LowShelf On

**Control Type**: binary
**Values**: off / on

**Function**: Enables low-frequency filtering in the diffusion network (reverb tail)
**Increasing**: Activates bass control; allows shaping of low-frequency decay
**Decreasing**: Bypasses filter; natural low-frequency decay
**Use Cases**:
  - Prevent muddy low-end buildup in reverb tail
  - Simulate bass absorption in rooms
  - Create tighter, cleaner reverb
  - Save CPU when not needed
**Typical Values**:
  - on: Use LowShelf Freq and Gain to shape bass
  - off: Full-range reverb tail

---

### Early Reflections

**Description**: These are the earliest echoes that you hear after they bounce off a room's walls, before the onset of the diffused reverberation tail. Their amplitude and distribution give an impression of the room's character.
**Sonic Focus**: Room character and spatial definition

**Technical Notes**:
- Spin applies modulation to the early reflections
- A higher Amount setting tends to provide a less-colored (more spectrally neutral) late diffusion response
- If the modulation rate is too high, doppler frequency shifting of the source sound will occur, along with surreal panning effects
- Shape control sculpts the prominence of the early reflections, as well as their overlap with the diffused sound
- With small values, the reflections decay more gradually and the diffused sound occurs sooner
- With large values, the reflections decay more rapidly and the diffused onset occurs later
- A higher value can sometimes improve the source's intelligibility, while a lower value may give a smoother decay

---

#### ER Spin Amount

**Control Type**: continuous
**Range**: 2 to 55

**Function**: Controls modulation depth (intensity) of early reflection timing variations
**Increasing**: Deeper timing modulation; more pronounced chorus/phasing effect; wider pitch variations
**Decreasing**: Shallower modulation; subtle movement; minimal pitch deviation
**Technical**: Sets peak deviation in milliseconds for ER delay modulation. Works with ER Spin Rate to determine modulation character.
**Use Cases**:
  - Fine-tune modulation intensity
  - Balance naturalness vs effect strength
  - Match modulation depth to source material
**Typical Values**:
  - subtle: Low values for barely audible movement
  - moderate: Medium values for natural complexity
  - extreme: High values for obvious, creative effects

**Ableton Manual**: Controls the amount of modulation applied to the early reflections
**Technical Spec**: A higher Amount setting tends to provide a less-colored (more spectrally neutral) late diffusion response
**Acoustic Principle**: Creates stereo movement by modulating the early reflection pattern

---

#### ER Spin Rate

**Control Type**: continuous
**Range**: 0.07 to 1.3 Hz

**Function**: Modulates early reflection timing with a low-frequency sine wave to add chorus-like movement
**Increasing**: More timing variation in early reflections; stronger chorus/phasing effect; increased perceived complexity and diffusion
**Decreasing**: Less modulation; more static, distinct early reflections; cleaner but potentially more artificial sound
**Technical**: Low-frequency sine wave modulates ER delay timing (2-55ms depth at 0.07-1.3Hz rate). Inspired by Lexicon 480L reverb algorithm. Creates cyclic delay variations that prevent metallic, static early reflections.
**Use Cases**:
  - Add naturalness to algorithmic reverb
  - Prevent metallic, static early reflections
  - Create richer, more complex reverb character
  - Emulate natural room variations
**Typical Values**:
  - subtle_movement: 0.07-0.2 Hz for barely perceptible modulation
  - pronounced_effect: 1.0-1.3 Hz, 20-55ms depth for obvious modulation
  - recommended: ~1.0 Hz, ~10ms depth for balanced natural sound

**Ableton Manual**: Controls the rate of modulation applied to the early reflections
**Technical Spec**: If the modulation rate is too high, doppler frequency shifting of the source sound will occur, along with surreal panning effects
**Acoustic Principle**: Speed of early reflection pattern rotation

---

#### ER Spin On

**Control Type**: binary
**Values**: off / on

**Function**: Master enable switch for early reflection modulation
**Increasing**: Enables ER timing modulation; activates chorus-like movement in early reflections
**Decreasing**: Disables modulation; early reflections remain static and unmodulated
**Use Cases**:
  - Add life and movement to early reflections
  - Prevent static, digital-sounding reflections
  - Create more natural, organic reverb character
**Typical Values**:
  - on: Use with ER Spin Rate and Amount to control modulation
  - off: Static, precise early reflections

---

#### ER Shape

**Control Type**: continuous
**Range**: 0 to 1

**Function**: Controls blend between early reflections and diffuse reverb tail
**Increasing**: Smoother transition from ER to tail; more cohesive, flowing reverb; less distinct early reflections
**Decreasing**: Distinct separation between ER and tail; gap in reverb onset; more articulated early reflections; potentially less natural
**Technical**: Adjusts crossfade timing and energy distribution between early reflection pattern and diffusion network.
**Use Cases**:
  - Create smooth, natural reverb decay
  - Emphasize or de-emphasize early reflections
  - Match reverb character to room type
  - Adjust reverb articulation
**Typical Values**:
  - separated: Low values for distinct ER stage
  - blended: High values for smooth, continuous reverb

**Ableton Manual**: Sculpts the prominence of the early reflections, as well as their overlap with the diffused sound
**Technical Spec**: With small values, the reflections decay more gradually and the diffused sound occurs sooner. With large values, the reflections decay more rapidly and the diffused onset occurs later
**Acoustic Principle**: A higher value can sometimes improve the source's intelligibility, while a lower value may give a smoother decay

---

### Global

**Description**: Controls that affect the overall reverb character including size, decay, and special functions.
**Sonic Focus**: Overall space character and special effects

**Technical Notes**:
- Predelay controls the delay time, in milliseconds, before the onset of the first early reflection
- One's impression of the size of a real room depends partly on this delay
- Typical values for natural sounds range from 1 ms to 25 ms
- The Size parameter controls the room's volume
- At one extreme, a very large size will lend a shifting, diffused delay effect to the reverb
- The other extreme — a very small value — will give it a highly colored, metallic feel
- The Decay control adjusts the time required for this reverb tail to drop to 1/1000th (-60 dB) of its initial amplitude
- The Freeze control freezes the diffuse response of the input sound. When on, the reverberation will sustain almost endlessly
- Flat bypasses the high and low shelf filters when Freeze is on
- Cut modifies Freeze by preventing the input signal from adding to the frozen reverberation
- The Stereo control determines the width of the output's stereo image
- At the highest setting of 120 degrees, each ear receives a reverberant channel that is independent of the other (this is also a property of the diffusion in real rooms)
- The Density chooser controls the tradeoff between reverb quality and performance. Sparse uses minimal CPU resources, while High delivers the richest reverberation

---

#### Predelay

**Control Type**: continuous
**Range**: 0.5 to 250 ms

**Function**: Time delay before sound reaches first reflective surface and reverb begins
**Increasing**: Longer gap between dry signal and reverb onset; preserves transient clarity; simulates larger distance to walls
**Decreasing**: Immediate reverb onset; tighter coupling with source; can muddy transients in fast material
**Technical**: Predelay simulates the time sound travels before hitting first reflective surface. Critical for separating direct sound from reverb tail.
**Use Cases**:
  - Preserve vocal/instrument attack transients (1-25ms typical)
  - Create sense of space and distance
  - Prevent muddiness in dense mixes
  - Sync reverb timing to tempo (calculated delays)
**Typical Values**:
  - distant: 50-100ms+ for larger spaces or creative effects
  - natural: 10-25ms for realistic room simulation
  - tight: 0-10ms for intimate, close sound

**Ableton Manual**: Controls the delay time, in milliseconds, before the onset of the first early reflection. This delays the reverberation relative to the input signal.
**Technical Spec**: Typical values for natural sounds range from 1 ms to 25 ms
**Acoustic Principle**: One's impression of the size of a real room depends partly on this delay

---

#### Room Size

**Control Type**: continuous
**Range**: 0.22 to 500

**Function**: Controls perceived room volume/dimensions; fundamental space parameter
**Increasing**: Larger perceived space; longer reflection spacing; more open, expansive character; potential for flutter at extremes
**Decreasing**: Smaller perceived space; tighter reflections; more intimate, focused character; can sound metallic at minimum
**Technical**: Adjusts all-pass filter delays in diffusion network. Affects reflection timing and spacing throughout algorithm.
**Use Cases**:
  - Set fundamental room character
  - Match reverb to musical context
  - Create special effects via automation
  - Simulate specific room types
**Typical Values**:
  - large: Expansive spaces; halls, cathedrals, canyons
  - medium: Natural room ambience; studios, living rooms
  - small: Tight, intimate spaces; vocal booths, small rooms

**Ableton Manual**: Controls the room's volume
**Technical Spec**: At one extreme, a very large size will lend a shifting, diffused delay effect. The other extreme — a very small value — will give it a highly colored, metallic feel
**Acoustic Principle**: Defines the dimensions of the virtual acoustic space

---

#### Decay Time

**Control Type**: continuous
**Range**: 200 to 60000 ms

**Function**: Controls how long reverb tail takes to decay to -60dB (1/1000th of initial volume)
**Increasing**: Longer reverb tail; more sustained ambience; larger perceived space; can muddy fast material
**Decreasing**: Shorter reverb tail; tighter, more controlled; smaller perceived space; cleaner in dense mixes
**Technical**: Fundamental reverb parameter setting RT60 (Reverberation Time). Critical for establishing space size and reverb density.
**Use Cases**:
  - Match reverb length to tempo and arrangement
  - Create intimate vs spacious character
  - Control reverb density and clarity
  - Simulate specific room types
**Typical Values**:
  - long: 3-8s for large halls and dramatic effects
  - infinite: Maximum + Freeze for pad-like sustain
  - medium: 1.5-3s for natural room ambience
  - tight: 0.5-1.5s for intimate, controlled spaces

**Ableton Manual**: Adjusts the time required for this reverb tail to drop to 1/1000th (-60 dB) of its initial amplitude
**Technical Spec**: Decay time to -60 dB
**Acoustic Principle**: Simulates how quickly sound energy dissipates in a space

---

#### Stereo Image

**Control Type**: continuous
**Range**: 0 to 120 degrees

**Function**: Controls spatial width of stereo reverb field from mono to wide stereo
**Increasing**: Wider stereo field; more spacious, immersive character; greater L/R separation; more realistic room simulation at high settings
**Decreasing**: Narrower stereo field; more focused, centered image; mono at minimum; artificial, unnatural character at very low settings
**Technical**: Adjusts decorrelation between L/R channels and stereo width of diffusion network. 0% = mono, 100% = maximum width.
**Use Cases**:
  - Create immersive stereo ambience
  - Adjust reverb width to mix context
  - Prevent excessive stereo spreading
  - Match reverb width to source material
**Typical Values**:
  - wide: 85-100% for expansive, immersive spaces
  - natural: 50-75% for realistic stereo imaging
  - mono: 0% for centered reverb

**Ableton Manual**: Determines the width of the output's stereo image
**Technical Spec**: At the highest setting of 120 degrees, each ear receives a reverberant channel that is independent of the other (this is also a property of the diffusion in real rooms). The lowest setting mixes the output signal to mono
**Acoustic Principle**: Controls left-right spread without affecting front-back depth

---

#### Density

**Control Type**: quantized

**Function**: Selects discrete algorithm preset affecting overall reflection pattern density
**Increasing**: Higher density preset; more complex reflection patterns; smoother, more lush character
**Decreasing**: Lower density preset; sparser reflections; more discrete, granular character
**Technical**: Quantized parameter selecting different diffusion network configurations. Works with Scale and Diffusion for fine control.
**Use Cases**:
  - Choose base diffusion complexity
  - Match reverb character to source
  - Balance smoothness vs articulation
**Typical Values**:
  - low: Sparse, discrete reflections
  - high: Dense, smooth reverb character
  - medium: Balanced reflection density

**Ableton Manual**: Controls the tradeoff between reverb quality and performance
**Technical Spec**: Sparse uses minimal CPU resources, while High delivers the richest reverberation
**Acoustic Principle**: Simulates number of reflections happening in the space

---

#### Freeze On

**Control Type**: binary
**Values**: off / on

**Function**: Captures and sustains current diffusion network state indefinitely; disables input and sets decay to infinite
**Increasing**: Freezes reverb tail; creates infinite sustain; no new input processed; existing reverb sustains endlessly
**Decreasing**: Normal operation; input processed; natural decay according to Decay Time parameter
**Technical**: Disables reverb input and sets internal feedback to 100%, creating infinite loop of diffusion network state. Use with Cut and Flat for control.
**Use Cases**:
  - Create ambient pads and textures
  - Build tension in arrangements
  - Isolate reverb tail for sound design
  - Create reverb swells and risers
**Typical Values**:
  - on: Infinite sustain; use Cut/Flat for control
  - off: Normal reverb operation

**Ableton Manual**: Freezes the diffuse response of the input sound. When on, the reverberation will sustain almost endlessly
**Technical Spec**: Flat bypasses the high and low shelf filters when Freeze is on. Cut modifies Freeze by preventing the input signal from adding to the frozen reverberation
**Acoustic Principle**: Captures reverb tail and loops it for infinite sustain

---

#### Cut On

**Control Type**: binary
**Values**: off / on

**Function**: When Freeze active, prevents new signal accumulation when unfreezing and re-freezing
**Increasing**: Clears frozen reverb before capturing new freeze; prevents buildup
**Decreasing**: Allows multiple freeze captures to layer; accumulates reverb content with each freeze
**Technical**: Determines whether diffusion network resets when entering freeze mode. Off allows additive freeze layering.
**Use Cases**:
  - Create layered, complex freeze textures
  - Prevent freeze buildup and overload
  - Control freeze capture behavior
**Typical Values**:
  - on: Clean freeze captures
  - off: Additive freeze layers

---

#### Flat On

**Control Type**: binary
**Values**: off / on

**Function**: When Freeze active, maintains frozen frequency balance vs allowing natural frequency decay
**Increasing**: Frozen spectrum remains constant; all frequencies sustain equally; static tone color
**Decreasing**: Frozen spectrum gradually loses energy according to filter settings; natural darkening over time
**Technical**: Bypasses Hi/Low Shelf filters during freeze. When off, frozen reverb still undergoes frequency-dependent decay.
**Use Cases**:
  - Maintain exact tone color when frozen
  - Create evolving vs static freeze textures
  - Control frozen reverb character
**Typical Values**:
  - on: Static frequency balance while frozen
  - off: Gradual frequency decay while frozen

---

#### Size Smoothing

**Control Type**: quantized

**Function**: Controls interpolation quality when Room Size changes via automation or modulation
**Increasing**: Smoother room size transitions; reduced pitch artifacts; higher CPU usage
**Decreasing**: More artifacts during size changes; audible pitch shifts; lower CPU usage
**Technical**: Adjusts algorithm used for interpolating all-pass delays during size changes. Higher quality prevents doppler-like pitch shifts.
**Use Cases**:
  - Smooth automated room size changes
  - Create special effects (choose low quality for pitch artifacts)
  - Balance quality vs CPU load
**Typical Values**:
  - smooth: Interpolated, minimal artifacts
  - basic: Fast switching, audible artifacts

---

### Input Filter

**Description**: The input signal passes first through low and high cut filters, whose X-Y controller allows changing the band's center frequency (X-axis) and bandwidth (Y-axis).
**Sonic Focus**: Pre-filtering to shape what enters the reverb

---

#### In Filter Freq

**Control Type**: continuous
**Range**: 50 to 18000 Hz

**Function**: Sets cutoff frequency for input high-pass or low-pass filter
**Increasing**: Moves cutoff higher; with lowcut removes more bass, with highcut darkens less
**Decreasing**: Moves cutoff lower; with lowcut removes less bass, with highcut darkens more
**Technical**: Works in conjunction with In LowCut/HighCut switches. Single control serves both filters depending on which is active.
**Use Cases**:
  - Tune reverb frequency response to source
  - Match reverb character to mix
  - Create frequency-specific spatial effects
**Typical Values**:
  - lowcut: 100-300Hz to remove bass mud
  - highcut: 3-8kHz for natural darkening

---

#### In Filter Width

**Control Type**: continuous
**Range**: 0.5 to 9

**Function**: Controls filter slope steepness (Q/resonance) for input filters
**Increasing**: Wider, gentler slope; more gradual frequency transition; natural sound
**Decreasing**: Narrower, steeper slope; sharper frequency cutoff; more pronounced filtering effect
**Technical**: Adjusts bandwidth/Q factor of input filters. Narrower width creates more resonant peak at cutoff frequency.
**Use Cases**:
  - Fine-tune filter character
  - Create resonant filter effects
  - Match filter slope to musical context
**Typical Values**:
  - wide: Gentle, natural filtering
  - narrow: Sharp, resonant filtering with character

---

#### In LowCut On

**Control Type**: binary
**Values**: off / on

**Function**: Enables high-pass filter on input signal before reverb processing
**Increasing**: Activates low frequency filtering; removes bass from reverb for cleaner, thinner character
**Decreasing**: Bypasses filter; allows full frequency spectrum into reverb including bass
**Use Cases**:
  - Prevent muddy low-end buildup in reverb
  - Keep bass dry and focused
  - Create space in dense mixes
  - Save CPU when not needed
**Typical Values**:
  - on: Use with In Filter Freq to control cutoff point
  - off: Full spectrum reverb

---

#### In HighCut On

**Control Type**: binary
**Values**: off / on

**Function**: Enables low-pass filter on input signal before reverb processing
**Increasing**: Activates high frequency filtering; removes treble/sparkle from reverb for darker, warmer character
**Decreasing**: Bypasses filter; allows full frequency spectrum into reverb including highs
**Use Cases**:
  - Create darker, vintage-style reverb
  - Reduce harsh high-frequency reflections
  - Match reverb tone to source material
  - Save CPU when not needed
**Typical Values**:
  - on: Use with In Filter Freq to control cutoff point
  - off: Bright, full-spectrum reverb

---

### Output

**Description**: At the reverb output, you can vary the amplitude of reflections and diffusion with the Reflect and Diffuse controls and adjust the effect's overall Dry/Wet mix.
**Sonic Focus**: Balance between early reflections, reverb tail, and dry signal

---

#### Reflect Level

**Control Type**: continuous
**Range**: -30 to 6 dB

**Function**: Controls output level of early reflections in dB
**Increasing**: Louder early reflections; more emphasis on room geometry; stronger spatial cues; can overpower tail
**Decreasing**: Quieter early reflections; less room character; smoother blend with tail; potential loss of spatial definition
**Technical**: Adjusts amplitude of early reflection stage relative to diffusion network. Critical balance for realistic room simulation.
**Use Cases**:
  - Balance ER vs tail prominence
  - Emphasize or de-emphasize room character
  - Adjust spatial definition
  - Fine-tune reverb mix
**Typical Values**:
  - subtle: -20 to -10dB for smooth, tail-focused reverb
  - balanced: -10 to 0dB for natural room character
  - prominent: 0 to +6dB for emphasized spatial cues

**Ableton Manual**: Controls the amplitude of reflections at the reverb output
**Technical Spec**: Can be varied independently of diffusion level
**Acoustic Principle**: Early reflections define room character

---

#### Diffuse Level

**Control Type**: continuous
**Range**: -30 to 6 dB

**Function**: Controls output level of diffusion network (reverb tail) in dB
**Increasing**: Louder reverb tail; more sustained ambience; denser, more present reverb; can overwhelm ER
**Decreasing**: Quieter reverb tail; less sustained ambience; emphasis on early reflections; cleaner, drier character
**Technical**: Adjusts amplitude of diffusion network relative to early reflections. Essential for balancing reverb character.
**Use Cases**:
  - Balance tail vs ER prominence
  - Control reverb density and sustain
  - Adjust ambience level
  - Fine-tune reverb mix
**Typical Values**:
  - dry: -20 to -10dB for room emphasis over tail
  - balanced: -10 to 0dB for natural reverb character
  - lush: 0 to +6dB for prominent, sustaining ambience

**Ableton Manual**: Controls the amplitude of diffusion at the reverb output
**Technical Spec**: Can be varied independently of reflection level
**Acoustic Principle**: Diffuse tail provides the 'wash' and sustain of reverb

---

#### Dry/Wet

**Control Type**: continuous
**Range**: 0 to 100 dB

**Function**: Controls mix balance between unprocessed (dry) signal and reverb (wet) signal
**Increasing**: More reverb in mix; more spatial depth; can drown out dry signal; appropriate for send/return use at 100%
**Decreasing**: Less reverb in mix; more present, dry signal; tighter, more focused sound; no reverb at 0%
**Technical**: Standard wet/dry mix control. 0% = dry only, 100% = wet only. Use 100% wet on return tracks, variable on inserts.
**Use Cases**:
  - Set at 100% for send/return reverb (standard)
  - Variable mix for insert reverb (less common)
  - Parallel processing techniques
  - Quick reverb amount adjustments
**Typical Values**:
  - parallel: 100% wet with track level control
  - send: 100% wet (return track standard)
  - insert: 10-40% wet (insert use)

**Ableton Manual**: Adjusts the effect's overall Dry/Wet mix
**Technical Spec**: Standard effect mix control
**Acoustic Principle**: Balance between original (dry) and reverb (wet) signal

---

### Parameter Relationships

**Master Parameters** (control other parameters):
- ER Spin On
- Chorus On
- LowShelf On
- HiFilter On
- Freeze On

**Dependencies**:
- **HiFilter Freq** controls: H, i, F, i, l, t, e, r,  , O, n
- **LowShelf Gain** controls: L, o, w, S, h, e, l, f,  , O, n
- **LowShelf Freq** controls: L, o, w, S, h, e, l, f,  , O, n
- **ER Spin Amount** controls: E, R,  , S, p, i, n,  , O, n
- **ER Spin Rate** controls: E, R,  , S, p, i, n,  , O, n
- **HiShelf Gain** controls: H, i, F, i, l, t, e, r,  , O, n
- **Chorus Amount** controls: C, h, o, r, u, s,  , O, n
- **Chorus Rate** controls: C, h, o, r, u, s,  , O, n

---

## Delay

**Device Signature**: `9bfcc8b6e739d9675c03f6fe0664cfada9ef7df1`
**Type**: delay
**Parameters**: 21

---

### Device

**Description**: Device on/off control
**Sonic Focus**: Enable or disable the entire effect

---

#### Device On

**Control Type**: binary
**Values**: Off / On

**Function**: Master bypass switch for entire delay device
**Increasing**: Enables delay processing; adds echo, space, and rhythm to signal
**Decreasing**: Bypasses all delay processing; passes dry signal through unchanged
**Use Cases**:
  - Quick A/B comparison of dry vs delayed signal
  - Automation for rhythmic delay drops
  - CPU conservation when delay not needed
**Typical Values**:
  - on: Active - full delay processing
  - off: Bypass - no delay processing

---

### Feedback

**Description**: Amount of output fed back into delay lines
**Sonic Focus**: Control delay repetition and sustain

**Technical Notes**:
- High feedback values produce infinite echoes
- Freeze endlessly cycles audio in buffer, ignoring new input

---

#### Feedback

**Control Type**: continuous
**Range**: 0.0 to 95.0 %

**Function**: Amount of delay output fed back into input for repeating echoes
**Increasing**: More repeats; longer decay; builds density; approaches infinite at high values; can self-oscillate
**Decreasing**: Fewer repeats; quick decay; cleaner; single echo at 0%
**Technical**: Internal feedback loop - each repeat is Feedback% of previous. At 0% = single delay, ~70-80% = noticeable decay, 95% = very long sustain approaching infinite.
**Use Cases**:
  - 0-30%: Single slapback or doubling
  - 40-60%: Multiple distinct echoes
  - 70-85%: Dense, reverb-like delay cloud
  - 90-95%: Infinite-style delays, dub effects, watch levels!
**Typical Values**:
  - reverb_like: 60-75%
  - single_echo: 0-20%
  - dub_delay: 75-90%
  - infinite: 90-95% (watch for buildup!)
  - short_tail: 30-50%

---

#### Freeze

**Control Type**: binary
**Values**: Off / On

**Function**: Captures and endlessly cycles current delay buffer, ignoring new input
**Increasing**: Freezes delay content; infinite sustain; no new input processed; creates pad-like textures
**Decreasing**: Normal delay operation; new input processed; natural decay according to Feedback
**Technical**: Disables input and sets internal feedback to 100%, creating infinite loop. Current buffer content sustains unchanged until Freeze disabled.
**Use Cases**:
  - Create ambient pads from delay tails
  - Freeze rhythmic patterns for layering
  - Build tension by sustaining delay content
  - Sound design - isolate and sustain delay artifacts
**Typical Values**:
  - on: Frozen buffer - use for pads/textures
  - off: Normal delay operation

---

### Filter Section

**Description**: Band-pass filter to shape delay repeats
**Sonic Focus**: Tone shaping to prevent buildup of lows or harsh highs

**Technical Notes**:
- Filter frequency and width controlled via X-Y controller in Live
- Disabled when Freeze is active

---

#### Filter On

**Control Type**: binary
**Values**: Off / On

**Function**: Enables band-pass filter in feedback loop to shape repeating echoes
**Increasing**: Activates filter; shapes frequency content of repeats; prevents buildup; adds character
**Decreasing**: Bypasses filter; full-range repeats; natural decay; more hi-fi
**Technical**: Band-pass filter in feedback path - each repeat passes through filter, progressively shaping tone. Essential for controlling frequency buildup at high feedback.
**Use Cases**:
  - Prevent muddy low-end buildup with high feedback
  - Create telephone/radio-style filtered delays
  - Dub-style frequency sweeps (automate Filter Freq)
  - Isolate specific frequency ranges in repeats
**Typical Values**:
  - on: Use Filter Freq/Width to shape tone
  - off: Clean, full-range delays

---

#### Filter Freq

**Control Type**: continuous
**Range**: 50.0 to 18000.0 Hz

**Function**: Center frequency of band-pass filter shaping delay repeats
**Increasing**: Higher center frequency; brighter, thinner repeats; less bass; telephone-like at extremes
**Decreasing**: Lower center frequency; darker, warmer repeats; more bass; can muddy at extremes
**Technical**: Exponential 50-18000Hz range. Sets center of bandpass - frequencies outside band are attenuated in feedback loop.
**Use Cases**:
  - 50-200Hz: Extreme lo-fi, bass-only delays
  - 300-800Hz: Telephone/radio character, vocal focus
  - 1000-3000Hz: Presence boost, cut lows and highs
  - 5000-12000Hz: Bright, airy delays, cut body
  - Automate for dub-style filter sweeps
**Typical Values**:
  - bright: 5000-10000Hz
  - presence: 1500-3000Hz
  - bass: 100-300Hz
  - telephone: 500-1000Hz

---

#### Filter Width

**Control Type**: continuous
**Range**: 0.5 to 9.0

**Function**: Bandwidth of band-pass filter - controls how much frequency range passes through
**Increasing**: Wider bandwidth; more frequencies pass; fuller sound; less filtering effect
**Decreasing**: Narrower bandwidth; fewer frequencies pass; thinner, more focused; stronger filtering
**Technical**: Range 0.5-9.0 (unitless Q factor). Low values = narrow, resonant filter. High values = gentle, broad filter.
**Use Cases**:
  - 0.5-2.0: Narrow, resonant filtering - isolate specific range
  - 2.5-5.0: Moderate filtering - shape without thinning too much
  - 6.0-9.0: Gentle filtering - subtle tone shaping
**Typical Values**:
  - wide: 6.0-9.0 (subtle shaping)
  - moderate: 3.0-5.0 (balanced)
  - narrow: 0.5-2.0 (strong character)

---

### Modulation

**Description**: LFO modulation for analog/tape-style delay character
**Sonic Focus**: Add movement and variation to delay times and filter

**Technical Notes**:
- Mod Freq sets LFO rate in Hertz
- Time modulation affects delay time for chorus-like effects
- Filter modulation adds movement to filter frequency
- Disabled when Freeze is active

---

#### Mod Freq

**Control Type**: continuous
**Range**: 0.01 to 40.0 Hz

**Function**: LFO rate in Hertz modulating delay time and/or filter frequency
**Increasing**: Faster modulation; quicker wobble; chorus to vibrato; can sound unstable at extremes
**Decreasing**: Slower modulation; gentle drift; subtle movement; more natural
**Technical**: Exponential 0.01-40Hz LFO. Low rates (0.01-0.5Hz) create slow drift, mid rates (0.5-5Hz) chorus-like, high rates (5-40Hz) vibrato to ring modulation effects.
**Use Cases**:
  - 0.01-0.3Hz: Slow tape-like drift, subtle movement
  - 0.5-3Hz: Chorus-like modulation, analog warmth
  - 3-8Hz: Vibrato effects, obvious modulation
  - 10-40Hz: Extreme vibrato, ring mod-like artifacts
**Typical Values**:
  - chorus: 0.5-2Hz
  - subtle: 0.05-0.2Hz
  - extreme: 10-40Hz
  - vibrato: 4-8Hz

---

#### Dly < Mod

**Control Type**: continuous
**Range**: 0.0 to 100.0 %

**Function**: Amount of LFO modulation applied to delay time
**Increasing**: More delay time variation; stronger chorus/vibrato; pitch warble; can be disorienting at extremes
**Decreasing**: Less variation; stable delay time; cleaner; subtle movement
**Technical**: 0-100% modulation depth. With Repitch mode, creates pitch shifting like tape wow/flutter. With Fade mode, creates time-stretch-like effects without pitch change.
**Use Cases**:
  - 0-10%: Subtle analog warmth, tape-like drift
  - 10-30%: Light chorus effect, movement
  - 30-60%: Obvious chorus, BBD-style analog delay
  - 60-100%: Extreme pitch modulation, special effects
  - Combine with slow Mod Freq for tape wow/flutter emulation
**Typical Values**:
  - chorus: 20-40% (chorus-like)
  - subtle: 5-15% (analog warmth)
  - extreme: 80-100% (special effects)
  - vibrato: 50-80% (obvious pitch)

---

#### Filter < Mod

**Control Type**: continuous
**Range**: 0.0 to 100.0 %

**Function**: Amount of LFO modulation applied to filter frequency
**Increasing**: More frequency sweeping; wah-like movement; dynamic filtering; can overwhelm at extremes
**Decreasing**: Less sweeping; static filter; cleaner; subtle movement
**Technical**: 0-100% modulation depth applied to Filter Freq. Creates auto-wah or phaser-like sweeping of filter center frequency.
**Use Cases**:
  - 0-15%: Subtle filter animation, analog-style drift
  - 20-40%: Noticeable auto-wah character
  - 50-75%: Strong sweeping, phaser-like effects
  - 80-100%: Extreme frequency sweeps, special effects
  - Combine with narrow Filter Width for resonant sweeps
**Typical Values**:
  - subtle: 5-15% (gentle sweep)
  - strong: 60-85% (dramatic sweeps)
  - extreme: 90-100% (full range sweeps)
  - auto_wah: 25-50% (obvious movement)

---

### Output

**Description**: Mix control between dry and wet signals
**Sonic Focus**: Balance processed delay with original signal

**Technical Notes**:
- Set to 100% on return tracks

---

#### Dry/Wet

**Control Type**: continuous
**Range**: 0.0 to 100.0 %

**Function**: Mix balance between unprocessed (dry) signal and delayed (wet) signal
**Increasing**: More delay in mix; more echo; can overwhelm dry signal; use 100% on return tracks
**Decreasing**: Less delay in mix; more dry signal; clearer; no delay at 0%
**Technical**: 0-100% wet mix. Insert use typically 10-40% wet. Return track use always 100% wet (dry signal already in mix). Equal-loudness toggle maintains perceived volume at 50/50.
**Use Cases**:
  - 0-20%: Subtle thickening, doubling effects
  - 20-40%: Clear delay presence, still dry-forward
  - 40-60%: Balanced wet/dry, obvious delay
  - 60-80%: Delay-forward, ambient
  - 100%: Return track use, parallel processing
**Typical Values**:
  - return_track: 100% (always)
  - balanced_insert: 30-50%
  - subtle_insert: 10-25%
  - ambient: 60-80%

---

### Ping Pong

**Description**: Stereo bouncing effect between left and right
**Sonic Focus**: Create wide stereo delay bouncing

**Technical Notes**:
- Signal alternates between left and right output

---

#### Ping Pong

**Control Type**: binary
**Values**: Off / On

**Function**: Alternates delayed signal between left and right outputs
**Increasing**: Signal bounces L→R→L; wide stereo field; rhythmic spatial movement
**Decreasing**: Normal stereo delay; static positioning; L and R independent
**Technical**: Internally cross-feeds delay lines - left output feeds right delay input and vice versa, creating bouncing effect.
**Use Cases**:
  - Wide stereo delay effects
  - Dub-style spatial movement
  - Rhythmic call-and-response patterns
  - Maximize stereo width with medium-high feedback
**Typical Values**:
  - on: Bouncing stereo (use with tempo sync for rhythmic bounce)
  - off: Standard stereo delay

---

### Time & Sync

**Description**: Delay time controls with tempo sync or free milliseconds
**Sonic Focus**: Core delay timing and synchronization

**Technical Notes**:
- Sync switches toggle between beat divisions (16ths) and milliseconds
- Link engages Stereo Link, applying left channel settings to right
- Delay Mode: Repitch creates tape-style pitch shifts, Fade crossfades smoothly, Jump immediately changes time

---

#### Delay Mode

**Control Type**: quantized

**Function**: Transition mode when changing delay time while processing audio
**Technical**: Determines how delay buffer responds to time changes. Repitch emulates tape mechanics with doppler shift, Fade uses crossfading to avoid artifacts, Jump is instant but can click.
**Use Cases**:
  - Repitch: Tape-style analog delay emulation, creative pitch effects
  - Fade: Performance-safe time changes, smooth transitions
  - Jump: Glitch effects, rhythmic stutters, aggressive sound design
**Typical Values**:
  - repitch: Default - tape-like pitch shifts (most musical)
  - jump: Instant - clicks present (special effects)
  - fade: Smooth - no artifacts (best for automation)

---

#### Link

**Control Type**: binary
**Values**: Off / On

**Function**: Stereo link - applies left channel's Sync and Time settings to right channel
**Increasing**: Locks both channels to same timing; mono-like delay behavior; centered image
**Decreasing**: Independent L/R timing; wide stereo image; complex rhythmic patterns
**Use Cases**:
  - Simplify control when identical L/R delays desired
  - Create centered, mono-style delay effects
  - Quick rhythmic delay setup with single time control
**Typical Values**:
  - on: Linked - centered mono delay
  - off: Independent L/R - stereo width

---

#### L Sync

**Control Type**: binary
**Values**: Off / On

**Function**: Toggles left channel between tempo-synced beat divisions and free milliseconds
**Increasing**: Beat-synced delay (16th note divisions); locked to tempo; rhythmic precision
**Decreasing**: Free time in milliseconds; independent of tempo; smooth time sweeps
**Use Cases**:
  - On: Rhythmic delays locked to song tempo
  - Off: Slapback, doubling, creative time-based effects
  - Off: Smooth delay time automation without rhythmic jumps
**Typical Values**:
  - on: Tempo sync - use L 16th divisions
  - off: Free time (1-5000ms) - use L Time knob

---

#### R Sync

**Control Type**: binary
**Values**: Off / On

**Function**: Toggles right channel between tempo-synced beat divisions and free milliseconds
**Increasing**: Beat-synced delay (16th note divisions); locked to tempo; rhythmic precision
**Decreasing**: Free time in milliseconds; independent of tempo; smooth time sweeps
**Use Cases**:
  - On: Rhythmic delays locked to song tempo
  - Off: Slapback, doubling, creative time-based effects
  - Mix: L synced + R free for complex polyrhythmic patterns
**Typical Values**:
  - on: Tempo sync - use R 16th divisions
  - off: Free time (1-5000ms) - use R Time knob

---

#### L Time

**Control Type**: continuous
**Range**: 1.0 to 5000.0 ms

**Function**: Left channel delay time in milliseconds when Sync is off
**Increasing**: Longer delays; increased space; more separation from source; rhythmic slowing
**Decreasing**: Shorter delays; tight to source; slapback to doubling character; faster rhythm
**Technical**: Exponential range 1-5000ms. Short times (1-50ms) create doubling/chorus, medium (50-500ms) slapback/echo, long (500-5000ms) rhythmic delays.
**Use Cases**:
  - 1-15ms: Doubling, thickening, subtle width
  - 20-80ms: Slapback echo (classic vocal effect)
  - 100-300ms: Quarter note-ish delays at various tempos
  - 500-5000ms: Long atmospheric delays, special effects
**Typical Values**:
  - special_fx: 2000-5000ms
  - doubling: 5-15ms
  - long_delay: 400-2000ms
  - short_echo: 150-300ms
  - slapback: 50-120ms

---

#### R Time

**Control Type**: continuous
**Range**: 1.0 to 5000.0 ms

**Function**: Right channel delay time in milliseconds when Sync is off
**Increasing**: Longer delays; increased space; more separation from source; rhythmic slowing
**Decreasing**: Shorter delays; tight to source; slapback to doubling character; faster rhythm
**Technical**: Exponential range 1-5000ms. Different L/R times create stereo width and polyrhythmic patterns.
**Use Cases**:
  - Match L Time for centered mono delay
  - Offset from L Time for wide stereo field
  - Create polyrhythmic patterns with different L/R times
  - Subtle offset (10-30ms) for stereo width without obvious delay
**Typical Values**:
  - polyrhythm: Different rhythmic values from L
  - stereo_width: L Time ± 10-50ms
  - mono_match: Same as L Time

---

#### L 16th

**Control Type**: quantized

**Function**: Left channel tempo-synced delay time in 16th note divisions when Sync is on
**Increasing**: Longer beat divisions; slower rhythm; more space between repeats
**Decreasing**: Shorter divisions; faster rhythm; tighter rhythmic patterns
**Technical**: Values 1, 2, 3, 4, 5, 6, 8, 16 represent multiples of 16th notes. 4 = quarter note, 8 = half note, 16 = whole note.
**Use Cases**:
  - 1-2: Very fast rhythmic delays (16th-8th notes)
  - 3-4: Standard rhythmic delays (dotted 8th, quarter)
  - 5-8: Slower delays (dotted quarter to half note)
  - 16: Whole note delays, long atmospheric
**Typical Values**:
  - long: 16 (whole note)
  - slow: 6-8 (half note range)
  - groove: 3-4 (dotted 8th-quarter)
  - fast: 1-2 (16th-8th note)

---

#### R 16th

**Control Type**: quantized

**Function**: Right channel tempo-synced delay time in 16th note divisions when Sync is on
**Increasing**: Longer beat divisions; slower rhythm; more space between repeats
**Decreasing**: Shorter divisions; faster rhythm; tighter rhythmic patterns
**Technical**: Values 1, 2, 3, 4, 5, 6, 8, 16 represent multiples of 16th notes. Different L/R divisions create polyrhythmic patterns.
**Use Cases**:
  - Match L 16th for centered mono delay
  - Offset for polyrhythmic patterns (e.g., L=4, R=3)
  - Create complex rhythmic textures with Ping Pong
  - Dub-style delays with different L/R divisions
**Typical Values**:
  - polyrhythm: Different divisions for complexity
  - dotted_rhythm: L=4, R=3 (quarter + dotted 8th)
  - mono_match: Same as L 16th

---

#### L Offset

**Control Type**: continuous
**Range**: -33.0 to 33.0 %

**Function**: Fine-tune left delay time offset as percentage when in Sync mode
**Increasing**: Delays timing later (positive offset); pushes beat slightly behind; laid-back groove
**Decreasing**: Advances timing earlier (negative offset); pulls beat forward; rushed feel
**Technical**: ±33% offset of selected beat division. At L 16th = 4 (quarter note), ±33% = ±33% of quarter note duration.
**Use Cases**:
  - Create swing or shuffle feels in synced delays
  - Offset delays slightly behind beat for laid-back feel
  - Slight advancement for pushing energy
  - Humanize mechanical synced delays
**Typical Values**:
  - push: -5 to -10% - ahead of beat energy
  - extreme: ±25 to ±33% - strong swing/rush
  - swing: +10 to +20% - behind beat groove
  - centered: 0% - on the beat

---

#### R Offset

**Control Type**: continuous
**Range**: -33.0 to 33.0 %

**Function**: Fine-tune right delay time offset as percentage when in Sync mode
**Increasing**: Delays timing later (positive offset); pushes beat slightly behind; laid-back groove
**Decreasing**: Advances timing earlier (negative offset); pulls beat forward; rushed feel
**Technical**: ±33% offset of selected beat division. Different L/R offsets create stereo timing variation and width.
**Use Cases**:
  - Match L Offset for centered timing adjustment
  - Offset differently from L for wide stereo field
  - Create subtle stereo movement with small L/R differences
  - Polyrhythmic patterns with different L/R offsets
**Typical Values**:
  - stereo_wide: Opposite sign from L Offset
  - match_L: Same as L Offset for mono
  - stereo_subtle: L Offset ± 5-10%

---

### Parameter Relationships

**Master Parameters** (control other parameters):
- L Sync
- R Sync
- Freeze
- Filter On

**Dependencies**:
- **Dly < Mod** controls: F, r, e, e, z, e
- **R 16th** controls: R,  , S, y, n, c
- **Mod Freq** controls: F, r, e, e, z, e
- **Filter Width** controls: F, i, l, t, e, r,  , O, n
- **Filter < Mod** controls: F, r, e, e, z, e
- **Filter Freq** controls: F, i, l, t, e, r,  , O, n
- **L 16th** controls: L,  , S, y, n, c

---

## Align Delay

**Device Signature**: `82da8ccee34e85facb2a264e3110618dc199938e`
**Type**: utility
**Parameters**: 15

---

### Device

**Description**: Device on/off control
**Sonic Focus**: Enable or disable the delay alignment

---

#### Device On

**Control Type**: binary
**Values**: off / on

---

### Distance Delay

**Description**: Distance-based delay with temperature compensation (Mode=Distance)
**Sonic Focus**: Calculate delays based on physical distance and speed of sound

**Technical Notes**:
- Active only when Mode=Distance
- Temperature affects speed of sound calculation
- Can use Meters or Feet via DistUnit toggle
- Can use Celsius or Fahrenheit via TempUnit toggle

---

#### Left meter

**Control Type**: continuous
**Range**: 0.0 to 100.0 m

---

#### Right meter

**Control Type**: continuous
**Range**: 0.0 to 100.0 m

---

#### Left Feet

**Control Type**: continuous
**Range**: 0.0 to 328.08 ft

---

#### Right Feet

**Control Type**: continuous
**Range**: 0.0 to 328.08 ft

---

#### Celsius

**Control Type**: continuous
**Range**: -20.0 to 60.0 °C

---

#### Fahrenheit

**Control Type**: continuous
**Range**: -4.0 to 140.0 °F

---

### Link

**Description**: Synchronize left and right delays
**Sonic Focus**: Lock left and right delay values together

---

#### Link L/R

**Control Type**: binary
**Values**: off / on

---

### Mode Selection

**Description**: Choose delay measurement mode
**Sonic Focus**: Time-based, sample-based, or distance-based delay

**Technical Notes**:
- Time mode: delays in milliseconds
- Samples mode: delays in sample count
- Distance mode: delays based on physical distance and temperature

---

#### Mode

**Control Type**: quantized

---

### Sample Delay

**Description**: Sample-based delay (Mode=Samples)
**Sonic Focus**: Sample-accurate alignment up to 200 samples

**Technical Notes**:
- Active only when Mode=Samples

---

#### Delay L Smp

**Control Type**: continuous
**Range**: 0.0 to 200.0 smp

---

#### Delay R smp

**Control Type**: continuous
**Range**: 0.0 to 200.0 smp

---

### Time Delay

**Description**: Time-based delay in milliseconds (Mode=Time)
**Sonic Focus**: Precise timing alignment up to 100ms

**Technical Notes**:
- Active only when Mode=Time

---

#### Left ms

**Control Type**: continuous
**Range**: 0.0 to 100.0 ms

---

#### Right ms

**Control Type**: continuous
**Range**: 0.0 to 100.0 ms

---

### Unit Selection

**Description**: Choose measurement units
**Sonic Focus**: Toggle between Meters/Feet and Celsius/Fahrenheit

---

#### DistUnit

**Control Type**: quantized

---

#### TempUnit

**Control Type**: quantized

---

### Parameter Relationships

**Master Parameters** (control other parameters):
- Mode

---

## Amp

**Device Signature**: `d554752f4be9eee62197c37b45b1c22237842c37`
**Type**: amp
**Parameters**: 10

---

### Amp Model

**Description**: Amplifier selection
**Sonic Focus**: Choose between seven classic amp models

**Technical Notes**:
- Each model has distinct tonal characteristics and distortion curves
- Physical modeling technology emulates electrical characteristics

---

#### Amp Type

**Control Type**: quantized

---

### Device

**Description**: Device on/off control
**Sonic Focus**: Enable or disable the entire effect

---

#### Device On

**Control Type**: binary
**Values**: Off / On

---

### Drive & Output

**Description**: Gain staging and output controls
**Sonic Focus**: Control distortion amount and output level

**Technical Notes**:
- Gain: primary distortion control (preamp)
- Volume: output level; adds power amp distortion on some models
- Dual Mono: doubles CPU, creates stereo width

---

#### Gain

**Control Type**: continuous
**Range**: 0.0 to 10.0

---

#### Volume

**Control Type**: continuous
**Range**: 0.0 to 10.0

---

#### Dual Mono

**Control Type**: binary
**Values**: Mono / Dual

---

#### Dry/Wet

**Control Type**: continuous
**Range**: 0.0 to 100.0 %

---

### Tone Controls

**Description**: EQ shaping in preamp and power amp stages
**Sonic Focus**: Shape frequency response and tonal character

**Technical Notes**:
- Bass/Middle/Treble: preamp stage EQ
- Presence: power amp stage high-frequency control
- Controls interact non-linearly with each other and with gain

---

#### Bass

**Control Type**: continuous
**Range**: 0.0 to 10.0

---

#### Middle

**Control Type**: continuous
**Range**: 0.0 to 10.0

---

#### Treble

**Control Type**: continuous
**Range**: 0.0 to 10.0

---

#### Presence

**Control Type**: continuous
**Range**: 0.0 to 10.0

---

### Parameter Relationships

---

## Compressor

**Device Signature**: `9e906e0ab3f18c4688107553744914f9ef6b9ee7`
**Type**: compressor
**Parameters**: 22

---

### Compression

**Description**: Core compression parameters
**Sonic Focus**: Control threshold, ratio, and attack/release envelope

**Technical Notes**:
- Threshold: level above which compression begins
- Ratio: amount of gain reduction applied above threshold
- Attack: how quickly compression engages after signal exceeds threshold
- Release: how quickly compression disengages after signal falls below threshold
- Auto Release adapts release time based on input signal dynamics

---

#### Threshold

**Control Type**: continuous
**Range**: -70.0 to 6.0 dB



---

#### Ratio

**Control Type**: continuous
**Range**: 1.0 to 100.0



---

#### Attack

**Control Type**: continuous
**Range**: 0.01 to 100.0 ms



---

#### Release

**Control Type**: continuous
**Range**: 1.0 to 3000.0 ms



---

#### Auto Release On/Off

**Control Type**: binary
**Values**: Off / On



---

#### Knee

**Control Type**: continuous
**Range**: 0.0 to 18.0 dB



---

#### Model

**Control Type**: quantized



---

### Device

**Description**: Device on/off control
**Sonic Focus**: Enable or disable the entire compressor effect

---

#### Device On

**Control Type**: binary
**Values**: Off / On



---

### Expansion

**Description**: Downward expansion (opposite of compression)
**Sonic Focus**: Reduce level of signals below threshold

**Technical Notes**:
- Expansion Ratio: amount of gain reduction for signals below threshold
- Useful for reducing noise floor or creating gating effects

---

#### Expansion Ratio

**Control Type**: continuous
**Range**: 1.0 to 2.0



---

### Output

**Description**: Output level and mixing controls
**Sonic Focus**: Control output gain, makeup gain, and dry/wet balance

**Technical Notes**:
- Output Gain: manual output level adjustment
- Makeup: automatic gain compensation (not available with external sidechain)
- Dry/Wet: blend between compressed and uncompressed signal
- LookAhead: analyze signal ahead of compression for more transparent results

---

#### Output Gain

**Control Type**: continuous
**Range**: -36.0 to 36.0 dB



---

#### Makeup

**Control Type**: binary
**Values**: Off / On



---

#### Dry/Wet

**Control Type**: continuous
**Range**: 0.0 to 100.0 %



---

#### LookAhead

**Control Type**: quantized



---

### Sidechain

**Description**: External sidechain input controls
**Sonic Focus**: Use external audio source to trigger compression

**Technical Notes**:
- S/C On: enable external sidechain input
- S/C Gain: adjust sidechain input level
- S/C Mix: blend between main input and sidechain (100% = full sidechain)
- S/C Listen: monitor sidechain signal for setup

---

#### S/C On

**Control Type**: binary
**Values**: Off / On



---

#### S/C Gain

**Control Type**: continuous
**Range**: -70.0 to 24.0 dB



---

#### S/C Mix

**Control Type**: continuous
**Range**: 0.0 to 100.0 %



---

#### S/C Listen

**Control Type**: binary
**Values**: Off / On



---

### Sidechain EQ

**Description**: Frequency-selective compression triggering
**Sonic Focus**: Filter sidechain signal to make compressor respond to specific frequencies

**Technical Notes**:
- S/C EQ On: enable sidechain EQ filtering
- Type: filter type (lowpass, bandpass, highpass, notch, peak)
- Freq: center/cutoff frequency
- Q: filter bandwidth/resonance
- Gain: boost/cut for peak filter type

---

#### S/C EQ On

**Control Type**: binary
**Values**: Off / On



---

#### S/C EQ Type

**Control Type**: quantized



---

#### S/C EQ Freq

**Control Type**: continuous
**Range**: 30.0 to 15000.0 Hz



---

#### S/C EQ Q

**Control Type**: continuous
**Range**: 0.1 to 18.0



---

#### S/C EQ Gain

**Control Type**: continuous
**Range**: -15.0 to 15.0 dB



---

### Parameter Relationships

**Master Parameters** (control other parameters):
- S/C On
- S/C EQ On

**Dependencies**:
- **S/C EQ Freq** controls: S, /, C,  , E, Q,  , O, n
- **S/C Mix** controls: S, /, C,  , O, n
- **S/C EQ Q** controls: S, /, C,  , E, Q,  , O, n
- **S/C Gain** controls: S, /, C,  , O, n
- **S/C EQ Gain** controls: S, /, C,  , E, Q,  , O, n
- **S/C EQ Type** controls: S, /, C,  , E, Q,  , O, n
- **S/C Listen** controls: S, /, C,  , O, n

---
