from __future__ import annotations

from typing import Any, Dict, Optional


def json_lenient_parse(text: str) -> Optional[Dict[str, Any]]:
    """Try to parse JSON with light repairs for common LLM artifacts.

    Repairs:
    - Strip markdown code fences
    - Normalize smart quotes to ASCII
    - Remove trailing commas before } or ]
    - Try largest-brace substring
    - As last resort, convert single quotes to double quotes (heuristic)
    """
    import re as _r
    t = str(text or "")
    if not t:
        return None
    # Strip code fences
    if t.strip().startswith("```"):
        parts = t.split("```")
        if len(parts) >= 3:
            t = parts[1] if parts[0].strip() == "" else parts[1]
    # Normalize quotes
    t = (
        t.replace("“", '"')
        .replace("”", '"')
        .replace("‟", '"')
        .replace("’", "'")
        .replace("‘", "'")
    )
    # Remove trailing commas
    t = _r.sub(r",\s*(\}|\])", r"\1", t)
    # Try direct parse
    try:
        import json as _json

        return _json.loads(t)
    except Exception:
        pass
    # Try largest brace substring
    i, j = t.find("{"), t.rfind("}")
    if i >= 0 and j > i:
        s = t[i : j + 1]
        s = _r.sub(r",\s*(\}|\])", r"\1", s)
        try:
            import json as _json

            return _json.loads(s)
        except Exception:
            pass
    # Last resort: convert single quotes to double quotes naively
    try:
        t2 = _r.sub(r"'", '"', t)
        import json as _json

        return _json.loads(t2)
    except Exception:
        return None

