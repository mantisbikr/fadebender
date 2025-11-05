from __future__ import annotations

import os
from typing import Any, Dict
from urllib.parse import urlparse
import socket

from fastapi import APIRouter, Response

from server.services.ableton_client import request_op
from server.config.feature_flags import get_flag_status


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


@router.get("/ready")
def readiness_check(response: Response) -> Dict[str, Any]:
    """Readiness check: verifies Ableton Live Remote Script is reachable.

    Returns 200 if Live is connected and responsive.
    Returns 503 Service Unavailable if Live is not connected.

    This is more stringent than /health - it actually tests connectivity
    to the Ableton Live Remote Script.
    """
    try:
        # Try a lightweight operation to test Live connectivity
        # Using get_transport since it's a simple, fast operation
        result = request_op("get_transport", timeout=0.5)

        if result and isinstance(result, dict):
            # Successfully got transport data from Live
            return {
                "status": "ready",
                "service": "ableton_live",
                "connected": True
            }
        else:
            # Request returned but with unexpected data
            response.status_code = 503
            return {
                "status": "not_ready",
                "service": "ableton_live",
                "connected": False,
                "reason": "unexpected_response"
            }
    except Exception as e:
        # Failed to connect to Live
        response.status_code = 503
        return {
            "status": "not_ready",
            "service": "ableton_live",
            "connected": False,
            "reason": "connection_failed",
            "error": str(e)
        }


@router.get("/features")
def feature_flags() -> Dict[str, Any]:
    """Get feature flag status for debugging.

    Returns all feature flags with their current values and sources
    (environment variable or default).
    """
    return {"flags": get_flag_status()}
