# Ableton Live Remote Script Capabilities & Automation Roadmap (Fadebender)

This document outlines the key Ableton Live control capabilities available through Remote Scripts, prioritized for Fadebender’s workflow goals: precision mixing, fast creative iteration, scene-based production organization, and **goal-driven automation recording**.

---

## 🎯 Core Principle

Fadebender **does not replicate the Ableton UI**.

Instead, it provides:

- **Faster workflows**
- **Musical intent → precise action**
- **History, snapshots, and reversibility**
- **Automation as expressive performance**

---

## ✅ Fully Supported Remote Script Capabilities

| Capability | Supported | Notes |
|-----------|-----------|-------|
| Track selection & focus | ✅ | Used to direct commands logically. |
| Scene selection / firing | ✅ | Useful for A/B arrangements and idea iteration. |
| Trigger / stop clips | ✅ | Session workflow compatibility. |
| Create empty MIDI/Audio clip | ✅ | `clip_slot.create_clip(length_in_beats)` |
| Rename tracks/scenes/clips | ✅ | Enables semantic labeling and Firestore memory. |
| Adjust track mixer controls | ✅ | Volume, pan, sends, arm, mute, solo. |
| Add/remove/reorder devices | ✅ | Critical for preset recall and effect workflows. |
| Adjust device parameters | ✅ | Core Fadebender feature. |
| Get/set tempo and meter | ✅ | Tempo-aware advice + click-to-record workflows. |
| Jump playhead to timeline positions | ✅ | Key for navigation + automation macros. |

---

## ⚠️ Limited or Context-Dependent Features

| Feature | Notes |
|--------|------|
| Arrangement ↔ Session view switching | Possible but UI-state dependent. |
| MIDI note insertion/editing | Basic creation possible, deep editing limited. |
| Warp/quantize control | Exists but not suitable for precision workflow in v1. |
| Track creation / return track creation | Not available via Remote Script alone (Max for Live required). |

---

## ❌ Not Supported (Technical API Limitations)

| Capability | Reason |
|-----------|--------|
| Reading waveforms or loudness (LUFS) | Audio signal data inaccessible. |
| Editing arrangement clips | Arrangement editing API extremely limited. |
| Direct automation lane editing (adding breakpoints) | No API layer for envelope graph manipulation. |

---

## ⭐ High-Value Fadebender Feature: **Automation Macros**
### Purpose
Allow the user to **describe** automation instead of **manually drawing it**.

> Example: “Increase reverb pre-delay from 5 ms to 80 ms over the last 2 bars of the chorus.”

### How It Works
Fadebender performs automation through **real-time parameter recording**:

1. Identify:
   - Track
   - Device
   - Parameter
2. Identify the time region:
   - By bar number
   - Clip bounds
   - Marker labels stored in Firestore
3. **Arm automation recording**
4. **Move the playhead to the start**
5. **Perform parameter movement over duration** (fade curve)
6. **Stop and disarm**, leaving a clean automation envelope behind.

### Supported Automation Shapes
| Shape | Description |
|-------|-------------|
| Linear | Smooth constant ramp. |
| Exponential | Musical swells (filters, reverbs). |
| Ease-in / Ease-out | Natural phrasing transitions. |

### Key Value for Users
- No lane hunting
- No drawing curves
- Repeatable + Undoable
- Encourages expressive production moves
- Works perfectly with snapshots

---

## Priority Roadmap

### Phase 1 — Workflow & Foundation (Immediate)
1. Track & Scene semantic naming (Firestore memory)
2. Jump-to-marker navigation
3. Add/remove device chain workflows
4. Clip creation for vocal/guitar takes

### Phase 1.5 — **Automation Macros (Hero Feature)**
5. Parameter ramp recording (linear + exponential)
6. Timeline anchoring to bar, scene, or marker
7. Undo stack integration + history log

### Phase 2 — Creative Patterning
8. Pattern-based MIDI generation for drums/percussion
9. Multi-device macro gestures (e.g., reverb swell + filter dip)

### Phase 3 — Advanced Expressiveness
10. Curve shaping presets (e.g., “dub techno wash”, “lofi swell”)
11. AI-assisted automation suggestions based on musical context

---

## Summary

Fadebender differentiates itself by:
- Understanding the musical goal
- Performing changes expressively
- Preserving history and reversibility
- Eliminating UI friction rather than imitating it

The **Automation Macro System** becomes a flagship capability that enables:
- Faster creative transitions
- Professional-grade movement without DAW fiddling
- A workflow no other DAW assistant currently provides

---