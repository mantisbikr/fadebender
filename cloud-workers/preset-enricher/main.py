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

        # Load device-specific KB files
        kb_paths = [
            f"devices/{device_type}/{device_type}.md",
            f"devices/{device_type}/reference.md",
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
    parameter_values: Dict[str, float],
    kb_content: str,
) -> Dict[str, Any]:
    """Generate rich metadata using LLM with knowledge base context.

    Args:
        device_name: Preset name
        device_type: Device category
        parameter_values: Current parameter values
        kb_content: Knowledge base markdown

    Returns:
        Metadata dict with description, audio_engineering, etc.
    """
    try:
        import vertexai
        from vertexai.generative_models import GenerativeModel

        vertexai.init(project=PROJECT_ID, location=LOCATION)

        # Build enriched prompt with KB
        prompt = f"""You are an expert audio engineer analyzing a {device_type} preset.

Preset Name: {device_name}
Device Type: {device_type}

Parameter Values:
{json.dumps(parameter_values, indent=2)}

# Knowledge Base Context

{kb_content}

# Task

Using the parameter values and knowledge base context, generate comprehensive metadata.

Generate a JSON object with this exact structure:

{{
  "description": {{
    "what": "Concise technical description of the preset's sonic character (1-2 sentences)",
    "when": ["Use case 1", "Use case 2", "Use case 3", "Use case 4", "Use case 5"],
    "why": "Deep audio engineering explanation covering: decay characteristics, frequency response, stereo imaging, psychoacoustic perception. Reference specific parameter values and their acoustic impact. (4-6 sentences)"
  }},
  "audio_engineering": {{
    "space_type": "Type of space being simulated (e.g., hall, room, plate)",
    "size": "Size descriptor with numeric reference from parameters",
    "decay_time": "RT60-style decay description with parameter values",
    "predelay": "Predelay amount and spatial reasoning with values",
    "frequency_character": "Frequency response description (bright/dark/neutral + EQ with parameter values)",
    "stereo_width": "Stereo width description with angle/parameter values",
    "diffusion": "Diffusion character (smooth/grainy/dense) with parameter values",
    "use_cases": [
      {{
        "source": "Audio source type (e.g., lead vocal, snare, synth pad)",
        "context": "Musical context (genre, arrangement)",
        "send_level": "Recommended send level (e.g., 15-25%)",
        "send_level_rationale": "Technical reasoning for this send level",
        "eq_prep": "Pre-send EQ recommendations (e.g., HPF @ 180 Hz)",
        "eq_rationale": "Why this EQ treatment is needed",
        "notes": "Additional mixing tips and gotchas"
      }},
      {{
        "source": "Different source type",
        "context": "Different context",
        "send_level": "Different level",
        "send_level_rationale": "Rationale",
        "eq_prep": "EQ settings",
        "eq_rationale": "EQ reasoning",
        "notes": "Additional notes"
      }},
      {{
        "source": "Third source",
        "context": "Third context",
        "send_level": "Level",
        "send_level_rationale": "Rationale",
        "eq_prep": "EQ",
        "eq_rationale": "Reasoning",
        "notes": "Notes"
      }},
      {{
        "source": "Fourth source",
        "context": "Fourth context",
        "send_level": "Level",
        "send_level_rationale": "Rationale",
        "eq_prep": "EQ",
        "eq_rationale": "Reasoning",
        "notes": "Notes"
      }}
    ]
  }},
  "natural_language_controls": {{
    "tighter": {{
      "params": {{"param_name": relative_change_value}},
      "explanation": "What happens and why (reference specific parameters)"
    }},
    "looser": {{"params": {{}}, "explanation": "..."}},
    "warmer": {{"params": {{}}, "explanation": "..."}},
    "brighter": {{"params": {{}}, "explanation": "..."}},
    "closer": {{"params": {{}}, "explanation": "..."}},
    "further": {{"params": {{}}, "explanation": "..."}},
    "wider": {{"params": {{}}, "explanation": "..."}},
    "narrower": {{"params": {{}}, "explanation": "..."}}
  }},
  "subcategory": "Specific category (e.g., hall, room, plate for reverb)",
  "warnings": {{
    "mono_compatibility": "Mono playback considerations if applicable",
    "cpu_usage": "CPU usage notes if complex settings",
    "mix_context": "Mixing context warnings",
    "frequency_buildup": "Frequency accumulation warnings if applicable",
    "low_end_accumulation": "Low-end buildup warnings if applicable"
  }},
  "genre_tags": ["genre1", "genre2", "genre3", "genre4"]
}}

Return ONLY valid JSON. Be specific, technical, and reference actual parameter values in your explanations.
"""

        model = GenerativeModel(MODEL_NAME)
        response = model.generate_content(
            prompt,
            generation_config={
                "temperature": 0.0,  # Deterministic
                "max_output_tokens": 4096,
                "top_p": 0.9,
            }
        )

        # Extract JSON from response
        response_text = response.text.strip()

        # Try to find JSON in response
        start = response_text.find("{")
        end = response_text.rfind("}") + 1

        if start >= 0 and end > start:
            json_str = response_text[start:end]
            metadata = json.loads(json_str)
            return metadata
        else:
            raise ValueError("No JSON found in response")

    except Exception as e:
        print(f"[LLM] Failed to generate metadata: {e}")
        # Return minimal fallback
        return {
            "description": {"what": f"{device_name} preset for {device_type}"},
            "subcategory": "unknown",
            "genre_tags": [],
        }


def update_preset_firestore(preset_id: str, metadata: Dict[str, Any]) -> bool:
    """Update preset in Firestore with generated metadata.

    Args:
        preset_id: Preset identifier
        metadata: Generated metadata dict

    Returns:
        True if updated successfully
    """
    try:
        from google.cloud import firestore

        client = firestore.Client(project=FIRESTORE_PROJECT)
        doc_ref = client.collection("presets").document(preset_id)

        # Update with metadata + status flags
        update_data = {
            **metadata,
            "metadata_status": "enriched",
            "metadata_version": 2,  # Cloud-enriched version
            "enriched_at": firestore.SERVER_TIMESTAMP,
        }

        doc_ref.update(update_data)
        print(f"[FIRESTORE] Updated preset {preset_id} with enriched metadata")
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

        print(f"[WORKER] Processing preset: {device_name} ({device_type})")
        print(f"[WORKER] Parameter count: {len(parameter_values)}")

        # Skip if already enriched
        if preset_data.get("metadata_version", 0) >= 2:
            print(f"[WORKER] Preset {preset_id} already enriched (v{preset_data.get('metadata_version')})")
            return ("OK: already enriched", 200)

        # Load knowledge base from GCS
        kb_content = load_knowledge_base(device_type)
        print(f"[WORKER] Loaded KB: {len(kb_content)} chars")

        # Generate metadata with LLM
        metadata = generate_metadata_with_kb(
            device_name=device_name,
            device_type=device_type,
            parameter_values=parameter_values,
            kb_content=kb_content,
        )

        print(f"[WORKER] Generated metadata keys: {list(metadata.keys())}")

        # Update Firestore
        success = update_preset_firestore(preset_id, metadata)

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
