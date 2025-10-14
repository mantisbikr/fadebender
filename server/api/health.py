from __future__ import annotations

import os
from typing import Any, Dict
from urllib.parse import urlparse
import socket

from fastapi import APIRouter


router = APIRouter()


@router.get("/health")
def server_health() -> Dict[str, Any]:
    """Simple controller health endpoint for UI status."""
    return {"status": "healthy", "service": "controller"}


@router.get("/llm/health")
def llm_health() -> Dict[str, Any]:
    """Quick LLM health: show resolved model/project/location and a JSON echo test.

    Does not consume many tokens; intended for debugging env issues.
    """
    import traceback

    model_name = os.getenv("LLM_MODEL") or os.getenv("VERTEX_MODEL") or "gemini-2.5-flash"
    project = os.getenv("VERTEX_PROJECT") or os.getenv("GOOGLE_CLOUD_PROJECT")
    location = os.getenv("VERTEX_LOCATION") or "us-central1"
    ok = False
    error = None
    tried = None

    # Lazy init Vertex if available; mirror behavior from app composition
    try:
        import vertexai  # type: ignore

        # Best-effort init to avoid hard dependency during local dev
        if project:
            try:
                vertexai.init(project=project, location=location)
            except Exception:
                # Defer errors to model call
                pass

        from vertexai.generative_models import GenerativeModel  # type: ignore
        m = GenerativeModel(model_name)
        # Use single quotes to avoid heavy escaping of JSON quotes
        prompt = 'Return a JSON object: {"ok": true, "note": "healthcheck"}'
        r = m.generate_content(
            prompt,
            generation_config={
                "response_mime_type": "application/json",
                "max_output_tokens": 64,
                "temperature": 0.0,
            },
        )
        txt = getattr(r, "text", "")
        tried = bool(txt)
        if txt:
            import json as _json

            data = _json.loads(txt)
            if isinstance(data, dict) and data.get("ok") is True:
                ok = True
        if not ok:
            error = "unexpected_response"
    except Exception as e:
        error = f"{e}\n{traceback.format_exc()}"

    return {
        "ok": ok,
        "model": model_name,
        "project": project,
        "location": location,
        "tried_text": tried,
        "error": error,
    }


@router.get("/controller/health")
def controller_health() -> Dict[str, Any]:
    """Lightweight health probe for the external controller (Node service).

    Uses CONTROLLER_BASE_URL env (default http://127.0.0.1:8721) and attempts a
    short TCP connect to the host:port. Does not perform HTTP requests to avoid
    extra dependencies. Returns status: online|offline and endpoint info.
    """
    base = os.getenv("CONTROLLER_BASE_URL", "http://127.0.0.1:8721")
    try:
        parsed = urlparse(base)
        host = parsed.hostname or "127.0.0.1"
        port = parsed.port or (8721 if (parsed.scheme or "http") == "http" else 443)
        ok = False
        try:
            with socket.create_connection((host, int(port)), timeout=0.3):
                ok = True
        except Exception:
            ok = False
        return {
            "status": "online" if ok else "offline",
            "endpoint": base,
            "host": host,
            "port": int(port),
        }
    except Exception as e:
        return {"status": "unknown", "endpoint": base, "error": str(e)}
