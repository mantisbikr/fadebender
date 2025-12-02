#!/usr/bin/env python3
"""
Test smart routing functionality
Tests Firestore direct queries vs RAG fallback
"""

import requests
import time
import json

def test_query(query, user_id, description):
    """Test a single query and print results"""
    print(f"\n{'='*70}")
    print(f"{description}")
    print(f"Query: {query}")
    print(f"{'='*70}")

    start = time.time()
    response = requests.post(
        'http://localhost:8722/help',
        json={'query': query, 'context': {'userId': user_id}}
    )
    total_time = time.time() - start

    if response.status_code != 200:
        print(f"❌ ERROR: HTTP {response.status_code}")
        print(response.text)
        return None

    data = response.json()

    print(f"✓ Mode: {data.get('mode', 'N/A')}")
    print(f"✓ Time: {total_time:.3f}s (server: {data.get('timing', {}).get('total', 'N/A')}s)")
    print(f"✓ Answer length: {len(data.get('answer', ''))} chars")
    print(f"\nAnswer preview:")
    print(data.get('answer', '')[:300])
    if len(data.get('answer', '')) > 300:
        print("...")

    return {
        'mode': data.get('mode'),
        'time': total_time,
        'server_time': data.get('timing', {}).get('total', 0),
        'length': len(data.get('answer', '')),
        'ok': data.get('ok', False)
    }


if __name__ == "__main__":
    print("=" * 70)
    print("SMART ROUTING TEST SUITE")
    print("=" * 70)
    print("Testing Firestore direct queries vs RAG fallback\n")

    results = []

    # Test 1: Factual count (should use Firestore)
    r1 = test_query(
        "how many reverb presets are available?",
        "test-firestore-count",
        "TEST 1: Factual Count (should use Firestore - instant)"
    )
    results.append(('Factual Count', r1))
    time.sleep(1)

    # Test 2: Factual list (should use Firestore)
    r2 = test_query(
        "list all reverb presets",
        "test-firestore-list",
        "TEST 2: Factual List (should use Firestore - instant)"
    )
    results.append(('Factual List', r2))
    time.sleep(1)

    # Test 3: Device parameters (should use Firestore)
    r3 = test_query(
        "what parameters can I control on the compressor?",
        "test-firestore-params",
        "TEST 3: Device Parameters (should use Firestore - instant)"
    )
    results.append(('Device Params', r3))
    time.sleep(1)

    # Test 4: Comparison (should fall back to RAG)
    r4 = test_query(
        "compare Cathedral and Church reverb presets",
        "test-rag-comparison",
        "TEST 4: Comparison (should fall back to RAG - slower)"
    )
    results.append(('Comparison', r4))

    # Summary
    print(f"\n{'='*70}")
    print("SUMMARY")
    print(f"{'='*70}")

    for name, result in results:
        if result:
            print(f"{name:20} | Mode: {result['mode']:20} | Time: {result['time']:.3f}s")

    # Calculate Firestore avg vs RAG
    firestore_times = [r['time'] for name, r in results[:3] if r and 'firestore' in r.get('mode', '').lower()]
    rag_times = [r['time'] for name, r in results[3:] if r and 'firestore' not in r.get('mode', '').lower()]

    if firestore_times:
        print(f"\n✓ Firestore average: {sum(firestore_times)/len(firestore_times):.3f}s")
    if rag_times:
        print(f"✓ RAG average: {sum(rag_times)/len(rag_times):.3f}s")

    if firestore_times and rag_times:
        speedup = (sum(rag_times)/len(rag_times)) / (sum(firestore_times)/len(firestore_times))
        print(f"\n🚀 Firestore is {speedup:.1f}x faster than RAG!")
