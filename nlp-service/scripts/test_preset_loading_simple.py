#!/usr/bin/env python3
"""
Test loading Reverb presets using raw parameter values.
Uses POST /op/return/device/param to set values directly.
"""

import sys
import requests
import json
from pathlib import Path
from google.cloud import firestore

sys.path.insert(0, str(Path(__file__).parent.parent))

BASE_URL = "http://127.0.0.1:8722"
REVERB_SIGNATURE = "64ccfc236b79371d0b45e913f81bf0f3a55c6db9"
RETURN_INDEX = 0
DEVICE_INDEX = 0


def get_params_meta():
    """Get params_meta to map param names to indices."""
    db = firestore.Client()
    doc = db.collection('device_mappings').document(REVERB_SIGNATURE).get()
    return doc.to_dict().get('params_meta', [])


def get_reverb_presets():
    """Get all Reverb presets from Firestore."""
    db = firestore.Client()
    all_presets = list(db.collection('presets').stream())

    reverb_presets = []
    for p in all_presets:
        data = p.to_dict()
        if data.get('structure_signature') == REVERB_SIGNATURE:
            reverb_presets.append({
                'id': p.id,
                'name': data.get('name', p.id),
                'parameter_values': data.get('parameter_values', {}),
                'category': data.get('category', 'unknown')
            })

    return reverb_presets


def apply_preset_raw(preset_data, params_meta):
    """Apply preset using raw parameter values."""
    param_values = preset_data['parameter_values']

    # Create name->index map with normalized names (handle slash/underscore variants)
    name_to_index = {p['name']: p['index'] for p in params_meta}

    # Also create variant map for common substitutions
    for p in params_meta:
        # Add underscore version if name has slash
        if '/' in p['name']:
            name_to_index[p['name'].replace('/', '_')] = p['index']
        # Add slash version if name has underscore
        if '_' in p['name']:
            name_to_index[p['name'].replace('_', '/')] = p['index']

    results = []
    print(f"\n  Applying {len(param_values)} parameters...")

    for param_name, value in param_values.items():
        param_index = name_to_index.get(param_name)
        if param_index is None:
            results.append({
                'param_name': param_name,
                'error': 'Parameter not found in params_meta',
                'success': False
            })
            continue

        try:
            response = requests.post(
                f"{BASE_URL}/op/return/device/param",
                json={
                    "return_index": RETURN_INDEX,
                    "device_index": DEVICE_INDEX,
                    "param_index": param_index,
                    "value": float(value)
                },
                timeout=5
            )

            if response.status_code == 200:
                results.append({
                    'param_name': param_name,
                    'target_value': value,
                    'success': True
                })
            else:
                results.append({
                    'param_name': param_name,
                    'target_value': value,
                    'error': f"HTTP {response.status_code}",
                    'success': False
                })
        except Exception as e:
            results.append({
                'param_name': param_name,
                'target_value': value,
                'error': str(e),
                'success': False
            })

    return results


def read_back_all_params():
    """Read back all parameter values from Live."""
    try:
        response = requests.get(
            f"{BASE_URL}/return/device/params",
            params={
                "index": RETURN_INDEX,
                "device": DEVICE_INDEX
            },
            timeout=5
        )

        if response.status_code == 200:
            data = response.json()
            params = data.get('data', {}).get('params', [])
            return {p['name']: {'value': p['value'], 'display': p['display_value']}
                    for p in params}
        else:
            print(f"  ⚠️  Error reading back params: HTTP {response.status_code}")
            return {}
    except Exception as e:
        print(f"  ⚠️  Error reading back params: {e}")
        return {}


def test_preset(preset_data, params_meta):
    """Test loading a single preset."""
    print(f"\n{'='*70}")
    print(f"Testing Preset: {preset_data['name']}")
    print(f"Category: {preset_data['category']}")
    print(f"{'='*70}")

    # Apply preset
    results = apply_preset_raw(preset_data, params_meta)

    successful = [r for r in results if r.get('success')]
    failed = [r for r in results if not r.get('success')]

    print(f"\n  Application Results:")
    print(f"    Total parameters: {len(results)}")
    print(f"    Successfully applied: {len(successful)}")
    print(f"    Failed: {len(failed)}")

    if failed:
        print(f"\n  ❌ Failed parameters:")
        for f in failed[:5]:
            print(f"    - {f['param_name']}: {f.get('error', 'unknown error')}")
        if len(failed) > 5:
            print(f"    ... and {len(failed) - 5} more")

    # Read back and compare
    print(f"\n  Reading back parameter values...")
    actual_values = read_back_all_params()

    if actual_values:
        errors = []
        for param_name, target_value in preset_data['parameter_values'].items():
            if param_name in actual_values:
                actual = actual_values[param_name]['value']
                target = float(target_value)

                # Calculate error
                if abs(target) < 0.0001:  # Avoid division by very small numbers
                    error_pct = abs(actual - target) * 100
                else:
                    error_pct = abs(actual - target) / abs(target) * 100

                errors.append({
                    'param_name': param_name,
                    'target': target,
                    'actual': actual,
                    'error_pct': error_pct,
                    'display': actual_values[param_name]['display']
                })

        # Sort by error
        errors.sort(key=lambda x: x['error_pct'], reverse=True)

        # Print worst offenders
        high_errors = [e for e in errors if e['error_pct'] > 2.0]
        if high_errors:
            print(f"\n  ⚠️  Parameters with >2% error:")
            for e in high_errors[:5]:
                print(f"    - {e['param_name']}: target={e['target']:.6f}, actual={e['actual']:.6f}, error={e['error_pct']:.2f}%")
            if len(high_errors) > 5:
                print(f"    ... and {len(high_errors) - 5} more")
        else:
            print(f"\n  ✅ All parameters within 2% error!")

        # Summary stats
        if errors:
            avg_error = sum(e['error_pct'] for e in errors) / len(errors)
            max_error = max(e['error_pct'] for e in errors)
            print(f"\n  Error Statistics:")
            print(f"    Average error: {avg_error:.3f}%")
            print(f"    Maximum error: {max_error:.3f}%")
            print(f"    Parameters >2% error: {len(high_errors)}/{len(errors)}")

        return {
            'preset_name': preset_data['name'],
            'total_params': len(results),
            'successful': len(successful),
            'failed': len(failed),
            'avg_error': sum(e['error_pct'] for e in errors) / len(errors) if errors else 0,
            'max_error': max(e['error_pct'] for e in errors) if errors else 0,
            'high_error_count': len(high_errors)
        }
    else:
        return {
            'preset_name': preset_data['name'],
            'total_params': len(results),
            'successful': len(successful),
            'failed': len(failed),
            'avg_error': None,
            'max_error': None,
            'high_error_count': None
        }


def main():
    print("="*70)
    print("REVERB PRESET LOADING TEST (Raw Values)")
    print("="*70)

    # Get params_meta
    print("\n[1/4] Loading params_meta...")
    params_meta = get_params_meta()
    print(f"✓ Loaded {len(params_meta)} parameters")

    # Get all Reverb presets
    print("\n[2/4] Loading Reverb presets from Firestore...")
    presets = get_reverb_presets()
    print(f"✓ Found {len(presets)} Reverb presets")

    # Select diverse presets to test
    print("\n[3/4] Selecting test presets...")

    # Select 5 diverse presets by name keywords
    keywords = ['cathedral', 'arena', 'bright', 'basement', 'ballad']
    test_presets = []

    for keyword in keywords:
        matching = [p for p in presets if keyword.lower() in p['name'].lower()]
        if matching:
            test_presets.append(matching[0])

    # If we didn't get 5, add more
    if len(test_presets) < 5:
        for p in presets:
            if p not in test_presets:
                test_presets.append(p)
                if len(test_presets) >= 5:
                    break

    print(f"✓ Selected {len(test_presets)} presets to test:")
    for p in test_presets:
        print(f"  - {p['name']} ({p['category']})")

    # Test each preset
    print("\n[4/4] Testing presets...")

    summary_results = []
    for preset in test_presets:
        result = test_preset(preset, params_meta)
        summary_results.append(result)

    # Final summary
    print("\n" + "="*70)
    print("FINAL SUMMARY")
    print("="*70)

    for r in summary_results:
        if r['avg_error'] is not None:
            status = "✅" if r['high_error_count'] == 0 and r['failed'] == 0 else "⚠️"
            print(f"\n{status} {r['preset_name']}")
            print(f"    Success rate: {r['successful']}/{r['total_params']}")
            print(f"    Avg error: {r['avg_error']:.3f}%")
            print(f"    Max error: {r['max_error']:.3f}%")
            if r['high_error_count'] > 0:
                print(f"    Params >2% error: {r['high_error_count']}")
        else:
            print(f"\n⚠️  {r['preset_name']}")
            print(f"    Success rate: {r['successful']}/{r['total_params']}")
            print(f"    Could not read back values for comparison")

    # Overall pass/fail
    valid_results = [r for r in summary_results if r['avg_error'] is not None]
    all_passed = all(r['high_error_count'] == 0 and r['failed'] == 0 for r in valid_results)

    print("\n" + "="*70)
    if all_passed and len(valid_results) == len(summary_results):
        print("✅ ALL PRESETS LOADED SUCCESSFULLY")
        print("All parameters match stored values!")
    else:
        print("⚠️  SOME PRESETS HAD ISSUES")
        print("Review individual preset results above")
    print("="*70)

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
