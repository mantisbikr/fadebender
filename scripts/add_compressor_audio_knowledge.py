#!/usr/bin/env python3
"""
Add comprehensive audio engineering knowledge to Compressor device mapping.
Phase 7: Audio Knowledge Curation
"""
import sys
import os
import argparse
os.environ["FIRESTORE_DATABASE_ID"] = "dev-display-value"
sys.path.insert(0, '/Users/sunils/ai-projects/fadebender')

from google.cloud import firestore
import json

COMPRESSOR_SIGNATURE = "9e906e0ab3f18c4688107553744914f9ef6b9ee7"

# Comprehensive audio knowledge for each parameter
PARAM_AUDIO_KNOWLEDGE = {
    "Device On": {
        "description": "Enables or bypasses the entire compressor effect",
        "sonic_impact": "When off, audio passes through unprocessed. Essential for A/B comparison of compressed vs. uncompressed signal.",
        "common_uses": ["Quick bypass for comparing processed and dry signal", "Automation to dynamically enable compression on specific sections"],
        "typical_ranges": {"Off": "Signal passes through unprocessed", "On": "Compression is active"},
        "interaction_notes": "When off, all other parameters have no effect on the signal"
    },
    
    "Threshold": {
        "description": "Sets the level (in dB) above which compression begins. Signals below threshold pass through unaffected.",
        "sonic_impact": "Lower threshold = more of the signal is compressed (more consistent but potentially less dynamic). Higher threshold = only peaks are controlled (more natural dynamics).",
        "common_uses": [
            "Vocals: -20 to -10 dB for consistent level",
            "Drums: -15 to -5 dB to control transients",
            "Bass: -20 to -12 dB for even low-end",
            "Mix bus: -6 to 0 dB for gentle glue"
        ],
        "typical_ranges": {
            "Gentle compression": "-20 to -15 dB",
            "Medium compression": "-15 to -8 dB",
            "Aggressive compression": "-8 to 0 dB"
        },
        "interaction_notes": "Works closely with Ratio - lower threshold with lower ratio = gentle overall compression. Lower threshold with high ratio = aggressive limiting effect."
    },
    
    "Ratio": {
        "description": "Determines compression strength. At 4:1, a 4dB increase above threshold becomes 1dB increase at output.",
        "sonic_impact": "Low ratios (2:1-3:1) sound transparent and musical. High ratios (8:1+) create obvious compression, useful for control or creative effects. 20:1+ acts as limiting.",
        "common_uses": [
            "Vocals: 3:1 to 6:1 for natural control",
            "Drums (kick/snare): 4:1 to 8:1 for punch",
            "Bass: 2:1 to 4:1 for consistency",
            "Master bus: 2:1 to 3:1 for glue",
            "Limiting: 10:1 to 20:1"
        ],
        "typical_ranges": {
            "Gentle (transparent)": "1:1 to 3:1",
            "Medium (musical)": "3:1 to 6:1",
            "Heavy (obvious)": "6:1 to 10:1",
            "Limiting": "10:1 to 20:1"
        },
        "interaction_notes": "Higher ratios require faster attack times to catch transients. With makeup gain, higher ratios can create aggressive 'pumping' effects."
    },
    
    "Expansion Ratio": {
        "description": "Controls downward expansion - reduces level of signals BELOW threshold. Opposite of compression.",
        "sonic_impact": "Increases dynamic range by making quiet parts quieter. Useful for noise reduction, creating space, or enhancing contrast between loud and soft passages.",
        "common_uses": [
            "Noise gate alternative (more musical than hard gating)",
            "Reducing room noise between vocal phrases",
            "Enhancing dynamic contrast in acoustic recordings",
            "Creating 'breathing' space in dense mixes"
        ],
        "typical_ranges": {
            "Subtle expansion": "1.0 to 1.5",
            "Moderate expansion": "1.5 to 3.0",
            "Strong expansion/gating": "3.0 to 10.0"
        },
        "interaction_notes": "Works below threshold while compression works above it. Can be used simultaneously for full dynamic control."
    },
    
    "Attack": {
        "description": "Time (in milliseconds) for compression to engage after signal exceeds threshold. Critical for transient shaping.",
        "sonic_impact": "Fast attack (< 5ms) = catches transients, can dull impact. Slow attack (> 20ms) = preserves punch, lets transients through before compression kicks in.",
        "common_uses": [
            "Vocals: 3-10ms for smooth, controlled sound",
            "Drums (punch): 10-30ms to preserve crack/thwack",
            "Drums (control): 0.1-2ms to tame peaks",
            "Bass: 20-50ms to preserve note attack",
            "De-essing: 0.1-1ms for fast sibilance control"
        ],
        "typical_ranges": {
            "Ultra-fast (peak control)": "0.01 to 1ms",
            "Fast (transient control)": "1 to 5ms",
            "Medium (balanced)": "5 to 15ms",
            "Slow (preserve punch)": "15 to 100ms+"
        },
        "interaction_notes": "Interacts closely with Release - fast attack + fast release = pumping. Fast attack + slow release = smooth leveling. Slow attack preserves transients that Ratio would otherwise reduce."
    },
    
    "Release": {
        "description": "Time for compression to return to normal after signal drops below threshold. Affects naturalness and groove.",
        "sonic_impact": "Fast release (< 100ms) = transparent, follows dynamics closely, can sound pumpy. Slow release (> 300ms) = smooth, musical, can sound sluggish on fast material.",
        "common_uses": [
            "Vocals: 40-150ms for natural response",
            "Drums: 50-150ms for rhythmic pump",
            "Bass: 100-300ms for smooth sustain",
            "Bus compression: 0.3-0.6s for glue",
            "Pumping effect: 20-80ms (timed to tempo)"
        ],
        "typical_ranges": {
            "Fast (transparent/pumpy)": "10 to 100ms",
            "Medium (musical)": "100 to 300ms",
            "Slow (smooth/glue)": "300 to 1000ms"
        },
        "interaction_notes": "Release time creates the compressor's 'character'. Too fast = unnatural pumping. Too slow = compression doesn't reset between transients. Should often match tempo for rhythmic material."
    },
    
    "Auto Release On/Off": {
        "description": "When enabled, release time adapts dynamically based on incoming signal. Program-dependent compression.",
        "sonic_impact": "Creates more natural, transparent compression that responds intelligently to different material. Fast material gets faster release, sustained notes get slower release.",
        "common_uses": [
            "Mixed program material (full mixes, complex sources)",
            "When you want 'set and forget' compression",
            "Material with varying dynamics and rhythms",
            "Quick compression without extensive tweaking"
        ],
        "typical_ranges": {
            "Off": "Manual release time (full control)",
            "On": "Adaptive release (automatic, program-dependent)"
        },
        "interaction_notes": "When enabled, the manual Release control is overridden. Best for complex material; manual control better for specific sounds."
    },
    
    "Output Gain": {
        "description": "Manual output level adjustment in dB. Compensates for level reduction caused by compression.",
        "sonic_impact": "Adds gain after compression. Essential for level matching when comparing compressed vs. uncompressed (louder often sounds 'better' but may not be).",
        "common_uses": [
            "Gain compensation after heavy compression",
            "Level matching for A/B comparison",
            "Driving into subtle distortion/saturation",
            "Parallel compression blend control"
        ],
        "typical_ranges": {
            "Light compression": "0 to 6 dB",
            "Medium compression": "6 to 15 dB",
            "Heavy compression": "15 to 30 dB"
        },
        "interaction_notes": "Use with Makeup off for manual control. Amount needed depends on Threshold, Ratio, and input signal level. Watch for clipping at output."
    },
    
    "Makeup": {
        "description": "Automatic gain compensation. Analyzes gain reduction and adds back approximately the same amount.",
        "sonic_impact": "Convenient for maintaining consistent perceived loudness. However, automatic makeup may not always match your desired output level.",
        "common_uses": [
            "Quick setup without gain matching math",
            "Maintaining consistent level during tweaking",
            "Starting point (then fine-tune with Output Gain)"
        ],
        "typical_ranges": {
            "Off": "Manual control via Output Gain",
            "On": "Automatic compensation"
        },
        "interaction_notes": "NOT available when using external sidechain (S/C On). When on, overrides Output Gain. For precise control, turn off and use Output Gain manually."
    },
    
    "Dry/Wet": {
        "description": "Blend control between uncompressed (dry) and compressed (wet) signal. Enables parallel compression.",
        "sonic_impact": "Parallel compression (< 100% wet) retains natural dynamics while adding power and density. Classic technique for drums, vocals, and mix bus.",
        "common_uses": [
            "Parallel drum compression: 30-50% wet (aggressive settings, heavy compression)",
            "Vocal parallel compression: 20-40% wet",
            "Mix bus parallel compression: 20-30% wet",
            "Full wet: 100% for normal compression"
        ],
        "typical_ranges": {
            "Normal compression": "100% wet",
            "Light parallel": "70-85% wet",
            "Medium parallel": "40-70% wet",
            "Heavy parallel": "20-40% wet (with aggressive compression)"
        },
        "interaction_notes": "Lower wet % allows more aggressive compression settings (high ratio, low threshold) since dry signal preserves transients and dynamics."
    },
    
    "Model": {
        "description": "Compression algorithm type: Peak (RMS/peak hybrid), RMS (average level), or Expand (includes expansion below threshold).",
        "sonic_impact": "Peak = catches fast transients, sounds precise. RMS = smoother, more musical, responds to average level. Expand = includes downward expansion.",
        "common_uses": [
            "Peak: Drums, transient-rich material, precise control",
            "RMS: Vocals, bass, mix bus, musical material",
            "Expand: When you need both compression AND expansion (full dynamic control)"
        ],
        "typical_ranges": {
            "Peak": "Fast response, transient control",
            "RMS": "Musical response, average level",
            "Expand": "Compression + expansion combined"
        },
        "interaction_notes": "RMS generally needs longer attack/release times than Peak for similar perceived compression. Expand mode enables Expansion Ratio parameter."
    },
    
    "Knee": {
        "description": "Transition smoothness around threshold. Low knee = abrupt (hard knee), high knee = gradual (soft knee).",
        "sonic_impact": "Hard knee (0.0) = obvious compression, can sound aggressive. Soft knee (1.0) = gentle, musical transition, less noticeable compression.",
        "common_uses": [
            "Hard knee (0.0-0.3): Precise control, limiting, obvious effect",
            "Medium knee (0.3-0.6): Balanced, versatile",
            "Soft knee (0.6-1.0): Transparent, musical, vocals, mix bus"
        ],
        "typical_ranges": {
            "Hard knee": "0.0 to 0.3",
            "Medium knee": "0.3 to 0.6",
            "Soft knee": "0.6 to 1.0"
        },
        "interaction_notes": "Soft knee makes compression less obvious, good for high ratios. Hard knee more pronounced, good for creative effects and obvious control."
    },
    
    "LookAhead": {
        "description": "Analyzes incoming signal slightly ahead of processing. Prevents overshoots and improves transient handling.",
        "sonic_impact": "More transparent compression, especially on fast transients. Catches peaks before they exceed threshold. Adds slight latency.",
        "common_uses": [
            "Mastering: maximum transparency",
            "Transient-rich material that needs precise control",
            "When you want most transparent possible compression",
            "Preventing overshoots on peak-controlled material"
        ],
        "typical_ranges": {
            "Off": "Zero latency, slightly less precise",
            "On": "Small latency, maximum precision and transparency"
        },
        "interaction_notes": "Most beneficial with fast attack times and high ratios. Small latency may cause phase issues in parallel setups - compensate with delay."
    },
    
    "S/C Listen": {
        "description": "Monitors the sidechain signal (what triggers compression). Essential for tuning sidechain EQ.",
        "sonic_impact": "Doesn't affect output - diagnostic tool only. Lets you hear exactly what frequency content is triggering compression.",
        "common_uses": [
            "Tuning sidechain EQ to isolate kick drum in mixed drums",
            "Verifying external sidechain input",
            "Diagnosing frequency-specific compression issues",
            "Setting up de-essing by isolating sibilant frequencies"
        ],
        "typical_ranges": {
            "Off": "Normal operation (compressed output)",
            "On": "Monitor sidechain signal (diagnostic)"
        },
        "interaction_notes": "Only audible when S/C EQ On or S/C On is enabled. Use to dial in EQ, then turn off for normal operation."
    },
    
    "S/C EQ On": {
        "description": "Enables frequency-selective compression triggering. Compression responds only to specific frequencies.",
        "sonic_impact": "Create frequency-specific dynamics (de-essing, controlling bass without affecting highs, etc.). Powerful for surgical compression.",
        "common_uses": [
            "De-essing: highpass to isolate sibilance (4-8kHz)",
            "Taming bass without dulling highs: lowpass around 200Hz",
            "Kick-triggered ducking from mixed drums: lowpass around 80Hz",
            "Controlling harsh mids: bandpass 2-4kHz"
        ],
        "typical_ranges": {
            "Off": "Compression responds to full frequency spectrum",
            "On": "Compression triggered by filtered signal"
        },
        "interaction_notes": "Enables S/C EQ Type, Freq, Q, and Gain controls. Use S/C Listen to tune the filter. Only affects detection, not output processing."
    },
    
    "S/C EQ Type": {
        "description": "Sidechain filter type: Lowpass, Bandpass, Highpass, Notch, or Peak. Determines which frequencies trigger compression.",
        "sonic_impact": "Shapes detection signal for frequency-specific compression. Lowpass = bass-triggered, Highpass = treble-triggered, Bandpass/Peak = specific range.",
        "common_uses": [
            "Lowpass: Kick-triggered ducking, bass-specific compression",
            "Highpass: De-essing, controlling sibilance",
            "Bandpass: Vocal presence control, specific frequency range",
            "Notch: Compression avoiding specific frequency",
            "Peak: Precise frequency-specific triggering"
        ],
        "typical_ranges": {
            "Lowpass": "Pass lows, trigger on bass/kick",
            "Bandpass": "Specific frequency range",
            "Highpass": "Pass highs, trigger on sibilance/cymbals",
            "Notch": "Remove specific frequency from detection",
            "Peak": "Emphasize specific frequency for detection"
        },
        "interaction_notes": "Use with S/C Listen to visualize filter effect. Freq and Q control the filter's center/cutoff and width."
    },
    
    "S/C EQ Freq": {
        "description": "Center/cutoff frequency for sidechain filter. Determines which frequency range triggers compression.",
        "sonic_impact": "Critical for frequency-selective compression. Wrong frequency = compression triggered by wrong content.",
        "common_uses": [
            "De-essing: 4-8kHz (where sibilance lives)",
            "Kick isolation: 60-100Hz",
            "Bass control: 80-200Hz",
            "Vocal presence: 2-5kHz"
        ],
        "typical_ranges": {
            "Sub-bass control": "40-80 Hz",
            "Bass/kick control": "60-150 Hz",
            "Body control": "200-500 Hz",
            "Presence control": "2-5 kHz",
            "De-essing": "4-10 kHz"
        },
        "interaction_notes": "Use S/C Listen to hear filtered signal while adjusting. Combine with Q to narrow or widen affected range. Sweep frequency to find problem area."
    },
    
    "S/C EQ Q": {
        "description": "Filter bandwidth/resonance. Low Q = wide, broad effect. High Q = narrow, surgical targeting.",
        "sonic_impact": "Controls selectivity. High Q isolates specific frequencies. Low Q affects broader range more musically.",
        "common_uses": [
            "Broad control: Q = 0.7-2.0 (musical, natural)",
            "Specific targeting: Q = 5-10 (surgical, precise)",
            "De-essing: Q = 2-5 (catch sibilance range)",
            "Kick isolation: Q = 1-3 (fundamental + harmonics)"
        ],
        "typical_ranges": {
            "Wide (musical)": "0.1 to 1.0",
            "Medium (balanced)": "1.0 to 5.0",
            "Narrow (surgical)": "5.0 to 18.0"
        },
        "interaction_notes": "Higher Q = more precise but can sound unnatural. Lower Q = broader, more musical response. Use S/C Listen to find sweet spot."
    },
    
    "S/C EQ Gain": {
        "description": "Boost or cut for Peak filter type. Emphasizes or reduces specific frequency in detection signal.",
        "sonic_impact": "Makes compression more or less sensitive to the filtered frequency. Boost = more triggering, Cut = less triggering at that frequency.",
        "common_uses": [
            "Boost: Emphasize kick fundamental for stronger ducking",
            "Boost: Enhance sibilance detection for de-essing",
            "Cut: Reduce unwanted frequency in detection",
            "Fine-tuning: Adjust sensitivity at target frequency"
        ],
        "typical_ranges": {
            "Cut": "-15 to 0 dB (reduce sensitivity)",
            "Flat": "0 dB (neutral)",
            "Boost": "0 to +15 dB (increase sensitivity)"
        },
        "interaction_notes": "Only active with Peak filter type. Use to fine-tune detection sensitivity without changing compression amount (Threshold does that)."
    },
    
    "S/C On": {
        "description": "Enables external sidechain input. Compression triggered by different audio source than what's being compressed.",
        "sonic_impact": "Classic 'ducking' effect. Bass ducks when kick hits, music ducks when voiceover speaks, creative rhythmic pumping.",
        "common_uses": [
            "Kick-triggered bass ducking (dance music staple)",
            "Voiceover ducking music (podcasts, narration)",
            "Rhythmic pumping effects (trance, house)",
            "Creative modulation (use any source to trigger compression)"
        ],
        "typical_ranges": {
            "Off": "Internal sidechain (compresses own signal)",
            "On": "External sidechain (choose external trigger)"
        },
        "interaction_notes": "When on, automatic Makeup is disabled (use Output Gain). Select external source in Live's routing. Combine with sidechain EQ for filtered detection."
    },
    
    "S/C Gain": {
        "description": "Adjusts external sidechain input level. Controls how strongly external source triggers compression.",
        "sonic_impact": "Higher gain = external source triggers compression more easily. Lower gain = requires stronger external signal to trigger compression.",
        "common_uses": [
            "Boosting weak sidechain trigger (0 to +12dB)",
            "Reducing strong sidechain trigger (-12 to 0dB)",
            "Fine-tuning ducking amount",
            "Compensating for level differences between tracks"
        ],
        "typical_ranges": {
            "Reduce sensitivity": "-24 to -6 dB",
            "Neutral": "0 dB",
            "Increase sensitivity": "+6 to +24 dB"
        },
        "interaction_notes": "Interact with Threshold to control overall compression amount. Higher S/C Gain = more compression for same Threshold setting."
    },
    
    "S/C Mix": {
        "description": "Blend between internal (0%) and external (100%) sidechain source. Enables hybrid triggering.",
        "sonic_impact": "100% = pure external sidechain. Lower values blend internal signal, creating hybrid detection that responds to both sources.",
        "common_uses": [
            "100%: Pure external ducking/sidechaining",
            "50-80%: Hybrid response (musical blend)",
            "0%: Bypass external sidechain (internal detection only)"
        ],
        "typical_ranges": {
            "Internal only": "0%",
            "Blend": "20-80%",
            "External only": "100%"
        },
        "interaction_notes": "Lower than 100% creates hybrid behavior - compression responds to both original and external signal. Useful for more musical, less obvious ducking."
    }
}

def add_audio_knowledge(auto_confirm=False):
    """Add comprehensive audio knowledge to Compressor mapping."""

    client = firestore.Client(database="dev-display-value")
    doc_ref = client.collection("device_mappings").document(COMPRESSOR_SIGNATURE)

    # Get current data
    doc = doc_ref.get()
    if not doc.exists:
        print(f"❌ Error: Compressor device not found")
        return False

    data = doc.to_dict()
    print(f"✓ Loaded Compressor device mapping")

    # Add audio knowledge to each parameter
    params_meta = data.get("params_meta", [])
    updated_count = 0

    print("\n" + "="*80)
    print("Adding audio knowledge to parameters...")
    print("="*80)

    for param in params_meta:
        name = param.get("name")
        if name in PARAM_AUDIO_KNOWLEDGE:
            param["audio_knowledge"] = PARAM_AUDIO_KNOWLEDGE[name]
            updated_count += 1
            print(f"  ✓ {name}")

    print(f"\n✓ Added audio knowledge to {updated_count} parameters")

    # Update params_meta
    data["params_meta"] = params_meta

    # Preview
    print("\n" + "="*80)
    print("PREVIEW")
    print("="*80)
    print(f"Device: Compressor")
    print(f"Parameters with audio knowledge: {updated_count}/{len(params_meta)}")
    
    # Show sample
    threshold = next((p for p in params_meta if p.get("name") == "Threshold"), None)
    if threshold and "audio_knowledge" in threshold:
        print(f"\nSample (Threshold):")
        ak = threshold["audio_knowledge"]
        print(f"  Description: {ak['description'][:80]}...")
        print(f"  Common uses: {len(ak['common_uses'])} listed")
        print(f"  Typical ranges: {len(ak['typical_ranges'])} defined")

    # Confirm
    print("\n" + "="*80)
    if auto_confirm:
        print("Auto-confirming changes...")
        response = 'yes'
    else:
        response = input("Apply audio knowledge to Firestore? (yes/no): ")

    if response.lower() not in ['yes', 'y']:
        print("❌ Aborted")
        return False

    # Update Firestore
    doc_ref.update(data)
    print("\n✅ SUCCESS - Audio knowledge added!")
    print(f"  Database: dev-display-value")
    print(f"  Parameters enriched: {updated_count}")

    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Add audio knowledge to Compressor")
    parser.add_argument('--yes', '-y', action='store_true', help='Auto-confirm')
    args = parser.parse_args()

    success = add_audio_knowledge(auto_confirm=args.yes)
    sys.exit(0 if success else 1)
