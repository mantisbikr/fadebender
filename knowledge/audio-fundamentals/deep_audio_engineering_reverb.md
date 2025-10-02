---
effect: reverb
category: audio engineering
tags: [space, ambience, vocals, drums, guitar, piano, bass]
use-cases: [clarity, depth, spatialization, glue, ambience]
---

# Deep Audio Engineering — Reverb (General Guide)

> A device‑agnostic reference you can use alongside any DAW or hardware. Focuses on sound design intent, parameter behavior, and repeatable recipes.

## 1) What Reverb Does (and Why Your Ear Loves It)
Reverb simulates the dense field of reflections created when sound interacts with an environment. Your brain reads those reflections to infer **size**, **distance**, **material**, and **envelopment**. Most algorithmic reverbs split processing into:

- **Early reflections (ER):** The first 5–80 ms of distinct echoes that define *apparent room size/position*. 
- **Late field / tail:** A diffuse, exponentially decaying wash that defines *space character and sustain*.

**Psychoacoustic anchors**
- **Haas / precedence window:** ~5–35 ms between direct sound and first reflection feels wider/bigger without distinct echo.
- **RT60 (decay):** Time for energy to drop 60 dB; longer = larger/lusher.
- **HF damping:** Soft surfaces absorb highs first → distant/warm perception.

## 2) Typical Signal Flow
```
Dry Source → (optional) Pre‑EQ/HPF → Pre‑Delay → Early Reflections → Diffusion/Density → Late Tail → Damping/Filters/EQ → Modulation → Width/Stereo Matrix → Wet Level → Mix
```
Use **sends** for most reverbs to share one space across tracks and to keep dry signals phase‑stable.

## 3) Core Parameters and What They Change
- **Pre‑Delay (0–80 ms typical):** Gap before the reverb starts. Longer = more clarity and perceived size.  
- **ER Level/Time/Pattern:** Moves the source forward/back and sets room identity.  
- **Size / Room:** Controls modal spacing and ER timing; larger increases ER delays and tail density growth.  
- **Decay / RT60 (0.3–8.0 s+):** How long the tail persists.  
- **Diffusion / Density:** Low diffusion = grainy/metallic flutter; high = smooth but can blur transients.  
- **Damping (HF/LF):** Frequency‑dependent decay. HF damping warms/darkens, LF damping tightens lows.  
- **Modulation (Rate/Depth):** Reduces metallic ringing. Too much = chorusy wash.  
- **EQ / Filters (pre/post):** Pre‑EQ sculpts what enters; post‑EQ shapes the tail.  
- **Stereo Width / Crossfeed:** Controls spread.  
- **Algorithm/Model:** *Plate, Room, Chamber, Hall, Spring, Shimmer/IR*.  

**Quick math:** Path length difference (meters) ≈ *pre‑delay (ms)* × 0.343.  

## 4) Interactions & Trade‑offs
- **Long decay + low damping** = mud.  
- **Short pre‑delay + high diffusion** = smearing.  
- **Bright tails** emphasize sibilance.  
- **Multiple spaces**: Stack short + long.

## 5) Common Use‑Cases (Good Starting Points)
- **Lead vocal — modern clarity plate**: Pre‑delay 20–30 ms · Decay 1.2–1.8 s · HPF 160–220 Hz.  
- **Snare — punchy plate**: Pre‑delay 0–10 ms · Decay 0.8–1.4 s · HPF 200–300 Hz.  
- **Drum room — glue**: Decay 0.4–0.8 s.  
- **Guitars — ambient wash**: Pre‑delay 10–20 ms · Decay 2–4 s.  
- **Piano — natural space**: Tail 1.2–2.0 s.  
- **Bass (sparingly)**: HPF ≥ 180 Hz, decay ≤ 0.8 s.

## 6) Engineering Recipes (Step‑by‑Step)
- **Vocal Plate Bus with Ducking**  
- **Snare Gated Plate**  
- **Drum Room Pump**  
- **Depth Staging**  
- **Shimmer Pad Stack**

## 7) Metering, Gain Staging, and Stability
- Aim for −18 to −12 dBFS average on returns.  
- Use spectrum analyzer.  
- Check mono collapse.

**RT60 formula:** g = 10^(−60 / (20·fs·RT60)).

## 8) Troubleshooting & Pitfalls
- **Muddy mix:** Shorten decay, HPF.  
- **Metallic ringing:** More diffusion or modulation.  
- **Sibilant splash:** LPF or de‑ess.  
- **Vocals smeared:** Add pre‑delay.  
- **Mono issues:** Reduce width.

## 9) Quick‑Start Table
| Source | Pre‑Delay | Decay (RT60) | Filters | Notes |
|---|---:|---:|---|---|
| Lead Vocal | 20–30 ms | 1.2–1.8 s | HPF 180–220 Hz, LPF 7–9 kHz | Add ducking |
| Snare | 0–10 ms | 0.8–1.4 s | HPF 200–300 Hz | Plate, gate |
| Drum Room | 0–5 ms | 0.4–0.8 s | HPF 120–180 Hz | Compress |
| Guitar | 10–20 ms | 2–4 s | HPF 150 Hz, LPF 6–8 kHz | Light modulation |
| Piano | 10–20 ms | 1.2–2.0 s | HPF 120–160 Hz | ER emphasis |
| Bass | 0–5 ms | ≤ 0.8 s | HPF ≥ 180 Hz | ER only |

## 10) Workflow Tips
- EQ both pre and post.  
- Prefer sends.  
- Automate pre‑delay and decay.

---
