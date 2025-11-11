#!/usr/bin/env python3
"""
Test the parse index builder with batch loading.
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

# Set database before any imports
os.environ['FIRESTORE_DATABASE_ID'] = 'dev-display-value'

from server.services.parse_index import build_index_from_mock_liveset

# Test with devices from the benchmark
test_devices = [
    "Reverb",
    "4th Bandpass",
    "Screamer",
    "8DotBall",
    "Ambience",
    "Bass Roundup",
    "Discrete",
    "Mix Gel",
    "8th Groove",
    "Chopped Delay"
]

print("=" * 80)
print("Testing Parse Index Builder with Batch Loading")
print("=" * 80)
print()

parse_index = build_index_from_mock_liveset(test_devices)

print()
print("=" * 80)
print("Parse Index Summary")
print("=" * 80)
print(f"Version: {parse_index['version']}")
print(f"Devices in set: {len(parse_index['devices_in_set'])}")
print(f"Device mappings: {len(parse_index['params_by_device'])}")
print(f"Mixer params: {len(parse_index['mixer_params'])}")
print(f"Typo corrections: {len(parse_index['typo_map'])}")
print()

# Show devices with params
print("Devices with param mappings:")
for device_name, info in parse_index['params_by_device'].items():
    param_count = len(info['params'])
    device_type = info.get('device_type', 'unknown')
    print(f"  {device_name:30s} → {param_count:3d} params ({device_type})")
