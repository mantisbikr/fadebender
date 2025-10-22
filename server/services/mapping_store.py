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

            # Read database configuration from environment
            project_id = os.getenv("FIRESTORE_PROJECT_ID")
            database_id = os.getenv("FIRESTORE_DATABASE_ID", "(default)")


            # Initialize client with database parameter
            if project_id and database_id and database_id != "(default)":
                self._client = firestore.Client(project=project_id, database=database_id)
            elif project_id:
                self._client = firestore.Client(project=project_id)
            else:
                self._client = firestore.Client()

            self._enabled = True
            self._backend = "firestore"
        except Exception as e:
            import traceback
            traceback.print_exc()
            self._client = None
            self._enabled = False
            self._backend = "disabled"
        # Local fallback dir for mappings
        try:
            import pathlib
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
                "device_type": device_meta.get("device_type", "unknown"),  # NEW: detected type
                "param_count": len(params),
                "param_names": [p.get("name") for p in params],
                "signature": signature,
                "tags": device_meta.get("tags", []),
                # Optional: persist grouping metadata when provided
                "groups": device_meta.get("groups", []),
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
                    # New schema fields
                    "quantized": bool(p.get("quantized", False)),
                    "control_type": p.get("control_type"),  # binary | quantized | continuous
                    "unit": p.get("unit"),
                    "labels": p.get("labels", []),
                    "label_map": p.get("label_map"),  # dict label -> value
                    "fit": p.get("fit"),
                    "group": p.get("group"),
                    "role": p.get("role"),  # master | dependent | None
                }
                doc.collection("params").document(doc_id).set(pdata, merge=True)
            return True
        except Exception:
            return False

    def get_device_map(self, signature: str) -> Optional[Dict[str, Any]]:
        if not self._enabled or not self._client:
            return None
        try:
            from server.config.app_config import get_debug_settings  # lazy import to avoid cycles
            dbg_cfg = get_debug_settings().get("firestore", False)
            dbg_env = str(os.getenv("FB_DEBUG_FIRESTORE", "")).lower() in ("1","true","yes","on")
            dbg = bool(dbg_cfg or dbg_env)
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
        except Exception as e:
            if str(os.getenv("FB_DEBUG_FIRESTORE", "")).lower() in ("1","true","yes","on"):
                import traceback
                traceback.print_exc()
            return None

    def get_device_type_by_name(self, device_name: str) -> Optional[str]:
        """Query Firestore for device_type by device_name.

        Checks presets collection first (for preset instances like "4th Bandpass"),
        then falls back to device_mappings (for generic device classes like "Delay").

        Args:
            device_name: Name of the device (e.g., "Reverb", "4th Bandpass")

        Returns:
            device_type string or None if not found
        """
        if not self._enabled or not self._client:
            return None
        try:
            # First try presets collection (preset instances use "category" field)
            query = self._client.collection("presets").where("device_name", "==", device_name).limit(1)
            results = list(query.stream())

            if results:
                data = results[0].to_dict()
                # Presets use "category" for device_type
                category = data.get("category")
                if category:
                    return category

            # Fallback to device_mappings collection (generic device classes)
            query = self._client.collection("device_mappings").where("device_name", "==", device_name).limit(1)
            results = list(query.stream())

            if results:
                data = results[0].to_dict()
                return data.get("device_type")

            return None
        except Exception as e:
            return None

    def get_device_param_names(self, device_signature: Optional[str] = None, device_name: Optional[str] = None) -> Optional[List[str]]:
        """Get list of parameter names for a device.

        Queries Firestore for device parameter names by signature or device name.
        Used for parameter validation and normalization.

        Args:
            device_signature: Structure signature hash (preferred for accuracy)
            device_name: Device name (fallback if signature not available)

        Returns:
            List of canonical parameter names or None if not found
        """
        if not self._enabled or not self._client:
            return None

        try:
            # Try signature first (most accurate)
            if device_signature:
                doc = self._client.collection("device_mappings").document(device_signature).get()
                if doc.exists:
                    data = doc.to_dict()
                    param_names = data.get("param_names")
                    if param_names and isinstance(param_names, list):
                        return param_names

            # Fallback: query by device_name in presets or device_mappings
            if device_name:
                # Try presets first
                query = self._client.collection("presets").where("device_name", "==", device_name).limit(1)
                results = list(query.stream())
                if results:
                    data = results[0].to_dict()

                    # Extract param names from parameter_values or parameter_display_values
                    param_values = data.get("parameter_values", {})
                    param_display_values = data.get("parameter_display_values", {})

                    # Keys are identical in both, use whichever exists
                    param_dict = param_values if param_values else param_display_values

                    if param_dict and isinstance(param_dict, dict):
                        param_names = list(param_dict.keys())
                        return param_names

                    # Fallback to recursive approach if no param dicts found
                    sig = data.get("structure_signature")
                    if sig:
                        return self.get_device_param_names(device_signature=sig)

                # Try device_mappings
                query = self._client.collection("device_mappings").where("device_name", "==", device_name).limit(1)
                results = list(query.stream())
                if results:
                    data = results[0].to_dict()
                    param_names = data.get("param_names")
                    if param_names and isinstance(param_names, list):
                        return param_names

            return None
        except Exception:
            return None

    # ---------- Prompt templates ----------
    def get_prompt_template(self, device_type: str) -> Optional[str]:
        """Fetch per-device-type prompt template from Firestore if enabled.

        Collection: prompt_templates
        Doc ID: device_type lowercased (e.g., 'delay', 'reverb')
        Field: template (string)
        """
        if not self._enabled or not self._client:
            return None
        try:
            dt = (device_type or "").strip().lower()
            if not dt:
                return None
            doc = self._client.collection("prompt_templates").document(dt).get()
            if not doc.exists:
                return None
            data = doc.to_dict() or {}
            tpl = data.get("template")
            if isinstance(tpl, str) and tpl.strip():
                return tpl
            return None
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
    def _local_path(self, signature: str, subdir: str = ""):
        """Get local file path for a signature.

        Args:
            signature: Device signature hash
            subdir: Optional subdirectory (e.g., "structures" for structure maps)

        Returns:
            Path to JSON file or None
        """
        import pathlib
        if not self._local_dir:
            return None
        if subdir:
            base = pathlib.Path(self._local_dir) / subdir
            base.mkdir(parents=True, exist_ok=True)
            return base / f"{signature}.json"
        return pathlib.Path(self._local_dir) / f"{signature}.json"

    def save_device_map_local(self, signature: str, device_meta: Dict[str, Any], params: List[Dict[str, Any]]) -> bool:
        """Save device structure mapping to local storage.

        Stores in structures/ subdirectory since signature is now structure-based
        (excludes device name). This enables all Ableton Reverb presets to share
        one structure file.

        Args:
            signature: Structure-based signature (no device name)
            device_meta: Metadata including name, device_type, groups
            params: List of learned parameters with fits, control types, etc.

        Returns:
            True if saved successfully
        """
        try:
            import json
            p = self._local_path(signature, subdir="structures")
            if not p:
                return False
            payload = {
                "device_name": device_meta.get("name"),
                "device_type": device_meta.get("device_type", "unknown"),
                "signature": signature,
                "params": params,
                # Include groups metadata if present
                "groups": device_meta.get("groups", []),
            }
            with open(p, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2)
            return True
        except Exception:
            return False

    def get_device_map_local(self, signature: str) -> Optional[Dict[str, Any]]:
        """Get device structure mapping from local storage.

        Args:
            signature: Structure-based signature

        Returns:
            Device mapping dict or None
        """
        try:
            import json
            p = self._local_path(signature, subdir="structures")
            if p and p.exists():
                with open(p, "r", encoding="utf-8") as f:
                    return json.load(f)
            return None
        except Exception:
            return None

    def list_local_maps(self) -> List[str]:
        """List all local mapping signatures from structures/ directory."""
        try:
            import pathlib
            if not self._local_dir:
                return []

            structures_dir = pathlib.Path(self._local_dir) / "structures"
            if not structures_dir.exists():
                return []

            return [fp.stem for fp in structures_dir.glob("*.json")]
        except Exception:
            return []

    def push_local_to_firestore(self, signature: str) -> bool:
        """Push a local mapping to Firestore.

        Reads from local storage (structures/ or root) and uploads to Firestore.
        """
        if not self._enabled or not self._client:
            return False
        data = self.get_device_map_local(signature)
        if not data:
            return False
        params = data.get("params") or []
        meta = {
            "name": data.get("device_name"),
            "device_type": data.get("device_type", "unknown"),
            "groups": data.get("groups", []),
        }
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

    # ---------- Device Mapping Storage (New Display-Value Architecture) ----------

    def get_device_mapping(self, device_signature: str) -> Optional[Dict[str, Any]]:
        """Get device mapping from Firestore.

        Args:
            device_signature: SHA1 hash of parameter structure

        Returns:
            Device mapping data or None
        """
        if not self._enabled or not self._client:
            return None

        try:
            doc = self._client.collection("device_mappings").document(device_signature).get()
            if not doc.exists:
                return None
            return doc.to_dict()
        except Exception as e:
            return None

    def save_device_mapping(self, device_signature: str, mapping_data: Dict[str, Any]) -> bool:
        """Save device mapping to Firestore.

        Args:
            device_signature: SHA1 hash of parameter structure
            mapping_data: Mapping metadata including param_structure

        Returns:
            True if saved successfully
        """
        if not self._enabled or not self._client:
            return False

        try:
            doc = self._client.collection("device_mappings").document(device_signature)
            doc.set(mapping_data, merge=True)
            return True
        except Exception as e:
            return False

    # ---------- Preset Storage (Firestore + Local) ----------

    def save_preset(
        self,
        preset_id: str,
        preset_data: Dict[str, Any],
        local_only: bool = False,
    ) -> bool:
        """Save preset to Firestore and/or local storage.

        Args:
            preset_id: Unique preset identifier (e.g., "reverb_arena_tail")
            preset_data: Complete preset metadata + parameter values
            local_only: If True, only save locally (for user presets before sync)

        Returns:
            True if saved successfully
        """
        from server.config.app_config import get_debug_settings
        dbg_cfg = get_debug_settings().get("firestore", False)
        dbg_env = str(os.getenv("FB_DEBUG_FIRESTORE", "")).lower() in ("1","true","yes","on")
        dbg = bool(dbg_cfg or dbg_env)

        # Only save locally for user presets (not stock)
        preset_type = preset_data.get("preset_type", "stock")
        is_user_preset = preset_type == "user" or "_user_" in preset_id

        local_ok = True
        if is_user_preset:
            local_ok = self._save_preset_local(preset_id, preset_data)

        if local_only:
            return local_ok

        if not self._enabled or not self._client:
            return local_ok

        # Save to Firestore
        try:
            doc = self._client.collection("presets").document(preset_id)
            doc.set(preset_data, merge=True)
            return True
        except Exception as e:
            return local_ok  # At least local succeeded for user presets

    def get_preset(self, preset_id: str) -> Optional[Dict[str, Any]]:
        """Get preset from Firestore or local cache (user presets only).

        Args:
            preset_id: Preset identifier

        Returns:
            Preset data or None
        """
        # Try Firestore first
        if self._enabled and self._client:
            try:
                doc = self._client.collection("presets").document(preset_id).get()
                if doc.exists:
                    return doc.to_dict()
            except Exception:
                pass

        # Fall back to local ONLY for user presets
        is_user_preset = "_user_" in preset_id
        if is_user_preset:
            return self._get_preset_local(preset_id)

        return None

    def list_presets(
        self,
        device_type: Optional[str] = None,
        structure_signature: Optional[str] = None,
        preset_type: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """List presets with optional filtering.

        Args:
            device_type: Filter by device type (reverb, delay, etc.)
            structure_signature: Filter by structure signature
            preset_type: Filter by preset type (stock, user)

        Returns:
            List of preset metadata (id + summary fields)
        """
        presets = []

        # Try Firestore first
        if self._enabled and self._client:
            try:
                query = self._client.collection("presets")
                # Prefer keyword 'filter' to avoid deprecation warning
                try:
                    from google.cloud.firestore_v1.base_query import FieldFilter  # type: ignore
                    def _where(q, field, op, val):
                        return q.where(filter=FieldFilter(field, op, val))
                except Exception:
                    def _where(q, field, op, val):
                        return q.where(field, op, val)

                if device_type:
                    query = _where(query, "category", "==", device_type)
                if structure_signature:
                    query = _where(query, "structure_signature", "==", structure_signature)
                if preset_type:
                    query = _where(query, "preset_type", "==", preset_type)

                for doc in query.stream():
                    data = doc.to_dict()
                    presets.append({
                        "id": doc.id,
                        "name": data.get("name"),
                        "device_name": data.get("device_name"),
                        "device_type": data.get("category"),
                        "subcategory": data.get("subcategory"),
                        "preset_type": data.get("preset_type"),
                        "structure_signature": data.get("structure_signature"),
                    })
                return presets
            except Exception:
                pass

        # Fall back to local ONLY for user presets
        if preset_type == "user":
            return self._list_presets_local(device_type, structure_signature, preset_type)

        return []

    def delete_preset(self, preset_id: str) -> bool:
        """Delete preset from Firestore and local storage.

        Args:
            preset_id: Preset identifier

        Returns:
            True if deleted successfully
        """
        local_ok = self._delete_preset_local(preset_id)

        if not self._enabled or not self._client:
            return local_ok

        try:
            self._client.collection("presets").document(preset_id).delete()
            return True
        except Exception:
            return local_ok

    # ---------- Local Preset Storage ----------

    def _preset_local_path(self, preset_id: str) -> Optional[Any]:
        """Get local path for preset file.

        Organizes presets by device type and preset type:
        ~/.fadebender/param_maps/presets/reverb/stock/arena_tail.json
        ~/.fadebender/param_maps/presets/reverb/user/my_custom.json
        """
        import pathlib
        if not self._local_dir:
            return None

        # Extract device type and preset type from ID or use defaults
        # Format: devicetype_presetname or just presetname
        parts = preset_id.split("_", 1)
        if len(parts) == 2:
            device_type, preset_name = parts
        else:
            device_type = "unknown"
            preset_name = preset_id

        # Assume stock unless user ID present in preset_id
        preset_type = "user" if "_user_" in preset_id else "stock"

        preset_dir = pathlib.Path(self._local_dir) / "presets" / device_type / preset_type
        preset_dir.mkdir(parents=True, exist_ok=True)

        return preset_dir / f"{preset_name}.json"

    def _save_preset_local(self, preset_id: str, preset_data: Dict[str, Any]) -> bool:
        """Save preset to local filesystem."""
        try:
            import json
            path = self._preset_local_path(preset_id)
            if not path:
                return False

            with open(path, "w", encoding="utf-8") as f:
                json.dump(preset_data, f, indent=2)
            return True
        except Exception:
            return False

    def _get_preset_local(self, preset_id: str) -> Optional[Dict[str, Any]]:
        """Get preset from local filesystem."""
        try:
            import json
            path = self._preset_local_path(preset_id)
            if not path or not path.exists():
                return None

            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None

    def _list_presets_local(
        self,
        device_type: Optional[str] = None,
        structure_signature: Optional[str] = None,
        preset_type: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """List presets from local filesystem."""
        import pathlib
        import json

        if not self._local_dir:
            return []

        presets = []
        preset_dir = pathlib.Path(self._local_dir) / "presets"

        if not preset_dir.exists():
            return []

        # Walk through all preset files
        for preset_file in preset_dir.rglob("*.json"):
            try:
                with open(preset_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                # Apply filters
                if device_type and data.get("category") != device_type:
                    continue
                if structure_signature and data.get("structure_signature") != structure_signature:
                    continue
                if preset_type and data.get("preset_type") != preset_type:
                    continue

                # Extract ID from path
                device_t = preset_file.parent.parent.name
                preset_name = preset_file.stem
                preset_id = f"{device_t}_{preset_name}"

                presets.append({
                    "id": preset_id,
                    "name": data.get("name"),
                    "device_name": data.get("device_name"),
                    "device_type": data.get("category"),
                    "subcategory": data.get("subcategory"),
                    "preset_type": data.get("preset_type"),
                    "structure_signature": data.get("structure_signature"),
                })
            except Exception:
                continue

        return presets

    def _delete_preset_local(self, preset_id: str) -> bool:
        """Delete preset from local filesystem."""
        try:
            path = self._preset_local_path(preset_id)
            if path and path.exists():
                path.unlink()
                return True
            return False
        except Exception:
            return False

    # ---------- Mixer Parameter Mappings ----------

    def get_mixer_param_names(self) -> Optional[List[str]]:
        """Get list of all mixer parameter names from Firestore.

        Queries mixer_mappings collection and returns all document IDs
        (which are the parameter names: "volume", "pan", "mute", etc.)

        Returns:
            List of mixer parameter names or None if not available
        """
        if not self._enabled or not self._client:
            return None

        try:
            # List all documents in mixer_mappings collection
            docs = self._client.collection("mixer_mappings").stream()
            param_names = [doc.id for doc in docs]
            return param_names if param_names else None

        except Exception:
            return None

    def get_mixer_param_mapping(self, param_name: str) -> Optional[Dict[str, Any]]:
        """Get mixer parameter mapping (e.g., pan, volume) from Firestore.

        Args:
            param_name: Parameter name ("pan", "volume", etc.)

        Returns:
            Mixer parameter mapping with display_value_presets or None
        """
        if not self._enabled or not self._client:
            return None

        try:
            doc = self._client.collection("mixer_mappings").document(param_name).get()
            if not doc.exists:
                return None
            return doc.to_dict()
        except Exception as e:
            return None

    def save_mixer_param_mapping(self, param_name: str, mapping_data: Dict[str, Any]) -> bool:
        """Save mixer parameter mapping to Firestore.

        Args:
            param_name: Parameter name ("pan", "volume", etc.)
            mapping_data: Mapping metadata including display_value_presets

        Returns:
            True if saved successfully
        """
        if not self._enabled or not self._client:
            return False

        try:
            doc = self._client.collection("mixer_mappings").document(param_name)
            doc.set(mapping_data, merge=True)
            return True
        except Exception as e:
            return False

    def get_mixer_channel_mapping(self, entity_type: str) -> Optional[Dict[str, Any]]:
        """Get consolidated mixer channel mapping (track/return/master) from Firestore.

        Args:
            entity_type: Entity type ("track", "return", or "master")

        Returns:
            Mixer channel mapping with params_meta or None
        """
        if not self._enabled or not self._client:
            return None

        try:
            doc_id = f"{entity_type}_channel"
            doc = self._client.collection("mixer_mappings").document(doc_id).get()
            if not doc.exists:
                # Fall back to old structure
                return None
            return doc.to_dict()
        except Exception as e:
            return None
