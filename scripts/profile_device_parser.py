#!/usr/bin/env python3
"""Profile device parser performance to identify bottlenecks.

This script times each device parser individually to find where the 123ms slowdown is coming from.
"""

import sys
import os
import time

# Add nlp-service to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'nlp-service'))

from parsers.device_parser import DEVICE_PARSERS, _get_device_pattern

# Test query that should match the first parser (parse_return_device_param)
TEST_QUERY = "set return a reverb decay to 2 seconds"
query_lower = TEST_QUERY.lower()

print("=" * 80)
print("Device Parser Performance Profile")
print("=" * 80)
print(f"Test query: {TEST_QUERY}")
print()

# First, check if _get_device_pattern is the culprit
print("Testing _get_device_pattern() cache...")
start = time.perf_counter()
pattern = _get_device_pattern()
time_first = (time.perf_counter() - start) * 1000
print(f"First call:  {time_first:8.2f}ms")

start = time.perf_counter()
pattern = _get_device_pattern()
time_cached = (time.perf_counter() - start) * 1000
print(f"Cached call: {time_cached:8.2f}ms")
print()

# Now test each parser individually
print("Testing each parser:")
print("-" * 80)

total_time = 0
matched_parser = None

for i, parser in enumerate(DEVICE_PARSERS):
    parser_name = parser.__name__

    start = time.perf_counter()
    try:
        result = parser(query_lower, TEST_QUERY, "", "gemini-2.5-flash-lite")
        elapsed_ms = (time.perf_counter() - start) * 1000

        if result:
            print(f"[{i}] {parser_name:45s} {elapsed_ms:8.2f}ms ✓ MATCHED")
            matched_parser = parser_name
            total_time += elapsed_ms
            break  # Stop at first match (like real execution)
        else:
            print(f"[{i}] {parser_name:45s} {elapsed_ms:8.2f}ms")
            total_time += elapsed_ms
    except Exception as e:
        elapsed_ms = (time.perf_counter() - start) * 1000
        print(f"[{i}] {parser_name:45s} {elapsed_ms:8.2f}ms ERROR: {e}")
        total_time += elapsed_ms

print("-" * 80)
print(f"Total time: {total_time:.2f}ms")
print()

if matched_parser:
    print(f"Matched by: {matched_parser}")
else:
    print("No parser matched!")

print()
print("=" * 80)
print("Running 10 iterations to measure variance...")
print("=" * 80)

# Run multiple iterations to see if there's variance (e.g., HTTP calls)
times = []
for iteration in range(10):
    start = time.perf_counter()

    for parser in DEVICE_PARSERS:
        try:
            result = parser(query_lower, TEST_QUERY, "", "gemini-2.5-flash-lite")
            if result:
                break
        except Exception:
            continue

    elapsed_ms = (time.perf_counter() - start) * 1000
    times.append(elapsed_ms)
    print(f"Iteration {iteration + 1}: {elapsed_ms:7.2f}ms")

print()
print(f"Average: {sum(times) / len(times):7.2f}ms")
print(f"Min:     {min(times):7.2f}ms")
print(f"Max:     {max(times):7.2f}ms")
print(f"Std dev: {(sum((t - sum(times)/len(times))**2 for t in times) / len(times))**0.5:7.2f}ms")
print()

# Check if there's high variance (indicates I/O operations)
variance = max(times) - min(times)
if variance > 50:
    print(f"⚠️  High variance ({variance:.2f}ms) detected - likely I/O operations (HTTP, Firestore, etc.)")
elif variance > 10:
    print(f"⚠️  Moderate variance ({variance:.2f}ms) detected - possible caching effects")
else:
    print(f"✓ Low variance ({variance:.2f}ms) - consistent performance")
