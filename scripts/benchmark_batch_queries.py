#!/usr/bin/env python3
"""
Benchmark batch query approach for parse index loading.
Compares sequential vs batch loading performance.
"""

import os
import sys
import time
import math
from pathlib import Path
from typing import Dict, List, Set

sys.path.insert(0, str(Path(__file__).parent.parent))

# Ensure we're using dev-display-value database
os.environ['FIRESTORE_DATABASE_ID'] = 'dev-display-value'

from google.cloud.firestore_v1.base_query import FieldFilter


class BatchParseIndexLoader:
    """Efficiently loads device mappings using batch queries."""

    def __init__(self):
        from server.services.mapping_store import MappingStore
        self.store = MappingStore()

        if not self.store.enabled or not self.store._client:
            raise RuntimeError("Firestore not enabled")

    def load_devices_batch(self, device_names: List[str]) -> Dict[str, Dict]:
        """Load device mappings using batch queries.

        Args:
            device_names: List of device names from snapshot

        Returns:
            Dict mapping device_name to {device_type, param_names, signature}
        """

        print(f"Loading {len(device_names)} devices using BATCH QUERIES...")
        print()

        # Step 1: Batch query presets to get signatures
        print("Step 1: Query presets for structure_signatures")
        print("-" * 60)

        start = time.time()
        name_to_sig = self._batch_query_presets(device_names)
        preset_time = (time.time() - start) * 1000

        print(f"  → Found signatures for {len(name_to_sig)}/{len(device_names)} devices")
        print(f"  → Time: {preset_time:.1f}ms")
        print()

        # Step 2: Extract unique signatures
        unique_sigs = set(name_to_sig.values())
        print(f"Step 2: Found {len(unique_sigs)} unique signatures")
        print()

        # Step 3: Batch query device_mappings by signatures
        print("Step 3: Query device_mappings for param_names")
        print("-" * 60)

        start = time.time()
        sig_to_mapping = self._batch_query_device_mappings(list(unique_sigs))
        mapping_time = (time.time() - start) * 1000

        print(f"  → Loaded mappings for {len(sig_to_mapping)}/{len(unique_sigs)} signatures")
        print(f"  → Time: {mapping_time:.1f}ms")
        print()

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

        total_time = preset_time + mapping_time

        print("-" * 60)
        print(f"Total batch loading time: {total_time:.1f}ms")
        print(f"Average per device: {total_time/len(device_names):.1f}ms")
        print()

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

            print(f"  Batch {i+1}/{num_batches}: Querying {len(batch)} devices...", end="")

            start = time.time()

            query = self.store._client.collection("presets").where(
                filter=FieldFilter("device_name", "in", batch)
            )

            docs = list(query.stream())
            elapsed = (time.time() - start) * 1000

            print(f" {elapsed:.0f}ms → {len(docs)} found")

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

        # Firestore allows batch gets, but for simplicity we'll use direct document access
        # In production, could use batch API for further optimization

        print(f"  Querying {len(signatures)} device_mappings...", end="")

        start = time.time()

        for sig in signatures:
            doc = self.store._client.collection("device_mappings").document(sig).get()

            if doc.exists:
                mapping = doc.to_dict()
                sig_to_mapping[sig] = mapping

        elapsed = (time.time() - start) * 1000

        print(f" {elapsed:.0f}ms")

        return sig_to_mapping


def compare_sequential_vs_batch():
    """Compare sequential vs batch loading performance."""

    # Test devices (with correct capitalization from snapshot)
    test_devices = [
        "Reverb",
        "4th Bandpass",
        "Screamer",
        "8DotBall",  # Note: capital D and B
        "Ambience",
        "Bass Roundup",
        "Discrete",
        "Mix Gel",
        "8th Groove",
        "Chopped Delay"
    ]

    print("=" * 80)
    print("Sequential vs Batch Query Comparison")
    print("=" * 80)
    print()

    # BATCH APPROACH
    print("APPROACH: BATCH QUERIES")
    print("=" * 80)

    loader = BatchParseIndexLoader()
    batch_results = loader.load_devices_batch(test_devices)

    print()
    print("Loaded devices:")
    for name, info in batch_results.items():
        print(f"  ✓ {name:30s} → {len(info['param_names']):3d} params ({info['device_type']})")

    missing = set(test_devices) - set(batch_results.keys())
    if missing:
        print()
        print("Missing devices:")
        for name in missing:
            print(f"  ✗ {name}")

    print()
    print("=" * 80)
    print("Extrapolation for Larger Sets")
    print("=" * 80)

    # The batch approach scales much better
    # With batching:
    # - Preset queries: ceil(N/10) queries
    # - Device mapping queries: M queries (where M = unique signatures)

    for num_devices in [20, 30, 50]:
        # Assume 70% unique signatures (realistic for diverse Live set)
        unique_sigs = int(num_devices * 0.7)

        # Preset queries: batches of 10
        preset_batches = math.ceil(num_devices / 10)
        preset_time = preset_batches * 700  # ~700ms per batch (observed)

        # Device mapping queries: all unique sigs
        # Could optimize with batch get, but sequential doc.get is ~50ms per doc
        mapping_time = unique_sigs * 50

        total_time = preset_time + mapping_time

        print(f"\n{num_devices} devices ({unique_sigs} unique signatures):")
        print(f"  Preset queries: {preset_batches} batches × 700ms = {preset_time}ms")
        print(f"  Mapping queries: {unique_sigs} docs × 50ms = {mapping_time}ms")
        print(f"  Total: {total_time}ms ({total_time/1000:.2f}s)")
        print(f"  Avg per device: {total_time/num_devices:.0f}ms")


if __name__ == "__main__":
    compare_sequential_vs_batch()
