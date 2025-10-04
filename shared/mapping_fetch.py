from __future__ import annotations

from typing import Any, Dict, List, Optional


def load_device_mapping(signature: str, project_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Fetch device mapping and params from Firestore device_mappings/{signature}.

    Returns a dict with at least keys: device_name, device_type, params: List[dict]
    """
    try:
        from google.cloud import firestore  # type: ignore
        client = firestore.Client(project=project_id) if project_id else firestore.Client()
        doc = client.collection("device_mappings").document(signature).get()
        if not doc.exists:
            return None
        data = doc.to_dict() or {}
        params: List[Dict[str, Any]] = []
        params_iter = client.collection("device_mappings").document(signature).collection("params").stream()
        for pdoc in params_iter:
            params.append(pdoc.to_dict() or {})
        data["params"] = params
        return data
    except Exception:
        return None

