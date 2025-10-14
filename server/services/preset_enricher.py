from __future__ import annotations

import json
import os
from typing import Any, Dict


async def generate_preset_metadata_llm(
    device_name: str,
    device_type: str,
    parameter_values: Dict[str, float],
) -> Dict[str, Any]:
    try:
        import vertexai  # type: ignore
        from vertexai.generative_models import GenerativeModel  # type: ignore
        # Initialize from env; tolerate failures
        project = os.getenv("VERTEX_PROJECT") or os.getenv("GOOGLE_CLOUD_PROJECT")
        location = os.getenv("VERTEX_LOCATION") or "us-central1"
        if project:
            try:
                vertexai.init(project=project, location=location)
            except Exception:
                pass
        model_name = os.getenv("LLM_MODEL") or os.getenv("VERTEX_MODEL") or "gemini-2.5-flash"
        model = GenerativeModel(model_name)
        prompt = f"""You are an expert audio engineer analyzing a {device_type} preset.

Preset Name: {device_name}
Device Type: {device_type}

Parameter Values:
{json.dumps(parameter_values, indent=2)}

Generate a concise JSON with:
{{
  "description": {{
    "what": "1-2 sentence technical description",
    "when": ["use case 1", "use case 2"],
    "why": "2-3 sentence rationale"
  }},
  "audio_engineering": {{
    "space_type": "",
    "size": "",
    "decay_time": "",
    "predelay": "",
    "frequency_character": "",
    "stereo_width": "",
    "diffusion": ""
  }},
  "natural_language_controls": {{}}
}}

Return ONLY valid JSON.
"""
        r = model.generate_content(
            prompt,
            generation_config={
                "response_mime_type": "application/json",
                "max_output_tokens": 1024,
                "temperature": 0.0,
            },
        )
        txt = getattr(r, "text", None)
        if not txt:
            raise RuntimeError("no_text")
        data = json.loads(txt)
        if isinstance(data, dict):
            return data
    except Exception:
        pass
    # Fallback minimal metadata
    return {
        "description": {"what": f"{device_name} preset for {device_type}"},
        "audio_engineering": {},
        "natural_language_controls": {},
    }

