"""
Parse Index Builder

Builds a device+parameter vocabulary index from:
1. Live set snapshot (what devices are currently loaded)
2. Firestore parameter names for each device

The parse index enables fast, device-context-aware parsing without
having to query Firestore on every parse operation.
"""

from __future__ import annotations

import math
import time
from typing import Any, Dict, List, Optional, Set
from datetime import datetime

from google.cloud.firestore_v1.base_query import FieldFilter

from server.services.mapping_store import MappingStore
from server.config.app_config import get_app_config


class ParseIndexBuilder:
    """Builds and maintains the parse index for device-context-aware parsing."""

    def __init__(self, store: Optional[MappingStore] = None):
        """Initialize builder with optional MappingStore instance."""
        self.store = store or MappingStore()

    def build_from_live_set(self, live_set_devices: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Build parse index from Live set device list.

        Args:
            live_set_devices: List of device dicts with 'name', 'device_type' (optional)
                Example: [{"name": "Reverb", "device_type": "reverb", "ordinals": 2}, ...]

        Returns:
            Parse index dict ready for serialization/use by parser
        """

        print(f"Building parse index from {len(live_set_devices)} devices in Live set...")
        start_time = time.time()

        # Collect unique device names (de-duplicate if same device appears multiple times)
        unique_devices: Dict[str, Dict[str, Any]] = {}

        for device in live_set_devices:
            name = device.get("name")
            if not name:
                continue

            if name not in unique_devices:
                unique_devices[name] = {
                    "name": name,
                    "aliases": [name.lower()],  # Start with lowercase version
                    "ordinals": device.get("ordinals", 1),  # How many instances in set
                    "device_type": device.get("device_type"),
                }
            else:
                # Increment ordinal count
                unique_devices[name]["ordinals"] += device.get("ordinals", 1)

        print(f"  Found {len(unique_devices)} unique device types")

        # Query Firestore for parameter names using batch queries
        print()
        print("Loading device mappings from Firestore...")

        device_names = list(unique_devices.keys())
        batch_start = time.time()
        device_mappings = self._load_devices_batch(device_names)
        batch_elapsed = time.time() - batch_start

        print(f"  Batch loading completed in {batch_elapsed*1000:.1f}ms")
        print(f"  Average: {batch_elapsed*1000/len(device_names):.1f}ms per device")
        print()

        # Build params_by_device from batch results
        params_by_device: Dict[str, Dict[str, Any]] = {}

        for device_name in device_names:
            mapping = device_mappings.get(device_name)

            if mapping and mapping.get("param_names"):
                param_names = mapping["param_names"]
                device_type = mapping.get("device_type", "unknown")

                params_by_device[device_name] = {
                    "params": param_names,
                    "device_type": device_type,
                    "aliases": self._build_param_aliases(device_name, param_names),
                }
                print(f"  ✓ {device_name:30s} → {len(param_names):3d} params ({device_type})")
            else:
                # No params found - will fall back to LLM at parse time
                params_by_device[device_name] = {
                    "params": [],
                    "device_type": "unknown",
                    "aliases": {},
                }
                print(f"  ✗ {device_name:30s} → no params found")

        # Build devices_in_set list
        devices_in_set = [
            {
                "name": info["name"],
                "aliases": info["aliases"],
                "ordinals": info.get("ordinals", 1),
            }
            for info in unique_devices.values()
        ]

        # Get mixer parameters from config
        mixer_params = self._get_mixer_params()

        # Build typo map (could be extended with learning/history)
        typo_map = self._get_typo_map()

        # Build device_type_index (device_type → [device_names])
        device_type_index = {}
        for dev_name, spec in params_by_device.items():
            dev_type = spec.get("device_type", "unknown")
            if dev_type not in device_type_index:
                device_type_index[dev_type] = []
            device_type_index[dev_type].append(dev_name)

        # Build param_to_device_types index (param_name → [device_types])
        param_to_device_types = {}
        for dev_name, spec in params_by_device.items():
            dev_type = spec.get("device_type", "unknown")
            for param_name in spec.get("params", []):
                if param_name not in param_to_device_types:
                    param_to_device_types[param_name] = []
                if dev_type not in param_to_device_types[param_name]:
                    param_to_device_types[param_name].append(dev_type)

        # Assemble final index
        parse_index = {
            "version": f"pi-{datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S')}Z",
            "devices_in_set": devices_in_set,
            "params_by_device": params_by_device,
            "device_type_index": device_type_index,
            "param_to_device_types": param_to_device_types,
            "mixer_params": mixer_params,
            "typo_map": typo_map,
        }

        total_time = time.time() - start_time

        print()
        print(f"Parse index built in {total_time*1000:.1f}ms")
        print(f"  Total devices: {len(devices_in_set)}")
        print(f"  Total params: {sum(len(p['params']) for p in params_by_device.values())}")

        return parse_index

    def _load_devices_batch(self, device_names: List[str]) -> Dict[str, Dict[str, Any]]:
        """Load device mappings using batch queries.

        Args:
            device_names: List of device names from snapshot

        Returns:
            Dict mapping device_name to {device_type, param_names, signature}
        """
        if not self.store.enabled or not self.store._client:
            return {}

        # Step 1: Batch query presets to get signatures
        name_to_sig = self._batch_query_presets(device_names)

        # Step 2: Extract unique signatures
        unique_sigs = set(name_to_sig.values())

        # Step 3: Batch query device_mappings by signatures
        sig_to_mapping = self._batch_query_device_mappings(list(unique_sigs))

        # Step 4: Build final results
        results = {}
        for device_name in device_names:
            sig = name_to_sig.get(device_name)
            if not sig:
                continue

            mapping = sig_to_mapping.get(sig)
            if not mapping:
                continue

            results[device_name] = {
                "device_type": mapping.get("device_type", "unknown"),
                "param_names": mapping.get("param_names", []),
                "signature": sig
            }

        return results

    def _batch_query_presets(self, device_names: List[str]) -> Dict[str, str]:
        """Query presets in batches to get device_name → signature mapping.

        Firestore IN queries support max 10 items, so we batch accordingly.
        """
        name_to_sig = {}
        batch_size = 10
        num_batches = math.ceil(len(device_names) / batch_size)

        for i in range(num_batches):
            batch = device_names[i * batch_size:(i + 1) * batch_size]

            query = self.store._client.collection("presets").where(
                filter=FieldFilter("device_name", "in", batch)
            )

            docs = list(query.stream())

            # Extract signatures
            for doc in docs:
                data = doc.to_dict()
                device_name = data.get("device_name")
                signature = data.get("structure_signature")

                if device_name and signature:
                    name_to_sig[device_name] = signature

        return name_to_sig

    def _batch_query_device_mappings(self, signatures: List[str]) -> Dict[str, Dict]:
        """Query device_mappings by document IDs (signatures).

        Uses Firestore's .get() for direct document access by ID.
        """
        sig_to_mapping = {}

        for sig in signatures:
            doc = self.store._client.collection("device_mappings").document(sig).get()

            if doc.exists:
                mapping = doc.to_dict()
                sig_to_mapping[sig] = mapping

        return sig_to_mapping

    def _build_param_aliases(self, device_name: str, param_names: List[str]) -> Dict[str, List[str]]:
        """Build parameter aliases from natural variations only (NO global config aliases).

        This is for device-context-aware parsing where we want to ELIMINATE parameter aliases
        and let device context disambiguate parameters instead.

        Args:
            device_name: Name of device
            param_names: List of canonical parameter names

        Returns:
            Dict mapping canonical name to list of natural variations (hyphen/space only)
        """
        aliases: Dict[str, List[str]] = {}

        # NO global aliases from config - that's what we're trying to eliminate!
        # NO hardcoded semantic aliases (mix→dry/wet, width→stereo image)
        # ONLY natural text variations for the same parameter name

        for param_name in param_names:
            param_aliases: Set[str] = set()

            # Add hyphen/space variations only (same semantic meaning)
            # "Low-Cut" → "Low Cut", "LowCut"
            if "-" in param_name:
                param_aliases.add(param_name.replace("-", " "))
                param_aliases.add(param_name.replace("-", ""))
            if " " in param_name:
                param_aliases.add(param_name.replace(" ", "-"))
                param_aliases.add(param_name.replace(" ", ""))

            if param_aliases:
                aliases[param_name] = sorted(list(param_aliases))

        return aliases

    def _get_mixer_params(self) -> List[str]:
        """Get list of mixer-level parameters from config.

        Returns:
            List of mixer parameter names
        """
        return [
            "volume",
            "pan",
            "mute",
            "solo",
            "send a",
            "send b",
            "send c",
            "send d",
            "send e",
        ]

    def _get_typo_map(self) -> Dict[str, str]:
        """Get typo correction map.

        Could be extended with learned typos from history.

        Returns:
            Dict mapping typo to correct spelling
        """
        return {
            "feedbakc": "feedback",
            "streo": "stereo",
            "volum": "volume",
            "volumz": "volume",
            "compresser": "compressor",
            "decai": "decay",
        }


def build_index_from_mock_liveset(device_names: List[str]) -> Dict[str, Any]:
    """Helper to build parse index from simple device name list.

    Args:
        device_names: List of device names (e.g., ["Reverb", "Delay", "Amp"])

    Returns:
        Parse index dict
    """
    builder = ParseIndexBuilder()

    # Convert simple names to device dicts
    devices = [{"name": name, "ordinals": 1} for name in device_names]

    return builder.build_from_live_set(devices)
