---
title: Ableton Live 11 — Reverb (Section 24.36)
tags: [ableton, live11, devices, audio, reverb]
section_id: live11.reverb
---

# Ableton Live 11 — Reverb

A practical, structured reference for the stock **Reverb** device in Ableton Live 11. Organized for LLM ingestion and quick human lookup.

---

## Table of Contents
- [Overview](#overview)
- [Signal Flow (Conceptual)](#signal-flow-conceptual)
- [Parameter Groups](#parameter-groups)
- [Input Filter](#input-filter)
- [Early Reflections](#early-reflections)
- [Diffusion Network (Tail)](#diffusion-network-tail)
- [Chorus (Optional Modulation)](#chorus-optional-modulation)
- [Global Settings](#global-settings)
- [Output](#output)
- [Practical Workflows](#practical-workflows)
- [Preset Recipes](#preset-recipes)
- [Controller/Remote Mapping Notes](#controllerremote-mapping-notes)
- [Quick Troubleshooting](#quick-troubleshooting)
- [Glossary](#glossary)

---

## Overview

**Reverb** simulates how sound reflects and decays in an acoustic space. It blends two broad components:

- **Early Reflections** — the first echoes that establish the sense of room, distance, and direction.
- **Diffused Tail** — the dense field of reflections that follows, perceived as the “reverb tail.”

Use **filters**, **frequency-dependent decay**, **modulation**, and **stereo width** to shape tone, texture, and space. Reverb can be used on **insert** or as a **send/return** effect.

---

## Signal Flow (Conceptual)

1. **Input Filter** (high/low cut tone-shaping before the verb)
2. **Early Reflections** (room character / proximity cues)
3. **Diffusion Network** (reverb tail; diffusion + shelves)
4. **Chorus** (optional modulation of the tail)
5. **Global** (predelay, size, decay, freeze, stereo, density/quality)
6. **Output** (Reflect level, Diffuse level, Dry/Wet balance)

> Tip: The **Input Filter** prevents low‑end rumble or harsh highs from over‑exciting the reverb stages.

---

## Parameter Groups

- **Input** — HP/LP filter XY pad and sliders, on/off per filter.
- **Early** — Spin on/off, Spin Amount, Spin Rate.
- **Tail** — High/Low shelves (enable + freq + gain), Diffusion, Scale.
- **Chorus** — On/Off, Amount, Rate.
- **Global** — Predelay, Smooth (None/Slow/Fast), Size, Decay, Freeze, Flat, Cut, Stereo (0°–120°), Density (quality/CPU).
- **Output** — Reflect (early level), Diffuse (tail level), Dry/Wet.

---

## Input Filter

**Purpose:** Shape the signal *before* it enters the reverb engine.

**Controls**
- **XY Pad** — X: cutoff/center frequency; Y: bandwidth (Q).
- **Sliders** — Numerical control of HP/LP if preferred.
- **On/Off per filter** — Disable unused filters to reduce CPU.

**Usage**
- **Tighten lows:** Raise the low‑cut to keep tails clean on bass‑heavy sources.
- **De‑harsh highs:** Lower the high‑cut to tame sibilance/cymbals before the verb.

---

## Early Reflections

**What it does:** Defines apparent **room character** and **source distance**.

**Controls**
- **Spin (On/Off)** — Enables modulation of early reflections.
- **Amount** — Modulation depth; reduces static coloration when used subtly.
- **Rate** — Modulation speed; very high values can introduce Doppler‑like pitch effects and wide panning artifacts.

**Guidance**
- Keep **Amount/Rate** moderate to add life without detuning.
- Disable **Spin** for static rooms or when saving CPU.

---

## Diffusion Network (Tail)

**What it does:** Generates the dense **reverb tail**.

**Controls**
- **High Shelf / Low Shelf** — Shape frequency‑dependent decay.
  - High shelf models air/material absorption (darker = shorter high‑frequency decay).
  - Low shelf thins the low end to avoid boomy tails.
  - Each shelf can be **disabled** to save CPU.
- **Diffusion** — Tail **density** (grainy ↔ smooth).
- **Scale** — Tail **coarseness/character**; with very small **Size**, this can be strongly colored/metallic.

**Workflow**
1. Start with shelves flat.
2. Dial **Diffusion** for texture.
3. Adjust **Scale** to taste (and revisit **Size** if the tail becomes metallic).

---

## Chorus (Optional Modulation)

**Purpose:** Adds subtle **motion** and width to the tail.

**Controls**
- **Amount** — Depth of modulation.
- **Rate** — Speed of modulation.
- **On/Off** — Disable for static/realistic rooms or when phase coherence matters.

**Use‑cases**
- Pads/vocals: gentle movement and width.
- Drums/percussion: often Off for clarity and punch.

---

## Global Settings

**Controls**
- **Predelay (ms)** — Delay before the first early reflections. Natural ranges: ~1–25 ms.
- **Smooth** — How **Size** changes are applied:
  - **None:** instant (may click/zipper on large moves)
  - **Slow** / **Fast:** ramps Size to avoid artifacts
- **Size** — Virtual room volume; **very small** can sound metallic, **very large** becomes washier/delay‑like.
- **Decay** — Time for tail to reach ~‑60 dB (RT60‑style).
- **Freeze** — Sustains the existing tail.
  - **Flat:** bypasses shelves while frozen (neutral sustain).
  - **Cut:** prevents new input from entering the frozen field.
- **Stereo (0°–120°)** — Output width; 0° mono, 120° fully independent L/R tails.
- **Density** — Quality vs CPU; higher = smoother/richer tails at higher CPU cost.

**Starting Points**
- **Small Room:** Predelay 3–8 ms • Size 10–20 • Decay 0.8–1.5 s • Stereo 60–90°
- **Hall:** Predelay 12–20 ms • Size 60–80 • Decay 2.5–4.5 s • Stereo 100–120°

---

## Output

**Controls**
- **Reflect** — Level of **early reflections**.
- **Diffuse** — Level of the **tail**.
- **Dry/Wet** — Global mix of processed vs dry signal.

**Gain Staging**
- On **return tracks**, set **Dry/Wet = 100%** and balance with send level.
- Increase **Reflect** for proximity (closer feel); raise **Diffuse** for distance/“air.”

---

## Practical Workflows

**Insert vs Send**
- **Insert:** Use conservative **Dry/Wet** (5–25%) and shape the input with filters to keep the source present.
- **Send/Return:** 100% wet; automate **send level** to place sources front/back in the mix.

**Space First, Tone Second**
1. Rough in **Size**, **Predelay**, **Decay**, **Stereo**.
2. Then use **shelves** and **Input Filter** to seat the reverb tonally.
3. Add **Chorus** only if the part benefits from movement.

**Freeze Tricks**
- **Ambient pads/drones:** Freeze + Flat, then slowly modulate **Size** with **Smooth=Slow**.
- **Gated‑style effects:** Freeze + Cut and automate output levels or mutes.

---

## Preset Recipes

> Always tweak **Dry/Wet** and **Decay** to taste for your material.

**Tight Room (vocals, drums)**
- Predelay 8 ms • Size 18 • Decay 1.2 s
- Early: Spin Off
- Tail: Diffusion 55, Scale 35; High Shelf −2 dB @ ~6 kHz; Low Shelf −1 dB @ ~150 Hz
- Stereo 80° • Density Medium
- Output: Reflect +1.5 dB, Diffuse 0 dB

**Drum Plate‑ish**
- Predelay 12 ms • Size 45 • Decay 1.8 s
- Chorus Off
- Tail: Diffusion 70, Scale 40; High Shelf −3 dB @ 7–8 kHz; Low Shelf −2 dB @ 180 Hz
- Stereo 100° • Density High
- Output: Reflect −1 dB, Diffuse +1.5 dB

**Lush Hall (pads)**
- Predelay 16 ms • Size 72 • Decay 3.8 s
- Chorus: Amount ~20%, Rate ~0.6 Hz
- Tail: Diffusion 80, Scale 30; High Shelf −4 dB @ 6–7 kHz; Low Shelf −3 dB @ 160 Hz
- Stereo 115° • Density High
- Output: Reflect −2 dB, Diffuse +3 dB

**Infinite Freeze Texture**
- Freeze On • Flat On • Cut On
- Predelay 0–5 ms • Size 50–80
- Modulate **Size** slowly (Smooth = Slow) for evolving drones.

---

## Controller/Remote Mapping Notes

**Suggested Pages (8 encoders each):**
1. **Core Space:** Dry/Wet · Predelay · Size · Decay · Stereo · Density · Reflect · Diffuse
2. **Character:** Diffusion · Scale · High Shelf Gain/Freq · Low Shelf Gain/Freq
3. **Motion/State:** Spin On/Amount/Rate · Chorus On/Amount/Rate · Freeze · Flat · Cut

**Live/Push Tips**
- Put a dedicated **Freeze Kill** macro that toggles **Freeze** and **Cut** simultaneously.
- Prioritize **Size**, **Decay**, **Predelay**, **Dry/Wet** on the first encoders for speed.

---

## Quick Troubleshooting

- **Muddy mix:** Raise input **low‑cut**; reduce **low shelf**; shorten **Decay**.
- **Harsh/sizzly tail:** Lower **high shelf**; reduce **Chorus Amount**; lower **Scale** or **Diffusion** if metallic.
- **Metallic/“ringy” room:** Increase **Size** slightly; adjust **Scale**; reduce **Diffusion** extremes.
- **Too wide/phasey:** Reduce **Stereo**; turn **Chorus** off; moderate **Spin Rate**.
- **Clicks when changing Size:** Set **Smooth** to **Slow** or **Fast**.

---

## Glossary

- **Early Reflections:** First, discrete echoes giving room cues.
- **Diffusion:** How densely reflections are packed; higher = smoother.
- **Scale:** Coarseness/character of the tail network.
- **Predelay:** Time offset before the first reflection arrives.
- **Freeze (Flat/Cut):** Sustain the tail; Flat bypasses shelves, Cut blocks new input.
- **Stereo (0°–120°):** Image width from mono to fully independent L/R.

