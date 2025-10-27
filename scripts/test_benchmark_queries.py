#!/usr/bin/env python3
"""Test individual benchmark queries to find failures."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'nlp-service'))
os.environ['NLP_MODE'] = 'regex_first'

from llm_daw import interpret_daw_command

queries = [
    'set track 1 volume to -12 dB',
    'set track 2 volume to -6 dB',
    'solo track 3',
    'mute return A',
    'set track 4 pan to 25% left',
    'set track 1 send A to -18 dB',
    'set return A volume to -6 dB',
    'set return A reverb decay to 2.5 s',
    'set return B delay feedback to 50%',
    'set return A reverb predelay to 20 ms',
    'set tack 1 vilme to -6 dB',
    'set retun A volme to -3 dB',
    'set track 2 paning to 50% right',
    'set track 1 sennd A to -12 dB',
    'set return A revreb dcay to 2 s',
    'set return A reverb predlay to 15 ms',
]

print(f"{'Status':6} {'Pipeline':15} | Query")
print("=" * 80)

for q in queries:
    result = interpret_daw_command(q)
    intent = result.get('intent')
    pipeline = result.get('meta', {}).get('pipeline', 'unknown')
    is_success = intent != 'clarification_needed'
    status = 'OK' if is_success else 'FAIL'
    print(f'{status:6} {pipeline:15} | {q[:50]}')
