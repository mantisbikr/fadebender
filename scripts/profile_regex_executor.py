#!/usr/bin/env python3
"""Profile the full regex_executor pathway."""

import sys
import os
import time

# Add nlp-service to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'nlp-service'))

from execution.regex_executor import try_regex_parse

TEST_QUERY = "set return a reverb decay to 2 seconds"

print("=" * 80)
print("Full regex_executor Path Performance")
print("=" * 80)
print(f"Test query: {TEST_QUERY}")
print()

# Run 10 iterations
times = []
for i in range(10):
    start = time.perf_counter()
    result, suspected_typos = try_regex_parse(TEST_QUERY, "", "gemini-2.5-flash-lite")
    elapsed_ms = (time.perf_counter() - start) * 1000
    times.append(elapsed_ms)
    print(f"Iteration {i + 1}: {elapsed_ms:7.2f}ms")

print()
print(f"Average: {sum(times) / len(times):7.2f}ms")
print(f"Min:     {min(times):7.2f}ms")
print(f"Max:     {max(times):7.2f}ms")
print()

if result:
    print(f"✓ Matched! Intent: {result.get('intent')}")
    print(f"  Pipeline: {result.get('meta', {}).get('pipeline')}")
else:
    print(f"✗ No match. Suspected typos: {suspected_typos}")
