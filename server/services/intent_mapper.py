from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple
from server.config.app_config import get_mixer_param_aliases
from server.services.intents.utils.mixer import get_mixer_param_meta, apply_mixer_fit_forward

# Mixer field aliases (config-driven)
_MIXER_PARAM_ALIASES: Dict[str, str] = {}
try:
    _MIXER_PARAM_ALIASES = get_mixer_param_aliases() or {}
except Exception:
    _MIXER_PARAM_ALIASES = {}

def _normalize_mixer_param(name: str) -> str:
    n = (name or "").strip().lower()
    return _MIXER_PARAM_ALIASES.get(n, n)


def _parse_track_target(track_str: str) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
    """Parse track string and return (domain, target_fields).

    Returns:
        ("track", {"track_index": 1}) for "Track 1"
        ("return", {"return_ref": "A"}) for "Return A"
        ("master", {}) for "Master"
        (None, None) if invalid
    """
    if not track_str:
        return None, None

    try:
        s = str(track_str).strip()

        # Track N → domain "track", track_index
        if s.lower().startswith("track "):
            n = int(s.split()[1])
            return "track", {"track_index": n}

        # Return A/B/C → domain "return", return_ref
        if s.lower().startswith("return "):
            letter = s.split()[1].upper()
            return "return", {"return_ref": letter}

        # Master → domain "master"
        if s.lower() == "master":
            return "master", {}

        # Plain digit → assume track index
        if s.isdigit():
            return "track", {"track_index": int(s)}

        # Otherwise treat as track by index if it's a number
        try:
            idx = int(s)
            return "track", {"track_index": idx}
        except:
            pass

    except Exception:
        pass

    return None, None


def map_llm_to_canonical(llm_intent: Dict[str, Any]) -> Tuple[Optional[Dict[str, Any]], List[str]]:
    """Map the LLM intent JSON into a canonical intent dict.

    Returns (canonical_intent_dict | None, errors[])
    """
    errors: List[str] = []

    kind = (llm_intent or {}).get("intent")
    targets = (llm_intent or {}).get("targets") or []
    op = (llm_intent or {}).get("operation") or {}

    # Debug logging for relative changes
    if kind == "relative_change":
        print(f"[DEBUG] Processing relative_change: targets={targets}, op={op}")

    # Only map control intents here; questions/clarifications bubble up to caller
    if kind not in ("set_parameter", "relative_change"):
        errors.append(f"non_control_intent:{kind}")
        return None, errors

    target = targets[0] if targets else {}
    track_str = target.get("track")
    domain, target_fields = _parse_track_target(track_str)

    if not domain or target_fields is None:
        errors.append("missing_or_invalid_track")
        return None, errors

    param_raw = (target.get("parameter") or "")
    plugin = target.get("plugin")
    device_ordinal = target.get("device_ordinal")

    # Only normalize mixer params if there's NO plugin (device operations keep original parameter names)
    parameter = str(param_raw).lower() if plugin else _normalize_mixer_param(str(param_raw).lower())
    op_type = (op.get("type") or "").lower()
    value = op.get("value")
    unit = op.get("unit")

    # Handle relative changes: convert to absolute by reading current value
    if op_type == "relative":
        # Import here to avoid circular dependency
        from server.core.deps import get_value_registry

        try:
            print(f"[DEBUG] Starting relative change conversion for {parameter}")
            registry = get_value_registry()
            print(f"[DEBUG] Got registry: {registry}")
            mixer_data = registry.get_mixer()
            print(f"[DEBUG] Got mixer_data keys: {mixer_data.keys() if mixer_data else 'None'}")

            # Get current value from registry (both normalized and display)
            current_normalized = None
            current_display = None
            current_unit = None

            if domain == "track" and "track_index" in target_fields:
                idx = target_fields["track_index"]
                track_data = mixer_data.get("track", {}).get(idx, {})
                param_data = track_data.get(parameter, {})
                current_normalized = param_data.get("normalized")
                current_display = param_data.get("display")
                current_unit = param_data.get("unit")
                # If we have normalized but no display/unit, synthesize display for common params
                if current_display is None and current_normalized is not None:
                    try:
                        if parameter == "volume":
                            # Use power-law fit from Firestore
                            param_meta = get_mixer_param_meta("track", "volume")
                            if param_meta and param_meta.get("fit"):
                                current_display = apply_mixer_fit_forward(param_meta, current_normalized)
                                current_unit = "dB"
                        elif parameter == "pan":
                            from server.services.intents.utils.mixer import get_mixer_display_range
                            dmin, dmax = get_mixer_display_range("pan")
                            scale = max(abs(dmin), abs(dmax))
                            current_display = float(current_normalized) * scale
                            current_unit = "%"
                    except Exception:
                        pass
            elif domain == "return" and "return_ref" in target_fields:
                # Map return letter to index (A=0, B=1, etc.)
                letter = target_fields["return_ref"]
                idx = ord(letter.upper()) - ord('A')
                return_data = mixer_data.get("return", {}).get(idx, {})
                param_data = return_data.get(parameter, {})
                current_normalized = param_data.get("normalized")
                current_display = param_data.get("display")
                current_unit = param_data.get("unit")
            elif domain == "master":
                # Master track
                master_data = mixer_data.get("master", {})
                param_data = master_data.get(parameter, {})
                current_normalized = param_data.get("normalized")
                current_display = param_data.get("display")
                current_unit = param_data.get("unit")

            if current_normalized is None:
                # ValueRegistry doesn't have the value - fetch it from Live
                print(f"[DEBUG] No current value in registry for {domain} {target_fields} {parameter}, fetching from Live...")

                # Import utilities to fetch and convert current value from Live
                from server.services.ableton_client import request_op, data_or_raw
                from server.services.intents.utils.mixer import get_mixer_display_range

                try:
                    if domain == "track" and "track_index" in target_fields:
                        idx = target_fields["track_index"]
                        print(f"[DEBUG] Requesting track status for track_index={idx}")
                        resp = request_op("get_track_status", timeout=1.0, track_index=idx)
                        print(f"[DEBUG] Got response: {resp}")
                        if resp:
                            track_info = data_or_raw(resp)
                            print(f"[DEBUG] track_info: {track_info}")

                            if parameter == "volume":
                                current_normalized = track_info.get("mixer", {}).get("volume")
                                # Prefer direct dB if provided by bridge
                                vdb = track_info.get("volume_db")
                                if vdb is not None:
                                    current_display = float(vdb)
                                    current_unit = "dB"
                                elif current_normalized is not None:
                                    # Use power-law fit from Firestore
                                    try:
                                        param_meta = get_mixer_param_meta("track", "volume")
                                        if param_meta and param_meta.get("fit"):
                                            current_display = apply_mixer_fit_forward(param_meta, current_normalized)
                                            current_unit = "dB"
                                        else:
                                            current_display = None
                                            current_unit = None
                                    except Exception:
                                        current_display = None
                                        current_unit = None
                            elif parameter == "pan":
                                # Tracks use 'pan' key, not 'panning'
                                current_normalized = track_info.get("mixer", {}).get("pan")
                                if current_normalized is not None:
                                    display_min, display_max = get_mixer_display_range("pan")
                                    display_scale = max(abs(display_min), abs(display_max))
                                    current_display = current_normalized * display_scale
                                    current_unit = "%"
                            elif parameter.startswith("send "):
                                send_letter = parameter.split()[-1]
                                send_idx = ord(send_letter.upper()) - ord('A')
                                print(f"[DEBUG] Requesting track sends for track_index={idx}")
                                sresp = request_op("get_track_sends", timeout=1.0, track_index=idx)
                                print(f"[DEBUG] Got track_sends response: {sresp}")
                                if sresp:
                                    sends_obj = data_or_raw(sresp)
                                    sends = sends_obj.get("sends", []) if isinstance(sends_obj, dict) else []
                                    for s in sends:
                                        if int(s.get("index", -1)) == send_idx:
                                            current_normalized = s.get("value")
                                            current_display = s.get("display_value")
                                            current_unit = "dB" if current_display is not None else None
                                            break

                    elif domain == "return" and "return_ref" in target_fields:
                        letter = target_fields["return_ref"]
                        ret_idx = ord(letter.upper()) - ord('A')
                        if parameter == "volume" or parameter == "pan":
                            print(f"[DEBUG] Requesting return tracks, will use index {ret_idx} for return {letter}")
                            resp = request_op("get_return_tracks", timeout=1.0)
                            print(f"[DEBUG] Got return response: {resp}")
                            if resp:
                                returns_data = data_or_raw(resp)
                                returns = returns_data.get('returns', []) if isinstance(returns_data, dict) else []
                                if isinstance(returns, list) and ret_idx < len(returns):
                                    ret_info = returns[ret_idx]
                                    if parameter == "volume":
                                        current_normalized = ret_info.get("mixer", {}).get("volume")
                                    elif parameter == "pan":
                                        current_normalized = ret_info.get("mixer", {}).get("pan")
                                        if current_normalized is not None:
                                            display_min, display_max = get_mixer_display_range("pan")
                                            display_scale = max(abs(display_min), abs(display_max))
                                            current_display = current_normalized * display_scale
                                            current_unit = "%"
                        elif parameter.startswith("send "):
                            # Fetch return sends via dedicated endpoint
                            print(f"[DEBUG] Requesting return sends for return_index={ret_idx}")
                            rs = request_op("get_return_sends", timeout=1.0, return_index=ret_idx)
                            print(f"[DEBUG] Got return_sends response: {rs}")
                            if rs:
                                sends_obj = data_or_raw(rs)
                                sends = sends_obj.get("sends", []) if isinstance(sends_obj, dict) else []
                                send_letter = parameter.split()[-1]
                                send_idx = ord(send_letter.upper()) - ord('A')
                                for s in sends:
                                    if int(s.get("index", -1)) == send_idx:
                                        current_normalized = s.get("value")
                                        current_display = s.get("display_value")
                                        current_unit = "dB" if current_display is not None else None
                                        break

                    elif domain == "master":
                        resp = request_op("get_master_status", timeout=1.0)
                        if resp:
                            master_info = data_or_raw(resp)
                            if parameter == "volume":
                                current_normalized = master_info.get("mixer", {}).get("volume")
                                # Use power-law fit from Firestore
                                if current_normalized is not None:
                                    try:
                                        param_meta = get_mixer_param_meta("master", "volume")
                                        if param_meta and param_meta.get("fit"):
                                            current_display = apply_mixer_fit_forward(param_meta, current_normalized)
                                            current_unit = "dB"
                                        else:
                                            current_display = None
                                            current_unit = None
                                    except Exception:
                                        current_display = None
                                        current_unit = None
                            elif parameter == "pan":
                                current_normalized = master_info.get("mixer", {}).get("pan")
                                if current_normalized is not None:
                                    from server.services.intents.utils.mixer import get_mixer_display_range
                                    display_min, display_max = get_mixer_display_range("pan")
                                    display_scale = max(abs(display_min), abs(display_max))
                                    current_display = current_normalized * display_scale
                                    current_unit = "%"
                            elif parameter == "cue":
                                current_normalized = master_info.get("mixer", {}).get("cue")
                                if current_normalized is not None:
                                    # Use power-law fit from Firestore (cue uses same fit as volume)
                                    try:
                                        param_meta = get_mixer_param_meta("master", "cue")
                                        if param_meta and param_meta.get("fit"):
                                            current_display = apply_mixer_fit_forward(param_meta, current_normalized)
                                            current_unit = "dB"
                                        else:
                                            current_display = None
                                            current_unit = None
                                    except Exception:
                                        current_display = None
                                        current_unit = None

                    print(f"[DEBUG] Fetched from Live - normalized: {current_normalized}, display: {current_display}, unit: {current_unit}")

                except Exception as fetch_error:
                    print(f"[DEBUG] Failed to fetch from Live: {fetch_error}")
                    errors.append(f"relative_change_fetch_error:{str(fetch_error)}")
                    return None, errors

                # Still no value after fetching from Live
                if current_normalized is None:
                    print(f"[DEBUG] Value not available in Live either")
                    errors.append("relative_change_no_current_value")
                    return None, errors

            print(f"[DEBUG] Current values - normalized: {current_normalized}, display: {current_display}, unit: {current_unit}")

            # Decide semantics based on parameter and unit
            delta_value = float(value)
            unit_l = str(unit or "").strip().lower()

            # Handle percent relative using normalized path (does not require display)
            if parameter in ("volume", "cue") and unit_l in ("%", "percent"):
                # Percent relative for volume/cue: operate in DISPLAY (dB) space to avoid large jumps
                # Use current_display if available; else approximate from normalized
                base_db = None
                if current_display is not None and (current_unit or "").lower() in ("db",):
                    try:
                        base_db = float(current_display)
                    except Exception:
                        base_db = None
                if base_db is None and current_normalized is not None:
                    try:
                        # Use piecewise fit from Firestore for domain-specific volume/cue conversion
                        entity_type = domain if domain in ("track", "return", "master") else "track"
                        param_meta = get_mixer_param_meta(entity_type, parameter)
                        if param_meta and param_meta.get("fit"):
                            base_db = apply_mixer_fit_forward(param_meta, current_normalized)
                        else:
                            base_db = None
                    except Exception:
                        base_db = None
                if base_db is None:
                    errors.append("relative_change_no_display_value")
                    return None, errors
                # Change percent of current magnitude toward 0 dB
                new_display = base_db + (delta_value / 100.0) * (0.0 - base_db)
                value = new_display
                unit = None  # use fit in executor
                op_type = "absolute"
            elif parameter in ("volume", "cue") and unit_l in ("db", ""):
                # Relative change in dB for volume/cue
                if current_display is None and current_normalized is not None:
                    try:
                        # Use piecewise fit from Firestore
                        entity_type = domain if domain in ("track", "return", "master") else "track"
                        param_meta = get_mixer_param_meta(entity_type, parameter)
                        if param_meta and param_meta.get("fit"):
                            current_display = apply_mixer_fit_forward(param_meta, current_normalized)
                            current_unit = "dB"
                    except Exception:
                        pass
                if current_display is None:
                    errors.append("relative_change_no_display_value")
                    return None, errors
                # Simple dB arithmetic
                current_display_value = float(current_display)
                new_display = current_display_value + delta_value
                value = new_display
                unit = None  # let executor use fit
                op_type = "absolute"
            elif parameter.startswith("send ") and unit_l in ("%", "percent") and current_normalized is not None:
                # Percent relative for sends: operate in DISPLAY (dB) space like volume.
                # Emit value in display domain and leave unit unset so executor uses fit.
                try:
                    from server.volume_utils import live_float_to_db_send  # type: ignore
                    base_db = float(live_float_to_db_send(float(current_normalized)))
                    new_display = base_db + (delta_value / 100.0) * (0.0 - base_db)
                    value = new_display
                    unit = None
                    op_type = "absolute"
                except Exception:
                    # Fallback: use normalized math if conversion not available
                    new_normalized = max(0.0, min(1.0, float(current_normalized) + (delta_value / 100.0)))
                    # Convert normalized to a display-like percent for continuity
                    value = new_normalized * 100.0
                    unit = "%"
                    op_type = "absolute"
            elif parameter.startswith("send ") and unit_l in ("db",):
                # Relative change in dB for sends; ensure we have a display value
                if current_display is None and current_normalized is not None:
                    try:
                        from server.volume_utils import live_float_to_db_send  # type: ignore
                        current_display = float(live_float_to_db_send(float(current_normalized)))
                        current_unit = "dB"
                    except Exception:
                        pass
                if current_display is None:
                    errors.append("relative_change_no_display_value")
                    return None, errors
                # Simple dB arithmetic
                current_display_value = float(current_display)
                new_display = current_display_value + delta_value
                value = new_display
                unit = None  # let executor use fit
                op_type = "absolute"
            elif parameter.startswith("send ") and unit_l in ("", "display"):
                # No unit provided for relative send change: default to dB semantics
                try:
                    if current_display is None and current_normalized is not None:
                        from server.volume_utils import live_float_to_db_send  # type: ignore
                        current_display = float(live_float_to_db_send(float(current_normalized)))
                        current_unit = "dB"
                except Exception:
                    pass
                if current_display is None:
                    errors.append("relative_change_no_display_value")
                    return None, errors
                current_display_value = float(current_display)
                new_display = current_display_value + delta_value
                value = new_display
                unit = None  # let executor use fit
                op_type = "absolute"
            else:
                if current_display is None:
                    errors.append("relative_change_no_display_value")
                    return None, errors
                # Default: arithmetic in display space and adopt display's unit
                current_display_value = float(current_display)
                new_display = current_display_value + delta_value
                value = new_display
                # For volume, prefer fit-driven conversion; omit unit to avoid misrouting
                if parameter == "volume":
                    unit = None
                else:
                    unit = current_unit
                op_type = "absolute"

            print(f"[DEBUG] Converted relative to absolute: value={value}, unit={unit}, op_type={op_type}")

        except Exception as e:
            print(f"[DEBUG] Exception in relative change handling: {type(e).__name__}: {str(e)}")
            import traceback
            traceback.print_exc()
            errors.append(f"relative_change_error:{str(e)}")
            return None, errors

    # Validate operation type and value
    if op_type != "absolute":
        print(f"[DEBUG] Unsupported op_type: {op_type}")
        errors.append(f"unsupported_op_type:{op_type}")
        return None, errors

    print(f"[DEBUG] Validation passed, proceeding to parameter mapping")

    # For mixer/sends we require numeric; for device we allow display strings
    def _to_float(v: Any) -> Optional[float]:
        try:
            return float(v)
        except Exception:
            return None

    # Helper: detect send letter even when spacing/case is odd (e.g., "sendB", "Send   A")
    def _extract_send_letter(p: str) -> Optional[str]:
        try:
            import re as _re
            s = str(p or "").lower()
            m = _re.search(r"\bsend\s*([a-d])\b", s)
            if m:
                return m.group(1).upper()
            # Very conservative fallback: exact single letter A-D only, and only if plugin is empty/generic
            s_clean = s.strip()
            if s_clean in ("a","b","c","d"):
                return s_clean.upper()
        except Exception:
            pass
        return None

    # Mixer controls: volume, pan, mute, solo
    if parameter in ("volume", "pan", "mute", "solo"):
        amount = _to_float(value)
        print(f"[DEBUG] Mixer parameter {parameter}: amount={amount}, value={value}, unit={unit}")
        if amount is None:
            print(f"[DEBUG] Failed to convert value to float: {value}")
            errors.append("invalid_value_amount")
            return None, errors
        intent = {
            "domain": domain,
            "action": "set",
            "field": parameter,
            "value": amount,
            "unit": unit,
            **target_fields
        }
        print(f"[DEBUG] Returning mixer intent: {intent}")
        return intent, []

    # Master cue control (mixer): only valid on master
    if parameter == "cue":
        if domain != "master":
            errors.append("unsupported_parameter_for_domain:cue")
            return None, errors
        amount = _to_float(value)
        if amount is None:
            errors.append("invalid_value_amount")
            return None, errors
        intent = {
            "domain": "master",
            "action": "set",
            "field": "cue",
            "value": amount,
            "unit": unit,
        }
        return intent, []

    # Send controls: "send A", "send B", etc. (prefer this mapping even if a plugin is present)
    send_letter = None
    if parameter.startswith("send "):
        try:
            send_letter = parameter.split()[-1].upper()
        except Exception:
            send_letter = None
    if send_letter is None:
        send_letter = _extract_send_letter(param_raw)
    if (parameter in ("send", "sends")) and send_letter is None:
        # No letter specified; treat as error for now
        errors.append("send_letter_missing")
        return None, errors
    if send_letter is not None:
        amount = _to_float(value)
        if amount is None:
            errors.append("invalid_value_amount")
            return None, errors
        intent = {
            "domain": domain,
            "action": "set",
            "field": "send",
            "send_ref": send_letter,
            "value": amount,
            "unit": unit,
            **target_fields
        }
        return intent, []

    # Device parameters: if plugin is specified
    if plugin:
        # Device params support numeric and display label values
        intent: Dict[str, Any] = {
            "domain": "device",
            "action": "set",
            "param_ref": parameter,
            **target_fields
        }
        # Pass through device name as a hint unless it's a generic placeholder
        try:
            pl = str(plugin).strip().lower()
            if pl not in ("device", "fx", "effect", "plugin") and pl:
                intent["device_name_hint"] = str(plugin)
        except Exception:
            pass
        try:
            if device_ordinal is not None:
                intent["device_ordinal_hint"] = int(device_ordinal)
        except Exception:
            pass
        amount = _to_float(value)
        unit_l = (unit or "").strip().lower()
        if amount is not None:
            intent["value"] = amount
            if unit is not None:
                intent["unit"] = unit
        else:
            # Treat as display string selection (e.g., Mode → Distance)
            if isinstance(value, str):
                intent["display"] = value
                # Keep unit if explicitly marked as 'display', else omit
                if unit_l == "display":
                    intent["unit"] = unit
            else:
                errors.append("invalid_value_amount")
                return None, errors
        # Need device_index - for now use 0 (first device on track/return)
        intent["device_index"] = 0
        return intent, []

    errors.append(f"unsupported_parameter:{parameter}")
    return None, errors
