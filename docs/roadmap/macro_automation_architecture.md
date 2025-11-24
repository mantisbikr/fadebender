# Fadebender Macro Automation Architecture

**Status**: Macro model + core compiler helpers implemented in backend models (no HTTP or scheduler yet).  
**Scope**: Parameter automation via planned macros (no new Remote Script features required).

Fadebender already controls Live transport and parameters (tracks, devices, sends) via AbletonOSC + the Remote Script. This doc defines a three‑layer model for building **macros** that turn a sequence of natural language commands into a deterministic, schedulable script for recording automation or performing repeatable operations.

The three layers:
- **Macro Model** – what a macro *is* (abstract steps and timing).
- **Compiler** – resolve references, validate against Live/project state, and flatten timing into an executable plan.
- **Scheduler** – execute the plan against Live (arm/record/transport/parameters) with beat‑aligned timing.

Natural language and UI sit above this model and will be implemented later.

---

## 1. Macro Model (Domain Schema)

The macro model is a small, explicit schema that represents *intent* in a backend‑friendly way. It is independent of the NLP surface and can be created either:
- by recording NL commands and mapping them to steps, or
- by editing JSON/Pydantic objects directly.

### 1.1 Core Types

**Anchors**
- `BeatAnchor`: absolute time in beats (`time_beats: float`).
- `LocatorAnchor`: reference to a *virtual* locator (`name: str`), resolved to a beat at compile time.

**MacroStep (union, implemented)**
- `ArmTrackStep`
  - `type: "arm_track"`
  - `track_index: int`
  - `arm: bool`
- `TransportStep`
  - `type: "transport"`
  - `action: "play" | "stop" | "session_record" | "arrangement_record" | "locate"`
  - `time_beats: float | None` (for `locate`)
- `SetParamStep`
  - `type: "set_param"`
  - `track_index: int`
  - `device_ref: str | None` (by name/index; resolved later)
  - `param_ref: str`
  - `value_display: str` (e.g. `"‑6 dB"`, `"0.7"`)
- `SweepParamStep`
  - `type: "sweep_param"`
  - `track_index: int`
  - `device_ref: str | None`
  - `param_ref: str`
  - `from_display: str`
  - `to_display: str`
  - `duration_beats: float`
  - `curve`: one of  
    - `"linear"`  
    - `"ease_in"` / `"ease_out"` / `"ease_in_out"`  
    - `"exp"` (exponential‑like)
    - `"log"` (log‑like)
- `WaitStep`
  - `type: "wait"`
  - `duration_beats: float`

Macros may also support high‑level “segment” steps (e.g. `play_segment` using virtual locators), but these can be compiled into the primitives above.

### 1.2 Macro Object

```jsonc
{
  "name": "Chorus volume swell",
  "description": "Fade up track 2 into the chorus",
  "start_anchor": { "kind": "locator", "name": "chorus_start" },
  "execution_mode": "relative",  // relative to start_anchor or absolute beats
  "steps": [ /* MacroStep[] */ ]
}
```

Key design goals:
- Stable, explicit type system (Pydantic models) that can be validated and versioned.
- Decoupled from NL phrasing and UI details.

---

## 2. Compiler Layer

The compiler turns a high‑level `Macro` into an **executable plan**:

1. **Resolve references**
   - Tracks → indices (using existing track/overview state).
   - Device/param refs → canonical IDs (using existing mapping/intent machinery).
   - Virtual locators → absolute beat positions.

2. **Validate**
   - Ensure all referenced tracks, devices, params, and locators exist.
   - Check durations/timings for sanity (e.g. `duration_beats > 0`).

3. **Flatten timing**
   - Compute a `start_time_beats` (from `start_anchor`).
   - For each step:
     - One‑shot actions get `scheduled_time_beats`.
     - Sweeps get `[start_time_beats, end_time_beats]`.

4. **Output an executable plan**
   - A simple list of scheduled operations:
   ```jsonc
   [
     { "time_beats": 32.0, "op": "arm_track", "track_index": 2, "arm": true },
     { "time_beats": 32.0, "op": "transport", "action": "session_record" },
     { "time_beats": [32.0, 48.0], "op": "sweep_param", ... },
     { "time_beats": 48.0, "op": "transport", "action": "stop" }
   ]
   ```

### 2.1 Current Compiler Implementation (in `server/models/macro.py`)

The compiler is implemented as a pure‑model helper:

- `compile_macro(macro: Macro, locator_resolver: Optional[Callable[[str], float]] = None) -> CompiledMacro`
  - Resolves `start_anchor`:
    - `BeatAnchor` → direct `base_time` in beats.
    - `LocatorAnchor` → uses `locator_resolver(name)` to get beats (required when locators are used).
  - Builds a linear beat timeline:
    - Maintains a `time_cursor` starting at `base_time`.
    - `WaitStep`: scheduled at `time_cursor`, then advances cursor by `duration_beats`.
    - `SweepParamStep`: scheduled from `[time_cursor, time_cursor + duration_beats]`, cursor advances to end.
    - All other steps: instantaneous at `time_cursor` (cursor unchanged).
  - Returns a `CompiledMacro` containing `ScheduledOp` objects with `time_beats`, optional `end_time_beats`, and the original step.

Additional helpers (also implemented, self‑contained):

- `validate_macro(macro: Macro) -> List[str]`
  - Structural checks only (no Live access):
    - `start_anchor.kind` is `"beats"` or `"locator"`.
    - `TransportStep`: `locate` must have `time_beats`, others must *not*.
    - `SetParamStep`: requires `param_ref` and `value_display`.
    - `SweepParamStep`: requires `param_ref`, `from_display`, `to_display`.
    - `WaitStep`: `duration_beats > 0`.
- `describe_compiled_macro(compiled: CompiledMacro) -> List[str>`
  - Human‑readable timeline strings, e.g.  
    `t=32: transport(action=session_record)`  
    `t=32→48: sweep_param(track=2, param=Dry/Wet, from=-12 dB, to=0 dB, curve=linear)`.
- `simulate_macro(macro: Macro) -> List[str>`
  - Convenience wrapper around `compile_macro` + `describe_compiled_macro` for debugging.
- Curve helpers for sweeps:
  - `curve_value(norm_t: float, curve: str) -> float` – maps normalized 0–1 to a curve‑adjusted 0–1.
  - `sample_sweep_times(duration_beats: float, steps: int) -> List[float]` – beat offsets across a sweep.
  - `sample_sweep_values(step: SweepParamStep, steps: int) -> List[float]` – normalized curve values across a sweep.

---

## 3. Scheduler Layer

The scheduler executes a `CompiledMacro` against Live:

- Drives transport via existing endpoints (`/transport`, `/song/cue/jump`, etc.).
- Uses existing HTTP/UDP operations for:
  - Track arm
  - Parameter set/sweep (by calling canonical intent/ops)
- Uses beat/time from `/transport` (or beat events) to decide when to fire each step.

Goals:
- Deterministic execution once the macro is compiled (no ambiguity about when anything happens).
- Reuse existing infrastructure; no new Remote Script features required.

Initial implementation is deferred; this doc only defines the interface the scheduler will consume.

---

## 4. Phase Plan

### Phase 1 – Models & Design (this change)
- ✅ Add `docs/roadmap/macro_automation_architecture.md` (this file).
- ✅ Add `server/models/macro.py` with:
  - Pydantic models for `Macro`, `MacroStep`, `ArmTrackStep`, `TransportStep`, `SetParamStep`, `SweepParamStep`, `WaitStep`.
  - `CompiledMacro` + `ScheduledOp` models.
  - A working `compile_macro()` that:
    - Handles `BeatAnchor` directly.
    - Supports `LocatorAnchor` via an injected `locator_resolver`.
    - Flattens timing into a simple beat timeline.
  - Structural validation via `validate_macro()`.
  - Simulation helpers: `describe_compiled_macro()` and `simulate_macro()`.
  - Sweep curve helpers: `curve_value()`, `sample_sweep_times()`, `sample_sweep_values()`.

No existing code paths are wired to these models yet; they are safe scaffolding that other parts of the app can adopt later.

### Phase 2 – Compiler Integration
- Add `/macro/compile` and `/macro/validate` endpoints that:
  - Accept a `Macro` payload.
  - Call `validate_macro()` then `compile_macro()` (injecting a locator resolver as needed).
  - Return either errors or a `CompiledMacro`.
- Integrate with existing track/device/param lookup and virtual locator storage.

### Phase 3 – Scheduler & Execution
- Implement a `MacroRunner` service that:
  - Starts at a given anchor (beats or virtual locator).
  - Uses `/transport` and parameter endpoints to execute the compiled operations.
  - Optionally rewinds and plays back a configured segment.

### Phase 4 – NLP & UI Integration
- Add a “macro builder” mode:
  - NL commands are mapped to `MacroStep`s instead of executing immediately.
  - UI shows an editable ordered list of steps.
- On “Create Macro”, send the `Macro` to `/macro/compile` and save on success.
- Add UX affordances for:
  - “Run now”
  - “Run from locator X”
  - “Preview this automation region”

---

## 6. UI Guidance (Initial)

High‑level goals for the macro builder UI:

- Treat macros as **scripts** the user can see and edit:
  - Show an ordered list of steps with time info (“at chorus start”, “over 4 bars”).
  - Allow reordering, editing, and deletion of steps.
- Make time semantics clear:
  - Let users choose a start anchor:
    - “Start at current playhead”
    - “Start at bar X”
    - “Start at virtual locator NAME”
  - For sweeps, present duration in musical units (bars/beats) and a curve selector.
- Distinguish **recording mode** from **execution**:
  - Recording mode:
    - NL commands (“set track 1 volume to ‑6 dB”, “sweep reverb wet from 20% to 80% over 4 bars”) append steps to the macro instead of acting immediately.
  - Execution:
    - After compile/validate, show a preview timeline (using `simulate_macro`) before the user confirms.
- Provide clear affordances:
  - Buttons:
    - “Add step” (manual form: choose type, track, parameter, etc.).
    - “Compile & validate” – calls `/macro/compile` / `/macro/validate`.
    - “Run now” – executes immediately.
    - Optional: “Run from locator…” / “Preview automation region”.
  - Inline errors:
    - Validation errors from `validate_macro` surfaced per step (e.g., “Unknown parameter”, “locate requires time”).

A minimal viable UI could be:

- Sidebar or panel for “Macro Builder”.
- Text list of steps with:
  - icon for type (arm/transport/param/sweep/wait),
  - textual description,
  - edit/delete controls.
- A simple form at the bottom to add a new step (type + fields).
- A toggle “Record NL into macro” that, when on, routes `/chat` results into macro steps instead of executing. 

---

## 5. Design Constraints and Non‑Goals for V1

Constraints:
- No new Remote Script features beyond what already exists.
- Base everything on:
  - Existing transport control (`/transport`, `/song/cue/jump`)
  - Existing parameter control (track/device endpoints + intents)
  - Virtual locators managed by Fadebender.

Non‑goals for V1:
- Programmatic drawing/editing of automation envelopes on Arrangement lanes.
- Complex branching/conditionals inside macros (if/else).
- Arbitrary curve editors (beyond a few simple curves for sweeps).

This keeps the system focused, testable, and aligned with Live’s supported APIs, while still delivering a powerful “preplanned automation macro” story. 
