#!/usr/bin/env python3
"""Test all 4 device relative parsers to verify correct parsing and operation type."""

import sys
import os

# Add nlp-service to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'nlp-service'))

from execution.regex_executor import try_regex_parse

# Test cases for each parser
test_cases = [
    # parse_return_device_param_relative
    ("increase return a reverb decay by 20 percent", {
        'intent': 'set_parameter',
        'targets': [{'track': 'Return A', 'plugin': 'reverb', 'parameter': 'Decay'}],
        'operation': {'type': 'relative', 'value': 20.0, 'unit': '%'}
    }),
    ("decrease return b reverb decay by 10 percent", {
        'intent': 'set_parameter',
        'targets': [{'track': 'Return B', 'plugin': 'reverb', 'parameter': 'Decay'}],
        'operation': {'type': 'relative', 'value': -10.0, 'unit': '%'}
    }),

    # parse_track_device_param_relative
    ("increase track 1 reverb decay by 20 percent", {
        'intent': 'set_parameter',
        'targets': [{'track': 'Track 1', 'plugin': 'reverb', 'parameter': 'decay'}],
        'operation': {'type': 'relative', 'value': 20.0, 'unit': '%'}
    }),
    ("lower track 2 delay time by 100 ms", {
        'intent': 'set_parameter',
        'targets': [{'track': 'Track 2', 'plugin': 'delay', 'parameter': 'time'}],
        'operation': {'type': 'relative', 'value': -100.0, 'unit': 'ms'}
    }),

    # parse_return_device_ordinal_relative
    ("increase return a device 1 dry wet by 15 percent", {
        'intent': 'set_parameter',
        'targets': [{'track': 'Return A', 'plugin': 'device', 'parameter': 'dry wet', 'device_ordinal': 1}],
        'operation': {'type': 'relative', 'value': 15.0, 'unit': '%'}
    }),
    ("decrease return c device 2 feedback by 5 percent", {
        'intent': 'set_parameter',
        'targets': [{'track': 'Return C', 'plugin': 'device', 'parameter': 'feedback', 'device_ordinal': 2}],
        'operation': {'type': 'relative', 'value': -5.0, 'unit': '%'}
    }),

    # parse_track_device_ordinal_relative
    ("increase track 1 device 2 gain by 3 db", {
        'intent': 'set_parameter',
        'targets': [{'track': 'Track 1', 'plugin': 'device', 'parameter': 'gain', 'device_ordinal': 2}],
        'operation': {'type': 'relative', 'value': 3.0, 'unit': 'dB'}
    }),
    ("raise track 3 device 1 volume by 6 db", {
        'intent': 'set_parameter',
        'targets': [{'track': 'Track 3', 'plugin': 'device', 'parameter': 'volume', 'device_ordinal': 1}],
        'operation': {'type': 'relative', 'value': 6.0, 'unit': 'dB'}
    }),
]

print("=" * 80)
print("Testing Device Relative Parsers")
print("=" * 80)
print()

passed = 0
failed = 0

for query, expected in test_cases:
    result, suspected_typos = try_regex_parse(query, "", "gemini-2.5-flash-lite")

    if not result:
        print(f"❌ FAIL: {query}")
        print(f"   Expected match, but got None")
        failed += 1
        continue

    # Check intent
    if result.get('intent') != expected['intent']:
        print(f"❌ FAIL: {query}")
        print(f"   Intent mismatch: {result.get('intent')} != {expected['intent']}")
        failed += 1
        continue

    # Check operation type (most important!)
    if result.get('operation', {}).get('type') != expected['operation']['type']:
        print(f"❌ FAIL: {query}")
        print(f"   Operation type mismatch: {result.get('operation', {}).get('type')} != {expected['operation']['type']}")
        failed += 1
        continue

    # Check value (including sign for decrease/lower)
    if result.get('operation', {}).get('value') != expected['operation']['value']:
        print(f"❌ FAIL: {query}")
        print(f"   Value mismatch: {result.get('operation', {}).get('value')} != {expected['operation']['value']}")
        failed += 1
        continue

    # Check unit
    if result.get('operation', {}).get('unit') != expected['operation']['unit']:
        print(f"❌ FAIL: {query}")
        print(f"   Unit mismatch: {result.get('operation', {}).get('unit')} != {expected['operation']['unit']}")
        failed += 1
        continue

    # Check target track
    if result.get('targets', [{}])[0].get('track') != expected['targets'][0]['track']:
        print(f"❌ FAIL: {query}")
        print(f"   Track mismatch: {result.get('targets', [{}])[0].get('track')} != {expected['targets'][0]['track']}")
        failed += 1
        continue

    # Check plugin
    if result.get('targets', [{}])[0].get('plugin') != expected['targets'][0]['plugin']:
        print(f"❌ FAIL: {query}")
        print(f"   Plugin mismatch: {result.get('targets', [{}])[0].get('plugin')} != {expected['targets'][0]['plugin']}")
        failed += 1
        continue

    print(f"✓ PASS: {query}")
    print(f"   Operation: {result['operation']['type']} {result['operation']['value']:+.1f} {result['operation']['unit'] or ''}")
    passed += 1

print()
print("=" * 80)
print("RESULTS")
print("=" * 80)
print(f"Passed: {passed}/{len(test_cases)}")
print(f"Failed: {failed}/{len(test_cases)}")
print()

if failed > 0:
    print("⚠️  Some tests failed - review implementation")
    sys.exit(1)
else:
    print("✓ All tests passed!")
    sys.exit(0)
