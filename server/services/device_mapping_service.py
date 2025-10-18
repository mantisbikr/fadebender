from __future__ import annotations

from typing import Any, Dict, List, Optional

from server.core.deps import get_store


def ensure_device_mapping(device_signature: str, device_type: str, params: List[Dict[str, Any]]) -> None:
    try:
        if not params or len(params) < 5:
            return
        store = get_store()
        mapping = store.get_device_mapping(device_signature)
        if mapping:
            return
        # Build params_meta (consolidated structure with all parameter info)
        params_meta = []
        for p in params:
            param_info = {
                "index": p.get("index"),
                "name": p.get("name"),
                "min": p.get("min", 0.0),
                "max": p.get("max", 1.0),
                # Additional fields will be added later by LLM analysis
                "control_type": None,
                "unit": None,
                "min_display": None,
                "max_display": None,
            }
            params_meta.append(param_info)
        import time as _time
        mapping_data = {
            "device_signature": device_signature,
            "device_type": device_type,
            "params_meta": params_meta,
            "param_count": len(params_meta),
            "created_at": int(_time.time()),
            "updated_at": int(_time.time()),
            "metadata_status": "pending_analysis",
        }
        store.save_device_mapping(device_signature, mapping_data)
    except Exception:
        # Non-fatal
        return

