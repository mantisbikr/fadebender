---
title: "Fadebender Remote Script — Track Controls Implementation Plan"
version: "1.0"
area: "Ableton Live Remote Scripts"
description: "Execution roadmap to achieve full track-level control via Python Remote Script + UI + LLM. Includes phased milestones, difficulty/priority tags, dependencies, acceptance tests, and rollout order."
last_updated: "2025-10-05"
tags: ["fadebender", "ableton", "remote-script", "lom", "ui", "llm", "roadmap"]
owners: ["Fadebender Core"]
---

# Fadebender Remote Script — Track Controls Implementation Plan

This document translates the **KB reference** (`knowledge/ableton-live/remote-scripts/track_controls_reference.md`) into an actionable engineering plan toward **feature completeness** across three layers:
- **RS**: Python Remote Script (LOM integration)
- **UI**: Web / app controls
- **LLM**: Chat intents → command router → RS

Difficulty legend: 🟢 Easy · 🟡 Medium · 🔴 Complex  
Priority legend: **P0** must-have · **P1** high · **P2** nice-to-have

---

## Phase 0 — Foundations (Infra & Dev Ergonomics) — **P0**
**Goal:** Stable dev loop, bidirectional state flow, safety rails.

| Item | Layer | Diff | Prio | Dependencies | Acceptance Criteria |
|---|---|---:|:---:|---|---|
| Event bus + state sync (track/clip/device) | RS↔UI | 🟡 | P0 | RS skeleton, WebSocket bridge | UI reflects RS changes <200ms; RS receives UI changes; no missed updates in 5-min stress test |
| Command router (intent → action) | LLM↔RS | 🟡 | P0 | Intent schema, reference resolver | Natural language command updates exact target; logs structured payloads |
| Safety confirmations | LLM | 🟢 | P0 | Toast/confirm UI | Destructive ops (“delete track”, “load set”) require confirmation; cancel leaves state unchanged |
| Error/Toast system | UI | 🟢 | P0 | Event bus | Visible success/failure with human-readable message & RS trace id |

---

## Phase R — Return Tracks First — **P0**
Goal: Implement all Return Track controls end‑to‑end before main track details, so FX sends workflows are complete early.

| Capability | RS | UI | LLM | Diff | Prio | Notes |
|---|---|---|---|:---:|:---:|---|
| Enumerate return tracks | ✅ | ✅ | ✅ | 🟢 | P0 | Done: `/returns` now includes mixer state |
| Return mixer: volume/pan | ✅ | ✅ | ✅ | 🟢 | P0 | Done: bounce-free UI; SSE refresh wired |
| Return mute/solo | ✅ | ✅ | ✅ | 🟢 | P0 | Done: silent refresh, no list flash |
| Return devices list | ✅ | ✅ | ✅ | 🟡 | P0 | Done with on/off + learn status |
| Return device param set | ✅ | ✅ | ✅ | 🟡 | P0 | Done: by name/index; learned mapping used |
| Return device bypass/on-off | ✅ | ✅ | ✅ | 🟢 | P0 | Done: Device On or Dry/Wet fallback |
| Insert device/preset on return | 🟡 | — | ✅ | 🔴 | P1 | Path-based insert; confirm target return |
| Optional: return→return sends | 🟡 | 🟡 | — | 🔴 | P2 | Only if Live pref allows; feature‑flag |

Exit criteria (Phase R):
- All return tracks visible; UI controls volume, pan, mute, solo; devices can be toggled and key params adjusted.
- LLM can “turn down reverb return 3dB”, “mute Return A”, “increase return reverb decay 15%”.
- SSE/state listeners reflect RS changes within 200ms typical.

---

## Phase 1 — Core Transport, Tracks, Mixing — **P0**
**Goal:** Daily-driver control end-to-end (RS, UI, LLM).

| Capability | RS | UI | LLM | Diff | Prio | Notes |
|---|---|---|---|:---:|:---:|---|
| Play/Stop/Record/Metronome/Tempo | ✅ | ✅ | ✅ | 🟢 | P0 | Added TransportBar (always visible); RS ops + server endpoints wired |
| Track create/delete/rename | ✅ | 🟡 | ✅ | 🟡 | P0 | UI supports Add/Delete; rename via inline edit & chat |
| Mute/Solo/Arm | ✅ | ✅ | ✅ | 🟢 | P0 | Keep exclusive solo semantics consistent with Live |
| Volume/Pan/Sends (A/B/C…) | ✅ | ✅ | ✅ | 🟡 | P0 | Bounce fixed; sends fetch on expand; stable sliders |
| Routing capture (chat-only) | ✅ | — | ✅ | 🟡 | P0 | Track input/output routing and monitor state exposed to LLM, even without UI knobs |
| Scene/Clip launch/stop | ✅ | ✅ | ✅ | 🟡 | P0 | Clip grid minimal; fire/stop buttons; scene column |

**Exit criteria (Phase 1):**
- Latency UI↔RS ≤ 200ms typical, ≤ 400ms p95 over 5 minutes.
- 95% of “everyday” operations possible via UI or LLM with parity.
- E2E test suite green for 100 randomized commands.

---

## Phase 2 — Devices & Presets (Deep Control) — **P1**
**Goal:** Confident device manipulation and parameter access.

| Capability | RS | UI | LLM | Diff | Prio | Dependencies | Acceptance |
|---|---|---|---|:---:|:---:|---|---|
| Device chain enumeration | ✅ | ✅ | ✅ | 🟢 | P1 | Phase 1 | Device tiles with on/off + top 8 params (banks) |
| Parameter control (by name/index) | ✅ | ✅ | ✅ | 🟡 | P1 | Value listeners | “Increase reverb decay 20%” sets param within bounds |
| Insert devices/presets by path | 🟡 | — | ✅ | 🔴 | P1 | Path index cache | Insert succeeds given valid absolute path; chat confirms |
| Macro banks & focus | ✅ | ✅ | 🟡 | 🟡 | P1 | Bank discovery | Macro strip shows 8 params; LLM can target “macro 2” |

**Exit criteria (Phase 2):**
- 100% mapped device parameters exposed via UI scroll/banks.
- LLM can address parameters by human names (case/locale tolerant).
- Insertion by absolute path works; errors toast with fix hints.

---

## Phase M — Master Track Essentials — **P1**
Goal: Master bus operations required for mix control.

| Capability | RS | UI | LLM | Diff | Prio | Notes |
|---|---|---|---|:---:|:---:|---|
| Master volume | ✅ | ✅ | ✅ | 🟢 | P1 | `LiveSet.master_track.mixer_device.volume` |
| Crossfader | ✅ | ✅ | 🟡 | 🟡 | P1 | `...mixer_device.crossfader`; UI + chat “set crossfader to B 70%” |
| Cue volume (if exposed) | 🟡 | 🟡 | — | 🟡 | P2 | `...mixer_device.cue_volume` availability varies by Live version |
| Cue/Main Out selection | — | — | — | 🔴 | P2 | Generally not exposed in LOM; document limitation for chat |
| Master devices list | ✅ | ✅ | 🟡 | 🟡 | P1 | Enable on/off; top params |
| Master device params | ✅ | ✅ | 🟡 | 🟡 | P1 | Carefully guard destructive processors |

Exit criteria (Phase M): master volume and crossfader controllable via UI and LLM; master device toggle/params supported.

---

## Phase 3 — Clips & MIDI Editing Essentials — **P1**
**Goal:** Clip lifecycle + minimal MIDI editing.

| Capability | RS | UI | LLM | Diff | Prio | Acceptance |
|---|---|---|---|:---:|:---:|---|
| Create empty MIDI clip (len/bars) | ✅ | 🟡 | ✅ | 🟢 | P1 | New clip appears focused; loop enabled; length respected |
| Duplicate clip | ✅ | — | ✅ | 🟢 | P1 | Target slot specified or auto-next empty; preserves loop |
| Quantize clip | ✅ | ✅ | ✅ | 🟡 | P1 | Quantize menu (1/8, 1/16…); “quantize to 1/16” works |
| Loop/Start/Length edits | ✅ | ✅ | ✅ | 🟡 | P1 | Knobs/fields in UI; LLM intents reflected live |
| Basic note ops (insert, clear) | 🟡 | 🟡 | 🟡 | 🔴 | P1 | Minimal grid insert; LLM “add 4 on C3” basic pass |

---

## Phase 4 — Automation & Envelopes — **P1**
**Goal:** Envelope reads/writes from LLM with UI preview.

| Capability | RS | UI | LLM | Diff | Prio | Dependencies | Acceptance |
|---|---|---|---|:---:|:---:|---|---|
| Read clip envelopes | 🟡 | ✅ | 🟡 | 🔴 | P1 | Param resolver | UI mini-plot of target envelope; readback verified |
| Write envelope points | 🟡 | 🟡 | 🟡 | 🔴 | P1 | Time/beat math | “Fade volume -6 dB over 2 bars” generates correct curve |
| Enable/disable automation | ✅ | ✅ | ✅ | 🟡 | P1 | Transport | Automation arm toggles correctly; overdub safe |

---

## Phase 5 — Routing, Browser, Monitoring — **P2**
**Goal:** Advanced control; mostly UI-first with LLM assist.

| Capability | RS | UI | LLM | Diff | Prio | Acceptance |
|---|---|---|---|:---:|:---:|---|
| Audio/MIDI I/O routing | ✅ | ✅ | 🟡 | 🟡 | P2 | Dropdowns show valid types/channels; LLM confirms ambiguity |
| Crossfader assignment | ✅ | ✅ | — | 🟢 | P2 | Per-track A/B/X visible and saved |
| Browser suggestions → path resolution | — | — | 🟡 | 🔴 | P2 | LLM suggests, then confirms actual file path |
| Metering (read-only)* | ❌ | 🟡 | — | 🔴 | P2 | If exposed via extension; show master/track VU |

\*Metering isn’t officially in LOM; consider a native helper later.

---

## Dependencies & Shared Components

- **Reference Resolver:** natural names → concrete indices (tracks, scenes, devices, parameters).  
- **Path Index Cache:** map friendly names to absolute device/preset paths (periodic scan or curated YAML).  
- **Quantization/Time Math:** shared utils for bars/beats → samples/ticks as RS needs.  
- **Value Listeners / SSE:** attach on track/mixer/param/clip to keep UI & LLM state coherent.  
- **Safety Policy:** centralized guardrails (confirmations, dry runs, rollbacks on error).  
- **Return/Bus Guardrails:** prevent feedback loops (e.g., return→return sends) via feature flags and validation.  
 - **Routing Catalog:** enumerate valid input/output types/channels per track and expose to LLM for disambiguation.  

---

## Transport — Implementation Notes (New)

- RS ops: `get_transport`, `set_transport { action: play|stop|record|metronome|tempo, value? }`
- Server endpoints:
  - GET `/transport` → `{ is_playing, is_recording, metronome, tempo }`
  - POST `/transport` with `{ action, value? }`
- UI: `TransportBar` always visible at top of Sidebar; controls Play/Stop, Record, Metronome, Tempo.
- SSE: optional `transport_changed` event emitted on change; UI polls on actions for now.

---

## Bridge Ops Spec (Routing & Monitor)

Implement these UDP ops in the Remote Script bridge to support server endpoints and LLM intents.

- `get_track_routing` (req)
  - Request: `{ op: "get_track_routing", track_index: number }`
  - Response: `{ ok, data: { monitor_state: "in"|"auto"|"off", audio_from: { type, channel }, audio_to: { type, channel }, midi_from?: { type, channel }, midi_to?: { type, channel }, options?: { audio_from_types: string[], audio_from_channels: string[], audio_to_types: string[], audio_to_channels: string[], midi_from_types?: string[], midi_from_channels?: string[], midi_to_types?: string[], midi_to_channels?: string[] } } }`

- `set_track_routing` (req)
  - Request: `{ op: "set_track_routing", track_index, monitor_state?, audio_from_type?, audio_from_channel?, audio_to_type?, audio_to_channel?, midi_from_type?, midi_from_channel?, midi_to_type?, midi_to_channel? }`
  - Response: `{ ok: boolean }`

- `get_return_routing` (req)
  - Request: `{ op: "get_return_routing", return_index }`
  - Response: `{ ok, data: { audio_to: { type, channel }, sends_mode?: "pre"|"post", options?: { audio_to_types: string[], audio_to_channels: string[], sends_modes?: ["pre","post"] } } }`

- `set_return_routing` (req)
  - Request: `{ op: "set_return_routing", return_index, audio_to_type?, audio_to_channel?, sends_mode? }`
  - Response: `{ ok: boolean }`

Server emits SSE events on changes:
- `track_routing_changed` with `{ track_index }`
- `return_routing_changed` with `{ return_index }`

Validation & behavior:
- RS should validate requested type/channel against `options` and return `{ ok:false, error:"invalid_selection" }` when out of range.
- For Live versions lacking certain fields (e.g., MIDI on audio tracks, sends_mode not exposed), omit fields in `data` and `options` gracefully.

## Non-Goals (for now)
- Opening plugin GUIs, OS dialogs, or Live Preferences screen.  
- Full piano-roll editor (beyond basic inserts/edits).  
- Library browsing by *name* without pre-indexed paths.

---

## Architecture Snapshot

```mermaid
flowchart LR
  Chat[LLM Chat] --> Router[Intent Router]
  UI[Web UI] <--> EventBus[Event Bus / WS]
  Router --> Bridge[RS Bridge API]
  EventBus --> Bridge
  Bridge --> RS[Python Remote Script]
  RS <--> Live[Live Object Model]
  RS --> Telemetry[Logs/Tracing]
  Router --> Telemetry
  UI --> Telemetry
