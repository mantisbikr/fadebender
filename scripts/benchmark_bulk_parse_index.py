#!/usr/bin/env python3
"""
Benchmark bulk parse index building with correct lookup chain:
  device_name → presets → structure_signature → device_mappings → param_names
"""

import sys
import time
from pathlib import Path
from typing import Dict, List, Optional

sys.path.insert(0, str(Path(__file__).parent.parent))

from google.cloud.firestore_v1.base_query import FieldFilter


class ParseIndexBulkLoader:
    """Efficiently loads device mappings with caching."""

    def __init__(self):
        from server.services.mapping_store import MappingStore
        self.store = MappingStore()

        if not self.store.enabled or not self.store._client:
            raise RuntimeError("Firestore not enabled")

        self._signature_cache = {}      # signature → device mapping
        self._name_to_sig_cache = {}    # device_name → signature

    def load_devices(self, device_names: List[str]) -> Dict[str, Dict]:
        """Load device mappings for multiple devices with caching.

        Args:
            device_names: List of device names from snapshot

        Returns:
            Dict mapping device_name to {device_type, param_names, signature}
        """

        results = {}

        for device_name in device_names:
            mapping = self._get_device_mapping(device_name)

            if mapping:
                results[device_name] = {
                    "device_type": mapping.get("device_type", "unknown"),
                    "param_names": mapping.get("param_names", []),
                    "signature": mapping.get("signature")
                }

        return results

    def _get_device_mapping(self, device_name: str) -> Optional[Dict]:
        """Get device mapping with two-level caching."""

        # Check name→signature cache
        if device_name in self._name_to_sig_cache:
            sig = self._name_to_sig_cache[device_name]
            print(f"  ↻ {device_name:30s} → signature cached")

            # Check signature→mapping cache
            if sig in self._signature_cache:
                print(f"    → mapping cached")
                return self._signature_cache[sig]

        # Step 1: Query presets for signature
        print(f"  ⚡ {device_name:30s} → querying presets...", end="")
        start = time.time()

        preset_query = self.store._client.collection("presets").where(
            filter=FieldFilter("device_name", "==", device_name)
        ).limit(1)

        preset_docs = list(preset_query.stream())
        preset_time = (time.time() - start) * 1000

        if not preset_docs:
            print(f" NOT FOUND ({preset_time:.0f}ms)")
            return None

        signature = preset_docs[0].to_dict().get("structure_signature")
        print(f" {preset_time:.0f}ms → sig: {signature[:8]}...")

        # Cache device_name → signature
        self._name_to_sig_cache[device_name] = signature

        # Check if we already have this signature's mapping
        if signature in self._signature_cache:
            print(f"    → mapping already loaded for this signature")
            return self._signature_cache[signature]

        # Step 2: Query device_mappings by signature
        print(f"    → querying device_mappings...", end="")
        start = time.time()

        mapping_doc = self.store._client.collection("device_mappings").document(signature).get()
        mapping_time = (time.time() - start) * 1000

        if not mapping_doc.exists:
            print(f" NOT FOUND ({mapping_time:.0f}ms)")
            return None

        mapping = mapping_doc.to_dict()
        mapping["signature"] = signature  # Add signature to mapping

        param_count = len(mapping.get("param_names", []))
        device_type = mapping.get("device_type", "unknown")

        print(f" {mapping_time:.0f}ms → {param_count} params, type: {device_type}")

        # Cache signature → mapping
        self._signature_cache[signature] = mapping

        return mapping


def benchmark_test_set(device_names: List[str], set_name: str):
    """Benchmark loading a set of devices."""

    print()
    print("=" * 80)
    print(f"{set_name}")
    print("=" * 80)
    print()

    loader = ParseIndexBulkLoader()

    start_total = time.time()
    results = loader.load_devices(device_names)
    total_time = (time.time() - start_total) * 1000

    print()
    print("-" * 80)
    print(f"Summary for {set_name}:")
    print(f"  Total time: {total_time:.1f}ms")
    print(f"  Devices loaded: {len(results)}/{len(device_names)}")
    print(f"  Average per device: {total_time/len(device_names):.1f}ms")
    print()

    # Show what was loaded
    print("Loaded devices:")
    for name, info in results.items():
        print(f"  ✓ {name:30s} → {len(info['param_names']):3d} params ({info['device_type']})")

    # Show what was missing
    missing = set(device_names) - set(results.keys())
    if missing:
        print()
        print("Missing devices:")
        for name in missing:
            print(f"  ✗ {name}")

    return results, total_time


def main():
    print("=" * 80)
    print("Parse Index Bulk Loading Benchmark")
    print("=" * 80)

    # Test Set 1: Known devices
    set1 = ["Reverb", "4th Bandpass", "Screamer", "8dotball"]

    # Test Set 2: More devices (includes some duplicates and new ones)
    set2 = [
        "Ambience",
        "Bass Roundup",
        "Discrete",
        "Loud Kneeless",
        "Mix Gel",
        "8th Groove",
        "Chopped Delay"
    ]

    # Test Set 1
    results1, time1 = benchmark_test_set(set1, "Test Set 1: Basic Devices")

    # Test Set 2 (should show caching benefits if any devices overlap)
    results2, time2 = benchmark_test_set(set2, "Test Set 2: Additional Devices")

    # Combined test to show caching across sets
    print()
    print("=" * 80)
    print("Test Set 3: Reload All (should show caching)")
    print("=" * 80)
    print()

    all_devices = set1 + set2

    loader = ParseIndexBulkLoader()
    # Pre-load set 1
    print("Pre-loading Set 1...")
    loader.load_devices(set1)

    print()
    print("Now loading combined set (should use cache for Set 1 devices)...")
    print()

    start = time.time()
    results_combined = loader.load_devices(all_devices)
    time_combined = (time.time() - start) * 1000

    print()
    print("-" * 80)
    print(f"Summary for Combined Test:")
    print(f"  Total time: {time_combined:.1f}ms")
    print(f"  Devices loaded: {len(results_combined)}/{len(all_devices)}")
    print(f"  Average per device: {time_combined/len(all_devices):.1f}ms")
    print()

    # Final summary
    print("=" * 80)
    print("Performance Summary")
    print("=" * 80)
    print(f"Set 1 ({len(set1)} devices): {time1:.1f}ms ({time1/len(set1):.1f}ms avg)")
    print(f"Set 2 ({len(set2)} devices): {time2:.1f}ms ({time2/len(set2):.1f}ms avg)")
    print(f"Combined with caching ({len(all_devices)} devices): {time_combined:.1f}ms ({time_combined/len(all_devices):.1f}ms avg)")
    print()

    total_params = sum(len(r["param_names"]) for r in results_combined.values())
    print(f"Total parameters loaded: {total_params}")
    print(f"Unique signatures cached: {len(loader._signature_cache)}")
    print(f"Device name→signature mappings: {len(loader._name_to_sig_cache)}")


if __name__ == "__main__":
    main()
