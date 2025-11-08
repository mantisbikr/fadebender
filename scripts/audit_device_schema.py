#!/usr/bin/env python3
"""Audit device mapping schemas in dev-display-value database."""
import os
os.environ['FIRESTORE_DATABASE_ID'] = 'dev-display-value'

from google.cloud import firestore

def audit_devices():
    client = firestore.Client(database='dev-display-value')
    docs = client.collection('device_mappings').stream()

    print('='*80)
    print('DEVICE SCHEMA STATUS AUDIT')
    print('='*80)
    print()

    devices = []
    for doc in docs:
        data = doc.to_dict()
        device_name = data.get('device_name', 'N/A')
        params_meta = data.get('params_meta', [])

        # Check schema status
        has_fit_type = any('fit_type' in p for p in params_meta)
        has_control_type = any('control_type' in p for p in params_meta)
        has_fit_object = any(isinstance(p.get('fit'), dict) for p in params_meta)
        has_grouping = 'grouping' in data
        has_sections = 'sections' in data

        # Count param types
        binary_count = sum(1 for p in params_meta if p.get('control_type') == 'binary' or p.get('fit_type') == 'binary')
        quant_count = sum(1 for p in params_meta if p.get('control_type') == 'quantized' or p.get('fit_type') == 'quantized')
        cont_count = sum(1 for p in params_meta if p.get('control_type') == 'continuous' or p.get('fit_type') == 'linear')

        # Determine status
        if has_control_type and has_fit_object and has_grouping and has_sections:
            status = '✅ STANDARD'
        elif has_control_type and has_grouping and has_sections:
            status = '⚠️  PARTIAL'
        elif has_fit_type:
            status = '❌ LEGACY'
        else:
            status = '⚠️  UNKNOWN'

        devices.append({
            'sig': doc.id[:8],
            'full_sig': doc.id,
            'name': device_name,
            'status': status,
            'params': len(params_meta),
            'binary': binary_count,
            'quant': quant_count,
            'cont': cont_count,
            'has_grouping': has_grouping,
            'has_sections': has_sections,
            'has_fit_type': has_fit_type,
            'has_control_type': has_control_type,
            'has_fit_object': has_fit_object
        })

    # Sort by status then name
    devices.sort(key=lambda x: (x['status'], x['name']))

    # Print header
    header = f"{'Signature':<10} {'Device':<20} {'Status':<12} {'Params':<7} {'B/Q/C':<10} {'Grp':<5} {'Sec':<5}"
    print(header)
    print('-'*80)

    # Print devices
    for d in devices:
        bqc = f"{d['binary']}/{d['quant']}/{d['cont']}"
        grp = '✓' if d['has_grouping'] else '✗'
        sec = '✓' if d['has_sections'] else '✗'
        row = f"{d['sig']:<10} {d['name']:<20} {d['status']:<12} {d['params']:<7} {bqc:<10} {grp:<5} {sec:<5}"
        print(row)

    print()
    print('='*80)
    print('SUMMARY')
    print('='*80)
    standard = sum(1 for d in devices if '✅' in d['status'])
    partial = sum(1 for d in devices if '⚠️' in d['status'])
    legacy = sum(1 for d in devices if '❌' in d['status'])
    print(f'✅ Standard schema: {standard} devices')
    print(f'⚠️  Partial/Unknown:  {partial} devices')
    print(f'❌ Legacy schema:   {legacy} devices')
    print()

    # Print details on devices needing work
    needs_work = [d for d in devices if '❌' in d['status'] or '⚠️' in d['status']]
    if needs_work:
        print('='*80)
        print('DEVICES NEEDING STANDARDIZATION')
        print('='*80)
        for d in needs_work:
            print(f"\n{d['name']} ({d['sig']})")
            print(f"  Signature: {d['full_sig']}")
            print(f"  Status: {d['status']}")
            print(f"  Has fit_type: {d['has_fit_type']}")
            print(f"  Has control_type: {d['has_control_type']}")
            print(f"  Has fit object: {d['has_fit_object']}")
            print(f"  Has grouping: {d['has_grouping']}")
            print(f"  Has sections: {d['has_sections']}")

    return devices

if __name__ == '__main__':
    audit_devices()
