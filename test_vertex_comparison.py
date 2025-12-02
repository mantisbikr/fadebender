#!/usr/bin/env python3
"""
Comprehensive comparison: OpenAI vs Vertex AI with Firestore smart routing
"""
import requests
import time
import json

def test_query(query, user_id, description):
    """Run a single test query and return results"""
    print(f"\n{'='*80}")
    print(f"{description}")
    print(f"Query: '{query}'")
    print(f"{'='*80}")

    start = time.time()
    try:
        response = requests.post(
            'http://localhost:8722/help',
            json={'query': query, 'context': {'userId': user_id}},
            timeout=60
        )
        total_time = time.time() - start

        if response.status_code != 200:
            return {
                'error': f"HTTP {response.status_code}",
                'time': total_time,
                'description': description
            }

        data = response.json()
        result = {
            'time': total_time,
            'server_time': data.get('timing', {}).get('total', 0),
            'mode': data.get('mode', 'unknown'),
            'rag_mode': data.get('rag_mode', 'N/A'),
            'answer_length': len(data.get('answer', '')),
            'answer': data.get('answer', '')[:300],
            'description': description
        }

        print(f"Mode: {result['mode']}")
        print(f"RAG Backend: {result['rag_mode']}")
        print(f"Time: {result['time']:.2f}s (server: {result['server_time']:.2f}s)")
        print(f"Answer length: {result['answer_length']} chars")
        print(f"Answer preview: {result['answer'][:200]}...")

        return result

    except Exception as e:
        total_time = time.time() - start
        print(f"ERROR: {str(e)}")
        return {
            'error': str(e),
            'time': total_time,
            'description': description
        }

def main():
    print("\n" + "="*80)
    print("VERTEX AI + FIRESTORE SMART ROUTING TEST")
    print("="*80)

    results = []

    # Test 1: Factual count (should use Firestore, bypass RAG)
    results.append(test_query(
        "how many reverb presets are there?",
        "vertex-test-1",
        "TEST 1: Factual Count (Firestore - instant)"
    ))
    time.sleep(2)

    # Test 2: Factual list (should use Firestore, bypass RAG)
    results.append(test_query(
        "list all compressor presets",
        "vertex-test-2",
        "TEST 2: Factual List (Firestore - instant)"
    ))
    time.sleep(2)

    # Test 3: Complex comparison (should use Vertex AI Search)
    results.append(test_query(
        "what is the difference between the Cathedral and Church reverb presets?",
        "vertex-test-3",
        "TEST 3: Preset Comparison (Vertex AI RAG)"
    ))
    time.sleep(2)

    # Test 4: Workflow question (should use Vertex AI Search)
    results.append(test_query(
        "how do I automate the reverb decay time in Ableton Live?",
        "vertex-test-4",
        "TEST 4: Workflow Question (Vertex AI RAG)"
    ))
    time.sleep(2)

    # Test 5: Best for question (semantic, should use Vertex AI)
    results.append(test_query(
        "what reverb preset is best for vocals?",
        "vertex-test-5",
        "TEST 5: Semantic Recommendation (Vertex AI RAG)"
    ))

    # Summary
    print("\n" + "="*80)
    print("SUMMARY - VERTEX AI + FIRESTORE ROUTING")
    print("="*80)

    firestore_queries = [r for r in results if r.get('mode', '').startswith('firestore')]
    vertex_queries = [r for r in results if r.get('rag_mode') == 'vertex']

    if firestore_queries:
        avg_firestore = sum(r['time'] for r in firestore_queries) / len(firestore_queries)
        print(f"\nFirestore Queries (factual): {len(firestore_queries)}")
        print(f"  Average time: {avg_firestore:.2f}s")
        print(f"  Modes: {[r['mode'] for r in firestore_queries]}")

    if vertex_queries:
        avg_vertex = sum(r['time'] for r in vertex_queries) / len(vertex_queries)
        print(f"\nVertex AI Queries (complex): {len(vertex_queries)}")
        print(f"  Average time: {avg_vertex:.2f}s")
        print(f"  Answer lengths: {[r['answer_length'] for r in vertex_queries]}")

    # Overall stats
    successful = [r for r in results if 'error' not in r]
    if successful:
        avg_total = sum(r['time'] for r in successful) / len(successful)
        print(f"\nOverall:")
        print(f"  Total queries: {len(results)}")
        print(f"  Successful: {len(successful)}")
        print(f"  Average time: {avg_total:.2f}s")
        print(f"  Min time: {min(r['time'] for r in successful):.2f}s")
        print(f"  Max time: {max(r['time'] for r in successful):.2f}s")

    # Errors
    errors = [r for r in results if 'error' in r]
    if errors:
        print(f"\nErrors: {len(errors)}")
        for err in errors:
            print(f"  - {err['description']}: {err['error']}")

    print("\n" + "="*80)

if __name__ == "__main__":
    main()
