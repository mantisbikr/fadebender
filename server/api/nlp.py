from __future__ import annotations

from typing import Any, Dict

import pathlib
import re
import sys

from fastapi import APIRouter, HTTPException

from server.models.requests import IntentParseBody
from server.services.ableton_client import request_op
from server.services.intent_mapper import map_llm_to_canonical


router = APIRouter()


@router.post("/intent/parse")
def intent_parse(body: IntentParseBody) -> Dict[str, Any]:
    """Parse NL text to canonical intent JSON (no execution).

    Preserves raw_intent for non-control intents (e.g., get_parameter) so
    NLP tests can validate structure even when ok=false. Adds optional
    'clarification' alongside raw_intent when disambiguation is possible.
    """
    # Import llm_daw dynamically from nlp-service (hyphen in folder name)
    nlp_dir = pathlib.Path(__file__).resolve().parent.parent.parent / "nlp-service"
    if nlp_dir.exists() and str(nlp_dir) not in sys.path:
        sys.path.insert(0, str(nlp_dir))
    try:
        from llm_daw import interpret_daw_command  # type: ignore
    except Exception as e:
        raise HTTPException(500, f"NLP module not available: {e}")

    # Lightweight pre-normalization for compact pan syntax (e.g., "25R"/"30L").
    text = str(body.text or "")
    m = re.search(r"\bpan\s+track\s+(\d+)\s+to\s+(-?\d+)\s*([LR])\b", text, flags=re.IGNORECASE)
    if m:
        idx = m.group(1)
        amt = m.group(2)
        side = m.group(3).upper()
        side_word = "left" if side == "L" else "right"
        text = re.sub(
            r"\bpan\s+track\s+\d+\s+to\s+-?\d+\s*[LR]\b",
            f"set track {idx} pan to {amt} {side_word}",
            text,
            flags=re.IGNORECASE,
        )

    raw_intent = interpret_daw_command(text, model_preference=body.model, strict=body.strict)

    # Post-process: Fix intent type for relative operations
    # Both regex and LLM parsers may return "set_parameter" for relative ops
    # But the correct intent should be "relative_change" when operation.type is "relative"
    if (raw_intent and
        raw_intent.get("intent") == "set_parameter" and
        raw_intent.get("operation", {}).get("type") == "relative"):
        raw_intent["intent"] = "relative_change"

    canonical, errors = map_llm_to_canonical(raw_intent)

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

