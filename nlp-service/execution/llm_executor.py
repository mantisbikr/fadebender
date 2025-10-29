"""LLM execution module for calling Vertex AI."""

from __future__ import annotations

import json
import os
from typing import Dict, Any

from config.llm_config import get_llm_project_id, get_default_model_name
from prompts.prompt_builder import build_daw_prompt
from fetchers import fetch_devices_cached, fetch_mixer_params_cached
from models.intent_types import Intent


def call_llm(query: str, model_preference: str | None = None) -> Intent:
    """Call LLM with cached device/param data.

    Uses caching to avoid repeated Firestore/HTTP calls.
    Typical latency: 2-4 seconds (dominated by LLM inference).

    Args:
        query: User query text
        model_preference: Optional model override

    Returns:
        Intent dictionary with LLM response

    Raises:
        Exception on LLM errors
    """
    # Fetch with caching (5 second TTL by default)
    known_devices = fetch_devices_cached()
    mixer_params = fetch_mixer_params_cached()

    from google import genai  # type: ignore
    from google.genai import types  # type: ignore

    project = get_llm_project_id()
    location = os.getenv("GCP_REGION", "us-central1")
    model_name = get_default_model_name(model_preference)

    # Initialize client with Vertex AI mode
    client = genai.Client(vertexai=True, project=project, location=location)

    prompt = build_daw_prompt(query, mixer_params, known_devices)

    # Generate content with configuration
    config = types.GenerateContentConfig(
        temperature=0.1,
        max_output_tokens=512,
        top_p=0.8,
        top_k=20,
    )

    resp = client.models.generate_content(
        model=model_name,
        contents=prompt,
        config=config
    )

    response_text = resp.text if hasattr(resp, 'text') else None
    if not response_text:
        raise RuntimeError("Empty LLM response")

    text = response_text.strip()
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end <= start:
        raise ValueError("No JSON found in response")

    result = json.loads(text[start:end + 1])
    result.setdefault("meta", {})["model_used"] = model_name
    return result
