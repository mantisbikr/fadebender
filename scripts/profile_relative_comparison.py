#!/usr/bin/env python3
"""Compare absolute vs relative device change performance."""

import sys
import os
import time

# Add nlp-service to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'nlp-service'))

from execution.regex_executor import try_regex_parse

# Test queries
ABSOLUTE_QUERY = "set return a reverb decay to 2 seconds"
RELATIVE_QUERY = "increase return a reverb decay by 20 percent"

print("=" * 80)
print("Absolute vs Relative Device Change Performance")
print("=" * 80)
print()

# Test absolute first (to warm up caches)
print("Testing ABSOLUTE device change (with warmup):")
print(f"Query: {ABSOLUTE_QUERY}")
print()

times_abs = []
for i in range(10):
    start = time.perf_counter()
    result, suspected_typos = try_regex_parse(ABSOLUTE_QUERY, "", "gemini-2.5-flash-lite")
    elapsed_ms = (time.perf_counter() - start) * 1000
    times_abs.append(elapsed_ms)
    if i == 0:
        print(f"Warmup:      {elapsed_ms:7.2f}ms")
    elif i < 3:
        print(f"Iteration {i}: {elapsed_ms:7.2f}ms")

print(f"... (skipping iterations 4-9)")
print(f"Avg (all 10): {sum(times_abs) / len(times_abs):7.2f}ms")
print(f"Avg (warm 2-10): {sum(times_abs[1:]) / len(times_abs[1:]):7.2f}ms")

if result:
    print(f"✓ Matched! Intent: {result.get('intent')}")
else:
    print(f"✗ No match")

print()
print("=" * 80)
print()

# Now test relative (should already be warm)
print("Testing RELATIVE device change (warm cache):")
print(f"Query: {RELATIVE_QUERY}")
print()

times_rel = []
for i in range(10):
    start = time.perf_counter()
    result, suspected_typos = try_regex_parse(RELATIVE_QUERY, "", "gemini-2.5-flash-lite")
    elapsed_ms = (time.perf_counter() - start) * 1000
    times_rel.append(elapsed_ms)
    if i < 3:
        print(f"Iteration {i + 1}: {elapsed_ms:7.2f}ms")

print(f"... (skipping iterations 4-10)")
print(f"Avg (all 10): {sum(times_rel) / len(times_rel):7.2f}ms")

if result:
    print(f"✓ Matched! Intent: {result.get('intent')}")
    print(f"  Suspected typos: {suspected_typos}")
else:
    print(f"✗ No regex match - will fall to LLM")
    print(f"  Suspected typos: {suspected_typos}")

print()
print("=" * 80)
print("SUMMARY")
print("=" * 80)
print(f"Absolute (warm avg): {sum(times_abs[1:]) / len(times_abs[1:]):7.2f}ms")
print(f"Relative (warm avg): {sum(times_rel) / len(times_rel):7.2f}ms")
print()

if result is None:
    print("⚠️  RELATIVE CHANGES NOT HANDLED BY REGEX - Falls to LLM (~300-400ms)")
    print("    This is the opportunity for optimization!")
else:
    print("✓ Both handled by regex - comparable performance")
