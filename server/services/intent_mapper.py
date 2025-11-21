from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple
from server.config.app_config import get_mixer_param_aliases, get_device_param_aliases
from server.services.intents.utils.mixer import get_mixer_param_meta, apply_mixer_fit_forward

# Mixer field aliases (config-driven)
_MIXER_PARAM_ALIASES: Dict[str, str] = {}
try:
    _MIXER_PARAM_ALIASES = get_mixer_param_aliases() or {}
except Exception:
    _MIXER_PARAM_ALIASES = {}

# Device parameter aliases (config-driven)
_DEVICE_PARAM_ALIASES: Dict[str, str] = {}
try:
    _DEVICE_PARAM_ALIASES = get_device_param_aliases() or {}
except Exception:
    _DEVICE_PARAM_ALIASES = {}

def _normalize_mixer_param(name: str) -> str:
    n = (name or "").strip().lower()
    return _MIXER_PARAM_ALIASES.get(n, n)


def _normalize_device_param(name: str) -> str:
    """Normalize device parameter name using aliases."""
    n = (name or "").strip().lower()
    return _DEVICE_PARAM_ALIASES.get(n, n)


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
    # Original utterance (if provided by NLP) for lightweight heuristics
    orig_utterance = str(((llm_intent or {}).get("meta") or {}).get("utterance") or "")

    # Debug logging for relative changes
    if kind == "relative_change":

    # Pass-through for transport intents (handled by chat_service and API directly)
    if kind == "transport":
        op = (llm_intent or {}).get("operation") or {}
        action = op.get("action")
        value = op.get("value")
        if not action:
            errors.append("missing_transport_action")
            return None, errors
        return {"domain": "transport", "action": str(action), "value": value}, []

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

    # Handle relative changes for MIXER parameters: convert to absolute by reading current value
    # Device parameters are handled later in their own section (line 517+)
    if op_type == "relative" and not (plugin or device_ordinal is not None):
        # Import here to avoid circular dependency
        from server.core.deps import get_value_registry

        try:
            registry = get_value_registry()
            mixer_data = registry.get_mixer()

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

                # Import utilities to fetch and convert current value from Live
                from server.services.ableton_client import request_op, data_or_raw
                from server.services.intents.utils.mixer import get_mixer_display_range

                try:
                    if domain == "track" and "track_index" in target_fields:
                        idx = target_fields["track_index"]
                        resp = request_op("get_track_status", timeout=1.0, track_index=idx)
                        if resp:
                            track_info = data_or_raw(resp)

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
                                sresp = request_op("get_track_sends", timeout=1.0, track_index=idx)
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
                            resp = request_op("get_return_tracks", timeout=1.0)
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
                            rs = request_op("get_return_sends", timeout=1.0, return_index=ret_idx)
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


                except Exception as fetch_error:
                    errors.append(f"relative_change_fetch_error:{str(fetch_error)}")
                    return None, errors

                # Still no value after fetching from Live
                if current_normalized is None:
                    errors.append("relative_change_no_current_value")
                    return None, errors


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
                unit = "dB"  # preserve dB unit so executor knows it's a display value, not normalized
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


        except Exception as e:
            import traceback
            traceback.print_exc()
            errors.append(f"relative_change_error:{str(e)}")
            return None, errors

    # Validate operation type and value (skip for device parameters - they handle their own conversion)
    if op_type != "absolute" and not (plugin or device_ordinal is not None):
        errors.append(f"unsupported_op_type:{op_type}")
        return None, errors


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
            m = _re.search(r"\bsend\s*([a-l])\b", s)
            if m:
                return m.group(1).upper()
            # Very conservative fallback: exact single letter A-D only, and only if plugin is empty/generic
            s_clean = s.strip()
            if s_clean in ("a","b","c","d"):
                return s_clean.upper()
        except Exception:
            pass
        return None

    # Device parameters: if plugin is specified OR device_ordinal is present
    # Check this FIRST, before mixer controls, to avoid routing device parameters to mixer
    if plugin or device_ordinal is not None:
        # For relative changes on device parameters, we need to fetch current value first
        if op_type == "relative":

            # Import read service to fetch current device parameter value
            from server.services.intents.read_service import read_intent as _read_intent_func
            from server.models.intents_api import ReadIntent

            try:
                # Normalize device parameter name using aliases
                normalized_param = _normalize_device_param(parameter)
                # Get lowercase version AFTER normalization for percent_additive check
                param_lower = normalized_param.lower()

                # Build read intent to fetch current value (resolve correct device index)
                read_payload = {
                    "domain": "device",
                    "param_ref": normalized_param,
                }

                # Resolve domain/index for resolver
                dev_domain = None
                dev_index: Optional[int] = None
                if "return_ref" in target_fields:
                    letter = target_fields["return_ref"]
                    ri = ord(letter.upper()) - ord('A')
                    read_payload["return_index"] = ri
                    dev_domain = "return"; dev_index = ri
                elif "track_index" in target_fields:
                    ti = int(target_fields["track_index"])  # type: ignore
                    read_payload["track_index"] = ti
                    dev_domain = "track"; dev_index = ti

                # Determine device_index using resolver when possible
                try:
                    if dev_domain and dev_index is not None:
                        from server.core.deps import get_device_resolver
                        resolver = get_device_resolver()
                        if dev_domain == "return":
                            di, _n, _notes = resolver.resolve_return(return_index=int(dev_index), device_name_hint=str(plugin or ""), device_ordinal_hint=int(device_ordinal) if device_ordinal else None)
                        else:
                            di, _n, _notes = resolver.resolve_track(track_index=int(dev_index), device_name_hint=str(plugin or ""), device_ordinal_hint=int(device_ordinal) if device_ordinal else None)
                        resolved_di = int(di)
                        # Verify the resolved device actually contains the target parameter; if not, scan others (no ordinal only)
                        try:
                            from server.services.ableton_client import request_op as _req
                            rb = _req("get_return_device_params" if dev_domain == "return" else "get_track_device_params", timeout=0.8, **({"return_index": int(dev_index), "device_index": resolved_di} if dev_domain == "return" else {"track_index": int(dev_index), "device_index": resolved_di}))
                            pms = ((rb or {}).get("data") or rb or {}).get("params") or []
                            has_param = any(str(p.get("name", "")).strip().lower() == param_lower or (param_lower in str(p.get("name", "")).strip().lower()) for p in pms)
                        except Exception:
                            has_param = False
                        if not has_param and device_ordinal is None:
                            # Scan devices to find one with the requested parameter
                            try:
                                # Get device list
                                if dev_domain == "return":
                                    dlr = _req("get_return_devices", timeout=0.8, return_index=int(dev_index)) or {}
                                    devs = ((dlr.get("data") or dlr) if isinstance(dlr, dict) else dlr).get("devices", [])
                                else:
                                    dlt = _req("get_track_devices", timeout=0.8, track_index=int(dev_index)) or {}
                                    devs = ((dlt.get("data") or dlt) if isinstance(dlt, dict) else dlt).get("devices", [])
                                for d in devs:
                                    try:
                                        cand_di = int(d.get("index", -1))
                                        rb2 = _req("get_return_device_params" if dev_domain == "return" else "get_track_device_params", timeout=0.8, **({"return_index": int(dev_index), "device_index": cand_di} if dev_domain == "return" else {"track_index": int(dev_index), "device_index": cand_di}))
                                        p2 = ((rb2 or {}).get("data") or rb2 or {}).get("params") or []
                                        if any(str(p.get("name", "")).strip().lower() == param_lower or (param_lower in str(p.get("name", "")).strip().lower()) for p in p2):
                                            resolved_di = cand_di
                                            break
                                    except Exception:
                                        continue
                            except Exception:
                                pass
                        read_payload["device_index"] = int(resolved_di)
                    elif device_ordinal is not None:
                        read_payload["device_index"] = int(device_ordinal) - 1
                    else:
                        read_payload["device_index"] = 0
                except Exception:
                    # Fallbacks
                    if device_ordinal is not None:
                        read_payload["device_index"] = int(device_ordinal) - 1
                    else:
                        read_payload["device_index"] = 0

                read_result = _read_intent_func(ReadIntent(**read_payload))

                if not read_result.get("ok"):
                    errors.append("relative_change_device_read_failed")
                    return None, errors

                current_normalized = read_result.get("normalized_value")
                current_display = read_result.get("display_value")

                if current_normalized is None:
                    errors.append("relative_change_device_no_current_value")
                    return None, errors


                # Apply relative change
                delta_value = float(value)
                unit_l = str(unit or "").strip().lower()

                # Get percent_always_additive config
                from server.config.app_config import get_percent_always_additive_config
                percent_additive_params = [p.lower() for p in get_percent_always_additive_config()]

                is_additive = (param_lower in percent_additive_params) or any(pa in param_lower for pa in percent_additive_params)

                # Check if this is a percent-based parameter (display value matches normalized * 100)
                # E.g., dry/wet: normalized=0.5, display=50% → IS percent parameter
                # E.g., predelay: normalized=0.77, display=60ms → NOT percent parameter
                is_percent_parameter = False
                # Force recognition for known percent parameters from config
                if param_lower in percent_additive_params:
                    is_percent_parameter = True
                elif current_display is not None:
                    try:
                        # Robust parse of display percent like "45%" or "45.0"
                        import re as _re
                        ds = str(current_display).strip()
                        m = _re.search(r"-?\d+(?:\.\d+)?", ds)
                        if m:
                            display_val = float(m.group(0))
                            expected_percent = float(current_normalized) * 100.0
                            # Allow 5% tolerance for floating point comparison
                            is_percent_parameter = abs(display_val - expected_percent) < 5.0 or ds.endswith('%')
                    except Exception:
                        pass

                # Handle percent units - work in DISPLAY space (0-100), not normalized space!
                if unit_l in ("%", "percent") and is_percent_parameter:
                    # This is a percent-based parameter (like dry/wet/feedback)
                    # Convert current normalized to display percent (0.5 → 50)
                    current_display_percent = float(current_normalized) * 100.0

                    # Check if this parameter uses additive math for percents
                    if is_additive:
                        # Additive: 50% + 20% = 70%
                        new_display_percent = current_display_percent + delta_value
                    else:
                        # Multiplicative: 50% + 20% = 50% * 1.20 = 60%
                        multiplier = 1.0 + (delta_value / 100.0)
                        new_display_percent = current_display_percent * multiplier

                    # Clamp to valid range (0-100)
                    new_display_percent = max(0.0, min(100.0, new_display_percent))
                    value = new_display_percent
                    unit = "percent"  # Keep as percent, let executor handle conversion

                else:
                    # For non-percent parameters (dB, Hz, ms, etc.)
                    # BUT check if the CHANGE is specified as a percent!
                    if current_display is None:
                        # Fall back to normalized arithmetic
                        new_normalized = float(current_normalized) + delta_value
                        new_normalized = max(0.0, min(1.0, new_normalized))
                        value = new_normalized
                        unit = "normalized"
                    else:
                        # Display value arithmetic
                        try:
                            current_display_val = float(current_display)
                            # Check if change is specified as percent of current value
                            # E.g., "decrease predelay by 20%" where predelay is in ms
                            unit_is_percent = unit_l in ("%", "percent")
                            # Heuristic: if NLP dropped the unit but utterance contains '%', treat as percent
                            if not unit_is_percent and orig_utterance and ("%" in orig_utterance) and abs(delta_value) <= 100.0:
                                unit_is_percent = True
                            if unit_is_percent:
                                # Calculate percentage of current value
                                # delta_value already has sign: +20 for increase, -20 for decrease
                                # E.g., 60ms with delta=-20: 60 * (1 + -20/100) = 60 * 0.8 = 48ms
                                multiplier = 1.0 + (delta_value / 100.0)
                                new_display = current_display_val * multiplier
                            else:
                                # Direct value change (e.g., "increase by 10ms")
                                # delta_value already has sign: +10 or -10
                                new_display = current_display_val + delta_value

                            value = new_display
                            # Keep original unit for display-space values
                        except Exception:
                            # Fall back to normalized
                            new_normalized = float(current_normalized) + delta_value
                            new_normalized = max(0.0, min(1.0, new_normalized))
                            value = new_normalized
                            unit = "normalized"


                # Update parameter to use normalized name (already set above)
                parameter = normalized_param

                # Mark as absolute so it passes validation below
                op_type = "absolute"

            except Exception as e:
                import traceback
                traceback.print_exc()
                errors.append(f"relative_change_device_error:{str(e)}")
                return None, errors

        # Device params support numeric and display label values
        intent: Dict[str, Any] = {
            "domain": "device",
            "action": "set",
            "param_ref": parameter,
        }

        # Convert target_fields to format expected by executor for device domain
        # Executor expects return_index (integer), but preserve return_ref for tests
        if "return_ref" in target_fields:
            letter = target_fields["return_ref"]
            intent["return_ref"] = letter  # Preserve for tests
            intent["return_index"] = ord(letter.upper()) - ord('A')
        elif "track_index" in target_fields:
            intent["track_index"] = target_fields["track_index"]
        # master domain doesn't need additional fields
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
            # Keep value numeric in canonical intent for tests; executor treats it as display unless 'normalized'
            intent["value"] = amount
            if unit_l:
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
        # Resolve device_index using shared resolver when possible
        try:
            dev_domain = "return" if ("return_index" in intent or "return_ref" in intent) else ("track" if "track_index" in intent else None)
            if dev_domain == "return":
                ri = intent.get("return_index") if intent.get("return_index") is not None else ord(str(intent.get("return_ref")).upper()) - ord('A')
                from server.core.deps import get_device_resolver
                di, _name, _notes = get_device_resolver().resolve_return(return_index=int(ri), device_name_hint=str(intent.get("device_name_hint", "")), device_ordinal_hint=int(device_ordinal) if device_ordinal else None)
                intent["device_index"] = int(di)
            elif dev_domain == "track":
                ti = int(intent.get("track_index"))
                from server.core.deps import get_device_resolver
                di, _name, _notes = get_device_resolver().resolve_track(track_index=ti, device_name_hint=str(intent.get("device_name_hint", "")), device_ordinal_hint=int(device_ordinal) if device_ordinal else None)
                intent["device_index"] = int(di)
            else:
                # Fallback to ordinal/0
                intent["device_index"] = int(device_ordinal) - 1 if device_ordinal is not None else 0
        except Exception:
            intent["device_index"] = int(device_ordinal) - 1 if device_ordinal is not None else 0
        return intent, []

    # Mixer controls: volume, pan, mute, solo (only if NOT a device parameter)
    # Check this AFTER device parameters to avoid routing device params with mixer-like names
    if parameter in ("volume", "pan", "mute", "solo"):
        amount = _to_float(value)
        if amount is None:
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

    # Send controls: "send A", "send B", etc.
    # Check this AFTER device parameters to avoid false matches when device_ordinal is present
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

    errors.append(f"unsupported_parameter:{parameter}")
    return None, errors
