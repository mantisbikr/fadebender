from __future__ import annotations

from typing import Any, Dict

import os
import pathlib
import re
import sys

from fastapi import APIRouter, HTTPException

from server.models.requests import IntentParseBody
from server.services.ableton_client import request_op
from server.services.intent_mapper import map_llm_to_canonical


router = APIRouter()

# Check if layered parser should be used
USE_LAYERED = os.getenv("USE_LAYERED_PARSER", "").lower() in ("1", "true", "yes")

# Module-level cache for parse index (only needed for layered parser)
_PARSE_INDEX = None


def _get_parse_index() -> Dict[str, Any]:
    """Get or build the parse index for layered parser.

    Builds index from Live set if available, otherwise returns minimal index.
    Cached at module level for performance.
    """
    global _PARSE_INDEX

    if _PARSE_INDEX is not None:
        return _PARSE_INDEX

    try:
        from server.services.parse_index.parse_index_builder import ParseIndexBuilder

        # Try to build index from Live snapshot devices (returns only for now).
        try:
            # Snapshot endpoint is exposed by this same server.
            # We only need device names/types; ordinals default to 1.
            import requests

            snap_resp = requests.get("http://127.0.0.1:8722/snapshot", timeout=2.0)
            live_devices = []
            if snap_resp.ok:
                snapshot = snap_resp.json()
                devices_data = (snapshot.get("data") or {}).get("devices", {})
                returns_data = devices_data.get("returns", {})
                for _, ret_data in returns_data.items():
                    for dev in ret_data.get("devices", []):
                        live_devices.append(
                            {
                                "name": dev.get("name"),
                                "device_type": str(dev.get("device_type", "unknown")).lower(),
                                "ordinals": 1,
                            }
                        )
            builder = ParseIndexBuilder()
            _PARSE_INDEX = builder.build_from_live_set(live_devices)
            print(f"[LAYERED] Built parse index with {len(_PARSE_INDEX.get('devices_in_set', []))} devices from snapshot")
        except Exception as e:
            print(f"[LAYERED] Failed to build parse index from snapshot: {e}, using minimal index")
            _PARSE_INDEX = {
                "version": "pi-minimal",
                "devices_in_set": [],
                "params_by_device": {},
                "device_type_index": {},
                "param_to_device_types": {},
                "mixer_params": ["volume", "pan", "mute", "solo", "send a", "send b", "send c", "send d"],
                "typo_map": {},
            }
    except Exception as e:
        print(f"[LAYERED] Failed to initialize parse index: {e}")
        _PARSE_INDEX = {
            "version": "pi-minimal",
            "devices_in_set": [],
            "params_by_device": {},
            "device_type_index": {},
            "param_to_device_types": {},
            "mixer_params": ["volume", "pan", "mute", "solo", "send a", "send b", "send c", "send d"],
            "typo_map": {},
        }

    return _PARSE_INDEX


@router.post("/intent/parse")
def intent_parse(body: IntentParseBody) -> Dict[str, Any]:
    """Parse NL text to canonical intent JSON (no execution).

    Preserves raw_intent for non-control intents (e.g., get_parameter) so
    NLP tests can validate structure even when ok=false. Adds optional
    'clarification' alongside raw_intent when disambiguation is possible.
    """

    # Lightweight pre-normalization for compact pan syntax.
    text = str(body.text or "")

    # Pattern 1: "pan track N to VALUE L/R" → "set track N pan to +/-VALUE"
    m = re.search(r"\bpan\s+track\s+(\d+)\s+to\s+(-?\d+)\s*([LR])\b", text, flags=re.IGNORECASE)
    if m:
        idx = m.group(1)
        amt = m.group(2)
        side = m.group(3).upper()
        # Encode direction as sign: left = negative, right = positive
        signed_amt = f"-{amt}" if side == "L" else amt
        text = re.sub(
            r"\bpan\s+track\s+\d+\s+to\s+-?\d+\s*[LR]\b",
            f"set track {idx} pan to {signed_amt}",
            text,
            flags=re.IGNORECASE,
        )
    else:
        # Pattern 2: "pan track N to VALUE" (without L/R) → "set track N pan to VALUE"
        m2 = re.search(r"\bpan\s+track\s+(\d+)\s+to\s+(-?\d+)\b", text, flags=re.IGNORECASE)
        if m2:
            idx = m2.group(1)
            amt = m2.group(2)
            text = re.sub(
                r"\bpan\s+track\s+\d+\s+to\s+-?\d+\b",
                f"set track {idx} pan to {amt}",
                text,
                flags=re.IGNORECASE,
            )

    # Pattern 3: "pan master to VALUE [L/R]" → "set master pan to +/-VALUE"
    m3 = re.search(r"\bpan\s+master\s+to\s+(-?\d+)\s*([LR])?\b", text, flags=re.IGNORECASE)
    if m3:
        amt = m3.group(1)
        side = m3.group(2)
        if side:
            side = side.upper()
            signed_amt = f"-{amt}" if side == "L" else amt
            text = re.sub(
                r"\bpan\s+master\s+to\s+-?\d+\s*[LR]\b",
                f"set master pan to {signed_amt}",
                text,
                flags=re.IGNORECASE,
            )
        else:
            text = re.sub(
                r"\bpan\s+master\s+to\s+-?\d+\b",
                f"set master pan to {amt}",
                text,
                flags=re.IGNORECASE,
            )

    # Pattern 4: "pan return X to VALUE [L/R]" → "set return X pan to +/-VALUE"
    m4 = re.search(r"\bpan\s+return\s+([A-L])\s+to\s+(-?\d+)\s*([LR])?\b", text, flags=re.IGNORECASE)
    if m4:
        ret = m4.group(1).upper()
        amt = m4.group(2)
        side = m4.group(3)
        if side:
            side = side.upper()
            signed_amt = f"-{amt}" if side == "L" else amt
            text = re.sub(
                r"\bpan\s+return\s+[A-C]\s+to\s+-?\d+\s*[LR]\b",
                f"set return {ret} pan to {signed_amt}",
                text,
                flags=re.IGNORECASE,
            )
        else:
            text = re.sub(
                r"\bpan\s+return\s+[A-C]\s+to\s+-?\d+\b",
                f"set return {ret} pan to {amt}",
                text,
                flags=re.IGNORECASE,
            )

    raw_intent: Dict[str, Any] | None = None

    # Try layered parser first when enabled
    if USE_LAYERED:
        try:
            from server.services.nlp.intent_builder import parse_command_layered

            parse_index = _get_parse_index()
            layered_intent = parse_command_layered(text, parse_index)
            if layered_intent:
                raw_intent = layered_intent
                try:
                    intent_name = str(raw_intent.get("intent"))
                except Exception:
                    intent_name = "unknown"
                print(f"[LAYERED] Parsed intent via layered pipeline: {intent_name}")
            else:
                print("[LAYERED] No intent parsed by layered pipeline, falling back to llm_daw")
        except Exception as e:
            print(f"[LAYERED] Error in layered parser: {e}; falling back to llm_daw")

    # Fallback (or default) path: use old llm_daw parser
    if raw_intent is None:
        # Import llm_daw dynamically from nlp-service (hyphen in folder name)
        nlp_dir = pathlib.Path(__file__).resolve().parent.parent.parent / "nlp-service"
        if nlp_dir.exists() and str(nlp_dir) not in sys.path:
            sys.path.insert(0, str(nlp_dir))
        try:
            from llm_daw import interpret_daw_command  # type: ignore
        except Exception as e:
            raise HTTPException(500, f"NLP module not available: {e}")

        raw_intent = interpret_daw_command(text, model_preference=body.model, strict=body.strict)

    # Post-process: Fix intent type for relative operations
    # Both regex and LLM parsers may return "set_parameter" for relative ops
    # But the correct intent should be "relative_change" when operation.type is "relative"
    if (
        raw_intent
        and raw_intent.get("intent") == "set_parameter"
        and raw_intent.get("operation", {}).get("type") == "relative"
    ):
        raw_intent["intent"] = "relative_change"

    # Post-process: Pan absolute commands with explicit left/right.
    # Normalize "25% left/right" into signed values (-25 / +25) for mixer pan.
    try:
        if raw_intent and raw_intent.get("intent") == "set_parameter":
            op = raw_intent.get("operation") or {}
            targets = raw_intent.get("targets") or []
            if (
                op.get("type") == "absolute"
                and isinstance(op.get("value"), (int, float))
                and any(
                    (t.get("plugin") is None and str(t.get("parameter", "")).lower() == "pan")
                    for t in targets
                )
            ):
                tl = text.lower()
                val = float(op.get("value") or 0.0)
                if "left" in tl and val > 0:
                    op["value"] = -val
                    op["unit"] = None  # treat as display percent
                elif "right" in tl and val < 0:
                    op["value"] = -val
                    op["unit"] = None
                raw_intent["operation"] = op
    except Exception:
        pass

    # Normalize parameter names in raw_intent for consistency (lowercase)
    # This ensures tests and UI get consistent parameter names regardless of parser.
    # Do this BEFORE calling intent_mapper so it gets normalized input.
    # Applies to mixer params for set/relative/get; device params keep original casing.
    if raw_intent and raw_intent.get("intent") in (
        "set_parameter",
        "relative_change",
        "get_parameter",
    ):
        targets = raw_intent.get("targets", [])
        normalized_targets = []
        for target in targets:
            param_raw = target.get("parameter") or ""
            plugin = target.get("plugin")
            # Normalize parameter name (lowercase for mixer params, preserve for device params)
            normalized_param = str(param_raw).lower() if not plugin else param_raw
            normalized_target = {**target, "parameter": normalized_param}
            normalized_targets.append(normalized_target)
        raw_intent["targets"] = normalized_targets

    canonical, errors = map_llm_to_canonical(raw_intent)

    # For GET queries, intent_mapper returns normalized_intent in canonical (not None)
    # Use the normalized version for raw_intent to ensure parameter names are lowercase
    if canonical and any(str(e).startswith("non_control_intent:get_parameter") for e in (errors or [])):
        return {"ok": False, "errors": errors, "raw_intent": canonical}

    if canonical is None:
        # Navigation intents (open_capabilities, list_capabilities) are valid UI intents
        # They don't go to the remote script, but should return ok=True for the UI to handle
        if raw_intent and raw_intent.get("intent") in ("open_capabilities", "list_capabilities"):
            return {"ok": True, "intent": raw_intent, "raw_intent": raw_intent}

        # Preserve original LLM output for non-control intents
        if any(str(e).startswith("non_control_intent") for e in (errors or [])):
            return {"ok": False, "errors": errors, "raw_intent": raw_intent}

        # Attempt to provide clarifying choices, keep raw_intent intact
        try:
            ov = request_op("get_overview", timeout=1.0) or {}
            data = (ov.get("data") or ov) if isinstance(ov, dict) else ov
            tracks = data.get("tracks") or []
            rs = request_op("get_return_tracks", timeout=1.0) or {}
            rdata = (rs.get("data") or rs) if isinstance(rs, dict) else rs
            rets = rdata.get("returns") or []
            question = "Which track or return do you mean?"
            choices = {
                "tracks": [{"index": int(t.get("index", 0)), "name": t.get("name")} for t in tracks],
                "returns": [
                    {
                        "index": int(r.get("index", 0)),
                        "name": r.get("name"),
                        "letter": chr(ord("A") + int(r.get("index", 0))),
                    }
                    for r in rets
                ],
            }
            clar = {"intent": "clarification_needed", "question": question, "choices": choices, "context": body.context}
            return {"ok": False, "errors": errors, "raw_intent": raw_intent, "clarification": clar}
        except Exception:
            return {"ok": False, "errors": errors, "raw_intent": raw_intent}

    return {"ok": True, "intent": canonical, "raw_intent": raw_intent}
