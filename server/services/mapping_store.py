from __future__ import annotations

import os
from typing import Any, Dict, List, Optional


class MappingStore:
    def __init__(self) -> None:
        self._client = None
        self._enabled = False
        # Try Firestore first
        try:
            from google.cloud import firestore  # type: ignore

            self._client = firestore.Client()
            self._enabled = True
            self._backend = "firestore"
        except Exception:
            self._client = None
            self._enabled = False
            self._backend = "disabled"

    @property
    def enabled(self) -> bool:
        return self._enabled

    @property
    def backend(self) -> str:
        return getattr(self, "_backend", "disabled")

    def save_device_map(
        self,
        signature: str,
        device_meta: Dict[str, Any],
        params: List[Dict[str, Any]],
    ) -> bool:
        if not self._enabled or not self._client:
            return False
        try:
            doc = self._client.collection("device_mappings").document(signature)
            meta = {
                "device_name": device_meta.get("name"),
                "param_count": len(params),
                "param_names": [p.get("name") for p in params],
                "signature": signature,
                "tags": device_meta.get("tags", []),
            }
            doc.set(meta, merge=True)
            # params subcollection
            for p in params:
                name = str(p.get("name"))
                pdata = {
                    "name": name,
                    "index": int(p.get("index", 0)),
                    "min": float(p.get("min", 0.0)),
                    "max": float(p.get("max", 1.0)),
                    "samples": p.get("samples", []),  # list of {value, display, display_num}
                    "quantized": bool(p.get("quantized", False)),
                    "unit": p.get("unit"),
                }
                doc.collection("params").document(name).set(pdata, merge=True)
            return True
        except Exception:
            return False

    def get_device_map(self, signature: str) -> Optional[Dict[str, Any]]:
        if not self._enabled or not self._client:
            return None
        try:
            doc = self._client.collection("device_mappings").document(signature).get()
            if not doc.exists:
                return None
            data = doc.to_dict() or {}
            # Pull params
            params_snap = self._client.collection("device_mappings").document(signature).collection("params").stream()
            params: List[Dict[str, Any]] = []
            for pdoc in params_snap:
                pdata = pdoc.to_dict() or {}
                params.append(pdata)
            data["params"] = params
            return data
        except Exception:
            return None

