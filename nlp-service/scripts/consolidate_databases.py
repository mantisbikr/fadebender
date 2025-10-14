#!/usr/bin/env python3
"""
Consolidate audio_knowledge from DEFAULT database to dev-display-value database.

This copies ONLY the audio_knowledge field from params_meta in DEFAULT
to params_meta in dev-display-value, preserving all other data.
"""

from google.cloud import firestore

REVERB_SIGNATURE = "64ccfc236b79371d0b45e913f81bf0f3a55c6db9"


def consolidate_audio_knowledge():
    """Copy audio_knowledge from DEFAULT to dev-display-value."""

    print("="*70)
    print("CONSOLIDATING AUDIO KNOWLEDGE")
    print("="*70)

    # Get DEFAULT database
    client_default = firestore.Client()
    print("\n[1/4] Reading audio_knowledge from DEFAULT database...")

    doc_default = client_default.collection('device_mappings').document(REVERB_SIGNATURE).get()
    if not doc_default.exists:
        print("❌ Reverb mapping not found in DEFAULT database!")
        return False

    params_meta_default = doc_default.to_dict().get('params_meta', [])
    audio_knowledge_map = {}

    for param in params_meta_default:
        if 'audio_knowledge' in param:
            audio_knowledge_map[param['name']] = param['audio_knowledge']

    print(f"✓ Found {len(audio_knowledge_map)} parameters with audio_knowledge")

    # Get dev-display-value database
    client_dev = firestore.Client(database='dev-display-value')
    print("\n[2/4] Reading params_meta from dev-display-value database...")

    doc_dev = client_dev.collection('device_mappings').document(REVERB_SIGNATURE).get()
    if not doc_dev.exists:
        print("❌ Reverb mapping not found in dev-display-value database!")
        return False

    params_meta_dev = doc_dev.to_dict().get('params_meta', [])
    print(f"✓ Found {len(params_meta_dev)} parameters")

    # Merge audio_knowledge
    print("\n[3/4] Merging audio_knowledge into dev-display-value params_meta...")
    updated_count = 0

    for param in params_meta_dev:
        param_name = param.get('name')
        if param_name in audio_knowledge_map:
            param['audio_knowledge'] = audio_knowledge_map[param_name]
            updated_count += 1
            print(f"  ✓ {param_name}")

    print(f"\n✓ Updated {updated_count} parameters with audio_knowledge")

    # Save back to dev-display-value
    print("\n[4/4] Saving updated params_meta to dev-display-value...")
    doc_ref_dev = client_dev.collection('device_mappings').document(REVERB_SIGNATURE)
    doc_ref_dev.update({'params_meta': params_meta_dev})
    print("✓ Saved successfully")

    # Verify
    print("\n" + "="*70)
    print("VERIFICATION")
    print("="*70)

    doc_verify = client_dev.collection('device_mappings').document(REVERB_SIGNATURE).get()
    params_verify = doc_verify.to_dict().get('params_meta', [])
    with_audio = sum(1 for p in params_verify if 'audio_knowledge' in p)

    print(f"\ndev-display-value database now has:")
    print(f"  Total params: {len(params_verify)}")
    print(f"  With audio_knowledge: {with_audio}")
    print(f"  With fits: {sum(1 for p in params_verify if 'fit' in p)}")
    print(f"  With boundaries: {sum(1 for p in params_verify if p.get('min_display') is not None)}")

    if with_audio == len(audio_knowledge_map):
        print("\n✅ CONSOLIDATION SUCCESSFUL!")
        print("\nNext steps:")
        print("1. Update server to use FIRESTORE_DATABASE_ID=dev-display-value")
        print("2. Update all scripts to use firestore.Client(database='dev-display-value')")
        return True
    else:
        print("\n⚠️  Something went wrong - audio_knowledge count doesn't match")
        return False


if __name__ == "__main__":
    import sys
    sys.exit(0 if consolidate_audio_knowledge() else 1)
