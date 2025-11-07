#!/usr/bin/env python3
"""Trace exactly what happens during parsing to understand the slowdown."""

import sys
import os
import time

# Add nlp-service to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'nlp-service'))

from parsers.device_parser import DEVICE_PARSERS
from parsers import apply_typo_corrections, parse_mixer_command

ABSOLUTE_QUERY = "set return a reverb decay to 2 seconds"
RELATIVE_QUERY = "increase return a reverb decay by 20 percent"

def trace_parsing(query, label):
    print("=" * 80)
    print(f"{label}")
    print("=" * 80)
    print(f"Query: {query}")
    print()

    # Step 1: Typo correction
    start = time.perf_counter()
    corrected = apply_typo_corrections(query)
    typo_time = (time.perf_counter() - start) * 1000
    print(f"1. Typo correction: {typo_time:.3f}ms")
    print(f"   Corrected: '{corrected}'")
    print()

    # Step 2: Try mixer parsers
    start = time.perf_counter()
    mixer_result = parse_mixer_command(corrected, query, "", "gemini-2.5-flash-lite")
    mixer_time = (time.perf_counter() - start) * 1000
    print(f"2. Mixer parsers: {mixer_time:.3f}ms")
    if mixer_result:
        print(f"   ✓ MATCHED by mixer parser!")
        return
    else:
        print(f"   ✗ No mixer match")
    print()

    # Step 3: Try device parsers one by one
    print(f"3. Device parsers:")
    total_device_time = 0
    for i, parser in enumerate(DEVICE_PARSERS):
        parser_name = parser.__name__
        start = time.perf_counter()
        try:
            result = parser(corrected, query, "", "gemini-2.5-flash-lite")
            elapsed = (time.perf_counter() - start) * 1000
            total_device_time += elapsed

            if result:
                print(f"   [{i}] {parser_name:45s} {elapsed:.3f}ms ✓ MATCHED")
                print()
                print(f"Total device parser time: {total_device_time:.3f}ms")
                print(f"Intent: {result.get('intent')}")
                return
            else:
                print(f"   [{i}] {parser_name:45s} {elapsed:.3f}ms")
        except Exception as e:
            elapsed = (time.perf_counter() - start) * 1000
            total_device_time += elapsed
            print(f"   [{i}] {parser_name:45s} {elapsed:.3f}ms ERROR")

    print()
    print(f"Total device parser time: {total_device_time:.3f}ms")
    print()
    print("❌ NO REGEX MATCH - Would fall to LLM (~300-400ms)")
    print()

# Warm up caches
apply_typo_corrections("warmup")
parse_mixer_command("warmup", "warmup", "", "gemini-2.5-flash-lite")

print("\n" * 2)

# Trace both queries
trace_parsing(ABSOLUTE_QUERY, "ABSOLUTE DEVICE CHANGE (Regex Match)")
print("\n" * 2)
trace_parsing(RELATIVE_QUERY, "RELATIVE DEVICE CHANGE (No Regex Match)")

print()
print("=" * 80)
print("ANALYSIS")
print("=" * 80)
print()
print("The slowdown is NOT because relative operations are inherently slow.")
print("It's because:")
print()
print("1. ✓ Absolute matches early in device parsers → fast regex path")
print("2. ✗ Relative has NO regex parser → tries all parsers → all fail")
print("3. ⚠️  Falls back to LLM (300-400ms) to understand the relative operation")
print()
print("The 'surgical fix' is to ADD regex parsers for relative operations,")
print("not to optimize anything that's currently slow!")
