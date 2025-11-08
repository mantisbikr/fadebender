# Audio Engineering Knowledge Base v1

A structured corpus to power the Advice Engine and map recommendations to concrete Ableton Live actions. Organized in three layers:

- **Principles** (why)
- **Techniques** (how)
- **Ableton Implementations** (what exactly to do in Live)

> Scope: **Vocals**, **Drums**, **Reverb & Space**, **Mix Bus** (comprehensive starter set). Keep device‑agnostic ideas in Principles/Techniques; reserve device specifics for Implementations.

---

## A) VOCALS

### Principles
- Capture first: mic choice, distance, pop filter, room control.
- Harshness & sibilance live in 2–6 kHz and 5–9 kHz respectively.
- Serial compression is smoother than one hard compressor.
- Pre‑delay separates vocal from reverb tail.

### Techniques
- High‑pass 70–110 Hz.
- Narrow dip for harshness (-1 to -4 dB, Q 5–9).
- Dynamic de‑ess (2–6 dB GR).
- Serial compression: 2–4 dB GR → 1–3 dB GR.
- Slap delay 80–140 ms or synced 1/8–1/4 for presence.

### Ableton Implementations
- **EQ Eight**: Band sweep for harshness; dynamic band for de‑ess (Live 12).
- **Compressor**: Serial; slower attack first, character second.
- **Hybrid Reverb**: Plate, pre‑delay ~40 ms, low‑cut @ 150 Hz.
- **Delay**: High‑cut to avoid hiss, returns preferred.

---

## B) DRUMS

### Principles
- Kick vs bass → sub ownership (40–80 Hz vs 80–120 Hz).
- Snare crack lives in 2–5 kHz; boxiness at ~500 Hz.
- Drum bus glue creates cohesion.

### Techniques
- Kick: cut boxiness 250–400 Hz; boost 60–80 Hz for weight.
- Snare: slight boost 200 Hz body; dip 500–800 Hz ring.
- Cymbals: high‑shelf tame 8–12 kHz if harsh.
- Parallel drum buss smash for excitement.

### Ableton Implementations
- **Drum Buss**: Drive 2–10%, Transient + for punch, Boom for sub.
- **Glue Compressor** on drum bus: 1.5–2:1 ratio, ~1–3 dB GR.
- **Sidechain Compressor** on bass keyed from kick.

---

## C) REVERB & SPACE

### Principles
- Pre‑delay preserves clarity.
- Early reflections define room size.
- Return tracks create consistent depth across the mix.

### Techniques
- Vocal plate: 20–60 ms pre‑delay, 0.8–2.0 s decay, low‑cut and high‑cut.
- Drum room: 0.4–1.2 s, minimal diffusion.
- Duck reverb return with sidechain for clarity.

### Ableton Implementations
- **Hybrid Reverb** on Return A.
- **Compressor (Sidechain)** post‑reverb to duck against vocal.
- **EQ Eight** to shape reverb tone.

---

## D) MIX BUS

### Principles
- Do as little as possible here—fix issues earlier in the chain.
- Target 0.5–2 dB glue compression.
- Mono the sub region; add width only above ~200 Hz.

### Techniques
- Glue comp: 1.5–2:1, slowish attack, auto release.
- Gentle shelves for air/body (+0.5 to +1 dB).
- Saturation for cohesion, not loudness.

### Ableton Implementations
- **Glue Compressor** on Master to glue.
- **Saturator** light for tone.
- **Limiter** last, ceiling -1.0 dB.

---

## Action Schema (Advice → Control)

```json
{
  "type": "set_param",
  "target": {"track": "", "device": "", "parameter": ""},
  "value_display": "",
  "value_normalized": null,
  "why": "",
  "confidence": 0.0
}
```

---

## Next Steps
- Add per-device parameter ranges from your device mapping DB.
- Add A/B listening checklists per technique.
- Add examples with values observed in real mixes.

