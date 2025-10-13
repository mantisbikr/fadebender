#!/usr/bin/env python3
"""
Test that we can perfectly recreate Reverb presets using our mapping.

Process:
1. Select 3-5 diverse Reverb presets from Firestore
2. For each preset, read all parameter display values
3. Apply all parameters to Live via /op/return/param_by_name API
4. Read back actual values from Live
5. Compare and calculate error metrics
"""

import sys
import requests
import json
from pathlib import Path
from google.cloud import firestore

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

BASE_URL = "http://127.0.0.1:8722"
REVERB_SIGNATURE = "64ccfc236b79371d0b45e913f81bf0f3a55c6db9"
RETURN_INDEX = 0
DEVICE_INDEX = 0


def get_reverb_presets():
    """Get all Reverb presets from Firestore."""
    db = firestore.Client()
    all_presets = list(db.collection('presets').stream())

    # Filter for Reverb using structure_signature
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


def apply_preset_via_api(preset_data):
    """Apply all parameters from a preset using our mapping API."""
    param_values = preset_data['parameter_values']
    results = []

    print(f"\n  Applying {len(param_values)} parameters...")

    for param_name, target_value in param_values.items():
        try:
            response = requests.post(
                f"{BASE_URL}/op/return/param_by_name",
                json={
                    "return_ref": str(RETURN_INDEX),
                    "device_ref": "0",  # First device on return track
                    "param_ref": param_name,
                    "target_display": str(target_value)
                },
                timeout=5
            )

            if response.status_code == 200:
                data = response.json()
                applied = data.get('applied', {})
                results.append({
                    'param_name': param_name,
                    'target': target_value,
                    'applied_display': applied.get('display'),
                    'applied_value': applied.get('value'),
                    'success': True
                })
            else:
                results.append({
                    'param_name': param_name,
                    'target': target_value,
                    'error': f"HTTP {response.status_code}",
                    'success': False
                })
        except Exception as e:
            results.append({
                'param_name': param_name,
                'target': target_value,
                'error': str(e),
                'success': False
            })

    return results


def calculate_error(target_str, applied_str):
    """Calculate percentage error between target and applied values."""
    try:
        target = float(target_str)
        applied = float(applied_str)

        if target == 0:
            return abs(applied) if applied != 0 else 0.0

        return abs(applied - target) / abs(target) * 100
    except (ValueError, TypeError):
        # For non-numeric values (labels), check exact match
        return 0.0 if str(target_str).lower() == str(applied_str).lower() else 100.0


def test_preset(preset_data):
    """Test loading a single preset."""
    print(f"\n{'='*70}")
    print(f"Testing Preset: {preset_data['name']}")
    print(f"Category: {preset_data['category']}")
    print(f"{'='*70}")

    # Apply preset
    results = apply_preset_via_api(preset_data)

    # Analyze results
    successful = [r for r in results if r.get('success')]
    failed = [r for r in results if not r.get('success')]

    print(f"\n  Results:")
    print(f"    Total parameters: {len(results)}")
    print(f"    Successfully applied: {len(successful)}")
    print(f"    Failed: {len(failed)}")

    if failed:
        print(f"\n  ❌ Failed parameters:")
        for f in failed:
            print(f"    - {f['param_name']}: {f.get('error', 'unknown error')}")

    # Calculate errors for successful params
    errors = []
    for r in successful:
        error = calculate_error(r['target'], r['applied_display'])
        errors.append({
            'param_name': r['param_name'],
            'target': r['target'],
            'applied': r['applied_display'],
            'error_pct': error
        })

    # Sort by error
    errors.sort(key=lambda x: x['error_pct'], reverse=True)

    # Print worst offenders
    high_errors = [e for e in errors if e['error_pct'] > 2.0]
    if high_errors:
        print(f"\n  ⚠️  Parameters with >2% error:")
        for e in high_errors[:5]:
            print(f"    - {e['param_name']}: target={e['target']}, applied={e['applied']}, error={e['error_pct']:.1f}%")
    else:
        print(f"\n  ✅ All parameters within 2% error!")

    # Summary stats
    if errors:
        avg_error = sum(e['error_pct'] for e in errors) / len(errors)
        max_error = max(e['error_pct'] for e in errors)
        print(f"\n  Error Statistics:")
        print(f"    Average error: {avg_error:.2f}%")
        print(f"    Maximum error: {max_error:.2f}%")
        print(f"    Parameters >2% error: {len(high_errors)}/{len(errors)}")

    return {
        'preset_name': preset_data['name'],
        'total_params': len(results),
        'successful': len(successful),
        'failed': len(failed),
        'avg_error': sum(e['error_pct'] for e in errors) / len(errors) if errors else 0,
        'max_error': max(e['error_pct'] for e in errors) if errors else 0,
        'high_error_count': len(high_errors) if errors else 0
    }


def main():
    print("="*70)
    print("REVERB PRESET LOADING TEST")
    print("="*70)

    # Get all Reverb presets
    print("\n[1/3] Loading Reverb presets from Firestore...")
    presets = get_reverb_presets()
    print(f"✓ Found {len(presets)} Reverb presets")

    # Select diverse presets to test
    print("\n[2/3] Selecting test presets...")

    # Try to get diverse categories
    categories = {}
    for p in presets:
        cat = p['category']
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(p)

    test_presets = []
    # Pick one from each category, max 5
    for cat, cat_presets in list(categories.items())[:5]:
        test_presets.append(cat_presets[0])

    print(f"✓ Selected {len(test_presets)} presets to test:")
    for p in test_presets:
        print(f"  - {p['name']} ({p['category']})")

    # Test each preset
    print("\n[3/3] Testing presets...")

    summary_results = []
    for preset in test_presets:
        result = test_preset(preset)
        summary_results.append(result)

    # Final summary
    print("\n" + "="*70)
    print("FINAL SUMMARY")
    print("="*70)

    for r in summary_results:
        status = "✅" if r['high_error_count'] == 0 and r['failed'] == 0 else "⚠️"
        print(f"\n{status} {r['preset_name']}")
        print(f"    Success rate: {r['successful']}/{r['total_params']}")
        print(f"    Avg error: {r['avg_error']:.2f}%")
        print(f"    Max error: {r['max_error']:.2f}%")
        if r['high_error_count'] > 0:
            print(f"    Params >2% error: {r['high_error_count']}")

    # Overall pass/fail
    all_passed = all(r['high_error_count'] == 0 and r['failed'] == 0 for r in summary_results)

    print("\n" + "="*70)
    if all_passed:
        print("✅ ALL PRESETS LOADED SUCCESSFULLY")
        print("All parameters within 2% error tolerance!")
    else:
        print("⚠️  SOME PRESETS HAD ERRORS")
        print("Review individual preset results above")
    print("="*70)

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
