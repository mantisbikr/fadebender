from __future__ import annotations

from typing import Any, Dict, Literal, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from server.services.ableton_client import request_op
from server.core.deps import get_store, get_device_resolver
from server.services.mapping_utils import make_device_signature
import math
import re as _re
from server.volume_utils import db_to_live_float, db_to_live_float_send
from server.config.app_config import get_app_config, get_feature_flags


router = APIRouter()


Domain = Literal["track", "return", "master", "device", "transport"]


class CanonicalIntent(BaseModel):
    domain: Domain = Field(..., description="Scope: track|return|master|device|transport")
    action: Literal["set"] = "set"

    # Targets (one of):
    track_index: Optional[int] = None
    return_index: Optional[int] = None      # numeric index (0-based) OR
    return_ref: Optional[str] = None        # letter reference: "A", "B", "C" (preferred for user-facing API)
    device_index: Optional[int] = None      # device on track or return (depending on which index is present)
    device_name_hint: Optional[str] = None  # optional hint to resolve device_index by name
    device_ordinal_hint: Optional[int] = None  # 1-based ordinal among matches (or among all if no name)

    # Field/parameter selection
    field: Optional[str] = None             # mixer field: volume|pan|mute|solo|cue|tempo|send
    send_index: Optional[int] = None        # numeric index (0-based) OR
    send_ref: Optional[str] = None          # letter reference: "A", "B", "C" (preferred for user-facing API)
    param_index: Optional[int] = None       # device param index (preferred)
    param_ref: Optional[str] = None         # device param lookup by name (contains match)

    # Value + unit (absolute only in v1)
    # For routing intents, value may be an object with routing keys
    value: Optional[Any] = None
    unit: Optional[str] = None             # db|percent|normalized|ms|hz|on|off
    # For device params: accept display strings (e.g., "245 ms", "5.0 kHz", "High")
    display: Optional[str] = None

    # Options
    dry_run: bool = False
    clamp: bool = True
    # Options for device param dependencies
    auto_enable_master: Optional[bool] = True


class ReadIntent(BaseModel):
    domain: Domain = Field(..., description="Scope: track|return|master|device|transport")
    # Targets (one of):
    track_index: Optional[int] = None
    return_index: Optional[int] = None
    return_ref: Optional[str] = None
    device_index: Optional[int] = None

    # Selection
    field: Optional[str] = None            # mixer field for track/return/master
    param_index: Optional[int] = None      # device param index (preferred)
    param_ref: Optional[str] = None        # device param name contains
    # For send reads (track/return)
    send_index: Optional[int] = None
    send_ref: Optional[str] = None


def _clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


def _letter_to_index(letter: str) -> int:
    """Convert letter reference to 0-based index.

    Examples:
        "A" or "a" → 0
        "B" or "b" → 1
        "C" or "c" → 2

    Raises HTTPException if invalid.
    """
    letter = letter.strip().upper()
    if len(letter) != 1 or not letter.isalpha():
        raise HTTPException(400, f"invalid_letter_reference:{letter}")
    return ord(letter) - ord('A')


def _resolve_return_index(intent: CanonicalIntent) -> int:
    """Resolve return index from either return_index or return_ref.

    Prefers return_ref if provided, falls back to return_index.
    Returns 0-based index for Live API.
    """
    if intent.return_ref is not None:
        return _letter_to_index(intent.return_ref)
    if intent.return_index is not None:
        idx = int(intent.return_index)
        if idx < 0:
            raise HTTPException(400, "return_index_must_be_at_least_0")
        return idx
    raise HTTPException(400, "return_index_or_return_ref_required")


def _resolve_send_index(intent: CanonicalIntent) -> int:
    """Resolve send index from either send_index or send_ref.

    Prefers send_ref if provided, falls back to send_index.
    Returns 0-based index for Live API.
    """
    if intent.send_ref is not None:
        return _letter_to_index(intent.send_ref)
    if intent.send_index is not None:
        idx = int(intent.send_index)
        if idx < 0:
            raise HTTPException(400, "send_index_must_be_at_least_0")
        return idx
    raise HTTPException(400, "send_index_or_send_ref_required")


def _resolve_param(params: list[dict], param_index: Optional[int], param_ref: Optional[str]) -> dict:
    if isinstance(param_index, int):
        for p in params:
            if int(p.get("index", -1)) == int(param_index):
                return p
        raise HTTPException(404, "param_not_found")
    if param_ref:
        import re as _re2
        def _norm_key(s: str) -> str:
            s0 = (s or "").lower()
            # unify common short forms: lo->low, hi->high where standalone
            s0 = _re2.sub(r"\blo\b", "low", s0)
            s0 = _re2.sub(r"\bhi\b", "high", s0)
            # remove separators
            s0 = _re2.sub(r"[^a-z0-9]", "", s0)
            # normalize known pairs
            s0 = s0.replace("locut", "lowcut").replace("hicut", "highcut")
            s0 = s0.replace("lowpass", "lowcut").replace("highpass", "highcut")
            s0 = s0.replace("drywet", "drywet")
            return s0

        pref_raw = str(param_ref or "").strip()
        pref = pref_raw.lower()
        pref_norm = _norm_key(pref_raw)
        names = [str(p.get("name", "")) for p in params]
        cand = [p for p in params if pref in str(p.get("name", "")).lower()]
        if len(cand) == 0 and pref_norm:
            pairs = [(p, _norm_key(str(p.get("name", "")))) for p in params]
            exact = [p for (p, nk) in pairs if nk == pref_norm]
            if exact:
                cand = exact
            else:
                cand = [p for (p, nk) in pairs if pref_norm in nk]
        if len(cand) == 1:
            return cand[0]
        if len(cand) == 0:
            starts = [n for n in names if n.lower().startswith(pref) or _norm_key(n).startswith(pref_norm)]
            contains = [n for n in names if (pref in n.lower()) or (pref_norm and pref_norm in _norm_key(n))]
            sugg = starts or contains or names[:8]
            raise HTTPException(404, f"param_not_found:{param_ref}; candidates={sugg}")
        raise HTTPException(409, f"param_ambiguous:{param_ref}; candidates={[p.get('name') for p in cand]}")
    raise HTTPException(400, "param_selector_required")


def _auto_enable_master_if_needed(params: list[dict], target_param_name: str) -> Optional[dict]:
    """Heuristic: if a related "X On" exists and is off, return that toggle param dict.

    This is a simple name-based approach to help users who set a dependent first.
    More robust, mapping-driven grouping can replace this later.
    """
    name = (target_param_name or "").lower()
    candidates = []
    # Common sections whose dependents often require an On toggle
    keys = [
        ("chorus", "chorus on"),
        ("er spin", "er spin on"),
        ("lowshelf", "low shelf on"),
        ("low shelf", "low shelf on"),
        ("hishelf", "hi shelf on"),
        ("high shelf", "hi shelf on"),
        ("hifilter", "hifilter on"),
        ("hi filter", "hifilter on"),
        ("freeze", "freeze on"),
    ]
    for k, toggle in keys:
        if k in name:
            candidates.append(toggle)
    if not candidates:
        return None
    # find first toggle present and currently off
    for p in params:
        pname = str(p.get("name", "")).lower()
        if any(t in pname for t in candidates):
            try:
                # Off if value ~ 0.0
                val = float(p.get("value", 0.0))
                vmin = float(p.get("min", 0.0)); vmax = float(p.get("max", 1.0))
                is_off = abs(val - vmin) <= 1e-6
                if is_off:
                    return p
            except Exception:
                continue
    return None


def _check_requires_for_effect(mapping: dict | None, params: list[dict], target_param_name: str) -> list[dict]:
    """Check requires_for_effect conditions and return prerequisite parameter changes.

    Returns a list of dicts with {param_dict, target_value} for parameters that need to be changed
    to satisfy the requirements. Empty list if no requirements or all satisfied.
    """
    if not mapping:
        return []
    try:
        grp = mapping.get("grouping") or {}
        requires = grp.get("requires_for_effect") or {}

        # Find requirement for target param (case-insensitive)
        target_lc = str(target_param_name or "").strip().lower()
        req_entry = None
        for k, v in requires.items():
            if str(k).strip().lower() == target_lc:
                req_entry = v
                break

        if not req_entry:
            return []

        # Check all_of conditions
        all_of = req_entry.get("all_of") or []
        if not isinstance(all_of, list):
            return []

        # Collect unsatisfied conditions
        prereqs = []
        for cond in all_of:
            if not isinstance(cond, dict):
                continue
            req_param_name = str(cond.get("param", "")).strip().lower()
            req_value = cond.get("value")

            # Find the parameter in params list
            param_dict = None
            for p in params:
                if str(p.get("name", "")).strip().lower() == req_param_name:
                    param_dict = p
                    break

            if param_dict is None:
                continue

            # Check if current value satisfies requirement
            current_val = float(param_dict.get("value", 0.0))
            req_val = float(req_value)

            # If not satisfied, add to prereqs
            if abs(current_val - req_val) > 1e-6:
                prereqs.append({
                    "param_dict": param_dict,
                    "target_value": req_val,
                    "note": f"requires_for_effect:{target_param_name}"
                })

        return prereqs
    except Exception:
        return []


def _master_from_mapping(mapping: dict | None, params: list[dict], target_param_name: str) -> Optional[dict]:
    """Resolve a master toggle strictly via Firestore mapping.grouping.

    Uses mapping.grouping.dependents { dependent_name: master_name } (case-insensitive exact match).
    Returns the master param dict if found, else None. No heuristics.
    """
    if not mapping:
        return None
    try:
        grp = mapping.get("grouping") or {}
        deps = grp.get("dependents") or {}
        dep_key = None
        dep_lc = str(target_param_name or "").strip().lower()
        for k in deps.keys():
            if str(k).strip().lower() == dep_lc:
                dep_key = k
                break
        if dep_key is None:
            return None
        master_name = str(deps.get(dep_key) or "").strip().lower()
        for p in params:
            if str(p.get("name", "")).strip().lower() == master_name:
                return p
    except Exception:
        return None
    return None


def _parse_target_display(s: str) -> Optional[float]:
    try:
        m = _re.search(r"-?\d+(?:\.\d+)?", str(s))
        if not m:
            return None
        return float(m.group(0))
    except Exception:
        return None


def _invert_fit_to_value(fit: dict, target_y: float, vmin: float, vmax: float) -> float:
    t = (lambda a, b, y: (y - b) / a)
    ftype = fit.get("type")
    coeffs = fit.get("coeffs", {})
    if ftype == "linear":
        a = float(coeffs.get("a", 1.0)); b = float(coeffs.get("b", 0.0))
        x = t(a, b, target_y)
    elif ftype == "log":
        a = float(coeffs.get("a", 1.0)); b = float(coeffs.get("b", 0.0))
        x = math.exp((target_y - b) / a) if a != 0 else vmin
    elif ftype == "exp":
        a = float(coeffs.get("a", 1.0)); b = float(coeffs.get("b", 1.0))
        if target_y <= 0:
            x = vmin
        else:
            x = math.log(target_y / a) / b if (a != 0 and b != 0) else vmin
    else:
        pts = fit.get("points") or []
        pts = sorted([
            (float(p.get("y")), float(p.get("x")))
            for p in pts
            if p.get("x") is not None and p.get("y") is not None
        ])
        if not pts:
            return vmin
        lo = None; hi = None
        for y, x in pts:
            if y <= target_y:
                lo = (y, x)
            if y >= target_y and hi is None:
                hi = (y, x)
        if lo and hi and hi[0] != lo[0]:
            y1, x1 = lo; y2, x2 = hi
            tfrac = (target_y - y1) / (y2 - y1)
            x = x1 + tfrac * (x2 - x1)
        else:
            x = lo[1] if lo else hi[1]
    return max(vmin, min(vmax, float(x)))


def _convert_unit_value(value: float, src: Optional[str], dest: Optional[str]) -> float:
    """Convert a numeric display value between basic units when needed.

    Supported conversions: ms<->s, Hz<->kHz, pass-through for percent.
    Unknown pairs return the original value.
    """
    s = (src or "").strip().lower()
    d = (dest or "").strip().lower()
    if not s or not d or s == d:
        return float(value)
    v = float(value)
    if s == "ms" and d == "s":
        return v / 1000.0
    if s == "s" and d == "ms":
        return v * 1000.0
    if s == "khz" and d == "hz":
        return v * 1000.0
    if s == "hz" and d == "khz":
        return v / 1000.0
    if s in ("percent", "%") and d in ("percent", "%"):
        return v
    return v

def _normalize_unit(u: Optional[str]) -> Optional[str]:
    if not u:
        return None
    s = str(u).strip().lower()
    if s in ("sec", "second", "seconds"):
        return "s"
    if s in ("millisecond", "milliseconds"):
        return "ms"
    if s in ("kilohertz", "kiloherz", "khz"):
        return "khz"
    if s in ("hertz", "herz", "hz"):
        return "hz"
    if s in ("percent", "percentage"):
        return "%"
    if s in ("db", "decibel", "decibels"):
        return "db"
    if s in ("degree", "degrees", "deg", "°"):
        return "degrees"
    return s


def _detect_display_unit(disp: str) -> Optional[str]:
    s = (disp or "").lower()
    if " khz" in s or "khz" in s:
        return "khz"
    if " hz" in s or s.endswith("hz"):
        return "hz"
    if " ms" in s or s.endswith("ms"):
        return "ms"
    if s.endswith(" s") or s.endswith(" sec") or s.endswith(" second") or s.endswith(" seconds") or s.endswith("s"):
        return "s"
    if "db" in s:
        return "db"
    if "degree" in s or "degrees" in s or "°" in s:
        return "degrees"
    if "%" in s:
        return "%"
    return None


def _get_mixer_param_meta(entity_type: str, param_name: str) -> Optional[Dict[str, Any]]:
    """Get parameter metadata from consolidated mixer channel mapping.

    Args:
        entity_type: Entity type ("track", "return", or "master")
        param_name: Parameter name ("volume", "pan", "mute", "solo", "sends", "cue")

    Returns:
        Parameter metadata dict from params_meta or None if not found
    """
    try:
        store = get_store()
        if not store.enabled:
            return None

        channel = store.get_mixer_channel_mapping(entity_type)
        if not channel:
            return None

        params_meta = channel.get("params_meta", [])
        return next((p for p in params_meta if p.get("name") == param_name), None)
    except Exception:
        return None


def _apply_mixer_fit_inverse(param_meta: Dict[str, Any], display_value: float) -> Optional[float]:
    """Convert display value to normalized using fit formula (inverse direction).

    Args:
        param_meta: Parameter metadata from params_meta
        display_value: Display value (e.g., -6.0 for dB, 25.0 for pan)

    Returns:
        Normalized value (0.0-1.0 for volume/cue, -1.0 to 1.0 for pan) or None if no fit
    """
    fit = param_meta.get("fit", {})
    fit_type = fit.get("type")
    coeffs = fit.get("coeffs", {})

    if fit_type == "power":
        # Power law: normalized = ((display - min_db) / range_db) ** gamma
        # Inverse: display = min_db + range_db * (normalized ** (1/gamma))
        min_db = coeffs.get("min_db")
        max_db = coeffs.get("max_db")
        gamma = coeffs.get("gamma")
        range_db = coeffs.get("range_db", max_db - min_db if (max_db and min_db) else None)

        if min_db is None or range_db is None or gamma is None:
            return None

        # Forward: dB → normalized
        normalized = ((display_value - min_db) / range_db) ** gamma
        return max(0.0, min(1.0, normalized))

    elif fit_type == "linear":
        # Linear: normalized = display_value / scale
        scale = coeffs.get("scale", 50.0)
        normalized = display_value / scale
        return max(-1.0, min(1.0, normalized))  # Pan range

    return None


def _apply_mixer_fit_forward(param_meta: Dict[str, Any], normalized_value: float) -> Optional[float]:
    """Convert normalized value to display using fit formula (forward direction).

    Args:
        param_meta: Parameter metadata from params_meta
        normalized_value: Normalized value (0.0-1.0 for volume/cue, -1.0 to 1.0 for pan)

    Returns:
        Display value (e.g., -6.0 for dB, 25.0 for pan) or None if no fit
    """
    fit = param_meta.get("fit", {})
    fit_type = fit.get("type")
    coeffs = fit.get("coeffs", {})

    if fit_type == "power":
        # Power law inverse: display = min_db + range_db * (normalized ** (1/gamma))
        min_db = coeffs.get("min_db")
        max_db = coeffs.get("max_db")
        gamma = coeffs.get("gamma")
        range_db = coeffs.get("range_db", max_db - min_db if (max_db and min_db) else None)

        if min_db is None or range_db is None or gamma is None:
            return None

        display = min_db + range_db * (normalized_value ** (1.0 / gamma))
        return display

    elif fit_type == "linear":
        # Linear inverse: display_value = normalized * scale
        scale = coeffs.get("scale", 50.0)
        display = normalized_value * scale
        return display

    return None


def _get_mixer_display_range(field: str):
    """Get display range (min, max) for a mixer field from Firestore mapping.

    Args:
        field: Mixer field name ("pan", "volume", etc.)

    Returns:
        Tuple of (display_min, display_max), or default fallback values
    """
    try:
        store = get_store()
        if not store.enabled:
            return (-50.0, 50.0) if field == "pan" else (0.0, 1.0)

        # Try new consolidated structure first
        # Determine entity type based on context (track is most common)
        for entity_type in ["track", "return", "master"]:
            pm = _get_mixer_param_meta(entity_type, field)
            if pm:
                dmin = pm.get("min_display")
                dmax = pm.get("max_display")
                if dmin is not None and dmax is not None:
                    return (float(dmin), float(dmax))

        # Fall back to old structure
        mapping = store.get_mixer_param_mapping(field)
        if not mapping:
            return (-50.0, 50.0) if field == "pan" else (0.0, 1.0)

        display_range = mapping.get("display_range", {})
        dmin = float(display_range.get("min", -50.0 if field == "pan" else 0.0))
        dmax = float(display_range.get("max", 50.0 if field == "pan" else 1.0))
        return (dmin, dmax)
    except Exception:
        return (-50.0, 50.0) if field == "pan" else (0.0, 1.0)


def _resolve_mixer_display_value(field: str, display: str) -> Optional[float]:
    """Resolve mixer parameter display value to normalized value using Firestore mappings.

    Args:
        field: Mixer field name ("pan", "volume", etc.)
        display: Display value string (e.g., "25L", "center", "unity")

    Returns:
        Normalized value or None if not found
    """
    try:
        store = get_store()
        if not store.enabled:
            return None

        # Try new consolidated structure first
        # Check all entity types for param metadata
        for entity_type in ["track", "return", "master"]:
            pm = _get_mixer_param_meta(entity_type, field)
            if pm:
                # Try numeric parsing first (for display values like "-6", "25")
                num = _parse_target_display(display)
                if num is not None and pm.get("fit"):
                    # Use fit formula to convert display → normalized
                    result = _apply_mixer_fit_inverse(pm, num)
                    if result is not None:
                        return result

                # Try preset lookup (for presets like "unity", "center")
                # Note: Presets are no longer in consolidated structure - fallback to old only

        # Fall back to old structure for presets
        mapping = store.get_mixer_param_mapping(field)
        if not mapping:
            return None

        presets = mapping.get("display_value_presets", {})
        if not isinstance(presets, dict):
            return None

        # Normalize the display string for lookup
        display_normalized = display.strip().lower()

        # Direct lookup
        if display_normalized in presets:
            return float(presets[display_normalized])

        # Try numeric parsing for display range values
        # For pan: use the display_range from mapping
        if field == "pan":
            num = _parse_target_display(display)
            if num is not None:
                # Get display range from Firestore mapping
                display_min, display_max = _get_mixer_display_range("pan")
                display_scale = max(abs(display_min), abs(display_max))
                # Convert display value to normalized (-1.0 to 1.0)
                return _clamp(float(num) / display_scale, -1.0, 1.0)

        return None
    except Exception:
        return None


def _generate_device_param_summary(
    param_name: str,
    param_meta: Optional[dict],
    old_value: float,
    new_value: float,
    new_display: str,
    device_name: str,
    return_ref: Optional[str] = None,
    track_index: Optional[int] = None,
    old_display: Optional[str] = None,
) -> str:
    """Generate a rich summary for a device parameter change.

    Args:
        param_name: Parameter name (e.g., "Decay Time")
        param_meta: Firestore params_meta dict for this parameter (may be None)
        old_value: Previous normalized value
        new_value: New normalized value
        new_display: New display value (e.g., "2.00 s")
        device_name: Device name (e.g., "Reverb")
        return_ref: Return letter reference (e.g., "A") if on a return
        track_index: Track index if on a track

    Returns:
        Human-readable summary string
    """
    # Build location context
    if return_ref:
        location = f"Return {return_ref} {device_name}"
    elif track_index is not None:
        location = f"Track {track_index} {device_name}"
    else:
        location = device_name

    # Direction of change: prefer display-based comparison (e.g., ms, dB) when available
    increased = new_value > old_value
    try:
        od = _parse_target_display(str(old_display)) if old_display is not None else None
        nd = _parse_target_display(str(new_display)) if new_display is not None else None
        if od is not None and nd is not None:
            increased = float(nd) > float(od)
    except Exception:
        pass
    direction_word = "increased" if increased else ("decreased" if new_value < old_value else "set")

    # Format numeric portion of display to max 2 decimals
    try:
        s = str(new_display)
        m = _re.search(r"-?\d+(?:\.\d+)?", s)
        if m:
            num = float(m.group(0))
            rounded = round(num, 2)
            # Trim trailing zeros
            num_str = (f"{rounded:.2f}").rstrip('0').rstrip('.')
            new_display = s[:m.start()] + num_str + s[m.end():]
    except Exception:
        pass

    # Base summary
    summary = f"Set {param_name} on {location} to {new_display}."

    # Add sonic context if available from params_meta
    if param_meta:
        audio_knowledge = param_meta.get("audio_knowledge", {})
        sonic_effect = audio_knowledge.get("sonic_effect", {})

        if sonic_effect:
            # Choose the appropriate sonic effect based on direction
            effect_text = None
            if increased and sonic_effect.get("increasing"):
                effect_text = sonic_effect.get("increasing")
            elif not increased and sonic_effect.get("decreasing"):
                effect_text = sonic_effect.get("decreasing")

            if effect_text:
                # Check if effect_text starts with a verb (already a complete sentence)
                # Otherwise treat it as a noun phrase describing the result
                first_word = effect_text.split()[0].lower() if effect_text else ""
                common_verbs = {"create", "creates", "add", "adds", "reduce", "reduces", "increase", "increases", "decrease", "decreases", "make", "makes"}

                if first_word in common_verbs:
                    # Already a verb phrase, use as-is
                    summary += f" This will {effect_text.lower()}."
                else:
                    # Noun phrase - describe the result
                    summary += f" Result: {effect_text}."
        elif audio_knowledge.get("audio_function"):
            # Fallback to general audio function if no directional effects
            summary += f" {audio_knowledge.get('audio_function')}."

    # Parameter-specific dynamic hints based on display value
    try:
        pname_lc = (param_name or "").strip().lower()
        disp_num = _parse_target_display(str(new_display))
        # Stereo Image heuristics (degrees: 0 = mono, ~120 = very wide)
        if disp_num is not None and "stereo image" in pname_lc:
            deg = float(disp_num)
            if deg <= 5:
                summary += " (mono)."
            elif deg <= 30:
                summary += " (narrow)."
            elif deg <= 75:
                summary += " (moderate width)."
            elif deg < 110:
                summary += " (wide)."
            else:
                summary += " (very wide)."
    except Exception:
        pass

    return summary


@router.post("/intent/execute")
def execute_intent(intent: CanonicalIntent) -> Dict[str, Any]:
    d = intent.domain
    field = intent.field or ""
    features = get_feature_flags()
    display_only_io = bool((features or {}).get("display_only_io", False))
    # Track routing execute
    if d == "track" and field == "routing" and intent.track_index is not None:
        ti = int(intent.track_index)
        # Build payload from optional kwargs on intent (only known keys will be passed through)
        allowed = {
            "monitor_state": None,
            "audio_from_type": None,
            "audio_from_channel": None,
            "audio_to_type": None,
            "audio_to_channel": None,
            "midi_from_type": None,
            "midi_from_channel": None,
            "midi_to_type": None,
            "midi_to_channel": None,
        }
        # Pydantic model doesn't carry arbitrary fields; support passing values via unit/display for now is not relevant.
        # Instead, accept these fields via value semantics is out-of-scope; expect clients to call set routing via dedicated API.
        # For intents, we allow attaching a dict under 'value' when field==routing.
        payload = {}
        if isinstance(intent.value, dict):
            for k in allowed.keys():
                v = intent.value.get(k)
                if v is not None:
                    payload[k] = v
        # Validate against available options to avoid sending unsupported values to Live
        cur = request_op("get_track_routing", timeout=1.0, track_index=ti) or {}
        data_cur = (cur.get("data") or cur) if isinstance(cur, dict) else {}
        opts = (data_cur or {}).get("options") or {}
        cfg = get_app_config()
        aliases = (cfg.get("routing_aliases") or {}).get("track", {})
        # Helper: normalize against options with case-insensitive match + alias map
        def _normalize_choice(val, option_key):
            if val is None:
                return None
            arr = opts.get(option_key) or []
            lower_map = {str(x).strip().lower(): str(x) for x in arr}
            v_in = str(val).strip()
            v_l = v_in.lower()
            if v_l in lower_map:
                return lower_map[v_l]
            # Alias map: aliases[option_key] is a dict of alias->canonical
            try:
                ali = ((aliases.get(option_key)) or {})
                target = ali.get(v_l)
                if target:
                    t_l = str(target).strip().lower()
                    if t_l in lower_map:
                        return lower_map[t_l]
            except Exception:
                pass
            return None
        # Normalize and validate each provided routing key
        if "audio_to_type" in payload:
            norm = _normalize_choice(payload.get("audio_to_type"), "audio_to_types")
            if norm is None:
                return {"ok": False, "error": "invalid_audio_to_type", "requested": payload.get("audio_to_type"), "allowed": opts.get("audio_to_types")}
            payload["audio_to_type"] = norm
        if "audio_to_channel" in payload:
            norm = _normalize_choice(payload.get("audio_to_channel"), "audio_to_channels")
            if norm is None:
                return {"ok": False, "error": "invalid_audio_to_channel", "requested": payload.get("audio_to_channel"), "allowed": opts.get("audio_to_channels")}
            payload["audio_to_channel"] = norm
        if "audio_from_type" in payload:
            norm = _normalize_choice(payload.get("audio_from_type"), "audio_from_types")
            if norm is None:
                return {"ok": False, "error": "invalid_audio_from_type", "requested": payload.get("audio_from_type"), "allowed": opts.get("audio_from_types")}
            payload["audio_from_type"] = norm
        if "audio_from_channel" in payload:
            norm = _normalize_choice(payload.get("audio_from_channel"), "audio_from_channels")
            if norm is None:
                return {"ok": False, "error": "invalid_audio_from_channel", "requested": payload.get("audio_from_channel"), "allowed": opts.get("audio_from_channels")}
            payload["audio_from_channel"] = norm
        if "midi_from_type" in payload:
            norm = _normalize_choice(payload.get("midi_from_type"), "midi_from_types")
            if norm is None:
                return {"ok": False, "error": "invalid_midi_from_type", "requested": payload.get("midi_from_type"), "allowed": opts.get("midi_from_types")}
            payload["midi_from_type"] = norm
        if "midi_from_channel" in payload:
            norm = _normalize_choice(payload.get("midi_from_channel"), "midi_from_channels")
            if norm is None:
                return {"ok": False, "error": "invalid_midi_from_channel", "requested": payload.get("midi_from_channel"), "allowed": opts.get("midi_from_channels")}
            payload["midi_from_channel"] = norm
        if "midi_to_type" in payload:
            norm = _normalize_choice(payload.get("midi_to_type"), "midi_to_types")
            if norm is None:
                return {"ok": False, "error": "invalid_midi_to_type", "requested": payload.get("midi_to_type"), "allowed": opts.get("midi_to_types")}
            payload["midi_to_type"] = norm
        if "midi_to_channel" in payload:
            norm = _normalize_choice(payload.get("midi_to_channel"), "midi_to_channels")
            if norm is None:
                return {"ok": False, "error": "invalid_midi_to_channel", "requested": payload.get("midi_to_channel"), "allowed": opts.get("midi_to_channels")}
            payload["midi_to_channel"] = norm
        if intent.dry_run:
            return {"ok": True, "preview": {"current": (cur.get("data") or cur), "apply": {"track_index": ti, **payload}}}
        resp = request_op("set_track_routing", timeout=1.2, track_index=ti, **payload)
        if not resp:
            raise HTTPException(504, "no_reply")
        return resp
    # Return routing execute
    if d == "return" and field == "routing" and intent.return_index is not None:
        ri = int(intent.return_index)
        allowed = {"audio_to_type": None, "audio_to_channel": None, "sends_mode": None}
        payload = {}
        if isinstance(intent.value, dict):
            for k in allowed.keys():
                v = intent.value.get(k)
                if v is not None:
                    payload[k] = v
        # Validate choices against options
        cur = request_op("get_return_routing", timeout=1.0, return_index=ri) or {}
        data_cur = (cur.get("data") or cur) if isinstance(cur, dict) else {}
        opts = (data_cur or {}).get("options") or {}
        cfg = get_app_config()
        aliases = (cfg.get("routing_aliases") or {}).get("return", {})
        def _normalize_choice(val, option_key):
            if val is None:
                return None
            arr = opts.get(option_key) or []
            lower_map = {str(x).strip().lower(): str(x) for x in arr}
            v_in = str(val).strip(); v_l = v_in.lower()
            if v_l in lower_map:
                return lower_map[v_l]
            try:
                ali = ((aliases.get(option_key)) or {})
                target = ali.get(v_l)
                if target:
                    t_l = str(target).strip().lower()
                    if t_l in lower_map:
                        return lower_map[t_l]
            except Exception:
                pass
            return None
        if "audio_to_type" in payload:
            norm = _normalize_choice(payload.get("audio_to_type"), "audio_to_types")
            if norm is None:
                return {"ok": False, "error": "invalid_audio_to_type", "requested": payload.get("audio_to_type"), "allowed": opts.get("audio_to_types")}
            payload["audio_to_type"] = norm
        if "audio_to_channel" in payload:
            norm = _normalize_choice(payload.get("audio_to_channel"), "audio_to_channels")
            if norm is None:
                return {"ok": False, "error": "invalid_audio_to_channel", "requested": payload.get("audio_to_channel"), "allowed": opts.get("audio_to_channels")}
            payload["audio_to_channel"] = norm
        if intent.dry_run:
            cur = request_op("get_return_routing", timeout=1.0, return_index=ri) or {}
            return {"ok": True, "preview": {"current": (cur.get("data") or cur), "apply": {"return_index": ri, **payload}}}
        resp = request_op("set_return_routing", timeout=1.2, return_index=ri, **payload)
        if not resp:
            raise HTTPException(504, "no_reply")
        return resp
    # Track mixer
    if d == "track" and field in ("volume", "pan", "mute", "solo"):
        if intent.track_index is None:
            raise HTTPException(400, "track_index_required")
        track_idx = int(intent.track_index)
        # Tracks are 1-based in Live API (Track 1 = index 1)
        if track_idx < 1:
            raise HTTPException(400, "track_index_must_be_at_least_1")
        # Validate track exists; provide helpful hint
        try:
            ov = request_op("get_overview", timeout=1.0) or {}
            tracks = ((ov.get("data") or ov) if isinstance(ov, dict) else ov).get("tracks", [])
            if tracks and track_idx > len(tracks):
                names = ", ".join([str(t.get("name", f"Track {t.get('index')}")) for t in tracks])
                raise HTTPException(404, f"track_out_of_range:{track_idx}; available=1..{len(tracks)}; tracks=[{names}]")
        except HTTPException:
            raise
        except Exception:
            pass
        # Value handling
        v = float(intent.value if intent.value is not None else 0.0)

        # Check for display value (string presets like "center", "25L", "unity")
        if intent.display and field in ("pan", "volume"):
            resolved = _resolve_mixer_display_value(field, intent.display)
            if resolved is not None:
                v = resolved
            # If display resolves to None, fall through to normal value handling

        if field == "volume":
            # Disallow normalized input when display_only_io is enabled
            if display_only_io and (intent.unit is None) and 0.0 <= v <= 1.0:
                raise HTTPException(400, "normalized_not_allowed_for_volume: provide dB (unit='db') or percent")
            if (intent.unit or "").lower() in ("db", "dB".lower()):
                v = db_to_live_float(v)
            elif (intent.unit or "").lower() in ("percent", "%"):
                v = v / 100.0
            v = _clamp(v, 0.0, 1.0) if intent.clamp else v
        elif field == "pan":
            # Pan: If value is outside [-1, 1], treat as display value and convert
            # Get display range from Firestore mapping (e.g., -50 to 50)
            if display_only_io and (intent.display is None) and -1.0 <= v <= 1.0 and not intent.unit:
                raise HTTPException(400, "normalized_not_allowed_for_pan: provide display like '30L'/'30R'")
            if abs(v) > 1.0:
                # Display value: convert using mapping range
                display_min, display_max = _get_mixer_display_range("pan")
                display_scale = max(abs(display_min), abs(display_max))
                v = _clamp(v, display_min, display_max) / display_scale
            else:
                # Already normalized -1.0 to 1.0
                v = _clamp(v, -1.0, 1.0) if intent.clamp else v
        elif field in ("mute", "solo"):
            # Treat >0.5 as on
            v = 1.0 if v >= 0.5 else 0.0
        if intent.dry_run:
            return {"ok": True, "preview": {"op": "set_mixer", "track_index": track_idx, "field": field, "value": v}}
        resp = request_op("set_mixer", timeout=1.0, track_index=track_idx, field=str(field), value=float(v))
        if not resp:
            raise HTTPException(504, "no_reply")
        return resp

    # Track sends
    if d == "track" and field == "send":
        if intent.track_index is None:
            raise HTTPException(400, "track_index_required")
        if intent.send_index is None and intent.send_ref is None:
            raise HTTPException(400, "send_index_or_send_ref_required")
        track_idx = int(intent.track_index)
        send_idx = _resolve_send_index(intent)
        # Tracks are 1-based, but sends are 0-based in Live API
        if track_idx < 1:
            raise HTTPException(400, "track_index_must_be_at_least_1")
        v = float(intent.value if intent.value is not None else 0.0)
        if display_only_io and (intent.unit is None) and 0.0 <= v <= 1.0:
            raise HTTPException(400, "normalized_not_allowed_for_send: provide dB (unit='db') or percent")
        # Add dB support for sends (range: -60dB to 0dB)
        if (intent.unit or "").lower() in ("db", "dB".lower()):
            v = db_to_live_float_send(v)
        elif (intent.unit or "").lower() in ("percent", "%"):
            v = v / 100.0
        v = _clamp(v, 0.0, 1.0) if intent.clamp else v
        if intent.dry_run:
            return {"ok": True, "preview": {"op": "set_send", "track_index": track_idx, "send_index": send_idx, "value": v}}
        resp = request_op("set_send", timeout=1.0, track_index=track_idx, send_index=send_idx, value=float(v))
        if not resp:
            raise HTTPException(504, "no_reply")
        return resp

    # Return mixer
    if d == "return" and field in ("volume", "pan", "mute", "solo"):
        return_idx = _resolve_return_index(intent)
        # Validate return index against available returns
        try:
            rs = request_op("get_return_tracks", timeout=1.0) or {}
            rets = ((rs.get("data") or rs) if isinstance(rs, dict) else rs).get("returns", [])
            if rets and (return_idx < 0 or return_idx >= len(rets)):
                letters = [chr(ord('A') + int(r.get("index", 0))) for r in rets]
                names = ", ".join([f"{letters[i]}:{str(rets[i].get('name',''))}" for i in range(len(rets))])
                raise HTTPException(404, f"return_out_of_range:{return_idx}; available=0..{len(rets)-1} (A..{letters[-1] if letters else 'A'}); returns=[{names}]")
        except HTTPException:
            raise
        except Exception:
            pass
        v = float(intent.value if intent.value is not None else 0.0)

        # Check for display value (string presets like "center", "25L", "unity")
        if intent.display and field in ("pan", "volume"):
            resolved = _resolve_mixer_display_value(field, intent.display)
            if resolved is not None:
                v = resolved

        if field == "volume":
            if display_only_io and (intent.unit is None) and 0.0 <= v <= 1.0:
                raise HTTPException(400, "normalized_not_allowed_for_volume: provide dB (unit='db') or percent")
            # Add dB support for return volume (range: -60dB to +6dB)
            if (intent.unit or "").lower() in ("db", "dB".lower()):
                v = db_to_live_float(v)
            elif (intent.unit or "").lower() in ("percent", "%"):
                v = v / 100.0
            v = _clamp(v, 0.0, 1.0) if intent.clamp else v
        elif field == "pan":
            if display_only_io and (intent.display is None) and -1.0 <= v <= 1.0 and not intent.unit:
                raise HTTPException(400, "normalized_not_allowed_for_pan: provide display like '30L'/'30R'")
            # Pan: If value is outside [-1, 1], treat as display value and convert
            # Get display range from Firestore mapping (e.g., -50 to 50)
            if abs(v) > 1.0:
                # Display value: convert using mapping range
                display_min, display_max = _get_mixer_display_range("pan")
                display_scale = max(abs(display_min), abs(display_max))
                v = _clamp(v, display_min, display_max) / display_scale
            else:
                # Already normalized -1.0 to 1.0
                v = _clamp(v, -1.0, 1.0) if intent.clamp else v
        elif field in ("mute", "solo"):
            v = 1.0 if v >= 0.5 else 0.0
        if intent.dry_run:
            return {"ok": True, "preview": {"op": "set_return_mixer", "return_index": return_idx, "field": field, "value": v}}
        resp = request_op("set_return_mixer", timeout=1.0, return_index=return_idx, field=str(field), value=float(v))
        if not resp:
            raise HTTPException(504, "no_reply")
        return resp

    # Return sends
    if d == "return" and field == "send":
        return_idx = _resolve_return_index(intent)
        # Validate return bounds
        try:
            rs = request_op("get_return_tracks", timeout=1.0) or {}
            rets = ((rs.get("data") or rs) if isinstance(rs, dict) else rs).get("returns", [])
            if rets and (return_idx < 0 or return_idx >= len(rets)):
                letters = [chr(ord('A') + int(r.get("index", 0))) for r in rets]
                raise HTTPException(404, f"return_out_of_range:{return_idx}; returns={letters}")
        except HTTPException:
            raise
        except Exception:
            pass
        send_idx = _resolve_send_index(intent)
        v = float(intent.value if intent.value is not None else 0.0)
        if display_only_io and (intent.unit is None) and 0.0 <= v <= 1.0:
            raise HTTPException(400, "normalized_not_allowed_for_send: provide dB (unit='db') or percent")
        # Add dB support for return sends (range: -60dB to 0dB)
        if (intent.unit or "").lower() in ("db", "dB".lower()):
            v = db_to_live_float_send(v)
        elif (intent.unit or "").lower() in ("percent", "%"):
            v = v / 100.0
        v = _clamp(v, 0.0, 1.0) if intent.clamp else v
        if intent.dry_run:
            return {"ok": True, "preview": {"op": "set_return_send", "return_index": return_idx, "send_index": send_idx, "value": v}}
        resp = request_op("set_return_send", timeout=1.0, return_index=return_idx, send_index=send_idx, value=float(v))
        if not resp:
            raise HTTPException(504, "no_reply")
        return resp

    # Master mixer (subset)
    if d == "master" and field in ("volume", "pan", "cue"):
        v = float(intent.value if intent.value is not None else 0.0)

        # Check for display value (string presets like "center", "25L", "unity")
        if intent.display and field in ("pan", "volume", "cue"):
            resolved = _resolve_mixer_display_value(field, intent.display)
            if resolved is not None:
                v = resolved

        if field == "volume":
            if (intent.unit or "").lower() in ("db", "dB".lower()):
                v = db_to_live_float(v)
            elif (intent.unit or "").lower() in ("percent", "%"):
                v = v / 100.0
            v = _clamp(v, 0.0, 1.0) if intent.clamp else v
        elif field == "cue":
            # Cue volume: only supports dB (no percent)
            if (intent.unit or "").lower() in ("db", "dB".lower()):
                v = db_to_live_float(v)
            # No else - if no unit specified, treat as error (user must specify dB)
            elif not intent.display:
                raise HTTPException(400, "cue_requires_db_unit_or_display_value")
            v = _clamp(v, 0.0, 1.0) if intent.clamp else v
        elif field == "pan":
            # Pan: If value is outside [-1, 1], treat as display value and convert
            # Get display range from Firestore mapping (e.g., -50 to 50)
            if abs(v) > 1.0:
                # Display value: convert using mapping range
                display_min, display_max = _get_mixer_display_range("pan")
                display_scale = max(abs(display_min), abs(display_max))
                v = _clamp(v, display_min, display_max) / display_scale
            else:
                # Already normalized -1.0 to 1.0
                v = _clamp(v, -1.0, 1.0) if intent.clamp else v
        if intent.dry_run:
            return {"ok": True, "preview": {"op": "set_master_mixer", "field": field, "value": v}}
        resp = request_op("set_master_mixer", timeout=1.0, field=str(field), value=float(v))
        if not resp:
            raise HTTPException(504, "no_reply")
        return resp

    # Device parameter (return device)
    if d == "device" and (intent.return_index is not None or intent.return_ref is not None) and intent.device_index is not None:
        ri = _resolve_return_index(intent)
        di = int(intent.device_index)
        # If hints provided, try to resolve index by name and/or ordinal
        if intent.device_name_hint or intent.device_ordinal_hint:
            try:
                devs_list = request_op("get_return_devices", timeout=1.0, return_index=ri) or {}
                devs = ((devs_list.get("data") or devs_list) if isinstance(devs_list, dict) else devs_list).get("devices", [])
                matches = []
                # Build matches by name when hint provided; else all devices
                if intent.device_name_hint:
                    hint = str(intent.device_name_hint).strip().lower()
                    hint_nos = hint.replace(" ", "")
                    for d in devs:
                        nm = str(d.get("name", ""))
                        nml = nm.strip().lower()
                        if nml == hint or nml.replace(" ", "") == hint_nos or (hint in nml) or (hint_nos in nml.replace(" ", "")):
                            matches.append(int(d.get("index", 0)))
                else:
                    matches = [int(d.get("index", 0)) for d in devs]
                matches = sorted(set(matches))
                ord_hint = int(intent.device_ordinal_hint) if intent.device_ordinal_hint else None
                if matches:
                    if ord_hint:
                        if 1 <= ord_hint <= len(matches):
                            di = matches[ord_hint - 1]
                        else:
                            # If an exact name match exists, prefer it and ignore the ordinal
                            try:
                                hint_raw = str(intent.device_name_hint or "").strip().lower()
                                exact = next((int(d.get('index', 0)) for d in devs if str(d.get('name','')).strip().lower() == hint_raw), None)
                            except Exception:
                                exact = None
                            if exact is not None:
                                di = exact
                            else:
                                # Ordinal out of range — return choices
                                choices = ", ".join([f"{int(d.get('index',0))}:{str(d.get('name',''))}" for d in devs])
                                raise HTTPException(404, f"device_ordinal_out_of_range:{ord_hint}; matches={len(matches)}; devices=[{choices}]")
                    else:
                        di = matches[0]
                else:
                    # No matches for name hint — return device list to help user
                    choices = ", ".join([f"{int(d.get('index',0))}:{str(d.get('name',''))}" for d in devs])
                    raise HTTPException(404, f"device_not_found_for_hint:{intent.device_name_hint}; devices=[{choices}]")
            except HTTPException:
                raise
            except Exception:
                pass
        # Validate device exists and capture friendly names
        try:
            devs_list = request_op("get_return_devices", timeout=1.0, return_index=ri) or {}
            devs = ((devs_list.get("data") or devs_list) if isinstance(devs_list, dict) else devs_list).get("devices", [])
            if devs and (di < 0 or di >= len(devs)):
                names = ", ".join([f"{int(d.get('index',0))}:{str(d.get('name',''))}" for d in devs])
                raise HTTPException(404, f"device_out_of_range:{di}; devices=[{names}] on Return {chr(ord('A')+ri)}")
        except HTTPException:
            raise
        except Exception:
            pass
        # Resolve device index using LiveIndex/Resolver when hints are provided
        try:
            if intent.device_name_hint or intent.device_ordinal_hint:
                resolver = get_device_resolver()
                di_res, _dname, _notes = resolver.resolve_return(
                    return_index=ri,
                    device_name_hint=intent.device_name_hint,
                    device_ordinal_hint=intent.device_ordinal_hint,
                )
                di = int(di_res)
        except Exception:
            pass
        # Read params to get min/max, resolve selection
        pr = request_op("get_return_device_params", timeout=1.2, return_index=ri, device_index=di)
        params = ((pr or {}).get("data") or {}).get("params") or []
        if not params:
            raise HTTPException(404, "params_not_found")
        # Apply alias resolution for param_ref before selection
        pref = _alias_param_name_if_needed(intent.param_ref)
        sel = _resolve_param(params, intent.param_index, pref)
        vmin = float(sel.get("min", 0.0)); vmax = float(sel.get("max", 1.0))
        x = float(intent.value if intent.value is not None else vmin)
        # If display provided, try mapping via params_meta fit/labels; fallback to refine if not dry_run
        used_display = False
        unit_lc = _normalize_unit(intent.unit)
        target_display = intent.display if intent.display is not None else (str(intent.value) if unit_lc == "display" and intent.value is not None else None)
        # Initialize mapping and pm (params_meta) early so we can use declared units
        mapping = None
        pm = None
        try:
            store = get_store()
            devs = request_op("get_return_devices", timeout=1.0, return_index=ri)
            devices = ((devs or {}).get("data") or {}).get("devices") or []
            dname = next((str(d.get("name", "")) for d in devices if int(d.get("index", -1)) == di), f"Device {di}")
            sig = make_device_signature(dname, params)
            mapping = store.get_device_mapping(sig) if store.enabled else None
            if mapping:
                pm = next((pme for pme in (mapping.get("params_meta") or []) if str(pme.get("name", "")).lower() == str(sel.get("name", "")).lower()), None)
        except Exception:
            mapping = None
            pm = None
        # Treat common display units as display-mode if value provided
        if target_display is None and unit_lc in ("ms", "s", "hz", "khz", "db", "%", "percent", "degrees", "on", "off") and intent.value is not None:
            target_display = str(intent.value)
        # If no explicit display provided, choose best interpretation based on mapping
        if target_display is None and intent.value is not None:
            try:
                val = float(intent.value)
                # Prefer declared unit from mapping
                if pm and isinstance(pm.get("unit"), str):
                    pm_unit = (pm.get("unit") or "").strip().lower()
                    if pm_unit in ("ms", "s", "hz", "khz", "db", "%", "degrees"):
                        target_display = str(val)
                        used_display = True
                # If min/max display exist and value is within that range, use display directly
                if target_display is None and pm is not None and pm.get("min_display") is not None and pm.get("max_display") is not None:
                    md = float(pm.get("min_display")); Mx = float(pm.get("max_display"))
                    if md <= val <= Mx:
                        target_display = str(val)
                        used_display = True
                    # Special case: 0..1 displays with human input in 0..100 → interpret as percent
                    elif md >= 0.0 and Mx <= 1.0 and 0.0 <= val <= 100.0:
                        unit_lc = "%"  # triggers percent handling later
            except Exception:
                pass

        if target_display is not None:
            used_display = True
            ty = _parse_target_display(target_display)
            # Label resolution - check label_map FIRST for quantized params (even if numeric)
            if pm and isinstance(pm.get("label_map"), dict):
                lm = pm.get("label_map") or {}
                lnorm = target_display.strip().lower()
                # Try exact match in label_map first
                # label_map format: {"0": "Clean", "1": "Boost", ...} (number → label)
                matched = False
                for k, v in lm.items():
                    if str(v).strip().lower() == lnorm:
                        x = float(k)
                        matched = True
                        break
                # If not matched, check for on/off synonyms
                if not matched:
                    if lnorm in {"on", "enable", "enabled", "true", "1", "yes"}:
                        x = vmax
                        matched = True
                    elif lnorm in {"off", "disable", "disabled", "false", "0", "no"}:
                        x = vmin
                        matched = True
                # Skip numeric processing if we matched a label
                if matched:
                    ty = None  # Prevent falling through to numeric handler
            # Handle common on/off without label_map present
            if ty is None and not pm.get("label_map"):
                lnorm = str(target_display).strip().lower()
                if lnorm in {"on", "enable", "enabled", "true", "1", "yes"}:
                    x = vmax
                elif lnorm in {"off", "disable", "disabled", "false", "0", "no"}:
                    x = vmin
            # Numeric display
            elif ty is not None:
                if pm and isinstance(pm.get("fit"), dict):
                    # Align input numeric with params_meta unit if provided
                    pm_unit = (pm.get("unit") or "").strip().lower()
                    # Detect unit from display string if unit_lc is empty
                    input_unit = unit_lc or _detect_display_unit(target_display) or pm_unit
                    ty_aligned = _convert_unit_value(float(ty), input_unit, pm_unit)
                    x = _invert_fit_to_value(pm.get("fit") or {}, float(ty_aligned), vmin, vmax)
                else:
                    # No fit; if dry_run, preview only
                    if intent.dry_run:
                        pv = {
                            "note": "approx_preview_no_fit",
                            "target_display": target_display,
                            "value_range": [vmin, vmax],
                        }
                        return {"ok": True, "preview": pv}
                    # Try a bounded bisection using live readbacks
                    # Probe ends for direction
                    try:
                        # Set to min
                        request_op("set_return_device_param", timeout=1.0, return_index=ri, device_index=di, param_index=int(sel.get("index", 0)), value=float(vmin))
                        rb0 = request_op("get_return_device_params", timeout=1.0, return_index=ri, device_index=di)
                        p0s = ((rb0 or {}).get("data") or {}).get("params") or []
                        p0 = next((p for p in p0s if int(p.get("index", -1)) == int(sel.get("index", 0))), None)
                        d0 = _parse_target_display(str((p0 or {}).get("display_value", "")))
                        # Set to max
                        request_op("set_return_device_param", timeout=1.0, return_index=ri, device_index=di, param_index=int(sel.get("index", 0)), value=float(vmax))
                        rb1 = request_op("get_return_device_params", timeout=1.0, return_index=ri, device_index=di)
                        p1s = ((rb1 or {}).get("data") or {}).get("params") or []
                        p1 = next((p for p in p1s if int(p.get("index", -1)) == int(sel.get("index", 0))), None)
                        d1 = _parse_target_display(str((p1 or {}).get("display_value", "")))
                        # Align target numeric to readback display units if needed
                        target = float(ty)
                        try:
                            rb_unit = _detect_display_unit(str((p1 or {}).get("display_value", ""))) or _detect_display_unit(str((p0 or {}).get("display_value", "")))
                            if rb_unit:
                                target = _convert_unit_value(target, unit_lc or rb_unit, rb_unit)
                        except Exception:
                            pass
                        if d0 is not None and d1 is not None:
                            lo = vmin; hi = vmax
                            # Ensure bounds order based on monotonicity
                            inc = d1 > d0
                            for _ in range(8):
                                mid = (lo + hi) / 2.0
                                request_op("set_return_device_param", timeout=1.0, return_index=ri, device_index=di, param_index=int(sel.get("index", 0)), value=float(mid))
                                rbm = request_op("get_return_device_params", timeout=1.0, return_index=ri, device_index=di)
                                pms = ((rbm or {}).get("data") or {}).get("params") or []
                                pmid = next((p for p in pms if int(p.get("index", -1)) == int(sel.get("index", 0))), None)
                                dmid = _parse_target_display(str((pmid or {}).get("display_value", "")))
                                if dmid is None:
                                    break
                                err = abs(dmid - target)
                                thresh = 0.02 * (abs(target) if target != 0 else 1.0)
                                if err <= thresh:
                                    x = mid
                                    break
                                if (dmid < target and inc) or (dmid > target and not inc):
                                    lo = mid
                                else:
                                    hi = mid
                            else:
                                x = (lo + hi) / 2.0
                    except Exception:
                        pass
        # Basic unit handling for device when numeric value passed: if mapping exists and unit is display-like, use fit; else percent scales within [vmin,vmax]
        if not used_display and unit_lc in ("percent", "%", "ms", "s", "hz", "khz", "degrees"):
            if pm and isinstance(pm.get("fit"), dict) and unit_lc not in ("percent", "%"):
                pm_unit = (pm.get("unit") or "").strip().lower()
                ty2 = _convert_unit_value(float(x), unit_lc, pm_unit)
                x = _invert_fit_to_value(pm.get("fit") or {}, float(ty2), vmin, vmax)
            elif unit_lc in ("percent", "%"):
                x = vmin + (vmax - vmin) * _clamp(x, 0.0, 100.0) / 100.0
        # Optional dependency enable (mapping only)
        # First check requires_for_effect (complex multi-condition dependencies)
        prereq_changes = []
        if intent.auto_enable_master is None or intent.auto_enable_master:
            prereq_changes = _check_requires_for_effect(mapping, params, str(sel.get("name", "")))

        # Then check simple master toggle dependency
        master_toggle = _master_from_mapping(mapping, params, str(sel.get("name", "")))
        if master_toggle is not None and (intent.auto_enable_master is None or intent.auto_enable_master):
            # Check if already in prereq_changes to avoid duplicates
            master_idx = int(master_toggle.get("index", 0))
            if not any(int(pc["param_dict"].get("index", -1)) == master_idx for pc in prereq_changes):
                prereq_changes.append({
                    "param_dict": master_toggle,
                    "target_value": float(master_toggle.get("max", 1.0)),
                    "note": "auto_enable_master"
                })

        preview: Dict[str, Any] = {"op": "set_return_device_param", "return_index": ri, "device_index": di, "param_index": int(sel.get("index", 0)), "value": float(_clamp(x, vmin, vmax) if intent.clamp else x)}

        # Add prereqs to preview
        if prereq_changes:
            preview["prereqs"] = [
                {
                    "op": "set_return_device_param",
                    "return_index": ri,
                    "device_index": di,
                    "param_index": int(pc["param_dict"].get("index", 0)),
                    "param_name": pc["param_dict"].get("name"),
                    "value": float(pc["target_value"]),
                    "note": pc["note"]
                }
                for pc in prereq_changes
            ]

        if intent.dry_run:
            return {"ok": True, "preview": preview}

        # Apply all prereq changes in order
        for prereq in prereq_changes:
            pd = prereq["param_dict"]
            request_op("set_return_device_param", timeout=1.0,
                      return_index=ri, device_index=di,
                      param_index=int(pd.get("index", 0)),
                      value=float(prereq["target_value"]))

        # Capture old value before change
        old_val = float(sel.get("value", 0.0))

        resp = request_op("set_return_device_param", timeout=1.0, return_index=ri, device_index=di, param_index=int(sel.get("index", 0)), value=float(preview["value"]))
        if not resp:
            raise HTTPException(504, "no_reply")

        # Read back new display value and generate rich summary
        try:
            readback = request_op("get_return_device_params", timeout=1.0, return_index=ri, device_index=di)
            rb_params = ((readback or {}).get("data") or {}).get("params") or []
            updated_param = next((p for p in rb_params if int(p.get("index", -1)) == int(sel.get("index", 0))), None)
            if updated_param:
                new_display = updated_param.get("display_value") or str(preview["value"])
                new_val = float(updated_param.get("value", preview["value"]))

                # Get device name
                devs = request_op("get_return_devices", timeout=0.8, return_index=ri)
                devices = ((devs or {}).get("data") or {}).get("devices") or []
                dname = next((str(d.get("name", "")) for d in devices if int(d.get("index", -1)) == di), f"Device {di}")

                # Generate summary with sonic context
                return_letter = chr(ord('A') + ri)
                summary = _generate_device_param_summary(
                    param_name=str(sel.get("name", "")),
                    param_meta=pm,
                    old_value=old_val,
                    new_value=new_val,
                    new_display=new_display,
                    device_name=dname,
                    return_ref=return_letter,
                    old_display=str(sel.get("display_value")) if sel.get("display_value") is not None else None
                )

                # Add summary to response
                if isinstance(resp, dict):
                    resp["summary"] = summary
                else:
                    resp = {"ok": True, "summary": summary}
        except Exception:
            # If summary generation fails, fall back to basic response
            pass

        # Attach return device capabilities so UI can render grouped cards
        if not intent.dry_run:
            try:
                from server.api.returns import get_return_device_capabilities
                caps = get_return_device_capabilities(index=ri, device=di)
                if isinstance(caps, dict) and caps.get("ok"):
                    if isinstance(resp, dict):
                        resp.setdefault("data", {})
                        resp["data"]["capabilities"] = caps.get("data")
            except Exception:
                pass

        return resp

    # Device parameter (track device)
    if d == "device" and intent.track_index is not None and intent.device_index is not None:
        ti = int(intent.track_index)
        di = int(intent.device_index)
        # If hints provided, try to resolve index by name and/or ordinal for track devices
        if intent.device_name_hint or intent.device_ordinal_hint:
            try:
                devs_list = request_op("get_track_devices", timeout=1.0, track_index=ti) or {}
                devs = ((devs_list.get("data") or devs_list) if isinstance(devs_list, dict) else devs_list).get("devices", [])
                matches = []
                if intent.device_name_hint:
                    hint = str(intent.device_name_hint).strip().lower()
                    hint_nos = hint.replace(" ", "")
                    for d in devs:
                        nm = str(d.get("name", ""))
                        nml = nm.strip().lower()
                        if nml == hint or nml.replace(" ", "") == hint_nos or (hint in nml) or (hint_nos in nml.replace(" ", "")):
                            matches.append(int(d.get("index", 0)))
                else:
                    matches = [int(d.get("index", 0)) for d in devs]
                matches = sorted(set(matches))
                ord_hint = int(intent.device_ordinal_hint) if intent.device_ordinal_hint else None
                if matches:
                    if ord_hint:
                        if 1 <= ord_hint <= len(matches):
                            di = matches[ord_hint - 1]
                        else:
                            # Prefer exact name match if available, ignore invalid ordinal
                            try:
                                hint_raw = str(intent.device_name_hint or "").strip().lower()
                                exact = next((int(d.get('index', 0)) for d in devs if str(d.get('name','')).strip().lower() == hint_raw), None)
                            except Exception:
                                exact = None
                            if exact is not None:
                                di = exact
                            else:
                                choices = ", ".join([f"{int(d.get('index',0))}:{str(d.get('name',''))}" for d in devs])
                                raise HTTPException(404, f"device_ordinal_out_of_range:{ord_hint}; matches={len(matches)}; devices=[{choices}]")
                    else:
                        di = matches[0]
                else:
                    choices = ", ".join([f"{int(d.get('index',0))}:{str(d.get('name',''))}" for d in devs])
                    raise HTTPException(404, f"device_not_found_for_hint:{intent.device_name_hint}; devices=[{choices}]")
            except HTTPException:
                raise
            except Exception:
                pass
        # Resolve device index using resolver when hints are present
        try:
            if intent.device_name_hint or intent.device_ordinal_hint:
                resolver = get_device_resolver()
                di_res, _dname, _notes = resolver.resolve_track(
                    track_index=ti,
                    device_name_hint=intent.device_name_hint,
                    device_ordinal_hint=intent.device_ordinal_hint,
                )
                di = int(di_res)
        except Exception:
            pass
        pr = request_op("get_track_device_params", timeout=1.2, track_index=ti, device_index=di)
        params = ((pr or {}).get("data") or {}).get("params") or []
        if not params:
            raise HTTPException(404, "params_not_found")
        pref = _alias_param_name_if_needed(intent.param_ref)
        sel = _resolve_param(params, intent.param_index, pref)
        vmin = float(sel.get("min", 0.0)); vmax = float(sel.get("max", 1.0))
        x = float(intent.value if intent.value is not None else vmin)
        used_display = False
        unit_norm_td = _normalize_unit(intent.unit)
        target_display = intent.display if intent.display is not None else (str(intent.value) if unit_norm_td == "display" and intent.value is not None else None)
        if target_display is None and unit_norm_td in ("ms", "s", "hz", "khz", "db", "%", "percent", "degrees", "on", "off") and intent.value is not None:
            target_display = str(intent.value)
        if target_display is not None:
            used_display = True
            # Mapping for track devices is not yet persisted; attempt readback refine only
            if intent.dry_run:
                return {"ok": True, "preview": {"note": "approx_preview_no_fit", "target_display": target_display, "value_range": [vmin, vmax]}}
            try:
                # Probe ends
                request_op("set_device_param", timeout=1.0, track_index=ti, device_index=di, param_index=int(sel.get("index", 0)), value=float(vmin))
                rb0 = request_op("get_track_device_params", timeout=1.0, track_index=ti, device_index=di)
                p0s = ((rb0 or {}).get("data") or {}).get("params") or []
                p0 = next((p for p in p0s if int(p.get("index", -1)) == int(sel.get("index", 0))), None)
                d0 = _parse_target_display(str((p0 or {}).get("display_value", "")))
                request_op("set_device_param", timeout=1.0, track_index=ti, device_index=di, param_index=int(sel.get("index", 0)), value=float(vmax))
                rb1 = request_op("get_track_device_params", timeout=1.0, track_index=ti, device_index=di)
                p1s = ((rb1 or {}).get("data") or {}).get("params") or []
                p1 = next((p for p in p1s if int(p.get("index", -1)) == int(sel.get("index", 0))), None)
                d1 = _parse_target_display(str((p1 or {}).get("display_value", "")))
                ty = _parse_target_display(target_display)
                # Align target to readback unit if detectable
                target = float(ty) if ty is not None else None
                try:
                    if target is not None:
                        rb_unit = _detect_display_unit(str((p1 or {}).get("display_value", ""))) or _detect_display_unit(str((p0 or {}).get("display_value", "")))
                        if rb_unit:
                            unit_lc_td = _normalize_unit(intent.unit)
                            target = _convert_unit_value(float(target), unit_lc_td or rb_unit, rb_unit)
                except Exception:
                    pass
                if d0 is not None and d1 is not None and target is not None:
                    lo = vmin; hi = vmax; inc = d1 > d0
                    for _ in range(8):
                        mid = (lo + hi) / 2.0
                        request_op("set_device_param", timeout=1.0, track_index=ti, device_index=di, param_index=int(sel.get("index", 0)), value=float(mid))
                        rbm = request_op("get_track_device_params", timeout=1.0, track_index=ti, device_index=di)
                        pms = ((rbm or {}).get("data") or {}).get("params") or []
                        pmid = next((p for p in pms if int(p.get("index", -1)) == int(sel.get("index", 0))), None)
                        dmid = _parse_target_display(str((pmid or {}).get("display_value", "")))
                        if dmid is None:
                            break
                        err = abs(dmid - float(target))
                        thresh = 0.02 * (abs(target) if target != 0 else 1.0)
                        if err <= thresh:
                            x = mid
                            break
                        if (dmid < float(target) and inc) or (dmid > float(target) and not inc):
                            lo = mid
                        else:
                            hi = mid
                    else:
                        x = (lo + hi) / 2.0
            except Exception:
                pass
        if not used_display and (_normalize_unit(intent.unit) or "") in ("percent", "%"):
            x = vmin + (vmax - vmin) * _clamp(x, 0.0, 100.0) / 100.0
        # Mapping-only policy: do not auto-enable for track devices (no mapping source yet)
        preview = {"op": "set_device_param", "track_index": ti, "device_index": di, "param_index": int(sel.get("index", 0)), "value": float(_clamp(x, vmin, vmax) if intent.clamp else x)}
        if intent.dry_run:
            return {"ok": True, "preview": preview}
        resp = request_op("set_device_param", timeout=1.0, track_index=ti, device_index=di, param_index=int(sel.get("index", 0)), value=float(preview["value"]))
        if not resp:
            raise HTTPException(504, "no_reply")
        return resp

    raise HTTPException(400, "unsupported_intent")


@router.post("/intent/read")
def read_intent(intent: ReadIntent) -> Dict[str, Any]:
    d = intent.domain
    features = get_feature_flags()
    display_only_io = bool((features or {}).get("display_only_io", False))
    if d == "track" and intent.track_index is not None and intent.field == "routing":
        ti = int(intent.track_index)
        cur = request_op("get_track_routing", timeout=1.0, track_index=ti)
        if not cur:
            raise HTTPException(504, "no_reply")
        return {"ok": True, "data": (cur.get("data") or cur)}
    if d == "return" and (intent.return_index is not None or intent.return_ref is not None) and intent.field == "routing":
        ri = _letter_to_index(intent.return_ref) if intent.return_ref is not None else int(intent.return_index)  # 0-based
        cur = request_op("get_return_routing", timeout=1.0, return_index=ri)
        if not cur:
            raise HTTPException(504, "no_reply")
        data = (cur.get("data") or cur)
        # Attach sends_capable signal using a quick probe
        try:
            s = request_op("get_return_sends", timeout=1.0, return_index=ri) or {}
            sdata = (s.get("data") or s) if isinstance(s, dict) else {}
            sends = (sdata or {}).get("sends") or []
            data["sends_capable"] = bool(sends)
        except Exception:
            data["sends_capable"] = False
        return {"ok": True, "data": data}
    # Track mixer fields
    if d == "track" and intent.track_index is not None and intent.field in ("volume", "pan", "mute", "solo"):
        ti = int(intent.track_index)
        st = request_op("get_track_status", timeout=1.0, track_index=ti)
        data = (st or {}).get("data") or st or {}
        mix = data.get("mixer") or {}
        field = str(intent.field)
        # Track mute/solo are top-level in get_track_status result
        if field in ("mute", "solo"):
            raw = data.get(field)
            norm = 1.0 if bool(raw) else 0.0 if raw is not None else None
            disp = "On" if norm == 1.0 else ("Off" if norm == 0.0 else None)
            out = {"ok": True, "field": field, "display_value": disp}
            if not display_only_io:
                out["normalized_value"] = norm
            return out
        raw = mix.get(field)
        # Volume display in dB
        if field == "volume":
            from server.volume_utils import live_float_to_db
            disp = None
            if raw is not None:
                try:
                    dbv = live_float_to_db(float(raw))
                    disp = f"{dbv:.1f} dB"
                except Exception:
                    disp = None
            out = {"ok": True, "field": field, "display_value": disp}
            if not display_only_io:
                out["normalized_value"] = raw
            return out
        # Pan normalize to 0..1 and display as L/R/C
        if field == "pan":
            pan_raw = float(raw) if raw is not None else None
            disp = None
            norm = None
            if pan_raw is not None:
                # Convert from [-1,1] to [0,1]
                norm = (pan_raw + 1.0) / 2.0
                if abs(pan_raw) < 0.01:
                    disp = "C"
                else:
                    # Use -50..+50 display scale for pan
                    amt = int(round(abs(pan_raw) * 50))
                    disp = f"{amt}{'R' if pan_raw > 0 else 'L'}"
            out = {"ok": True, "field": field, "display_value": disp}
            if not display_only_io:
                out["normalized_value"] = norm
            return out
        # Fallback
        out = {"ok": True, "field": field, "display_value": None}
        if not display_only_io:
            out["normalized_value"] = raw
        return out
    # Track send
    if d == "track" and intent.track_index is not None and intent.field == "send":
        ti = int(intent.track_index)
        # Support send_ref (A/B/C...) or send_index; fallback to param_index for compatibility
        if intent.send_ref is not None:
            si = _letter_to_index(str(intent.send_ref))
        elif intent.send_index is not None:
            si = int(intent.send_index)
        elif intent.param_index is not None:
            si = int(intent.param_index)
        else:
            raise HTTPException(400, "send_index_or_send_ref_required")
        rs = request_op("get_track_sends", timeout=1.0, track_index=ti)
        data = (rs or {}).get("data") or rs or {}
        sends = data.get("sends") or []
        send = next((s for s in sends if int(s.get("index", -1)) == si), None)
        raw = (send or {}).get("value")
        disp = (send or {}).get("display_value")
        if disp is None and raw is not None:
            try:
                from server.volume_utils import live_float_to_db_send
                disp = f"{live_float_to_db_send(float(raw)):.1f} dB"
            except Exception:
                disp = None
        out = {"ok": True, "field": "send", "send_index": si, "display_value": disp}
        if not display_only_io:
            out["normalized_value"] = raw
        return out
    # Return mixer fields
    if d == "return" and (intent.return_index is not None or intent.return_ref is not None) and intent.field in ("volume", "pan", "mute", "solo"):
        ri = _letter_to_index(intent.return_ref) if intent.return_ref is not None else int(intent.return_index)
        rs = request_op("get_return_tracks", timeout=1.0)
        data = (rs or {}).get("data") or rs or {}
        rets = data.get("returns") or []
        ret = next((r for r in rets if int(r.get("index", -1)) == ri), None)
        mix = (ret or {}).get("mixer") or {}
        field = str(intent.field)
        raw = mix.get(field)
        # Volume dB formatting
        if field == "volume":
            from server.volume_utils import live_float_to_db
            disp = None
            if raw is not None:
                try:
                    dbv = live_float_to_db(float(raw))
                    disp = f"{dbv:.1f} dB"
                except Exception:
                    disp = None
            out = {"ok": True, "field": field, "display_value": disp}
            if not display_only_io:
                out["normalized_value"] = raw
            return out
        if field == "pan":
            pan_raw = float(raw) if raw is not None else None
            disp = None
            norm = None
            if pan_raw is not None:
                norm = (pan_raw + 1.0) / 2.0
                if abs(pan_raw) < 0.01:
                    disp = "C"
                else:
                    # Use -50..+50 display scale for pan
                    amt = int(round(abs(pan_raw) * 50))
                    disp = f"{amt}{'R' if pan_raw > 0 else 'L'}"
            out = {"ok": True, "field": field, "display_value": disp}
            if not display_only_io:
                out["normalized_value"] = norm
            return out
        if field in ("mute", "solo"):
            norm = 1.0 if bool(raw) else 0.0 if raw is not None else None
            disp = "On" if norm == 1.0 else ("Off" if norm == 0.0 else None)
            out = {"ok": True, "field": field, "display_value": disp}
            if not display_only_io:
                out["normalized_value"] = norm
            return out
        out = {"ok": True, "field": field, "display_value": None}
        if not display_only_io:
            out["normalized_value"] = raw
        return out
    # Return send
    if d == "return" and (intent.return_index is not None or intent.return_ref is not None) and intent.field == "send":
        ri = _letter_to_index(intent.return_ref) if intent.return_ref is not None else int(intent.return_index)
        if intent.send_ref is not None:
            si = _letter_to_index(str(intent.send_ref))
        elif intent.send_index is not None:
            si = int(intent.send_index)
        elif intent.param_index is not None:
            si = int(intent.param_index)
        else:
            raise HTTPException(400, "send_index_or_send_ref_required")
        rs = request_op("get_return_sends", timeout=1.0, return_index=ri)
        data = (rs or {}).get("data") or rs or {}
        sends = data.get("sends") or []
        send = next((s for s in sends if int(s.get("index", -1)) == si), None)
        raw = (send or {}).get("value")
        disp = (send or {}).get("display_value")
        if disp is None and raw is not None:
            try:
                from server.volume_utils import live_float_to_db_send
                disp = f"{live_float_to_db_send(float(raw)):.1f} dB"
            except Exception:
                disp = None
        out = {"ok": True, "field": "send", "send_index": si, "display_value": disp}
        if not display_only_io:
            out["normalized_value"] = raw
        return out
    # Master mixer
    if d == "master" and intent.field in ("volume", "pan"):
        ms = request_op("get_master_status", timeout=1.0)
        data = (ms or {}).get("data") or ms or {}
        mix = data.get("mixer") or {}
        field = str(intent.field)
        raw = mix.get(field)
        if field == "volume":
            from server.volume_utils import live_float_to_db
            disp = None
            if raw is not None:
                try:
                    dbv = live_float_to_db(float(raw))
                    disp = f"{dbv:.1f} dB"
                except Exception:
                    disp = None
            return {"ok": True, "field": field, "normalized_value": raw, "display_value": disp}
        if field == "pan":
            pan_raw = float(raw) if raw is not None else None
            norm = None
            disp = None
            if pan_raw is not None:
                norm = (pan_raw + 1.0) / 2.0
                if abs(pan_raw) < 0.01:
                    disp = "C"
                else:
                    # Use -50..+50 display scale for pan
                    amt = int(round(abs(pan_raw) * 50))
                    disp = f"{amt}{'R' if pan_raw > 0 else 'L'}"
            return {"ok": True, "field": field, "normalized_value": norm, "display_value": disp}
        return {"ok": True, "field": field, "normalized_value": raw, "display_value": None}
    # Device parameter (return device)
    if d == "device" and (intent.return_index is not None or intent.return_ref is not None) and intent.device_index is not None:
        ri = _resolve_return_index(intent)
        di = int(intent.device_index)
        pr = request_op("get_return_device_params", timeout=1.2, return_index=ri, device_index=di)
        params = ((pr or {}).get("data") or {}).get("params") or []
        if not params:
            raise HTTPException(404, "params_not_found")
        pref = _alias_param_name_if_needed(intent.param_ref)
        sel = _resolve_param(params, intent.param_index, pref)
        # Mapping meta
        store = get_store()
        devs = request_op("get_return_devices", timeout=1.0, return_index=ri)
        devices = ((devs or {}).get("data") or {}).get("devices") or []
        dname = next((str(dv.get("name", "")) for dv in devices if int(dv.get("index", -1)) == di), f"Device {di}")
        sig = make_device_signature(dname, params)
        mapping = None
        pm = None
        try:
            mapping = store.get_device_mapping(sig) if store.enabled else None
            if mapping:
                pm = next((pme for pme in (mapping.get("params_meta") or []) if str(pme.get("name", "")).lower() == str(sel.get("name", "")).lower()), None)
        except Exception:
            pm = None
        # Extract audio knowledge and label_map for richer responses
        audio_knowledge = None
        label_map = None
        min_display = None
        max_display = None
        if isinstance(pm, dict):
            audio_knowledge = pm.get("audio_knowledge")
            label_map = pm.get("label_map")
            min_display = pm.get("min_display")
            max_display = pm.get("max_display")

        # Determine toggle hints for UI
        try:
            name_lc = str(sel.get("name", "")).strip().lower()
            vmin = float(sel.get("min", 0.0)); vmax = float(sel.get("max", 1.0)); curv = float(sel.get("value", 0.0))
            is_toggle = name_lc.endswith(" on") or (abs(vmin) <= 1e-6 and abs(vmax - 1.0) <= 1e-6)
            is_on = None
            if is_toggle:
                is_on = bool(curv >= (vmin + 0.5 * (vmax - vmin)))
        except Exception:
            is_toggle = False; is_on = None

        dev_out = {
            "ok": True,
            "unit": (pm.get("unit") if isinstance(pm, dict) else None),
            "min": sel.get("min"),
            "max": sel.get("max"),
            "display_value": sel.get("display_value"),
            "has_fit": bool(isinstance(pm, dict) and isinstance(pm.get("fit"), dict)),
            "has_label_map": bool(isinstance(pm, dict) and isinstance(pm.get("label_map"), dict)),
            "param_name": sel.get("name"),
            "param_index": sel.get("index"),
            "audio_knowledge": audio_knowledge,
            "label_map": label_map,
            "min_display": min_display,
            "max_display": max_display,
            "is_toggle": is_toggle,
            "is_on": is_on,
        }
        if not display_only_io:
            dev_out["normalized_value"] = sel.get("value")
        return dev_out
    # Device parameter (track device)
    if d == "device" and intent.track_index is not None and intent.device_index is not None:
        ti = int(intent.track_index)
        di = int(intent.device_index)
        pr = request_op("get_track_device_params", timeout=1.2, track_index=ti, device_index=di)
        params = ((pr or {}).get("data") or {}).get("params") or []
        if not params:
            raise HTTPException(404, "params_not_found")
        pref = _alias_param_name_if_needed(intent.param_ref)
        sel = _resolve_param(params, intent.param_index, pref)
        # Determine toggle hints for UI (track device)
        try:
            name_lc = str(sel.get("name", "")).strip().lower()
            vmin = float(sel.get("min", 0.0)); vmax = float(sel.get("max", 1.0)); curv = float(sel.get("value", 0.0))
            is_toggle = name_lc.endswith(" on") or (abs(vmin) <= 1e-6 and abs(vmax - 1.0) <= 1e-6)
            is_on = None
            if is_toggle:
                is_on = bool(curv >= (vmin + 0.5 * (vmax - vmin)))
        except Exception:
            is_toggle = False; is_on = None

        dev_out = {
            "ok": True,
            "unit": None,
            "min": sel.get("min"),
            "max": sel.get("max"),
            "display_value": sel.get("display_value"),
            "has_fit": False,
            "has_label_map": False,
            "param_name": sel.get("name"),
            "param_index": sel.get("index"),
            "is_toggle": is_toggle,
            "is_on": is_on,
        }
        if not display_only_io:
            dev_out["normalized_value"] = sel.get("value")
        return dev_out
    raise HTTPException(400, "unsupported_read")
_COMMON_PARAM_ALIASES = {
    # Generic device param aliases (lowercased)
    "mix": "dry/wet",
    "wet": "dry/wet",
    "dry": "dry/wet",
    "dry wet": "dry/wet",
    "dry / wet": "dry/wet",
    # Cut filters and shelves
    "lo cut": "low cut",
    "locut": "low cut",
    "lowcut": "low cut",
    "hi cut": "high cut",
    "hicut": "high cut",
    "highcut": "high cut",
    "lo shelf": "low shelf",
    "loshelf": "low shelf",
    "hi shelf": "hi shelf",
    "hishelf": "hi shelf",
    # Filter types and common abbreviations
    "low pass": "low cut",
    "low-pass": "low cut",
    "lpf": "low cut",
    "lp": "low cut",
    "high pass": "high cut",
    "high-pass": "high cut",
    "hpf": "high cut",
    "hp": "high cut",
    # Q / Bandwidth / Resonance family
    "bandwidth": "q",
    "bw": "q",
    "q factor": "q",
    "q-factor": "q",
    "res": "q",
    "resonance": "q",
    # Rate / Speed / Tempo-ish controls
    "speed": "rate",
    # Depth / Amount / Intensity family
    "intensity": "depth",
    "amt": "amount",
    # Feedback abbreviations
    "fbk": "feedback",
    "feed back": "feedback",
    "feedback amount": "feedback",
    "width": "stereo image",
    "stereo width": "stereo image",
    "image": "stereo image",
    "decay time": "decay",
    "pre delay": "predelay",
    "pre-delay": "predelay",
}

def _alias_param_name_if_needed(name: Optional[str]) -> Optional[str]:
    if not name:
        return name
    n = str(name).strip().lower()
    return _COMMON_PARAM_ALIASES.get(n, name)
