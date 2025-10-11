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
# Safety: disable direct Gemini API usage by default (cost-control)
DISABLE_GENAI = str(os.getenv("DISABLE_GENAI", "1")).lower() in ("1", "true", "yes", "on")
if DISABLE_GENAI:
    GENAI_API_KEY = None

# Rate limiting: Max LLM calls per hour to prevent runaway costs
MAX_LLM_CALLS_PER_HOUR = int(os.getenv("MAX_LLM_CALLS_PER_HOUR", "20"))  # Conservative limit
_llm_call_timestamps = []  # Track recent call times


def load_grouping_config(device_name: str) -> Dict[str, Any]:
    """Load grouping configuration from param_learn_config.

    Args:
        device_name: Device name (e.g., "AudioEffectGroupDelay")

    Returns:
        Grouping config with masters, dependents, dependent_master_values
    """
    try:
        from google.cloud import storage
        import json

        # Load param_learn.json from GCS (synced from configs/)
        client = storage.Client(project=PROJECT_ID)
        bucket = client.bucket(KB_BUCKET)

        # Try to load from GCS first
        try:
            blob = bucket.blob("configs/param_learn.json")
            if blob.exists():
                content = blob.download_as_text()
                config = json.loads(content)
                grouping = config.get("grouping", {})
                print(f"[GROUPING] Loaded config from GCS")
            else:
                print(f"[GROUPING] configs/param_learn.json not found in GCS, using defaults")
                grouping = {}
        except Exception as e:
            print(f"[GROUPING] Failed to load from GCS: {e}, using defaults")
            grouping = {}

        # Match device type to grouping config
        device_name_lower = device_name.lower()
        for device_type, grp_cfg in grouping.items():
            if device_type.lower() in device_name_lower:
                print(f"[GROUPING] Matched device '{device_name}' to grouping config '{device_type}'")
                return grp_cfg

        # Fallback to default
        default_cfg = grouping.get("default", {
            "masters": [],
            "dependents": {},
            "dependent_master_values": {},
            "skip_auto_enable": []
        })
        print(f"[GROUPING] No specific grouping config for '{device_name}', using default")
        return default_cfg

    except Exception as e:
        print(f"[GROUPING] Failed to load grouping config: {e}")
        return {
            "masters": [],
            "dependents": {},
            "dependent_master_values": {},
            "skip_auto_enable": []
        }


def filter_inactive_parameters(
    parameter_values: Dict[str, float],
    grouping_config: Dict[str, Any]
) -> Dict[str, float]:
    """Filter out inactive parameters based on master switch states.

    Args:
        parameter_values: Dict of param_name -> normalized_value (0.0-1.0)
        grouping_config: Grouping config with dependents and dependent_master_values

    Returns:
        Filtered dict with only active parameters
    """
    dependents = grouping_config.get("dependents", {})
    dependent_master_values = grouping_config.get("dependent_master_values", {})

    if not dependents:
        # No grouping rules, return all parameters
        return parameter_values

    # Build reverse lookup: master -> list of dependents
    master_to_deps: Dict[str, List[str]] = {}
    for dep_name, master_name in dependents.items():
        master_to_deps.setdefault(master_name, []).append(dep_name)

    filtered = {}
    for param_name, param_value in parameter_values.items():
        # Check if this parameter is a dependent
        if param_name in dependents:
            master_name = dependents[param_name]
            master_value = parameter_values.get(master_name)

            if master_value is None:
                # Master not found, include dependent by default
                filtered[param_name] = param_value
                continue

            # Check if dependent should be active
            required_master_value = dependent_master_values.get(param_name)
            if required_master_value is not None:
                # Exact match required (e.g., L 16th active when L Sync=1.0)
                if abs(master_value - required_master_value) < 0.01:
                    filtered[param_name] = param_value
                # else: Skip inactive dependent
            else:
                # No specific value required, active when master > 0.5
                if master_value > 0.5:
                    filtered[param_name] = param_value
        else:
            # Not a dependent, include it
            filtered[param_name] = param_value

    excluded = set(parameter_values.keys()) - set(filtered.keys())
    if excluded:
        print(f"[GROUPING] Excluded {len(excluded)} inactive parameters: {', '.join(sorted(excluded))}")

    return filtered


def convert_parameter_values(
    parameter_values: Dict[str, float],
    structure_signature: str
) -> Dict[str, Any]:
    """Convert normalized parameter values to display using shared mapping and fits.

    Also filters out inactive parameters based on grouping rules.
    """
    try:
        from shared.mapping_fetch import load_device_mapping
        from shared.param_convert import to_display
        from shared.aliases import canonical_name
    except Exception as e:
        print(f"[MAPPING] Shared modules unavailable: {e}")
        return {name: {"value": None, "display": f"{val:.3f}", "normalized": float(val)} for name, val in parameter_values.items()}

    mapping = load_device_mapping(structure_signature, project_id=FIRESTORE_PROJECT)
    if not mapping or not isinstance(mapping.get("params"), list):
        print(f"[MAPPING] No mapping found for signature {structure_signature}")
        return {name: {"value": None, "display": f"{val:.3f}", "normalized": float(val)} for name, val in parameter_values.items()}

    # Load grouping config and filter inactive parameters
    device_name = mapping.get("device_name", structure_signature)
    grouping_config = load_grouping_config(device_name)
    filtered_params = filter_inactive_parameters(parameter_values, grouping_config)

    idx = {str(p.get("name", "")).lower(): p for p in mapping["params"]}
    converted: Dict[str, Any] = {}
    for raw_name, norm_value in filtered_params.items():
        lp = idx.get(str(raw_name).lower())
        cname = canonical_name(raw_name)
        if lp:
            disp_str, disp_num = to_display(float(norm_value), lp)
            converted[cname] = {
                "value": disp_num if disp_num is not None else None,
                "display": disp_str,
                "unit": lp.get("unit") or None,
                "normalized": float(norm_value),
            }
        else:
            converted[cname] = {"value": None, "display": f"{norm_value:.3f}", "normalized": float(norm_value)}

    return converted


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


def check_rate_limit() -> bool:
    """Check if we're within rate limit. Returns True if OK to proceed."""
    global _llm_call_timestamps
    import time
    now = time.time()
    hour_ago = now - 3600

    # Remove calls older than 1 hour
    _llm_call_timestamps = [ts for ts in _llm_call_timestamps if ts > hour_ago]

    if len(_llm_call_timestamps) >= MAX_LLM_CALLS_PER_HOUR:
        print(f"[RATE_LIMIT] ⚠️  Hit rate limit: {len(_llm_call_timestamps)} calls in last hour (max: {MAX_LLM_CALLS_PER_HOUR})")
        return False

    _llm_call_timestamps.append(now)
    print(f"[RATE_LIMIT] ✓ OK: {len(_llm_call_timestamps)}/{MAX_LLM_CALLS_PER_HOUR} calls in last hour")
    return True


def load_prompt_template(device_type: str) -> tuple[str, Dict[str, Any]]:
    """Load prompt template and schema from Firestore for device type.

    Args:
        device_type: Device category (delay, reverb, etc.)

    Returns:
        Tuple of (prompt_template, audio_engineering_schema)
    """
    from google.cloud import firestore

    client = firestore.Client(project=FIRESTORE_PROJECT)
    device_type_l = str(device_type or "").lower()

    # Load prompt template
    template_doc = client.collection("prompt_templates").document(device_type_l).get()
    if template_doc.exists:
        template_data = template_doc.to_dict()
        prompt_template = template_data.get("template", "")
        print(f"[PROMPT] Loaded template for {device_type_l} from Firestore")
    else:
        print(f"[PROMPT] No template found for {device_type_l}, using fallback")
        prompt_template = """You are an expert audio engineer analyzing a {device_type} preset.

Preset Name: {device_name}
Device Type: {device_type}

Parameter Values:
{parameter_values}

# Knowledge Base Context

{kb_context}

# Task

Using the parameter values and knowledge base context, generate comprehensive metadata for this preset.
Be specific, technical, and reference actual parameter values in your explanations."""

    # Load device-specific audio_engineering schema
    schema_doc = client.collection("schemas").document(f"{device_type_l}_audio_engineering").get()
    if schema_doc.exists:
        ae_schema = schema_doc.to_dict()
        print(f"[SCHEMA] Loaded audio_engineering schema for {device_type_l} from Firestore")
    else:
        print(f"[SCHEMA] No audio_engineering schema found for {device_type_l}, using generic fallback")
        # Generic fallback schema
        ae_schema = {
            "type": "object",
            "properties": {
                "character": {"type": "string"},
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
                            "notes": {"type": "string"}
                        }
                    }
                }
            }
        }

    return prompt_template, ae_schema


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
    # Check rate limit first
    if not check_rate_limit():
        print("[WORKER] Skipping LLM call due to rate limit")
        return {}, False, "rate_limited", None

    try:
        # Load prompt template and schema from Firestore
        prompt_template, ae_schema = load_prompt_template(device_type)

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

        # Build response schema with device-specific audio_engineering
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
                "audio_engineering": ae_schema,  # Device-specific schema from Firestore
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

        # Build enriched prompt using template
        prompt = prompt_template.format(
            device_type=device_type,
            device_name=device_name,
            parameter_values=params_formatted,
            kb_context=kb_content
        )

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

        # Use Vertex AI (primary path)
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

        # Always use chunked mode for robustness
        print("[LLM] Using chunked generation per section")
        base_context = f"Preset Name: {device_name}\nDevice Type: {device_type}\n\nParameter Values:\n{params_formatted}\n\n# Knowledge Base Context\n\n{kb_content}\n"

        sections: Dict[str, Any] = {}
        sec_ok = 0; sec_fail = 0

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
            sec_fail += 1
        else:
            sec_ok += 1

        # Audio engineering (device-specific fields from schema)
        ae_fields = list(ae_schema.get("properties", {}).keys())
        ae_prompt = (
            f"Generate only the 'audio_engineering' JSON object with keys {', '.join(ae_fields)}.\n"
            "Return ONLY the JSON for audio_engineering."
        )
        r = model.generate_content(base_context + "\n# Task\n" + ae_prompt)
        try:
            sections["audio_engineering"], _ = parse_llm_json(r.text.strip())
        except Exception as e:
            print(f"[LLM] audio_engineering parse failed: {e}")
            sec_fail += 1
        else:
            sec_ok += 1

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
            sec_fail += 1
        else:
            sec_ok += 1

        # Subcategory
        sub_prompt = (
            f"Return a JSON object: {{\"subcategory\": <string>}} for the specific subtype of {device_type}."
        )
        r = model.generate_content(base_context + "\n# Task\n" + sub_prompt)
        try:
            sub_obj, _ = parse_llm_json(r.text.strip())
            if isinstance(sub_obj, dict) and "subcategory" in sub_obj:
                sections["subcategory"] = sub_obj["subcategory"]
        except Exception as e:
            print(f"[LLM] subcategory parse failed: {e}")
            sec_fail += 1
        else:
            if "subcategory" in sections:
                sec_ok += 1

        # Warnings
        warn_prompt = (
            "Generate only the 'warnings' JSON object with keys mono_compatibility, cpu_usage, mix_context, frequency_buildup, low_end_accumulation. Return ONLY JSON."
        )
        r = model.generate_content(base_context + "\n# Task\n" + warn_prompt)
        try:
            sections["warnings"], _ = parse_llm_json(r.text.strip())
        except Exception as e:
            print(f"[LLM] warnings parse failed: {e}")
            sec_fail += 1
        else:
            sec_ok += 1

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
            sec_fail += 1
        else:
            if "genre_tags" in sections:
                sec_ok += 1

        metadata = sections

        required_top = {"description", "audio_engineering", "natural_language_controls", "subcategory", "warnings", "genre_tags"}
        ok = isinstance(metadata, dict) and required_top.issubset(set(metadata.keys()))
        print(f"[METRICS] vertex_chunked sections_ok={sec_ok} sections_failed={sec_fail}")
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
        # Verify Pub/Sub authentication (Cloud Run with --no-allow-unauthenticated)
        # Pub/Sub will include Authorization header with service account token
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            print("[WORKER] ⚠️  Unauthorized request rejected (no Bearer token)")
            return ("Unauthorized", 401)

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
        "provider": "genai" if GENAI_API_KEY else "vertex",
    }


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
