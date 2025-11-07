from __future__ import annotations

"""
Gemini File Search integration for grounded /help answers.

If FB_FEATURE_HELP_RAG=1 (or feature flag 'help_rag' enabled), attempts to
answer help queries using Google Gemini File Search. Falls back to local
knowledge search on errors or when not configured.
"""

import os
from typing import Any, Dict, List, Optional


def _supported_model(model: str) -> str:
    """Return a File Search compatible model (flash/pro)."""
    m = (model or "").lower()
    if "2.5-pro" in m:
        return "gemini-2.5-pro"
    # File Search supports flash/pro; default to flash
    return "gemini-2.5-flash"


def try_gemini_file_search(query: str, context: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
    """Call Gemini with File Search tool. Returns None on any error."""
    try:
        from google import genai  # type: ignore
        from google.genai import types  # type: ignore
    except Exception:
        return None

    store_name = os.getenv("GEMINI_FILE_SEARCH_STORE")
    if not store_name:
        return None

    # Resolve project/location and model
    def _project_id() -> str:
        return os.getenv("LLM_PROJECT_ID") or os.getenv("GOOGLE_CLOUD_PROJECT") or os.getenv("PROJECT_ID") or "fadebender"

    def _model_for_context() -> str:
        try:
            # Prefer server-side config
            from server.config.app_config import get_model_for_operation  # type: ignore
            return _supported_model(get_model_for_operation("context_analysis"))
        except Exception:
            pass
        # Fallback to env or default
        m = os.getenv("VERTEX_MODEL") or os.getenv("LLM_MODEL") or os.getenv("GEMINI_MODEL") or "gemini-2.5-flash"
        return _supported_model(m)

    project = _project_id()
    location = os.getenv("GCP_REGION", "us-central1")
    model = _model_for_context()

    try:
        client = genai.Client(vertexai=True, project=project, location=location)

        tools = [
            types.Tool(
                file_search=types.FileSearch(
                    file_search_store_names=[store_name]
                )
            )
        ]

        system_prompt = (
            "You are a DAW audio assistant. Answer concisely with actionable steps. "
            "If relevant, include short bullet tips."
        )

        cfg = types.GenerateContentConfig(
            tools=tools,
            temperature=0.2,
            max_output_tokens=768,
        )

        contents = [
            types.Content(role="user", parts=[system_prompt + "\n\nQuestion: " + query])
        ]

        resp = client.models.generate_content(
            model=model,
            contents=contents,
            config=cfg,
        )

        text = getattr(resp, "text", None)
        if not text:
            return None

        # Extract citations if available
        sources: List[Dict[str, str]] = []
        try:
            cand0 = (resp.candidates or [None])[0]
            gm = getattr(cand0, "grounding_metadata", None)
            # The structure may differ by SDK version; be defensive
            if gm and hasattr(gm, "sources"):
                for s in (gm.sources or []):
                    # Try to map to {source, title}
                    src = getattr(s, "uri", None) or getattr(s, "source", None) or getattr(s, "display_name", None)
                    title = getattr(s, "title", None) or getattr(s, "display_name", None) or ""
                    if src or title:
                        sources.append({"source": str(src or title), "title": str(title or src or "")})
        except Exception:
            pass

        return {"ok": True, "answer": text.strip(), "sources": sources}
    except Exception:
        return None


__all__ = ["try_gemini_file_search"]
