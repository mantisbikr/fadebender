from __future__ import annotations

import json
import os
import pathlib
from typing import Any, Dict, Optional

try:  # optional dependency
    import vertexai  # type: ignore
    from vertexai.generative_models import GenerativeModel  # type: ignore
except Exception:  # pragma: no cover - vertex SDK is optional
    vertexai = None  # type: ignore
    GenerativeModel = None  # type: ignore

from server.services.mapping_store import MappingStore

_VERTEX_INITED = False


def vertex_init_once() -> None:
    global _VERTEX_INITED
    if _VERTEX_INITED or vertexai is None:
        return
    project = os.getenv("VERTEX_PROJECT") or os.getenv("GOOGLE_CLOUD_PROJECT")
    location = os.getenv("VERTEX_LOCATION") or "us-central1"
    if not project:
        return
    try:
        vertexai.init(project=project, location=location)  # type: ignore[union-attr]
        _VERTEX_INITED = True
    except Exception:
        _VERTEX_INITED = False


def json_lenient_parse(text: str) -> Optional[Dict[str, Any]]:
    import re as _r

    t = str(text or "")
    if not t:
        return None
    if t.strip().startswith("```"):
        parts = t.split("```")
        if len(parts) >= 3:
            t = parts[1] if parts[0].strip() == "" else parts[1]
    t = (
        t.replace("“", '"')
        .replace("”", '"')
        .replace("‟", '"')
        .replace("’", "'")
        .replace("‘", "'")
    )
    t = _r.sub(r",\s*(\}|\])", r"\1", t)
    try:
        import json as _json

        return _json.loads(t)
    except Exception:
        pass
    i, j = t.find("{"), t.rfind("}")
    if i >= 0 and j > i:
        s = t[i : j + 1]
        s = _r.sub(r",\s*(\}|\])", r"\1", s)
        try:
            import json as _json

            return _json.loads(s)
        except Exception:
            pass
    t2 = t
    if t2.count('"') < 2 and t2.count("'") >= 4:
        t2 = t2.replace("'", '"')
        t2 = _r.sub(r",\s*(\}|\])", r"\1", t2)
        try:
            import json as _json

            return _json.loads(t2)
        except Exception:
            return None
    return None


def preset_metadata_schema() -> Dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            "description": {
                "type": "object",
                "properties": {
                    "what": {"type": "string"},
                    "when": {"type": "array", "items": {"type": "string"}},
                    "why": {"type": "string"},
                },
                "required": ["what"],
                "additionalProperties": True,
            },
            "audio_engineering": {"type": "object"},
            "natural_language_controls": {"type": "object"},
            "warnings": {"type": "object"},
            "genre_tags": {"type": "array", "items": {"type": "string"}},
            "subcategory": {"type": "string"},
        },
        "additionalProperties": True,
    }


def _kb_excerpt(device_type: str) -> str:
    try:
        base = pathlib.Path(os.getcwd()) / "knowledge" / "audio-fundamentals"
        if device_type.lower() == "reverb":
            path = base / "deep_audio_engineering_reverb.md"
        elif device_type.lower() == "delay":
            path = base / "deep_audio_engineering_delay.md"
        else:
            path = None
        if path and path.exists():
            txt = path.read_text(encoding="utf-8", errors="ignore")
            return txt.strip().replace("\n", " ")[:600]
    except Exception:
        return ""
    return "This preset leverages time-domain processing and frequency-domain shaping to achieve the desired psychoacoustic perception in a mix."


def basic_metadata_fallback(device_name: str, device_type: str, parameter_values: Dict[str, float]) -> Dict[str, Any]:
    desc = {
        "what": f"{device_name} preset for {device_type}",
        "when": ["general purpose", "subtle ambience"],
        "why": "Automatically generated fallback without LLM.",
    }

    ae: Dict[str, Any] = {}
    if device_type == "reverb":
        decay = None
        for key in ("Decay", "Decay Time", "DecayTime"):
            if key in parameter_values:
                decay = float(parameter_values[key])
                break
        predelay = None
        for key in ("Predelay", "PreDelay", "Pre-Delay"):
            if key in parameter_values:
                predelay = float(parameter_values[key])
                break
        ae = {
            "space_type": "hall" if (decay or 0) >= 3.5 else "room",
            "decay_time": f"~{decay:.2f}s" if decay is not None else None,
            "predelay": f"~{predelay:.0f} ms" if predelay is not None else None,
            "frequency_character": "neutral",
            "stereo_width": "wide",
            "diffusion": "smooth",
            "use_cases": [
                {
                    "source": "vocal",
                    "context": "ballad",
                    "send_level": "15-25%",
                    "notes": "Fallback guidance",
                }
            ],
        }

    default_use_cases = [
        {
            "source": "lead vocal",
            "context": "ballad",
            "send_level": "15-25%",
            "send_level_rationale": "maintain intelligibility while adding space",
            "eq_prep": "HPF 100 Hz, gentle de-ess",
            "eq_rationale": "reduce mud and sibilance feeding the reverb",
            "notes": "consider a pre-delay of 20-40 ms to preserve consonants",
        },
        {
            "source": "electric guitar",
            "context": "solo",
            "send_level": "10-20%",
            "send_level_rationale": "share space without washing transients",
            "eq_prep": "HPF 120 Hz, tilt -1 dB @ 4 kHz",
            "eq_rationale": "avoid low-end buildup and harshness",
            "notes": "wider stereo helpful for size, beware mono collapse",
        },
        {
            "source": "synth pad",
            "context": "ambient",
            "send_level": "25-40%",
            "send_level_rationale": "embrace tail for texture",
            "eq_prep": "HPF 80 Hz",
            "eq_rationale": "protect low-end clarity",
            "notes": "increase diffusion for smoother tail",
        },
        {
            "source": "drums",
            "context": "room enhancement",
            "send_level": "5-12%",
            "send_level_rationale": "enhance room sense without blurring hits",
            "eq_prep": "HPF 150 Hz, notch 500 Hz",
            "eq_rationale": "control boxiness",
            "notes": "short decay <1.2s for punch",
        },
    ]

    kb_text = _kb_excerpt(device_type)

    return {
        "description": {
            **desc,
            "why": (desc.get("why") or "") + " " + kb_text,
        },
        "audio_engineering": {
            **ae,
            "use_cases": default_use_cases if device_type == "reverb" else default_use_cases[:4],
        },
        "natural_language_controls": {},
        "warnings": {},
        "genre_tags": [],
        "subcategory": ae.get("space_type") if isinstance(ae, dict) else "unknown",
    }


async def generate_preset_metadata_llm(
    device_name: str,
    device_type: str,
    parameter_values: Dict[str, float],
    *,
    store: Optional[MappingStore] = None,
) -> Dict[str, Any]:
    if GenerativeModel is None:
        return basic_metadata_fallback(device_name, device_type, parameter_values)

    import sys

    nlp_dir = pathlib.Path(__file__).resolve().parent.parent / "nlp-service"
    if nlp_dir.exists() and str(nlp_dir) not in sys.path:
        sys.path.insert(0, str(nlp_dir))

    try:
        from config.llm_config import get_default_model_name, get_llm_project_id  # type: ignore
    except Exception:
        return basic_metadata_fallback(device_name, device_type, parameter_values)

    try:
        project = get_llm_project_id()
        location = os.getenv("GCP_REGION", "us-central1")
        model_name = get_default_model_name()
        if vertexai is None or GenerativeModel is None:
            return basic_metadata_fallback(device_name, device_type, parameter_values)
        vertexai.init(project=project, location=location)  # type: ignore[union-attr]
    except Exception:
        pass

    vertex_init_once()

    kb_context = ""
    try:
        base = pathlib.Path(os.getcwd()) / "knowledge" / "audio-fundamentals"
        if device_type.lower() == "reverb":
            doc = base / "deep_audio_engineering_reverb.md"
        elif device_type.lower() == "delay":
            doc = base / "deep_audio_engineering_delay.md"
        else:
            doc = None
        if doc and doc.exists():
            kb_context = doc.read_text(encoding="utf-8", errors="ignore")[:20000]
    except Exception:
        kb_context = ""

    model_name = os.getenv("LLM_MODEL") or os.getenv("VERTEX_MODEL") or "gemini-2.5-flash"
    model = GenerativeModel(
        model_name,  # type: ignore[arg-type]
        system_instruction="You are an expert audio engineer. Respond with STRICT JSON only.",
    )
    params_json = json.dumps(parameter_values or {}, indent=2, ensure_ascii=False)

    template_override = None
    if store is not None:
        try:
            template_override = store.get_prompt_template(device_type)
        except Exception:
            template_override = None

    if template_override and isinstance(template_override, str) and template_override.strip():
        enriched_prompt = (
            template_override.replace("{{device_type}}", str(device_type))
            .replace("{{device_name}}", str(device_name))
            .replace("{{parameter_values}}", params_json)
            .replace("{{kb_context}}", kb_context or "")
        )
    else:
        enriched_prompt = f"""
You are generating authoritative audio engineering metadata for a {device_type} preset.

KB Context (verbatim excerpts from internal knowledge):
---
{kb_context}
---

Preset Name: {device_name}
Parameter Values:
{params_json}

Requirements:
- Output STRICT JSON only (no prose).
- Provide a deeply technical description and rationale grounded in the KB Context and parameter values.
- audio_engineering.use_cases MUST include at least 4 detailed entries with send_level, eq_prep, and rationale fields.
- natural_language_controls MUST include all listed controls with parameter suggestions and explanations grounded in psychoacoustics.
- Prefer precise numeric guidance when possible.

JSON schema/layout to follow:
{json.dumps(preset_metadata_schema(), indent=2)}

Return ONLY valid JSON.
"""

    try:
        resp = model.generate_content(
            enriched_prompt,
            generation_config={
                "temperature": 0.0,
                "max_output_tokens": 4096,
                "top_p": 0.9,
                "response_mime_type": "application/json",
            },
        )
    except Exception:
        resp = model.generate_content(
            enriched_prompt,
            generation_config={
                "temperature": 0.0,
                "max_output_tokens": 4096,
                "top_p": 0.9,
            },
        )

    def quality_ok(data: Dict[str, Any]) -> bool:
        try:
            why = str(((data or {}).get("description") or {}).get("why") or "")
            use_cases = ((data or {}).get("audio_engineering") or {}).get("use_cases") or []
            return len(why) >= 200 and isinstance(use_cases, list) and len(use_cases) >= 4
        except Exception:
            return False

    def try_enrich(meta_in: Dict[str, Any]) -> Dict[str, Any]:
        try:
            enrich_prompt = f"""
You are enriching existing preset metadata using the KB Context.
KB Context:
---
{kb_context}
---
Original Metadata JSON:
{json.dumps(meta_in, indent=2)}

Improve it to meet these minimums:
- description.why >= 200 characters with deeper technical reasoning
- audio_engineering.use_cases must contain at least 4 detailed entries (with send_level, eq_prep, and clear rationale)
Return STRICT JSON only with the same keys expanded.
"""
            resp2 = model.generate_content(
                enrich_prompt,
                generation_config={
                    "temperature": 0.2,
                    "max_output_tokens": 4096,
                    "top_p": 0.9,
                    "response_mime_type": "application/json",
                },
            )
            text = getattr(resp2, "text", None)
            if text:
                meta2 = json.loads(text)
                if quality_ok(meta2):
                    return meta2
                merged = dict(meta_in)
                merged.update(meta2)
                return merged
        except Exception:
            return meta_in
        return meta_in

    response_text = getattr(resp, "text", None)
    if response_text:
        try:
            meta = json_lenient_parse(response_text) or json.loads(response_text)
            if not quality_ok(meta):
                meta = try_enrich(meta)
            return meta
        except Exception:
            pass

    try:
        candidates = getattr(resp, "candidates", []) or []
        for candidate in candidates:
            content = getattr(candidate, "content", None)
            parts = getattr(content, "parts", []) if content else []
            for part in parts:
                text = getattr(part, "text", None)
                if not text:
                    continue
                try:
                    meta = json_lenient_parse(text) or json.loads(text)
                    if not quality_ok(meta):
                        meta = try_enrich(meta)
                    return meta
                except Exception:
                    segment = str(text)
                    start, end = segment.find("{"), segment.rfind("}")
                    if start >= 0 and end > start:
                        meta = json_lenient_parse(segment[start : end + 1]) or json.loads(segment[start : end + 1])
                        if not quality_ok(meta):
                            meta = try_enrich(meta)
                        return meta
    except Exception:
        pass

    try:
        to_dict_fn = getattr(resp, "to_dict", None)
        if callable(to_dict_fn):
            parsed = to_dict_fn()

            def find_json_like(obj):
                if isinstance(obj, str) and obj.strip().startswith("{") and obj.strip().endswith("}"):
                    try:
                        return json.loads(obj)
                    except Exception:
                        segment = obj
                        start, end = segment.find("{"), segment.rfind("}")
                        if start >= 0 and end > start:
                            return json.loads(segment[start : end + 1])
                if isinstance(obj, dict):
                    for value in obj.values():
                        result = find_json_like(value)
                        if result is not None:
                            return result
                if isinstance(obj, list):
                    for item in obj:
                        result = find_json_like(item)
                        if result is not None:
                            return result
                return None

            candidate_meta = find_json_like(parsed)
            if candidate_meta is not None:
                if not quality_ok(candidate_meta):
                    candidate_meta = try_enrich(candidate_meta)
                return candidate_meta
    except Exception:
        pass

    raw_text = str(response_text or "").strip()
    start, end = raw_text.find("{"), raw_text.rfind("}")
    if start >= 0 and end > start:
        try:
            meta = json_lenient_parse(raw_text[start : end + 1]) or json.loads(raw_text[start : end + 1])
            if not quality_ok(meta):
                meta = try_enrich(meta)
            return meta
        except Exception:
            pass

    try:
        def generate_section(title: str, template: str) -> Dict[str, Any] | None:
            prompt = f"""
You are generating STRICT JSON for the '{title}' section only. No prose, no markdown.
KB Context (may help):
---
{kb_context}
---
Preset: {device_name} ({device_type})
Parameter Values:
{json.dumps(parameter_values, indent=2)}

Expected JSON skeleton to fill (return exactly this object with content populated):
{template}
"""
            result = model.generate_content(
                prompt,
                generation_config={
                    "temperature": 0.0,
                    "max_output_tokens": 2048,
                    "top_p": 0.9,
                    "response_mime_type": "application/json",
                },
            )
            text = getattr(result, "text", None)
            if not text:
                return None
            return json_lenient_parse(text) or json.loads(text)

        description = generate_section(
            "description",
            json.dumps({"description": {"what": "", "when": ["", "", "", ""], "why": ""}}, indent=2),
        ) or {}

        engineering = generate_section(
            "audio_engineering",
            json.dumps(
                {
                    "audio_engineering": {
                        "space_type": "",
                        "size": "",
                        "decay_time": "",
                        "predelay": "",
                        "frequency_character": "",
                        "stereo_width": "",
                        "diffusion": "",
                        "use_cases": [
                            {
                                "source": "",
                                "context": "",
                                "send_level": "",
                                "send_level_rationale": "",
                                "eq_prep": "",
                                "eq_rationale": "",
                                "notes": "",
                            }
                        ],
                    }
                },
                indent=2,
            ),
        ) or {}

        controls = generate_section(
            "natural_language_controls",
            json.dumps(
                {
                    "natural_language_controls": {
                        "tighter": {"params": {}, "explanation": ""},
                        "looser": {"params": {}, "explanation": ""},
                        "warmer": {"params": {}, "explanation": ""},
                        "brighter": {"params": {}, "explanation": ""},
                        "closer": {"params": {}, "explanation": ""},
                        "further": {"params": {}, "explanation": ""},
                        "wider": {"params": {}, "explanation": ""},
                        "narrower": {"params": {}, "explanation": ""},
                    }
                },
                indent=2,
            ),
        ) or {}

        merged: Dict[str, Any] = {}
        for chunk in (description, engineering, controls):
            merged.update(chunk or {})
        if merged:
            if not quality_ok(merged):
                merged = try_enrich(merged)
            return merged
    except Exception:
        pass

    return basic_metadata_fallback(device_name, device_type, parameter_values)
