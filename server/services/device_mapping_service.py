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
        # Build parameter structure from params
        param_structure = []
        for p in params:
            param_info = {
                "index": p.get("index"),
                "name": p.get("name"),
                "min": p.get("min", 0.0),
                "max": p.get("max", 1.0),
            }
            param_structure.append(param_info)
        import time as _time
        mapping_data = {
            "device_signature": device_signature,
            "device_type": device_type,
            "param_structure": param_structure,
            "param_count": len(param_structure),
            "created_at": int(_time.time()),
            "updated_at": int(_time.time()),
            "metadata_status": "pending_analysis",
        }
        store.save_device_mapping(device_signature, mapping_data)
    except Exception:
        # Non-fatal
        return

