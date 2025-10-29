#!/usr/bin/env python3
"""Test script for preset cache and alias generation."""

import sys
import os

# Add nlp-service to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'nlp-service'))

from learning.preset_cache_store import force_refresh, _generate_device_aliases

def main():
    # Test alias generation
    print('=== Testing Alias Generation ===')
    print()

    test_names = [
        'FabFilter Pro-Q 3',
        'Valhalla VintageVerb',
        'Ambience',
        'Big',
        'Cathedral',
        'Delay'
    ]

    for name in test_names:
        aliases = _generate_device_aliases(name)
        print(f'{name}:')
        for alias in aliases:
            print(f'  - {alias}')
        print()

    # Load from Firestore
    print('=' * 60)
    print('=== Loading from Firestore ===')
    print('=' * 60)
    categories, device_aliases = force_refresh()

    print(f'\nCategories ({len(categories)}): {sorted(categories)}')
    print(f'\nDevice aliases ({len(device_aliases)}):')
    for alias, canonical in sorted(device_aliases.items()):
        print(f'  {alias:20} → {canonical}')

if __name__ == '__main__':
    main()
