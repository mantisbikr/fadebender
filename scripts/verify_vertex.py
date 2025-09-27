#!/usr/bin/env python3
"""
Verify Vertex AI configuration for Fadebender.

Checks:
- Required env vars (project, region, credentials, model)
- Credentials file present
- vertexai import/init works
- Minimal generate_content call works against chosen model

Prints a JSON summary to stdout.
"""
from __future__ import annotations

import json
import os
import sys


def main() -> int:
    info = {
        "project_id": os.getenv("LLM_PROJECT_ID") or os.getenv("GOOGLE_CLOUD_PROJECT") or os.getenv("PROJECT_ID"),
        "region": os.getenv("GCP_REGION", "us-central1"),
        "credentials": os.getenv("GOOGLE_APPLICATION_CREDENTIALS"),
        "model": os.getenv("GEMINI_MODEL", "gemini-1.5-flash"),
        "strict": os.getenv("LLM_STRICT"),
    }

    result = {"ok": False, "steps": [], "env": info}

    # Step 1: basic env checks
    if not info["project_id"]:
        result["steps"].append({"ok": False, "step": "env_project", "error": "LLM_PROJECT_ID/PROJECT_ID not set"})
        print(json.dumps(result, indent=2))
        return 1
    else:
        result["steps"].append({"ok": True, "step": "env_project"})

    if not info["credentials"] or not os.path.exists(info["credentials"]):
        result["steps"].append({"ok": False, "step": "env_credentials", "error": "GOOGLE_APPLICATION_CREDENTIALS missing or file not found"})
        print(json.dumps(result, indent=2))
        return 1
    else:
        result["steps"].append({"ok": True, "step": "env_credentials"})

    # Step 2: import/init vertexai
    try:
        import vertexai  # type: ignore
        from vertexai.generative_models import GenerativeModel  # type: ignore
        result["steps"].append({"ok": True, "step": "import_vertexai"})
    except Exception as e:
        result["steps"].append({"ok": False, "step": "import_vertexai", "error": str(e)})
        print(json.dumps(result, indent=2))
        return 1

    try:
        vertexai.init(project=info["project_id"], location=info["region"])  # type: ignore
        result["steps"].append({"ok": True, "step": "vertex_init"})
    except Exception as e:
        result["steps"].append({"ok": False, "step": "vertex_init", "error": str(e)})
        print(json.dumps(result, indent=2))
        return 1

    # Step 3: minimal model call
    try:
        model = GenerativeModel(info["model"])  # type: ignore
        resp = model.generate_content("ping", generation_config={"max_output_tokens": 8, "temperature": 0.0})
        text = getattr(resp, "text", "")
        result["steps"].append({"ok": True, "step": "generate_content", "response": (text or "<ok>")[:120]})
        result["ok"] = True
        print(json.dumps(result, indent=2))
        return 0
    except Exception as e:
        result["steps"].append({"ok": False, "step": "generate_content", "error": str(e)})
        print(json.dumps(result, indent=2))
        return 2


if __name__ == "__main__":
    sys.exit(main())

