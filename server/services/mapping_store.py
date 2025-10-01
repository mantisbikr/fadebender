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
        # Local fallback dir for mappings
        try:
            import pathlib, os
            # Prefer user cache dir to avoid dev server reloads on file changes
            local_dir = os.getenv("FB_LOCAL_MAP_DIR")
            if local_dir:
                p = pathlib.Path(local_dir)
            else:
                p = pathlib.Path.home() / ".fadebender" / "param_maps"
            p.mkdir(parents=True, exist_ok=True)
            self._local_dir = p
        except Exception:
            self._local_dir = None

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
                # Sanitize document ID to avoid Firestore path issues
                doc_id = name.replace("/", "_").replace("\\", "_")
                pdata = {
                    "name": name,
                    "index": int(p.get("index", 0)),
                    "min": float(p.get("min", 0.0)),
                    "max": float(p.get("max", 1.0)),
                    "samples": p.get("samples", []),  # list of {value, display, display_num}
                    "quantized": bool(p.get("quantized", False)),
                    "unit": p.get("unit"),
                }
                doc.collection("params").document(doc_id).set(pdata, merge=True)
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

    def delete_device_map(self, signature: str) -> bool:
        if not self._enabled or not self._client:
            return False
        try:
            doc_ref = self._client.collection("device_mappings").document(signature)
            # Delete params subcollection docs
            try:
                for pdoc in doc_ref.collection("params").stream():
                    pdoc.reference.delete()
            except Exception:
                pass
            # Delete main doc
            doc_ref.delete()
            return True
        except Exception:
            return False

    # ---------- Local fallback (filesystem) ----------
    def _local_path(self, signature: str):
        import pathlib
        if not self._local_dir:
            return None
        return pathlib.Path(self._local_dir) / f"{signature}.json"

    def save_device_map_local(self, signature: str, device_meta: Dict[str, Any], params: List[Dict[str, Any]]) -> bool:
        try:
            import json
            p = self._local_path(signature)
            if not p:
                return False
            payload = {
                "device_name": device_meta.get("name"),
                "signature": signature,
                "params": params,
            }
            with open(p, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2)
            return True
        except Exception:
            return False

    def get_device_map_local(self, signature: str) -> Optional[Dict[str, Any]]:
        try:
            import json
            p = self._local_path(signature)
            if not p or not p.exists():
                return None
            with open(p, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None

    def list_local_maps(self) -> List[str]:
        try:
            import pathlib
            if not self._local_dir:
                return []
            sigs: List[str] = []
            for fp in pathlib.Path(self._local_dir).glob("*.json"):
                sigs.append(fp.stem)
            return sigs
        except Exception:
            return []

    def push_local_to_firestore(self, signature: str) -> bool:
        if not self._enabled or not self._client:
            return False
        data = self.get_device_map_local(signature)
        if not data:
            return False
        params = data.get("params") or []
        meta = {"name": data.get("device_name")}
        return self.save_device_map(signature, meta, params)

    def push_all_local(self) -> int:
        count = 0
        for sig in self.list_local_maps():
            try:
                if self.push_local_to_firestore(sig):
                    count += 1
            except Exception:
                continue
        return count
