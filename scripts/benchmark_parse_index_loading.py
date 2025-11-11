#!/usr/bin/env python3
"""
Benchmark script to measure Firestore lazy loading performance for parse index.

Tests loading parameter names for 25-30 unique device types to simulate
a realistic Live set and measure if lazy loading is acceptable (<500ms total).
"""

import sys
import time
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from server.services.mapping_store import MappingStore


def benchmark_device_param_loading():
    """Benchmark parameter name loading for 25-30 unique devices."""

    print("=" * 80)
    print("Parse Index Firestore Loading Benchmark")
    print("=" * 80)
    print()

    # Simulate a user's Live set with diverse devices
    test_devices = [
        # Audio Effects
        "Reverb",
        "Echo",
        "Delay",
        "Grain Delay",
        "Filter Delay",

        # Dynamics
        "Compressor",
        "Glue Compressor",
        "Multiband Dynamics",
        "Limiter",

        # EQ
        "EQ Eight",
        "EQ Three",
        "Channel EQ",

        # Distortion/Saturation
        "Saturator",
        "Overdrive",
        "Amp",
        "Cabinet",
        "Pedal",

        # Modulation
        "Chorus",
        "Phaser",
        "Flanger",
        "Auto Pan",
        "Auto Filter",

        # Utility
        "Utility",
        "Spectrum",

        # Instruments (if present)
        "Operator",
        "Analog",
        "Sampler",
        "Wavetable",

        # Special devices/racks
        "Vinyl Distortion",
        "Erosion",
    ]

    print(f"Testing {len(test_devices)} unique device types...")
    print()

    # Initialize store
    store = MappingStore()

    if not store.enabled:
        print("❌ FAILED: Firestore not enabled")
        print("Check FIRESTORE_PROJECT_ID and credentials")
        return

    print(f"✓ Firestore connection: {store.backend}")
    print()

    # Test 1: Cold start - load all devices sequentially
    print("Test 1: Cold Start (Sequential Loading)")
    print("-" * 80)

    cold_start = time.time()
    results = []

    for device_name in test_devices:
        start = time.time()
        param_names = store.get_device_param_names(device_name=device_name)
        elapsed = (time.time() - start) * 1000  # ms

        if param_names:
            results.append({
                "device": device_name,
                "params": len(param_names),
                "time_ms": elapsed
            })
            status = "✓"
        else:
            results.append({
                "device": device_name,
                "params": 0,
                "time_ms": elapsed
            })
            status = "✗"

        print(f"  {status} {device_name:30s} → {len(param_names or []):3d} params in {elapsed:6.1f}ms")

    cold_total = (time.time() - cold_start) * 1000

    print()
    print(f"Cold Start Total: {cold_total:.1f}ms")
    print()

    # Test 2: Warm cache - reload same devices
    print("Test 2: Warm Cache (Re-loading)")
    print("-" * 80)

    warm_start = time.time()
    warm_results = []

    for device_name in test_devices[:10]:  # Test subset for warm cache
        start = time.time()
        param_names = store.get_device_param_names(device_name=device_name)
        elapsed = (time.time() - start) * 1000

        warm_results.append(elapsed)
        print(f"  ✓ {device_name:30s} → {elapsed:6.1f}ms")

    warm_total = (time.time() - warm_start) * 1000
    warm_avg = sum(warm_results) / len(warm_results) if warm_results else 0

    print()
    print(f"Warm Cache Total: {warm_total:.1f}ms (avg: {warm_avg:.1f}ms per device)")
    print()

    # Statistics
    print("=" * 80)
    print("Summary Statistics")
    print("=" * 80)

    loaded = [r for r in results if r["params"] > 0]
    not_found = [r for r in results if r["params"] == 0]

    if loaded:
        times = [r["time_ms"] for r in loaded]
        avg_time = sum(times) / len(times)
        max_time = max(times)
        min_time = min(times)

        print(f"Devices Found:     {len(loaded)}/{len(test_devices)}")
        print(f"Devices Missing:   {len(not_found)}")
        print()
        print(f"Cold Start:")
        print(f"  Total Time:      {cold_total:.1f}ms")
        print(f"  Average/Device:  {avg_time:.1f}ms")
        print(f"  Min/Max:         {min_time:.1f}ms / {max_time:.1f}ms")
        print()
        print(f"Warm Cache:")
        print(f"  Average/Device:  {warm_avg:.1f}ms")
        print()

        # Verdict
        print("=" * 80)
        print("Verdict")
        print("=" * 80)

        if cold_total < 500:
            print(f"✅ EXCELLENT: Cold start {cold_total:.1f}ms < 500ms target")
            print("   Lazy loading will be imperceptible to users")
        elif cold_total < 1000:
            print(f"✓ ACCEPTABLE: Cold start {cold_total:.1f}ms < 1s")
            print("   Lazy loading acceptable with async/background loading")
        elif cold_total < 2000:
            print(f"⚠ MARGINAL: Cold start {cold_total:.1f}ms approaching 2s")
            print("   Consider caching strategies or batch loading")
        else:
            print(f"❌ TOO SLOW: Cold start {cold_total:.1f}ms > 2s")
            print("   Lazy loading will cause noticeable delays")

        print()

        if warm_avg < 50:
            print(f"✅ Cache Performance: {warm_avg:.1f}ms avg is excellent")
        elif warm_avg < 100:
            print(f"✓ Cache Performance: {warm_avg:.1f}ms avg is good")
        else:
            print(f"⚠ Cache Performance: {warm_avg:.1f}ms avg could be improved")

    else:
        print("❌ No devices found in Firestore")
        print("   Ensure device mappings are populated")

    if not_found:
        print()
        print("Missing devices (will require fallback to LLM):")
        for r in not_found:
            print(f"  • {r['device']}")

    print()


if __name__ == "__main__":
    benchmark_device_param_loading()
