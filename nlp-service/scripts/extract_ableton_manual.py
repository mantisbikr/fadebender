#!/usr/bin/env python3
"""
Extract Ableton manual information and structure it for integration
into dev-display-value database.

Input: /tmp/reverb_ableton_manual_info.rtf (converted to text)
Output: Structured JSON with manual_context and sections data
"""

import json
from pathlib import Path

REVERB_SIGNATURE = "64ccfc236b79371d0b45e913f81bf0f3a55c6db9"
OUTPUT_FILE = Path(__file__).parent.parent / "docs" / "technical" / "reverb_manual_context.json"


def extract_manual_context():
    """Extract structured manual context from Ableton Live manual."""

    # Manual text extracted from RTF
    manual_data = {
        "device_signature": REVERB_SIGNATURE,
        "device_name": "Reverb",
        "device_description": "Reverb is an audio effect that simulates the acoustic properties of audio as it echoes throughout a physical space.",

        # Section-level knowledge for LLM context
        "sections": {
            "Input Processing": {
                "technical_name": "Input Filter",
                "description": "The input signal passes first through low and high cut filters, whose X-Y controller allows changing the band's center frequency (X-axis) and bandwidth (Y-axis).",
                "parameters": ["In Filter Freq", "In Filter Width", "In Filter Type"],
                "sonic_focus": "Pre-filtering to shape what enters the reverb"
            },

            "Early Reflections": {
                "technical_name": "Early Reflections",
                "description": "These are the earliest echoes that you hear after they bounce off a room's walls, before the onset of the diffused reverberation tail. Their amplitude and distribution give an impression of the room's character.",
                "parameters": ["ER Spin Amount", "ER Spin Rate", "ER Spin On", "ER Shape"],
                "sonic_focus": "Room character and spatial definition",
                "technical_notes": [
                    "Spin applies modulation to the early reflections",
                    "A higher Amount setting tends to provide a less-colored (more spectrally neutral) late diffusion response",
                    "If the modulation rate is too high, doppler frequency shifting of the source sound will occur, along with surreal panning effects",
                    "Shape control sculpts the prominence of the early reflections, as well as their overlap with the diffused sound",
                    "With small values, the reflections decay more gradually and the diffused sound occurs sooner",
                    "With large values, the reflections decay more rapidly and the diffused onset occurs later",
                    "A higher value can sometimes improve the source's intelligibility, while a lower value may give a smoother decay"
                ]
            },

            "Diffusion Network": {
                "technical_name": "Diffusion Network",
                "description": "The Diffusion Network creates the reverberant tail that follows the early reflections.",
                "parameters": ["Diffusion", "Scale", "HiFilter Freq", "HiFilter Type", "LowShelf Freq", "LowShelf Gain"],
                "sonic_focus": "Reverb tail texture and frequency response",
                "technical_notes": [
                    "High and low shelving filters provide frequency-dependent reverberation decay",
                    "The high-frequency decay models the absorption of sound energy due to air, walls and other materials in the room (people, carpeting and so forth)",
                    "The low shelf provides a thinner decay",
                    "The Diffusion and Scale parameters provide additional control over the diffusion's density and coarseness",
                    "When the room size is extremely small, have a large impact on the coloration contributed by the diffusion"
                ]
            },

            "Chorus": {
                "technical_name": "Chorus",
                "description": "The Chorus section adds a little modulation and motion to the diffusion.",
                "parameters": ["Chorus Amount", "Chorus Rate", "Chorus On"],
                "sonic_focus": "Movement and richness in the reverb tail",
                "technical_notes": [
                    "You can control the modulation Amount and Rate, or deactivate it altogether"
                ]
            },

            "Global Settings": {
                "technical_name": "Global Settings",
                "description": "Controls that affect the overall reverb character including size, decay, and special functions.",
                "parameters": ["Predelay", "Room Size", "Decay Time", "Stereo Image", "Density", "Freeze On", "Cut On", "Flat On", "Quality"],
                "sonic_focus": "Overall space character and special effects",
                "technical_notes": [
                    "Predelay controls the delay time, in milliseconds, before the onset of the first early reflection",
                    "One's impression of the size of a real room depends partly on this delay",
                    "Typical values for natural sounds range from 1 ms to 25 ms",
                    "The Size parameter controls the room's volume",
                    "At one extreme, a very large size will lend a shifting, diffused delay effect to the reverb",
                    "The other extreme — a very small value — will give it a highly colored, metallic feel",
                    "The Decay control adjusts the time required for this reverb tail to drop to 1/1000th (-60 dB) of its initial amplitude",
                    "The Freeze control freezes the diffuse response of the input sound. When on, the reverberation will sustain almost endlessly",
                    "Flat bypasses the high and low shelf filters when Freeze is on",
                    "Cut modifies Freeze by preventing the input signal from adding to the frozen reverberation",
                    "The Stereo control determines the width of the output's stereo image",
                    "At the highest setting of 120 degrees, each ear receives a reverberant channel that is independent of the other (this is also a property of the diffusion in real rooms)",
                    "The Density chooser controls the tradeoff between reverb quality and performance. Sparse uses minimal CPU resources, while High delivers the richest reverberation"
                ]
            },

            "Output": {
                "technical_name": "Output",
                "description": "At the reverb output, you can vary the amplitude of reflections and diffusion with the Reflect and Diffuse controls and adjust the effect's overall Dry/Wet mix.",
                "parameters": ["Reflect Level", "Diffuse Level", "Dry/Wet"],
                "sonic_focus": "Balance between early reflections, reverb tail, and dry signal"
            }
        },

        # Parameter-specific manual context (to be merged with audio_knowledge)
        "manual_context": {
            "Predelay": {
                "official_description": "Controls the delay time, in milliseconds, before the onset of the first early reflection. This delays the reverberation relative to the input signal.",
                "technical_spec": "Typical values for natural sounds range from 1 ms to 25 ms",
                "acoustic_principle": "One's impression of the size of a real room depends partly on this delay"
            },

            "Decay Time": {
                "official_description": "Adjusts the time required for this reverb tail to drop to 1/1000th (-60 dB) of its initial amplitude",
                "technical_spec": "Decay time to -60 dB",
                "acoustic_principle": "Simulates how quickly sound energy dissipates in a space"
            },

            "Room Size": {
                "official_description": "Controls the room's volume",
                "technical_spec": "At one extreme, a very large size will lend a shifting, diffused delay effect. The other extreme — a very small value — will give it a highly colored, metallic feel",
                "acoustic_principle": "Defines the dimensions of the virtual acoustic space"
            },

            "Diffusion": {
                "official_description": "Provides control over the diffusion's density and coarseness",
                "technical_spec": "When the room size is extremely small, has a large impact on the coloration contributed by the diffusion",
                "acoustic_principle": "Simulates how many surfaces scatter sound and how evenly they do it"
            },

            "Scale": {
                "official_description": "Provides additional control over the diffusion's density and coarseness",
                "technical_spec": "When the room size is extremely small, has a large impact on the coloration contributed by the diffusion",
                "acoustic_principle": "Adjusts the time spacing between early reflections"
            },

            "ER Spin Amount": {
                "official_description": "Controls the amount of modulation applied to the early reflections",
                "technical_spec": "A higher Amount setting tends to provide a less-colored (more spectrally neutral) late diffusion response",
                "acoustic_principle": "Creates stereo movement by modulating the early reflection pattern"
            },

            "ER Spin Rate": {
                "official_description": "Controls the rate of modulation applied to the early reflections",
                "technical_spec": "If the modulation rate is too high, doppler frequency shifting of the source sound will occur, along with surreal panning effects",
                "acoustic_principle": "Speed of early reflection pattern rotation"
            },

            "ER Shape": {
                "official_description": "Sculpts the prominence of the early reflections, as well as their overlap with the diffused sound",
                "technical_spec": "With small values, the reflections decay more gradually and the diffused sound occurs sooner. With large values, the reflections decay more rapidly and the diffused onset occurs later",
                "acoustic_principle": "A higher value can sometimes improve the source's intelligibility, while a lower value may give a smoother decay"
            },

            "HiFilter Freq": {
                "official_description": "High shelving filter for frequency-dependent reverberation decay",
                "technical_spec": "Models the absorption of sound energy due to air, walls and other materials in the room (people, carpeting and so forth)",
                "acoustic_principle": "In nature, high frequencies absorb faster than lows in most spaces"
            },

            "LowShelf Freq": {
                "official_description": "Low shelving filter for frequency-dependent reverberation decay",
                "technical_spec": "Provides a thinner decay",
                "acoustic_principle": "Controls low frequency content to manage clarity vs warmth"
            },

            "Stereo Image": {
                "official_description": "Determines the width of the output's stereo image",
                "technical_spec": "At the highest setting of 120 degrees, each ear receives a reverberant channel that is independent of the other (this is also a property of the diffusion in real rooms). The lowest setting mixes the output signal to mono",
                "acoustic_principle": "Controls left-right spread without affecting front-back depth"
            },

            "Density": {
                "official_description": "Controls the tradeoff between reverb quality and performance",
                "technical_spec": "Sparse uses minimal CPU resources, while High delivers the richest reverberation",
                "acoustic_principle": "Simulates number of reflections happening in the space"
            },

            "Freeze On": {
                "official_description": "Freezes the diffuse response of the input sound. When on, the reverberation will sustain almost endlessly",
                "technical_spec": "Flat bypasses the high and low shelf filters when Freeze is on. Cut modifies Freeze by preventing the input signal from adding to the frozen reverberation",
                "acoustic_principle": "Captures reverb tail and loops it for infinite sustain"
            },

            "Chorus Amount": {
                "official_description": "Controls the amount of modulation and motion added to the diffusion",
                "technical_spec": "Can be deactivated altogether",
                "acoustic_principle": "Adds movement and richness through pitch variation"
            },

            "Chorus Rate": {
                "official_description": "Controls the rate of modulation and motion added to the diffusion",
                "technical_spec": "Can be deactivated altogether",
                "acoustic_principle": "Speed of pitch modulation in reverb tail"
            },

            "Reflect Level": {
                "official_description": "Controls the amplitude of reflections at the reverb output",
                "technical_spec": "Can be varied independently of diffusion level",
                "acoustic_principle": "Early reflections define room character"
            },

            "Diffuse Level": {
                "official_description": "Controls the amplitude of diffusion at the reverb output",
                "technical_spec": "Can be varied independently of reflection level",
                "acoustic_principle": "Diffuse tail provides the 'wash' and sustain of reverb"
            },

            "Dry/Wet": {
                "official_description": "Adjusts the effect's overall Dry/Wet mix",
                "technical_spec": "Standard effect mix control",
                "acoustic_principle": "Balance between original (dry) and reverb (wet) signal"
            }
        }
    }

    return manual_data


def main():
    print("="*70)
    print("EXTRACTING ABLETON MANUAL CONTEXT")
    print("="*70)

    manual_data = extract_manual_context()

    # Ensure output directory exists
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    # Write structured JSON
    with open(OUTPUT_FILE, "w") as f:
        json.dump(manual_data, f, indent=2)

    print(f"\n✓ Extracted manual context for Reverb")
    print(f"  - Sections: {len(manual_data['sections'])}")
    print(f"  - Parameter contexts: {len(manual_data['manual_context'])}")
    print(f"\n✓ Saved to: {OUTPUT_FILE}")

    return True


if __name__ == "__main__":
    import sys
    sys.exit(0 if main() else 1)
