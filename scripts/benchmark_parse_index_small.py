#!/usr/bin/env python3
"""
Benchmark param loading for small device set (reverb, delay, amp, compressor).
Tests both sequential and batch loading approaches.
"""

import sys
import time
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from server.services.mapping_store import MappingStore


def benchmark_sequential_loading():
    """Benchmark loading 4 devices sequentially."""

    devices = ["Reverb", "Delay", "Amp", "Compressor"]

    print("=" * 80)
    print("Sequential Loading (4 devices)")
    print("=" * 80)

    store = MappingStore()

    if not store.enabled:
        print("❌ Firestore not enabled")
        return None

    print(f"✓ Connected to Firestore ({store.backend})")
    print()

    start_total = time.time()
    results = []

    for device_name in devices:
        start = time.time()
        param_names = store.get_device_param_names(device_name=device_name)
        elapsed_ms = (time.time() - start) * 1000

        if param_names:
            print(f"  ✓ {device_name:15s} → {len(param_names):3d} params in {elapsed_ms:6.1f}ms")
            results.append({
                "device": device_name,
                "params": param_names,
                "time_ms": elapsed_ms
            })
        else:
            print(f"  ✗ {device_name:15s} → NOT FOUND ({elapsed_ms:6.1f}ms)")
            results.append({
                "device": device_name,
                "params": [],
                "time_ms": elapsed_ms
            })

    total_ms = (time.time() - start_total) * 1000

    print()
    print(f"Total: {total_ms:.1f}ms")

    if results:
        avg_ms = sum(r["time_ms"] for r in results) / len(results)
        print(f"Average per device: {avg_ms:.1f}ms")

        # Extrapolate to 20-25 devices
        for count in [20, 25]:
            extrapolated = avg_ms * count
            print(f"Extrapolated for {count} devices: {extrapolated:.0f}ms ({extrapolated/1000:.2f}s)")

    return results


def benchmark_batch_loading():
    """Test batch loading all device_mappings at once."""

    devices = ["Reverb", "Delay", "Amp", "Compressor"]

    print()
    print("=" * 80)
    print("Batch Loading (single query for all param_names)")
    print("=" * 80)

    store = MappingStore()

    if not store.enabled or not store._client:
        print("❌ Firestore not enabled")
        return None

    from google.cloud.firestore_v1.base_query import FieldFilter

    start = time.time()

    # Query all device_mappings where device_name is in our list
    query = store._client.collection("device_mappings").where(
        filter=FieldFilter("device_name", "in", devices)
    )

    docs = list(query.stream())
    elapsed_ms = (time.time() - start) * 1000

    print(f"  Queried {len(docs)} devices in {elapsed_ms:.1f}ms")
    print()

    results = {}
    for doc in docs:
        data = doc.to_dict()
        device_name = data.get("device_name")
        param_names = data.get("param_names", [])

        if device_name and param_names:
            results[device_name] = param_names
            print(f"  ✓ {device_name:15s} → {len(param_names):3d} params")

    # Check which devices were missing
    for device in devices:
        if device not in results:
            print(f"  ✗ {device:15s} → NOT FOUND")

    print()
    print(f"Batch query time: {elapsed_ms:.1f}ms")
    print(f"Time per device: {elapsed_ms/len(devices):.1f}ms")

    # Extrapolate
    for count in [20, 25]:
        # Firestore IN queries support up to 10 items, so we'd need ceil(count/10) queries
        import math
        num_queries = math.ceil(count / 10)
        extrapolated = elapsed_ms * num_queries
        print(f"Extrapolated for {count} devices ({num_queries} batches): {extrapolated:.0f}ms")

    return results


def test_bulk_download():
    """Test downloading ALL device mappings and caching locally."""

    print()
    print("=" * 80)
    print("Bulk Download Test (all device_mappings)")
    print("=" * 80)

    store = MappingStore()

    if not store.enabled or not store._client:
        print("❌ Firestore not enabled")
        return

    start = time.time()

    # Get all device_mappings
    all_docs = list(store._client.collection("device_mappings").stream())

    elapsed_ms = (time.time() - start) * 1000

    print(f"  Downloaded {len(all_docs)} device mappings in {elapsed_ms:.1f}ms")
    print()

    # Build lookup dict
    param_lookup = {}
    for doc in all_docs:
        data = doc.to_dict()
        device_name = data.get("device_name")
        param_names = data.get("param_names", [])

        if device_name and param_names:
            param_lookup[device_name] = param_names

    print(f"  Built lookup for {len(param_lookup)} devices")

    # Test lookup speed
    test_devices = ["Reverb", "Delay", "Amp", "Compressor"]

    lookup_start = time.time()
    for device in test_devices:
        params = param_lookup.get(device, [])
    lookup_ms = (time.time() - lookup_start) * 1000

    print(f"  In-memory lookup for 4 devices: {lookup_ms:.4f}ms (instant!)")
    print()

    # Save to JSON
    output_path = Path(__file__).parent.parent / "server" / "services" / "parse_index" / "device_params_cache.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    cache_data = {
        "version": "v1",
        "downloaded_at": time.time(),
        "param_names": param_lookup
    }

    with open(output_path, "w") as f:
        json.dump(cache_data, f, indent=2)

    file_size = output_path.stat().st_size
    print(f"  Saved cache to: {output_path}")
    print(f"  File size: {file_size:,} bytes ({file_size/1024:.1f} KB)")
    print()
    print("=" * 80)
    print("Recommendation")
    print("=" * 80)
    print("✅ BULK DOWNLOAD approach is best:")
    print(f"   • One-time download: {elapsed_ms:.0f}ms")
    print(f"   • Subsequent lookups: <1ms (instant)")
    print(f"   • Cache size: {file_size/1024:.1f} KB (tiny!)")
    print()
    print("   Strategy:")
    print("   1. Download all device param_names on first session")
    print("   2. Cache locally (JSON file or in-memory)")
    print("   3. Refresh periodically (e.g., daily or on-demand)")
    print()


if __name__ == "__main__":
    sequential_results = benchmark_sequential_loading()
    batch_results = benchmark_batch_loading()
    test_bulk_download()
