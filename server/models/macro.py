from __future__ import annotations

from typing import Callable, List, Literal, Optional, Union

from pydantic import BaseModel, Field, validator


class BeatAnchor(BaseModel):
    kind: Literal["beats"] = "beats"
    time_beats: float


class LocatorAnchor(BaseModel):
    kind: Literal["locator"] = "locator"
    name: str


Anchor = Union[BeatAnchor, LocatorAnchor]


class ArmTrackStep(BaseModel):
    type: Literal["arm_track"] = "arm_track"
    track_index: int
    arm: bool = True


class TransportStep(BaseModel):
    type: Literal["transport"] = "transport"
    action: Literal["play", "stop", "session_record", "arrangement_record", "locate"]
    time_beats: Optional[float] = None  # used for 'locate'


class SetParamStep(BaseModel):
    type: Literal["set_param"] = "set_param"
    track_index: int
    device_ref: Optional[str] = None
    param_ref: str
    value_display: str


class SweepParamStep(BaseModel):
    type: Literal["sweep_param"] = "sweep_param"
    track_index: int
    device_ref: Optional[str] = None
    param_ref: str
    from_display: str
    to_display: str
    duration_beats: float = Field(..., gt=0.0)
    curve: Literal[
        "linear",
        "ease_in",
        "ease_out",
        "ease_in_out",
        "exp",
        "log",
    ] = "linear"


class WaitStep(BaseModel):
    type: Literal["wait"] = "wait"
    duration_beats: float = Field(..., gt=0.0)


MacroStep = Union[ArmTrackStep, TransportStep, SetParamStep, SweepParamStep, WaitStep]


class Macro(BaseModel):
    """High-level macro description (NLP/UI independent)."""

    name: str
    description: Optional[str] = None
    start_anchor: Optional[Anchor] = None
    execution_mode: Literal["relative", "absolute"] = "relative"
    steps: List[MacroStep]

    @validator("steps")
    def _non_empty_steps(cls, v: List[MacroStep]) -> List[MacroStep]:
        if not v:
            raise ValueError("macro must contain at least one step")
        return v


class ScheduledOp(BaseModel):
    """Single scheduled operation in compiled macro.

    For sweeps, end_time_beats is not None and represents the end of the interval.
    """

    time_beats: float
    end_time_beats: Optional[float] = None
    step: MacroStep


class CompiledMacro(BaseModel):
    """Flattened, validated macro ready for execution by a scheduler."""

    name: str
    steps: List[ScheduledOp]


def compile_macro(
    macro: Macro,
    locator_resolver: Optional[Callable[[str], float]] = None,
) -> CompiledMacro:
    """Compile a Macro into a simple beat-timeline plan.

    Current capabilities (beat-only, no Live access):
    - Supports BeatAnchor start (or no anchor = 0.0 beats).
    - Treats macros as linear timelines:
      - Wait steps advance the time cursor by duration_beats.
      - SweepParamStep spans [t, t + duration_beats].
      - Other steps are instantaneous at the current time cursor.

    Locator anchors are not yet resolved here and will raise a ValueError.
    """
    # Resolve start anchor
    base_time = 0.0
    if macro.start_anchor is not None:
        anchor = macro.start_anchor
        if isinstance(anchor, BeatAnchor) or getattr(anchor, "kind", None) == "beats":
            base_time = float(getattr(anchor, "time_beats", 0.0))
        elif getattr(anchor, "kind", None) == "locator":
            if locator_resolver is None:
                raise ValueError("Locator anchors require a locator_resolver")
            base_time = float(locator_resolver(getattr(anchor, "name", "")))
        else:
            raise ValueError("Unsupported anchor type in compile_macro")

    time_cursor = base_time
    scheduled: List[ScheduledOp] = []
    for step in macro.steps:
        if isinstance(step, WaitStep):
            # Represent wait as an op at the current time, then advance.
            scheduled.append(ScheduledOp(time_beats=time_cursor, end_time_beats=time_cursor, step=step))
            time_cursor += float(step.duration_beats)
        elif isinstance(step, SweepParamStep):
            start_t = time_cursor
            end_t = time_cursor + float(step.duration_beats)
            scheduled.append(ScheduledOp(time_beats=start_t, end_time_beats=end_t, step=step))
            time_cursor = end_t
        else:
            # Instantaneous operation at current time.
            scheduled.append(ScheduledOp(time_beats=time_cursor, end_time_beats=None, step=step))
            # time_cursor unchanged for instantaneous steps
    return CompiledMacro(name=macro.name, steps=scheduled)


def describe_compiled_macro(compiled: CompiledMacro) -> List[str]:
    """Return a human-readable timeline description for debugging/simulation."""
    lines: List[str] = []
    for op in compiled.steps:
        step = op.step
        if op.end_time_beats is not None and op.end_time_beats != op.time_beats:
            prefix = f"t={op.time_beats:g}→{op.end_time_beats:g}"
        else:
            prefix = f"t={op.time_beats:g}"

        if isinstance(step, ArmTrackStep):
            lines.append(f"{prefix}: arm_track(track={step.track_index}, arm={step.arm})")
        elif isinstance(step, TransportStep):
            if step.action == "locate" and step.time_beats is not None:
                lines.append(f"{prefix}: transport(action=locate, time_beats={step.time_beats:g})")
            else:
                lines.append(f"{prefix}: transport(action={step.action})")
        elif isinstance(step, SetParamStep):
            dev = f", device={step.device_ref}" if step.device_ref else ""
            lines.append(
                f"{prefix}: set_param(track={step.track_index}{dev}, "
                f"param={step.param_ref}, value={step.value_display})"
            )
        elif isinstance(step, SweepParamStep):
            dev = f", device={step.device_ref}" if step.device_ref else ""
            lines.append(
                f"{prefix}: sweep_param(track={step.track_index}{dev}, param={step.param_ref}, "
                f"from={step.from_display}, to={step.to_display}, curve={step.curve})"
            )
        elif isinstance(step, WaitStep):
            lines.append(f"{prefix}: wait({step.duration_beats:g} beats)")
        else:
            # Fallback for future step types
            lines.append(f"{prefix}: {step}")
    return lines


def simulate_macro(macro: Macro) -> List[str]:
    """Compile and describe a macro timeline without touching Live.

    This is intended for debugging, testing, and future API responses
    (e.g. showing users what will happen before execution).
    """
    compiled = compile_macro(macro)
    return describe_compiled_macro(compiled)


def curve_value(norm_t: float, curve: str) -> float:
    """Map a normalized position t in [0,1] to a curve-adjusted value in [0,1].

    This is a pure helper for future schedulers that want to generate intermediate
    values for SweepParamStep. It does not touch Live or other modules.
    """
    # Clamp to [0, 1] defensively
    if norm_t <= 0.0:
        t = 0.0
    elif norm_t >= 1.0:
        t = 1.0
    else:
        t = float(norm_t)

    if curve == "linear":
        return t
    if curve == "ease_in":
        # Quadratic ease-in
        return t * t
    if curve == "ease_out":
        # Quadratic ease-out
        u = 1.0 - t
        return 1.0 - u * u
    if curve == "ease_in_out":
        # Smoothstep (cubic) ease-in/out
        return t * t * (3.0 - 2.0 * t)
    if curve == "exp":
        # Exponential-like: slow start, fast end
        # Keep it bounded and gentle: t^3
        return t * t * t
    if curve == "log":
        # Log-like: fast start, slow end
        # Use a simple power < 1; avoid log(0)
        return t ** 0.5
    # Fallback for unexpected curve names
    return t


def sample_sweep_times(duration_beats: float, steps: int) -> List[float]:
    """Return beat offsets (0..duration_beats) for a sweep, evenly spaced.

    This is a generic helper a future scheduler can use to decide at which
    beat offsets to emit parameter updates.
    """
    if steps <= 1 or duration_beats <= 0.0:
        return [0.0]
    dt = float(duration_beats) / float(steps - 1)
    return [i * dt for i in range(steps)]


def sample_sweep_values(step: SweepParamStep, steps: int) -> List[float]:
    """Return normalized [0..1] values along a sweep's curve.

    This helper is independent of actual parameter ranges; a scheduler can map
    these normalized values onto concrete Live parameter values.
    """
    if steps <= 1:
        return [curve_value(0.0, step.curve)]
    times = sample_sweep_times(step.duration_beats, steps)
    duration = float(step.duration_beats)
    out: List[float] = []
    for t in times:
        norm = 0.0 if duration <= 0.0 else float(t) / duration
        out.append(curve_value(norm, step.curve))
    return out


def validate_macro(macro: Macro) -> List[str]:
    """Lightweight structural validation for macros (no Live access).

    Returns a list of human-readable error messages. Empty list means "valid".
    """
    errors: List[str] = []

    # Validate start anchor compatibility
    if macro.start_anchor is not None:
        kind = getattr(macro.start_anchor, "kind", None)
        if kind not in ("beats", "locator"):
            errors.append(f"unsupported start_anchor kind: {kind!r}")

    # Per-step checks
    for idx, step in enumerate(macro.steps):
        prefix = f"step {idx}"
        if isinstance(step, TransportStep):
            if step.action == "locate" and step.time_beats is None:
                errors.append(f"{prefix}: transport 'locate' requires time_beats")
            if step.action != "locate" and step.time_beats is not None:
                errors.append(f"{prefix}: time_beats is only valid for action='locate'")
        elif isinstance(step, SetParamStep):
            if not step.param_ref:
                errors.append(f"{prefix}: set_param must have param_ref")
            if not step.value_display:
                errors.append(f"{prefix}: set_param must have value_display")
        elif isinstance(step, SweepParamStep):
            if not step.param_ref:
                errors.append(f"{prefix}: sweep_param must have param_ref")
            if not step.from_display or not step.to_display:
                errors.append(f"{prefix}: sweep_param must have from_display and to_display")
        elif isinstance(step, WaitStep):
            # Pydantic already enforces duration_beats > 0, but keep a safety net
            if step.duration_beats <= 0:
                errors.append(f"{prefix}: wait.duration_beats must be > 0")

    return errors
