Absolutely—that understanding is right: your LOM layer handles named-value ↔ normalized-value conversions (and back), while AbletonOSC handles the transport (sending/receiving normalized values to/from Live’s parameters and objects). Below is a detailed, drop-in doc you can paste into your repo and point ChatGPT-in-VSCode at to produce an implementation plan and code.

⸻


---
title: "Fadebender: LOM Value Mapping + OSC Bridge — Implementation Brief"
version: "1.0"
audience: "ChatGPT-in-VSCode / engineering"
last_updated: "2025-10-06"
owners: ["Fadebender Core"]
status: "Draft — implementation planning"
---

## 0) Executive Summary

We are building a layered control stack for Ableton Live:

- **Value Mapping Layer (LOM Mapper)** — converts **named parameters in physical units** (e.g., `Delay Time = 3s`, `Volume = -6 dB`) to **Live’s normalized 0–1 values** and back. It also houses **auto-learning** to infer or refine parameter scales and ranges.
- **Transport Layer (OSC Bridge)** — speaks **OSC** to the **AbletonOSC** Remote Script inside Live, making **get/set** requests for tracks, clips, devices, and mixer parameters. AbletonOSC and Live’s LOM do **not** perform unit conversions; they use normalized floats and provide `display_value` for readback.

**Key principle:** All human/LLM-facing semantics live in the **LOM Mapper**, while **OSC** is a dumb pipe with structured endpoints.

---

## 1) Goals & Non-Goals

### Goals
- Deterministic, testable **parameter translation** across core devices and mixer.
- Clean **OSC API façade** for UI and LLM router (no Live specifics leaking upward).
- **Auto-learning** that safely probes parameters/presets to refine mappings.
- Bidirectional **state sync**: RS/OSC updates → UI & chat.

### Non-Goals (for this phase)
- Full browser/library search (only absolute paths if needed).
- Metering/RMS (not in LOM; future native helper).
- Complex piano-roll editing (basic clip ops only).

---

## 2) High-Level Architecture

LLM Chat ──► Intent Router ──► Control API (Facade) ──► LOM Mapper ──► OSC Bridge ──► AbletonOSC (Remote Script) ──► Live (LOM)
▲                         │               │
│                         └── Auto-Learn ─┘
UI ◄──────────── State Events (WebSocket) ◄─ OSC Bridge ◄─ AbletonOSC

- **Intent Router**: turns NL intents into typed commands (e.g., `SetParam(track=2, device="Reverb", param="Decay Time", value="3s")`).
- **Control API (Facade)**: single entrypoint the UI & LLM call; hides OSC/Live details.
- **LOM Mapper**: named param ⇄ normalized value; units ⇄ display; clamps, nudges, tolerances.
- **OSC Bridge**: sends `/live/...` messages, subscribes to change events, rebroadcasts via WebSocket.

---

## 3) Folder Structure (proposed)

fadebender/
engine/
control_api.py            # Facade used by UI & LLM
lom_mapper/
init.py
mapping_core.py         # conversions, clamping, tolerance check
unit_parsers.py         # “3s”, “500ms”, “-6dB”, “20%” → floats
scales.py               # linear/log/exp utilities
registry.py             # read/write param_registry.yml
learners/
preset_probe.py       # controlled write→readback to learn curves
curve_fit.py          # infer scale from samples
osc_bridge/
client.py               # send() / request() wrappers
server.py               # subscribe to OSC events; WS broadcast
schema.py               # endpoint constants, message schemas
config/
param_registry.yml        # seed + learned mappings
endpoints.yml             # OSC routes used by the bridge
ui/
components/               # Track inspector, device tiles, clip grid
docs/
ADR-osc-vs-rs.md

---

## 4) Interfaces & Contracts

### 4.1 Control API (Facade)

```python
# control_api.py
@dataclass
class ParamSpec:
    track: int
    device: str            # e.g., "Reverb", "EQ Eight"
    param: str             # e.g., "Decay Time", "1 Freq"
    target: Union[str, float]  # "3s", "-6 dB", 0.25, {"relative": "+2 dB"}
    mode: Literal["absolute", "relative"] = "absolute"

class ControlAPI:
    async def set_param(self, spec: ParamSpec) -> dict:
        """
        1) Parse unit → physical value (if string).
        2) Lookup mapping in registry; if missing, call learner (optional) or fail gracefully.
        3) Convert physical → normalized (0–1), clamp to bounds.
        4) Send OSC set; re-read display_value; verify within tolerance.
        5) Return {ok, before, after, display_value, norm_value}.
        """

    async def get_param(self, track: int, device: str, param: str) -> dict:
        """
        Read normalized + display_value via OSC; translate to physical if known.
        """

    async def clip_create(self, track: int, slot: int, bars: float) -> dict: ...
    async def clip_fire(self, track: int, slot: int) -> dict: ...
    async def transport(self, action: Literal["play","stop","record","metronome","tempo"], value: Any=None) -> dict: ...

4.2 LOM Mapper

# mapping_core.py
def to_normalized(device: str, param: str, physical_value: float, reg: Registry) -> float: ...
def to_physical(device: str, param: str, normalized_value: float, reg: Registry) -> float: ...
def clamp(norm: float) -> float: ...

# unit_parsers.py
parse("3s") -> 3.0
parse("500ms") -> 0.5
parse("-6dB") -> -6.0
parse("20%") -> 0.2

Scales (examples):
	•	linear(a, b): norm = (x - a) / (b - a)
	•	log10(a, b): norm = (log10(x) - log10(a)) / (log10(b) - log10(a))
	•	exp(a, b): use ln-space like log; inverse accordingly.

4.3 OSC Bridge (selected routes)
	•	/live/tempo (get), /live/tempo/set <float>
	•	/live/play, /live/stop, /live/record
	•	/live/track/set/volume <track> <norm>
	•	/live/track/set/pan <track> <norm>
	•	/live/track/set/send <track> <send_index> <norm>
	•	/live/device/set/parameter <track> <device_index> <param_index> <norm>
	•	/live/clip/create <track> <slot> <beats>
	•	/live/clip/fire <track> <slot>

Bridge provides await osc.request(route, *args) and emits on_event(topic, payload) over WebSocket.

⸻

5) Param Registry (seed + learn)

# config/param_registry.yml
"Track":
  "Volume":
    unit: "dB"
    scale: "linear_db"    # mapper knows min=-70, max=+6
    min: -70
    max: 6
  "Pan":
    unit: "%"
    scale: "linear_bipolar" # -1..+1
    min: -1
    max: 1

"Reverb":
  "Decay Time":
    unit: "s"
    scale: "log10"
    min: 0.1
    max: 60
  "Dry/Wet":
    unit: "%"
    scale: "linear_01"
    min: 0
    max: 1

"Delay":
  "Time":
    unit: "s"
    scale: "log10"
    min: 0.001
    max: 10

	•	Auto-learning writes back learned: true, tightens bounds, and can annotate:

notes: "Live 12.0.5 Simple Delay 'Time' behaves closer to exp; using log10 as approximation."



⸻

6) Error Handling & Guardrails
	•	Clamping: All normalized values clamped to [0, 1].
	•	Relative writes: {"relative": "+2 dB"} honored via physical delta → normalized delta; clamp result.
	•	Round-trip verify: After write, re-read display_value. If tolerance exceeded (e.g., > 5%), retry or report.
	•	Destructive ops (delete track, load set): return requires_confirmation: true.
	•	Ambiguity (device/param not found): return candidates and a resolution_hint.

⸻

7) Acceptance Criteria
	•	AC1: Setting Delay Time = "3s" yields display_value ~ "3.0 s" ± 0.1s within two attempts.
	•	AC2: Volume = "-6 dB" returns display_value ~ "-6.0 dB" ± 0.2dB and state event notifies UI.
	•	AC3: Relative change "+2 dB" adjusts from any starting point with clamping at fader floor.
	•	AC4: If registry lacks mapping, API responds with unsupported_parameter and (optionally) offers learn: true path.
	•	AC5: End-to-end latency UI/LLM → RS reflected in UI ≤ 200ms median on localhost.

⸻

8) Milestones (implementation order)
	1.	M1 – Transport & Mixer Core (P0)
	•	Tempo, Play/Stop/Record/Metronome
	•	Track Volume/Pan/Sends (Mapper + OSC)
	•	Round-trip verify + events
	2.	M2 – Reverb & Delay (P0)
	•	Decay/Size/Wet (Reverb), Time/Feedback/Wet (Delay)
	•	Unit parsing + log/exponential scales
	3.	M3 – Clip Basics (P1)
	•	Create 4/8-bar clip, loop on/off, fire/stop, start/loop points
	4.	M4 – Devices (P1)
	•	Utility, EQ Eight, Compressor/Glue, Auto Filter, Saturator, Limiter
	•	Add mappings incrementally; read first, relative change second, absolute last
	5.	M5 – Routing (P2)
	•	Audio/MIDI I/O, monitor state, crossfader assign (UI-first, confirm via chat)
	6.	M6 – Automation (P2)
	•	Read envelopes, basic write (segments); verify via display

⸻

9) Test Plan (condensed)
	•	Unit (Mapper): linear/log/exp conversions; unit parsing; clamping; relative math.
	•	Contract (OSC Bridge): schema validation (args count/types), retry policy.
	•	E2E: scripted flows (e.g., “create 4-bar clip on Track 2, set tempo 120, decay 3s”) assert UI echo and Live state.
	•	Learn Mode: safe probe (small step), capture (norm, display), update registry diff.

⸻

10) Prompts for ChatGPT-in-VSCode (copy/paste)

Prompt A — Plan & Scaffolding

You are the lead engineer. Using the brief in docs/LOM-OSC-brief.md, generate:
	1.	a step-by-step implementation plan for M1 and M2,
	2.	Python modules: engine/control_api.py, engine/lom_mapper/{mapping_core.py,unit_parsers.py,scales.py,registry.py},
	3.	OSC bridge: engine/osc_bridge/{client.py,server.py,schema.py} with example routes,
	4.	seed config/param_registry.yml for Track, Reverb, Delay.
Include docstrings and TODOs for future devices. No placeholders where concrete logic is known.

Prompt B — Tests

Generate unit tests for mapping_core.py covering linear/log/exp conversions, clamping, relative writes, and unit parsing. Then create E2E test skeletons that simulate OSC responses for tempo, track volume, and reverb decay. Aim for deterministic assertions and round-trip display_value verification.

Prompt C — Learn Mode

Implement engine/lom_mapper/learners/preset_probe.py that:
	•	Takes (device, param), generates candidate normalized steps, writes them (osc),
	•	Reads back display_value, fits scale (log/linear/exp),
	•	Proposes registry patch (YAML). Include safety bounds and rollback on failure.

⸻

11) Risks & Mitigations
	•	Parameter name variance (locale, racks): Use parameter IDs when possible; fall back to fuzzy name match and confirm.
	•	Scale mismatch: Keep tolerance checks; prefer relative nudges early.
	•	Latency spikes: Coalesce rapid changes; debounce UI sends; ensure localhost for OSC.

⸻

12) Decision Log
	•	Use AbletonOSC as transport (MIT, modifiable).
	•	Mapper owns semantics (units, scales, learning).
	•	Facade isolates callers (UI/LLM) from Live specifics.

⸻


If you want, I can immediately follow up with:
- a **seed `param_registry.yml`** covering Utility, EQ Eight, Compressor/Glue, Auto Filter, Saturator, Limiter, and
- the **exact Python scaffolding** for `control_api.py`, `mapping_core.py`, and the OSC bridge with a couple of working endpoints.