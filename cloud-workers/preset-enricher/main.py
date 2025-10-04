"""
Cloud Run worker for preset metadata enrichment.

Triggered by Pub/Sub messages when presets are captured.
Loads preset from Firestore, fetches knowledge base from GCS,
generates rich metadata with LLM, and updates Firestore.
"""
from __future__ import annotations

import os
import json
import base64
from typing import Any, Dict, List
from flask import Flask, request

# Initialize Flask app
app = Flask(__name__)

# Environment configuration
PROJECT_ID = os.getenv("VERTEX_PROJECT") or os.getenv("GOOGLE_CLOUD_PROJECT")
LOCATION = os.getenv("VERTEX_LOCATION", "us-central1")
MODEL_NAME = os.getenv("VERTEX_MODEL", "gemini-2.5-flash")
KB_BUCKET = os.getenv("KB_BUCKET", "fadebender-kb")
FIRESTORE_PROJECT = os.getenv("FIRESTORE_PROJECT_ID", PROJECT_ID)
LLM_CHUNKED_ONLY = str(os.getenv("LLM_CHUNKED_ONLY", "1")).lower() in ("1", "true", "yes", "on")
GENAI_API_KEY = os.getenv("LLM_API_KEY") or os.getenv("GENAI_API_KEY") or os.getenv("GOOGLE_API_KEY")


def convert_parameter_values(
    parameter_values: Dict[str, float],
    structure_signature: str
) -> Dict[str, Any]:
    """Convert normalized parameter values to display values using device mapping.

    Args:
        parameter_values: Dict of parameter_name -> normalized_value (0-1)
        structure_signature: Device structure signature to look up mapping

    Returns:
        Dict of parameter_name -> {value: float, display: str, unit: str}
    """
    try:
        from google.cloud import firestore
        import math

        client = firestore.Client(project=FIRESTORE_PROJECT)
        mapping_doc = client.collection("device_mappings").document(structure_signature).get()

        if not mapping_doc.exists:
            print(f"[MAPPING] No mapping found for signature {structure_signature}")
            return {name: {"value": val, "display": f"{val:.3f}"} for name, val in parameter_values.items()}

        # Load parameter mappings
        params_ref = mapping_doc.reference.collection("params")
        param_mappings = {}
        for pdoc in params_ref.stream():
            pdata = pdoc.to_dict()
            param_name = pdata.get("name")
            if param_name:
                param_mappings[param_name] = pdata

        print(f"[MAPPING] Loaded {len(param_mappings)} parameter mappings")

        # Convert each parameter
        converted = {}
        for param_name, norm_value in parameter_values.items():
            param_map = param_mappings.get(param_name)
            if not param_map:
                converted[param_name] = {"value": norm_value, "display": f"{norm_value:.3f}"}
                continue

            fit = param_map.get("fit")
            unit = param_map.get("unit", "")

            # Apply fit to convert normalized to display value
            if fit and fit.get("type"):
                fit_type = fit["type"]

                if fit_type == "linear":
                    # y = a*x + b
                    a, b = fit.get("a", 1.0), fit.get("b", 0.0)
                    display_val = a * norm_value + b

                elif fit_type == "exp":
                    # y = exp(b) * exp(a*x)
                    a, b = fit.get("a", 0.0), fit.get("b", 0.0)
                    display_val = math.exp(b) * math.exp(a * norm_value)

                elif fit_type == "log":
                    # Inverse: x = ln(norm), y = a*ln(norm) + b
                    a, b = fit.get("a", 1.0), fit.get("b", 0.0)
                    if norm_value > 0:
                        display_val = a * math.log(norm_value) + b
                    else:
                        display_val = norm_value

                elif fit_type == "piecewise":
                    # Linear interpolation between points
                    points = fit.get("points", [])
                    if not points:
                        display_val = norm_value
                    else:
                        # Find surrounding points
                        points_sorted = sorted(points, key=lambda p: p["x"])
                        if norm_value <= points_sorted[0]["x"]:
                            display_val = points_sorted[0]["y"]
                        elif norm_value >= points_sorted[-1]["x"]:
                            display_val = points_sorted[-1]["y"]
                        else:
                            # Interpolate
                            for i in range(len(points_sorted) - 1):
                                p1, p2 = points_sorted[i], points_sorted[i + 1]
                                if p1["x"] <= norm_value <= p2["x"]:
                                    t = (norm_value - p1["x"]) / (p2["x"] - p1["x"])
                                    display_val = p1["y"] + t * (p2["y"] - p1["y"])
                                    break
                            else:
                                display_val = norm_value
                else:
                    display_val = norm_value
            else:
                display_val = norm_value

            # Format display string
            if unit:
                if abs(display_val) >= 1000:
                    display_str = f"{display_val:.1f} {unit}"
                elif abs(display_val) >= 10:
                    display_str = f"{display_val:.2f} {unit}"
                else:
                    display_str = f"{display_val:.3f} {unit}"
            else:
                display_str = f"{display_val:.3f}"

            converted[param_name] = {
                "value": display_val,
                "display": display_str,
                "unit": unit,
                "normalized": norm_value
            }

        return converted

    except Exception as e:
        print(f"[MAPPING] Failed to convert parameters: {e}")
        import traceback
        traceback.print_exc()
        return {name: {"value": val, "display": f"{val:.3f}"} for name, val in parameter_values.items()}


def load_knowledge_base(device_type: str) -> str:
    """Load knowledge base markdown files from GCS for device type.

    Args:
        device_type: Device category (reverb, delay, etc.)

    Returns:
        Concatenated markdown content
    """
    try:
        from google.cloud import storage

        client = storage.Client(project=PROJECT_ID)
        bucket = client.bucket(KB_BUCKET)

        # Load device-specific KB files (aligned with repo structure synced to GCS)
        device_type_l = str(device_type or "").lower()
        kb_paths: list[str] = []
        if device_type_l == "reverb":
            kb_paths += [
                "ableton-live/audio-effects/reverb.md",
                "audio-fundamentals/deep_audio_engineering_reverb.md",
            ]
        elif device_type_l == "delay":
            kb_paths += [
                "ableton-live/audio-effects/delay.md",
                "audio-fundamentals/deep_audio_engineering_delay.md",
            ]
        # Common fundamentals
        kb_paths += [
            "audio-fundamentals/audio-engineering-principles.md",
            "audio-fundamentals/audio_concepts.md",
        ]

        kb_content = []
        for path in kb_paths:
            try:
                blob = bucket.blob(path)
                if blob.exists():
                    content = blob.download_as_text()
                    kb_content.append(f"# {path}\n\n{content}\n")
            except Exception:
                continue

        return "\n---\n\n".join(kb_content) if kb_content else ""
    except Exception as e:
        print(f"[KB] Failed to load knowledge base: {e}")
        return ""


def generate_metadata_with_kb(
    device_name: str,
    device_type: str,
    parameter_values: Dict[str, Any],
    kb_content: str,
) -> tuple[Dict[str, Any], bool, str | None, str | None]:
    """Generate rich metadata using LLM with knowledge base context.

    Args:
        device_name: Preset name
        device_type: Device category
        parameter_values: Dict of param_name -> {value, display, unit} or float
        kb_content: Knowledge base markdown

    Returns:
        Metadata dict with description, audio_engineering, etc.
    """
    try:
        # Format parameter values for prompt
        def format_params(params: Dict[str, Any]) -> str:
            """Format parameters for LLM prompt - use display values if available."""
            lines = []
            for name, val in params.items():
                if isinstance(val, dict) and "display" in val:
                    lines.append(f"  {name}: {val['display']}")
                else:
                    lines.append(f"  {name}: {val}")
            return "\n".join(lines)

        params_formatted = format_params(parameter_values)

        # Define response schema as JSON Schema dict (usable by google-generativeai, convertible for vertex)
        response_schema_dict = {
            "type": "object",
            "properties": {
                "description": {
                    "type": "object",
                    "properties": {
                        "what": {"type": "string"},
                        "when": {"type": "array", "items": {"type": "string"}},
                        "why": {"type": "string"},
                    },
                    "required": ["what", "when", "why"],
                },
                "audio_engineering": {
                    "type": "object",
                    "properties": {
                        "space_type": {"type": "string"},
                        "size": {"type": "string"},
                        "decay_time": {"type": "string"},
                        "predelay": {"type": "string"},
                        "frequency_character": {"type": "string"},
                        "stereo_width": {"type": "string"},
                        "diffusion": {"type": "string"},
                        "use_cases": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "source": {"type": "string"},
                                    "context": {"type": "string"},
                                    "send_level": {"type": "string"},
                                    "send_level_rationale": {"type": "string"},
                                    "eq_prep": {"type": "string"},
                                    "eq_rationale": {"type": "string"},
                                    "notes": {"type": "string"},
                                },
                                "required": [
                                    "source",
                                    "context",
                                    "send_level",
                                    "send_level_rationale",
                                    "eq_prep",
                                    "eq_rationale",
                                    "notes",
                                ],
                            },
                        },
                    },
                    "required": [
                        "space_type",
                        "size",
                        "decay_time",
                        "predelay",
                        "frequency_character",
                        "stereo_width",
                        "diffusion",
                        "use_cases",
                    ],
                },
                "natural_language_controls": {
                    "type": "object",
                    "properties": {
                        "tighter": {
                            "type": "object",
                            "properties": {
                                "params": {"type": "object"},
                                "explanation": {"type": "string"},
                            },
                            "required": ["params", "explanation"],
                        },
                        "looser": {
                            "type": "object",
                            "properties": {
                                "params": {"type": "object"},
                                "explanation": {"type": "string"},
                            },
                            "required": ["params", "explanation"],
                        },
                        "warmer": {
                            "type": "object",
                            "properties": {
                                "params": {"type": "object"},
                                "explanation": {"type": "string"},
                            },
                            "required": ["params", "explanation"],
                        },
                        "brighter": {
                            "type": "object",
                            "properties": {
                                "params": {"type": "object"},
                                "explanation": {"type": "string"},
                            },
                            "required": ["params", "explanation"],
                        },
                        "closer": {
                            "type": "object",
                            "properties": {
                                "params": {"type": "object"},
                                "explanation": {"type": "string"},
                            },
                            "required": ["params", "explanation"],
                        },
                        "further": {
                            "type": "object",
                            "properties": {
                                "params": {"type": "object"},
                                "explanation": {"type": "string"},
                            },
                            "required": ["params", "explanation"],
                        },
                        "wider": {
                            "type": "object",
                            "properties": {
                                "params": {"type": "object"},
                                "explanation": {"type": "string"},
                            },
                            "required": ["params", "explanation"],
                        },
                        "narrower": {
                            "type": "object",
                            "properties": {
                                "params": {"type": "object"},
                                "explanation": {"type": "string"},
                            },
                            "required": ["params", "explanation"],
                        },
                    },
                    "required": [
                        "tighter",
                        "looser",
                        "warmer",
                        "brighter",
                        "closer",
                        "further",
                        "wider",
                        "narrower",
                    ],
                },
                "subcategory": {"type": "string"},
                "warnings": {
                    "type": "object",
                    "properties": {
                        "mono_compatibility": {"type": "string"},
                        "cpu_usage": {"type": "string"},
                        "mix_context": {"type": "string"},
                        "frequency_buildup": {"type": "string"},
                        "low_end_accumulation": {"type": "string"},
                    },
                },
                "genre_tags": {"type": "array", "items": {"type": "string"}},
            },
            "required": [
                "description",
                "audio_engineering",
                "natural_language_controls",
                "subcategory",
                "warnings",
                "genre_tags",
            ],
        }

        # Build enriched prompt with KB
        prompt = f"""You are an expert audio engineer analyzing a {device_type} preset.

Preset Name: {device_name}
Device Type: {device_type}

Parameter Values:
{params_formatted}

# Knowledge Base Context

{kb_content}

# Task

Using the parameter values and knowledge base context, generate comprehensive metadata.

Guidelines:
- description.what: Concise technical description of the preset's sonic character (1-2 sentences)
- description.when: Array of 5 specific use cases
- description.why: Deep audio engineering explanation covering decay characteristics, frequency response, stereo imaging, psychoacoustic perception. Reference specific parameter values and their acoustic impact. (4-6 sentences)
- audio_engineering.space_type: Type of space being simulated (e.g., hall, room, plate)
- audio_engineering.size: Size descriptor with numeric reference from parameters
- audio_engineering.decay_time: RT60-style decay description with parameter values
- audio_engineering.predelay: Predelay amount and spatial reasoning with values
- audio_engineering.frequency_character: Frequency response description (bright/dark/neutral + EQ with parameter values)
- audio_engineering.stereo_width: Stereo width description with angle/parameter values
- audio_engineering.diffusion: Diffusion character (smooth/grainy/dense) with parameter values
- audio_engineering.use_cases: Array of 4 detailed use cases with source, context, send_level, send_level_rationale, eq_prep, eq_rationale, notes
- natural_language_controls: For each control (tighter, looser, warmer, brighter, closer, further, wider, narrower), provide params object with parameter adjustments and explanation
- subcategory: Specific category (e.g., hall, room, plate for reverb)
- warnings: Object with mono_compatibility, cpu_usage, mix_context, frequency_buildup, low_end_accumulation
- genre_tags: Array of 4 relevant genres

Be specific, technical, and reference actual parameter values in your explanations.

Output formatting rules:
- Return ONLY a single JSON object that strictly matches the schema.
- Do not include any prose, comments, or code fences.
"""

        def parse_llm_json(txt: str) -> tuple[Dict[str, Any], str | None]:
            import re
            # Strip fenced code blocks if present
            fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", txt)
            candidate = fence.group(1) if fence else txt
            # Try strict JSON first
            try:
                return json.loads(candidate), None
            except Exception as e1:
                # Try extracting the largest object substring
                start = candidate.find("{")
                end = candidate.rfind("}")
                recovered = candidate[start : end + 1] if start != -1 and end != -1 and end > start else candidate
                try:
                    return json.loads(recovered), None
                except Exception as e2:
                    # Try JSON5 if available
                    try:
                        import json5  # type: ignore
                        try:
                            return json5.loads(candidate), None
                        except Exception:
                            return json5.loads(recovered), None
                    except Exception:
                        # Provide debug snippet to help diagnose
                        dbg = recovered[:1600] if isinstance(recovered, str) else str(recovered)[:1600]
                        raise ValueError(f"Failed to parse LLM JSON: {e2}") from e2
        # If API key is provided, use google-generativeai with response_schema for stricter JSON
        if GENAI_API_KEY:
            import google.generativeai as genai  # type: ignore
            genai.configure(api_key=GENAI_API_KEY)
            gmodel = genai.GenerativeModel(MODEL_NAME)

            def gcall(prompt_text: str, schema: dict) -> str:
                cfg = {
                    "temperature": 0.0,
                    "top_p": 0.9,
                    "max_output_tokens": 4096,
                    "response_mime_type": "application/json",
                    "response_schema": schema,
                }
                resp = gmodel.generate_content(prompt_text, generation_config=cfg)
                return (resp.text or "").strip()

            # Always use chunked mode for robustness
            base_context = f"Preset Name: {device_name}\nDevice Type: {device_type}\n\nParameter Values:\n{params_formatted}\n\n# Knowledge Base Context\n\n{kb_content}\n"

            metadata: Dict[str, Any] = {}
            dbg_text = None

            # description schema
            desc_schema = response_schema_dict["properties"]["description"]
            desc_prompt = (
                "Generate only the 'description' object. Return ONLY JSON."
            )
            try:
                t = gcall(base_context + "\n# Task\n" + desc_prompt, desc_schema)
                metadata["description"], _ = parse_llm_json(t)
            except Exception as e:
                print(f"[LLM] GENAI description parse failed: {e}")

            # audio_engineering
            ae_schema = response_schema_dict["properties"]["audio_engineering"]
            ae_prompt = (
                "Generate only the 'audio_engineering' object. Return ONLY JSON."
            )
            try:
                t = gcall(base_context + "\n# Task\n" + ae_prompt, ae_schema)
                metadata["audio_engineering"], _ = parse_llm_json(t)
            except Exception as e:
                print(f"[LLM] GENAI audio_engineering parse failed: {e}")

            # natural_language_controls
            nlc_schema = response_schema_dict["properties"]["natural_language_controls"]
            nlc_prompt = (
                "Generate only the 'natural_language_controls' object. Return ONLY JSON."
            )
            try:
                t = gcall(base_context + "\n# Task\n" + nlc_prompt, nlc_schema)
                metadata["natural_language_controls"], _ = parse_llm_json(t)
            except Exception as e:
                print(f"[LLM] GENAI natural_language_controls parse failed: {e}")

            # subcategory
            sub_schema = {"type": "object", "properties": {"subcategory": {"type": "string"}}, "required": ["subcategory"]}
            sub_prompt = "Return only: {\"subcategory\": <string>}"
            try:
                t = gcall(base_context + "\n# Task\n" + sub_prompt, sub_schema)
                sub_obj, _ = parse_llm_json(t)
                if isinstance(sub_obj, dict) and "subcategory" in sub_obj:
                    metadata["subcategory"] = sub_obj["subcategory"]
            except Exception as e:
                print(f"[LLM] GENAI subcategory parse failed: {e}")

            # warnings
            warn_schema = response_schema_dict["properties"]["warnings"]
            warn_prompt = "Generate only the 'warnings' object. Return ONLY JSON."
            try:
                t = gcall(base_context + "\n# Task\n" + warn_prompt, warn_schema)
                metadata["warnings"], _ = parse_llm_json(t)
            except Exception as e:
                print(f"[LLM] GENAI warnings parse failed: {e}")

            # genre_tags
            genre_schema = {"type": "object", "properties": {"genre_tags": {"type": "array", "items": {"type": "string"}}}, "required": ["genre_tags"]}
            genre_prompt = "Return only: {\"genre_tags\": [<string>, <string>, <string>, <string>]}"
            try:
                t = gcall(base_context + "\n# Task\n" + genre_prompt, genre_schema)
                gobj, _ = parse_llm_json(t)
                if isinstance(gobj, dict) and "genre_tags" in gobj:
                    metadata["genre_tags"] = gobj["genre_tags"]
            except Exception as e:
                print(f"[LLM] GENAI genre_tags parse failed: {e}")

            required_top = {"description", "audio_engineering", "natural_language_controls", "subcategory", "warnings", "genre_tags"}
            ok = isinstance(metadata, dict) and required_top.issubset(set(metadata.keys()))
            print(f"[LLM] GENAI chunked assembled; ok={ok}")
            return metadata, ok, None, dbg_text

        # Otherwise use Vertex path (as implemented previously)
        import vertexai
        from vertexai.generative_models import (
            GenerativeModel,
            GenerationConfig,
        )
        # Optional structured output types (not available in some SDK versions)
        try:
            from vertexai.generative_models import Schema, Type  # type: ignore
            HAS_VERTEX_SCHEMA = True
        except Exception:
            Schema = None  # type: ignore
            Type = None  # type: ignore
            HAS_VERTEX_SCHEMA = False

        vertexai.init(project=PROJECT_ID, location=LOCATION)

        def to_vertex_schema(d: dict):
            tmap = {
                "object": Type.OBJECT if HAS_VERTEX_SCHEMA else None,
                "array": Type.ARRAY if HAS_VERTEX_SCHEMA else None,
                "string": Type.STRING if HAS_VERTEX_SCHEMA else None,
                "number": Type.NUMBER if HAS_VERTEX_SCHEMA else None,
                "integer": Type.INTEGER if HAS_VERTEX_SCHEMA else None,
                "boolean": Type.BOOLEAN if HAS_VERTEX_SCHEMA else None,
                "null": Type.NULL if HAS_VERTEX_SCHEMA else None,
            }
            t = d.get("type")
            if t is None:
                vtype = Type.OBJECT if HAS_VERTEX_SCHEMA else None
            else:
                if t not in tmap:
                    raise ValueError(f"Unsupported schema type: {t}")
                vtype = tmap[t]
            props = d.get("properties") or None
            items = d.get("items") or None
            required = d.get("required") or None
            if not HAS_VERTEX_SCHEMA:
                return None
            return Schema(
                type=vtype,
                properties={k: to_vertex_schema(v) for k, v in (props or {}).items()} if props else None,
                items=to_vertex_schema(items) if isinstance(items, dict) else None,
                required=required,
            )

        vertex_schema = to_vertex_schema(response_schema_dict) if HAS_VERTEX_SCHEMA else None

        model = GenerativeModel(MODEL_NAME)
        # Single-shot is bypassed if chunked-only
        parse_failed = True if LLM_CHUNKED_ONLY else False
        metadata: Dict[str, Any] = {}
        dbg_text = None
        if not LLM_CHUNKED_ONLY:
            try:
                kwargs = {}
                if vertex_schema is not None:
                    kwargs["response_schema"] = vertex_schema
                gen_config = GenerationConfig(
                    temperature=0.0,
                    max_output_tokens=4096,
                    top_p=0.9,
                    response_mime_type="application/json",
                    **kwargs,
                )
                response = model.generate_content(prompt, generation_config=gen_config)
            except TypeError as te:
                print(f"[LLM] Structured output unsupported, retrying without response_*: {te}")
                try:
                    gen_config = GenerationConfig(temperature=0.0, max_output_tokens=4096, top_p=0.9)
                    response = model.generate_content(prompt, generation_config=gen_config)
                except TypeError as te2:
                    print(f"[LLM] generation_config unsupported, calling with defaults: {te2}")
                    response = model.generate_content(prompt)

            response_text = response.text.strip()
            print(f"[LLM] Raw response length: {len(response_text)} chars")
            print(f"[LLM] First 200 chars: {response_text[:200]}")
            try:
                metadata, _dbg = parse_llm_json(response_text)
            except Exception as parse_err:
                print(f"[LLM] JSON parsing failed (single-shot): {parse_err}")
                dbg_text = response_text[:1600]
                parse_failed = True
                metadata = {}

        required_top = {"description", "audio_engineering", "natural_language_controls", "subcategory", "warnings", "genre_tags"}
        def have_all(d: Dict[str, Any]) -> bool:
            return isinstance(d, dict) and required_top.issubset(set(d.keys()))

        if parse_failed or not have_all(metadata):
            print("[LLM] Falling back to chunked generation per section")
            base_context = f"Preset Name: {device_name}\nDevice Type: {device_type}\n\nParameter Values:\n{params_formatted}\n\n# Knowledge Base Context\n\n{kb_content}\n"

            sections: Dict[str, Any] = {}
            # Description
            desc_prompt = (
                "Generate only the 'description' JSON object with keys what (string), when (array of 5 strings), why (string).\n"
                "Return ONLY the JSON for description, no prose."
            )
            r = model.generate_content(base_context + "\n# Task\n" + desc_prompt)
            try:
                sections["description"], _ = parse_llm_json(r.text.strip())
            except Exception as e:
                print(f"[LLM] description parse failed: {e}")

            # Audio engineering
            ae_prompt = (
                "Generate only the 'audio_engineering' JSON object with keys space_type, size, decay_time, predelay, frequency_character, stereo_width, diffusion, use_cases (array of 4 objects with source, context, send_level, send_level_rationale, eq_prep, eq_rationale, notes).\n"
                "Return ONLY the JSON for audio_engineering."
            )
            r = model.generate_content(base_context + "\n# Task\n" + ae_prompt)
            try:
                sections["audio_engineering"], _ = parse_llm_json(r.text.strip())
            except Exception as e:
                print(f"[LLM] audio_engineering parse failed: {e}")

            # Natural language controls
            nlc_prompt = (
                "Generate only the 'natural_language_controls' JSON object with keys tighter, looser, warmer, brighter, closer, further, wider, narrower. \n"
                "Each is an object with params (object mapping parameter names to numeric adjustments or target values) and explanation (string).\n"
                "Return ONLY the JSON for natural_language_controls."
            )
            r = model.generate_content(base_context + "\n# Task\n" + nlc_prompt)
            try:
                sections["natural_language_controls"], _ = parse_llm_json(r.text.strip())
            except Exception as e:
                print(f"[LLM] natural_language_controls parse failed: {e}")

            # Subcategory
            sub_prompt = (
                "Return a JSON object: {\"subcategory\": <string>} for the specific subtype (e.g., hall, room, plate)."
            )
            r = model.generate_content(base_context + "\n# Task\n" + sub_prompt)
            try:
                sub_obj, _ = parse_llm_json(r.text.strip())
                if isinstance(sub_obj, dict) and "subcategory" in sub_obj:
                    sections["subcategory"] = sub_obj["subcategory"]
            except Exception as e:
                print(f"[LLM] subcategory parse failed: {e}")

            # Warnings
            warn_prompt = (
                "Generate only the 'warnings' JSON object with keys mono_compatibility, cpu_usage, mix_context, frequency_buildup, low_end_accumulation. Return ONLY JSON."
            )
            r = model.generate_content(base_context + "\n# Task\n" + warn_prompt)
            try:
                sections["warnings"], _ = parse_llm_json(r.text.strip())
            except Exception as e:
                print(f"[LLM] warnings parse failed: {e}")

            # Genre tags
            genre_prompt = (
                "Return a JSON object: {\"genre_tags\": [<string>, <string>, <string>, <string>]}."
            )
            r = model.generate_content(base_context + "\n# Task\n" + genre_prompt)
            try:
                genre_obj, _ = parse_llm_json(r.text.strip())
                if isinstance(genre_obj, dict) and "genre_tags" in genre_obj:
                    sections["genre_tags"] = genre_obj["genre_tags"]
            except Exception as e:
                print(f"[LLM] genre_tags parse failed: {e}")

            if sections:
                metadata = {**metadata, **sections}

        ok = have_all(metadata)
        print(f"[LLM] Successfully generated structured metadata with keys: {list(metadata.keys()) if isinstance(metadata, dict) else 'n/a'}; ok={ok}")
        return metadata, ok, None, None

    except Exception as e:
        print(f"[LLM] Failed to generate metadata: {e}")
        import traceback
        tb = traceback.format_exc()
        print(f"[LLM] Full traceback:\n{tb}")
        # Return minimal fallback and flag as not ok
        fallback = {
            "description": {"what": f"{device_name} preset for {device_type}"},
            "subcategory": "unknown",
            "genre_tags": [],
        }
        # Attach a small debug snippet if available
        debug_snippet = locals().get("dbg_text")
        return fallback, False, str(e), debug_snippet


def update_preset_firestore(
    preset_id: str,
    metadata: Dict[str, Any],
    ok: bool,
    error: str | None = None,
    debug: str | None = None,
) -> bool:
    """Update preset in Firestore with generated metadata.

    Args:
        preset_id: Preset identifier
        metadata: Generated metadata dict

    Returns:
        True if updated successfully
    """
    try:
        from google.cloud import firestore
        from google.cloud.firestore_v1 import DELETE_FIELD  # type: ignore

        client = firestore.Client(project=FIRESTORE_PROJECT)
        doc_ref = client.collection("presets").document(preset_id)

        # Flatten metadata if nested (fix LLM returning nested structure)
        flattened_metadata = {}
        for key, value in metadata.items():
            # If value is a dict with a single key matching the parent key, flatten it
            if isinstance(value, dict) and len(value) == 1 and key in value:
                print(f"[FIRESTORE] Flattening nested {key}")
                flattened_metadata[key] = value[key]
            else:
                flattened_metadata[key] = value

        # Update with metadata + status flags
        update_data: Dict[str, Any] = {**flattened_metadata}
        if ok:
            update_data.update(
                {
                    "metadata_status": "enriched",
                    "metadata_version": 2,  # Cloud-enriched version
                    "enriched_at": firestore.SERVER_TIMESTAMP,
                    # Clear previous errors on success
                    "metadata_error": DELETE_FIELD,
                    "metadata_debug": DELETE_FIELD,
                }
            )
        else:
            # Mark as pending/fallback and persist error for visibility
            update_data.update(
                {
                    "metadata_status": "pending_enrichment",
                    # Do not bump metadata_version to 2 on failure
                    "enriched_at": firestore.SERVER_TIMESTAMP,
                }
            )
            if error:
                # Truncate error to keep document size small
                err_text = error[:500]
                update_data["metadata_error"] = err_text
            if debug:
                update_data["metadata_debug"] = debug[:1500]

        doc_ref.update(update_data)
        print(
            f"[FIRESTORE] Updated preset {preset_id} with {'enriched' if ok else 'fallback/pending'} metadata"
        )
        return True

    except Exception as e:
        print(f"[FIRESTORE] Failed to update preset {preset_id}: {e}")
        return False


@app.route("/", methods=["POST"])
def handle_pubsub():
    """Handle Pub/Sub push message."""
    try:
        envelope = request.get_json()
        if not envelope:
            return ("Bad Request: no Pub/Sub message", 400)

        # Decode Pub/Sub message
        pubsub_message = envelope.get("message", {})
        data = base64.b64decode(pubsub_message.get("data", "")).decode("utf-8")
        message = json.loads(data)

        event = message.get("event")
        preset_id = message.get("preset_id")

        print(f"[WORKER] Received event: {event}, preset_id: {preset_id}")

        if event != "preset_enrich_requested" or not preset_id:
            return ("OK: skipped", 200)

        # Load preset from Firestore
        from google.cloud import firestore
        client = firestore.Client(project=FIRESTORE_PROJECT)
        doc = client.collection("presets").document(preset_id).get()

        if not doc.exists:
            print(f"[WORKER] Preset {preset_id} not found in Firestore")
            return ("OK: preset not found", 200)

        preset_data = doc.to_dict()
        device_name = preset_data.get("name", "Unknown")
        device_type = preset_data.get("category", "unknown")
        parameter_values = preset_data.get("parameter_values", {})
        structure_signature = preset_data.get("structure_signature")

        print(f"[WORKER] Processing preset: {device_name} ({device_type})")
        print(f"[WORKER] Parameter count: {len(parameter_values)}")
        print(f"[WORKER] Structure signature: {structure_signature}")

        # Skip if already enriched
        if preset_data.get("metadata_version", 0) >= 2:
            print(f"[WORKER] Preset {preset_id} already enriched (v{preset_data.get('metadata_version')})")
            return ("OK: already enriched", 200)

        # Convert parameter values to display values using device mapping
        if structure_signature:
            converted_params = convert_parameter_values(parameter_values, structure_signature)
            print(f"[WORKER] Converted {len(converted_params)} parameters to display values")
        else:
            print(f"[WORKER] No structure signature, using raw normalized values")
            converted_params = {name: {"value": val, "display": f"{val:.3f}"} for name, val in parameter_values.items()}

        # Load knowledge base from GCS
        kb_content = load_knowledge_base(device_type)
        print(f"[WORKER] Loaded KB: {len(kb_content)} chars")

        # Generate metadata with LLM using converted values
        metadata, ok, err, debug = generate_metadata_with_kb(
            device_name=device_name,
            device_type=device_type,
            parameter_values=converted_params,
            kb_content=kb_content,
        )

        print(f"[WORKER] Generated metadata keys: {list(metadata.keys())}; ok={ok}")
        if not ok and err:
            print(f"[WORKER] LLM generation error: {err}")
            if debug:
                print(f"[WORKER] LLM output (trimmed): {debug[:300]}")

        # Update Firestore
        success = update_preset_firestore(preset_id, metadata, ok, err, debug)

        if success:
            return ("OK: enriched", 200)
        else:
            return ("Error: update failed", 500)

    except Exception as e:
        print(f"[WORKER] Error: {e}")
        import traceback
        traceback.print_exc()
        return (f"Error: {str(e)}", 500)


@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "preset-enricher",
        "project": PROJECT_ID,
        "location": LOCATION,
        "model": MODEL_NAME,
    }


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
