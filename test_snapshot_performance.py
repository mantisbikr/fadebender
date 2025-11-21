#!/usr/bin/env python3
"""Compare performance: old snapshot (multiple UDP calls) vs new (single UDP call)."""

import requests
import time
import json

BASE_URL = "http://127.0.0.1:8722"

def test_old_snapshot():
    """Test current snapshot endpoint (multiple UDP calls)."""
    print("\n=== Testing OLD snapshot (multiple UDP calls) ===")
    start = time.time()
    resp = requests.get(f"{BASE_URL}/snapshot?force_refresh=true", timeout=15)
    elapsed = time.time() - start

    if resp.status_code == 200:
        data = resp.json()
        track_count = len(data.get("tracks", []))
        return_count = len(data.get("returns", []))

        # Count total devices
        total_devices = sum(len(t.get("devices", [])) for t in data.get("tracks", []))
        total_devices += sum(len(r.get("devices", [])) for r in data.get("returns", []))
        total_devices += len(data.get("master", {}).get("devices", []))

        print(f"✓ Success: {track_count} tracks, {return_count} returns, {total_devices} devices")
        print(f"⏱️  Time: {elapsed:.3f}s")
        return elapsed
    else:
        print(f"✗ Failed: {resp.status_code}")
        return None


def test_new_snapshot(skip_param_values=False):
    """Test new snapshot endpoint (single UDP call)."""
    mode = "structure only" if skip_param_values else "with params"
    print(f"\n=== Testing NEW snapshot ({mode}, single UDP call) ===")
    start = time.time()
    resp = requests.get(
        f"{BASE_URL}/snapshot/full?skip_param_values={str(skip_param_values).lower()}",
        timeout=15
    )
    elapsed = time.time() - start

    if resp.status_code == 200:
        result = resp.json()
        data = result.get("data", {})
        perf = result.get("performance", {})

        track_count = len(data.get("tracks", []))
        return_count = len(data.get("returns", []))

        # Count total devices
        total_devices = sum(len(t.get("devices", [])) for t in data.get("tracks", []))
        total_devices += sum(len(r.get("devices", [])) for r in data.get("returns", []))
        total_devices += len(data.get("master", {}).get("devices", []))

        # Count total params (if included)
        total_params = 0
        if not skip_param_values:
            for t in data.get("tracks", []):
                for d in t.get("devices", []):
                    total_params += len(d.get("params", []))
            for r in data.get("returns", []):
                for d in r.get("devices", []):
                    total_params += len(d.get("params", []))
            for d in data.get("master", {}).get("devices", []):
                total_params += len(d.get("params", []))

        print(f"✓ Success: {track_count} tracks, {return_count} returns, {total_devices} devices")
        if total_params:
            print(f"  Parameters: {total_params} total")
        print(f"⏱️  Time: {elapsed:.3f}s (UDP: {perf.get('elapsed_seconds', 0):.3f}s)")
        return elapsed
    else:
        print(f"✗ Failed: {resp.status_code}")
        print(resp.text[:500])
        return None


if __name__ == "__main__":
    print("Snapshot Performance Comparison")
    print("=" * 50)

    # Test old approach
    old_time = test_old_snapshot()

    # Test new approach (structure only)
    new_time_struct = test_new_snapshot(skip_param_values=True)

    # Test new approach (with params)
    new_time_full = test_new_snapshot(skip_param_values=False)

    # Summary
    print("\n" + "=" * 50)
    print("SUMMARY")
    print("=" * 50)

    if old_time and new_time_struct:
        speedup = old_time / new_time_struct
        print(f"Structure only: {speedup:.1f}x faster ({old_time:.3f}s → {new_time_struct:.3f}s)")

    if old_time and new_time_full:
        speedup = old_time / new_time_full
        saving = old_time - new_time_full
        print(f"With params:    {speedup:.1f}x faster ({old_time:.3f}s → {new_time_full:.3f}s)")
        print(f"                Saved {saving:.3f}s")
