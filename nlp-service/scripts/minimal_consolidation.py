#!/usr/bin/env python3
"""
Enhanced consolidation: Merge audio_knowledge, manual_context, and sections
into dev-display-value database.

This creates a comprehensive knowledge base for LLM-based audio assistance.
"""

import json
from pathlib import Path
from google.cloud import firestore

REVERB_SIGNATURE = "64ccfc236b79371d0b45e913f81bf0f3a55c6db9"
MANUAL_CONTEXT_FILE = Path(__file__).parent.parent / "docs" / "technical" / "reverb_manual_context.json"


def minimal_consolidation():
    """Merge audio_knowledge, manual_context, and sections into dev-display-value."""

    print("="*70)
    print("ENHANCED KNOWLEDGE CONSOLIDATION")
    print("="*70)

    # Load manual context
    print("\n[1/5] Loading Ableton manual context...")
    with open(MANUAL_CONTEXT_FILE, 'r') as f:
        manual_data = json.load(f)

    manual_context_map = manual_data['manual_context']
    sections_data = manual_data['sections']
    print(f"✓ Loaded manual context for {len(manual_context_map)} parameters")
    print(f"✓ Loaded {len(sections_data)} sections")

    # Get DEFAULT database
    client_default = firestore.Client()
    print("\n[2/5] Reading from DEFAULT database...")

    doc_default = client_default.collection('device_mappings').document(REVERB_SIGNATURE).get()
    if not doc_default.exists:
        print("❌ Reverb mapping not found in DEFAULT database!")
        return False

    data_default = doc_default.to_dict()
    params_meta_default = data_default.get('params_meta', [])
    device_name_default = data_default.get('device_name')

    # Extract audio_knowledge
    audio_knowledge_map = {}
    for param in params_meta_default:
        if 'audio_knowledge' in param:
            audio_knowledge_map[param['name']] = param['audio_knowledge']

    print(f"✓ Found {len(audio_knowledge_map)} parameters with audio_knowledge")
    print(f"✓ Found device_name: {device_name_default}")

    # Get dev-display-value database
    client_dev = firestore.Client(database='dev-display-value')
    print("\n[3/5] Reading from dev-display-value database...")

    doc_dev = client_dev.collection('device_mappings').document(REVERB_SIGNATURE).get()
    if not doc_dev.exists:
        print("❌ Reverb mapping not found in dev-display-value database!")
        return False

    data_dev = doc_dev.to_dict()
    params_meta_dev = data_dev.get('params_meta', [])
    print(f"✓ Found {len(params_meta_dev)} parameters")

    # Merge audio_knowledge AND manual_context
    print("\n[4/5] Merging knowledge into dev-display-value...")
    updated_audio = 0
    updated_manual = 0

    for param in params_meta_dev:
        param_name = param.get('name')

        # Add audio_knowledge (from DEFAULT database)
        # Handle name variant (Dry_Wet vs Dry/Wet)
        if param_name in audio_knowledge_map:
            param['audio_knowledge'] = audio_knowledge_map[param_name]
            updated_audio += 1
        elif param_name == 'Dry/Wet' and 'Dry_Wet' in audio_knowledge_map:
            param['audio_knowledge'] = audio_knowledge_map['Dry_Wet']
            updated_audio += 1

        # Add manual_context (from Ableton manual)
        if param_name in manual_context_map:
            param['manual_context'] = manual_context_map[param_name]
            updated_manual += 1
            print(f"  ✓ {param_name} (audio + manual)")
        elif param_name in audio_knowledge_map:
            print(f"  ✓ {param_name} (audio only)")

    print(f"\n✓ Updated {updated_audio} parameters with audio_knowledge")
    print(f"✓ Updated {updated_manual} parameters with manual_context")

    # Save back to dev-display-value
    print("\n[5/5] Saving to dev-display-value...")
    doc_ref_dev = client_dev.collection('device_mappings').document(REVERB_SIGNATURE)

    # Update params_meta, device_name, AND sections
    update_data = {
        'params_meta': params_meta_dev,
        'device_name': device_name_default,
        'sections': sections_data,
        'device_description': manual_data.get('device_description', '')
    }

    doc_ref_dev.update(update_data)
    print("✓ Saved successfully")

    # Verify
    print("\n" + "="*70)
    print("VERIFICATION")
    print("="*70)

    doc_verify = client_dev.collection('device_mappings').document(REVERB_SIGNATURE).get()
    data_verify = doc_verify.to_dict()
    params_verify = data_verify.get('params_meta', [])
    device_name_verify = data_verify.get('device_name')
    sections_verify = data_verify.get('sections', {})

    with_audio = sum(1 for p in params_verify if 'audio_knowledge' in p)
    with_manual = sum(1 for p in params_verify if 'manual_context' in p)
    with_fits = sum(1 for p in params_verify if 'fit' in p)
    with_boundaries = sum(1 for p in params_verify if p.get('min_display') is not None)

    print(f"\ndev-display-value database now has:")
    print(f"  device_name: {device_name_verify}")
    print(f"  device_description: {bool(data_verify.get('device_description'))}")
    print(f"  Total params: {len(params_verify)}")
    print(f"  With audio_knowledge: {with_audio}")
    print(f"  With manual_context: {with_manual}")
    print(f"  With fits: {with_fits}")
    print(f"  With boundaries: {with_boundaries}")
    print(f"  Has grouping metadata: {bool(data_verify.get('grouping'))}")
    print(f"  Sections defined: {len(sections_verify)}")

    success = (
        with_audio == len(audio_knowledge_map) and
        with_manual > 0 and
        len(sections_verify) == len(sections_data) and
        device_name_verify == device_name_default
    )

    if success:
        print("\n✅ ENHANCED CONSOLIDATION SUCCESSFUL!")
        print("\n🎉 dev-display-value now has:")
        print("  ✓ Audio engineering knowledge (your expertise)")
        print("  ✓ Ableton manual context (official definitions)")
        print("  ✓ Section groupings (for LLM navigation)")
        print("  ✓ Display-value presets (curve fitting)")
        print("\n💡 This comprehensive knowledge base enables:")
        print("  - High-level device discovery ('I want airy guitars')")
        print("  - Section-based guidance ('tell me about Early Reflections')")
        print("  - Parameter-specific tuning ('how to make it brighter')")
        print("\nNext step: Update .env to set FIRESTORE_DATABASE_ID=dev-display-value")
        return True
    else:
        print("\n⚠️  Something went wrong")
        print(f"  Expected audio_knowledge: {len(audio_knowledge_map)}, got: {with_audio}")
        print(f"  Expected manual_context: {len(manual_context_map)}, got: {with_manual}")
        print(f"  Expected sections: {len(sections_data)}, got: {len(sections_verify)}")
        return False


if __name__ == "__main__":
    import sys
    sys.exit(0 if minimal_consolidation() else 1)
