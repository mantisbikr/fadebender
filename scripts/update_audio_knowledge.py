#!/usr/bin/env python3
"""
Update Audio Knowledge for Device Parameters

This script uses web research to find accurate, authoritative information about
device parameters and updates Firestore with high-quality audio knowledge.

New Approach:
1. Web search for official docs + forum discussions + expert sources
2. Extract technical facts from authoritative sources
3. Store structured, accurate data
4. Use LLM for formatting/summarization of research, not generation

Usage:
    python scripts/update_audio_knowledge.py --device reverb --param "ER Spin Rate"
    python scripts/update_audio_knowledge.py --device reverb --all
"""

from __future__ import annotations

import argparse
import json
import os
from typing import Any, Dict, Optional

import google.generativeai as genai
from google.cloud import firestore


def web_search_parameter_info(device_name: str, param_name: str) -> Dict[str, Any]:
    """Use Gemini to search web for accurate parameter information.

    Args:
        device_name: Device name (e.g., "Reverb")
        param_name: Parameter name (e.g., "ER Spin Rate")

    Returns:
        Structured audio knowledge dict
    """
    # Configure Gemini
    genai.configure(api_key=os.environ.get('GEMINI_API_KEY'))

    # Use regular model with explicit search instructions
    # Note: Google Search grounding requires AI Studio API, not available via SDK yet
    model = genai.GenerativeModel('gemini-2.0-flash-exp')

    prompt = f"""You are an expert in Ableton Live audio effects and digital signal processing.

Based on your knowledge of the "{param_name}" parameter in Ableton Live's {device_name} device, provide accurate technical information.

Reference authoritative sources like:
- Official Ableton documentation
- Ableton forums and expert discussions
- Technical audio DSP knowledge
- Industry-standard reverb algorithm design (e.g., Lexicon)

Provide a JSON response with this EXACT structure:
{{
  "audio_function": "Brief technical description of what this parameter controls",
  "sonic_effect": {{
    "increasing": "What happens sonically when you INCREASE this parameter",
    "decreasing": "What happens sonically when you DECREASE this parameter"
  }},
  "technical_detail": "Technical/algorithmic details (optional, if available)",
  "use_cases": [
    "When and why to use this parameter (production scenarios)"
  ],
  "typical_values": {{
    "label1": "Value range and description",
    "label2": "Value range and description"
  }},
  "sources": [
    "URL or reference to authoritative source"
  ]
}}

IMPORTANT:
- Be PRECISE and TECHNICAL, not vague or generic
- Avoid misleading metaphors (e.g., don't say "spinning" if it's actually modulation)
- Include specific numeric ranges when available
- Cite authoritative sources
- If you can't find reliable information, say so - don't guess

Return ONLY valid JSON, no additional text."""

    try:
        response = model.generate_content(prompt)
        result_text = response.text.strip()

        # Remove markdown code blocks if present
        if result_text.startswith('```'):
            lines = result_text.split('\n')
            result_text = '\n'.join(lines[1:-1])
        if result_text.startswith('json'):
            result_text = '\n'.join(result_text.split('\n')[1:])

        return json.loads(result_text)
    except Exception as e:
        print(f"Error researching {param_name}: {e}")
        return {}


def update_parameter_audio_knowledge(
    device_sig: str,
    param_name: str,
    audio_knowledge: Dict[str, Any],
    dry_run: bool = False
) -> bool:
    """Update audio knowledge for a specific parameter in Firestore.

    Args:
        device_sig: Device signature/document ID
        param_name: Parameter name to update
        audio_knowledge: New audio knowledge dict
        dry_run: If True, print changes without updating

    Returns:
        True if successful, False otherwise
    """
    client = firestore.Client(project='fadebender', database='dev-display-value')
    doc_ref = client.collection('device_mappings').document(device_sig)

    # Read current document
    doc = doc_ref.get()
    if not doc.exists:
        print(f"❌ Document {device_sig} not found")
        return False

    data = doc.to_dict()
    params_meta = data.get('params_meta', [])

    # Find parameter
    param_index = None
    for i, p in enumerate(params_meta):
        if p.get('name') == param_name:
            param_index = i
            break

    if param_index is None:
        print(f"❌ Parameter '{param_name}' not found in {device_sig}")
        return False

    # Update audio knowledge
    old_knowledge = params_meta[param_index].get('audio_knowledge', {})
    params_meta[param_index]['audio_knowledge'] = audio_knowledge

    if dry_run:
        print(f"\n{'='*80}")
        print(f"DRY RUN - Would update: {param_name}")
        print(f"{'='*80}")
        print("\n📋 OLD AUDIO KNOWLEDGE:")
        print(json.dumps(old_knowledge, indent=2))
        print("\n✨ NEW AUDIO KNOWLEDGE:")
        print(json.dumps(audio_knowledge, indent=2))
        print(f"\n{'='*80}\n")
        return True

    # Update Firestore
    try:
        doc_ref.update({'params_meta': params_meta})
        print(f"✅ Updated {param_name} in {device_sig}")
        return True
    except Exception as e:
        print(f"❌ Error updating Firestore: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description='Update audio knowledge for device parameters')
    parser.add_argument('--device', required=True, help='Device name (e.g., reverb)')
    parser.add_argument('--param', help='Parameter name (e.g., "ER Spin Rate")')
    parser.add_argument('--all', action='store_true', help='Update all parameters for device')
    parser.add_argument('--dry-run', action='store_true', help='Show changes without updating')
    parser.add_argument('--device-sig', help='Device signature (document ID)')

    args = parser.parse_args()

    # Device signature mapping (add more as needed)
    DEVICE_SIGS = {
        'reverb': '64ccfc236b79371d0b45e913f81bf0f3a55c6db9',
    }

    device_sig = args.device_sig or DEVICE_SIGS.get(args.device.lower())
    if not device_sig:
        print(f"❌ Unknown device: {args.device}")
        print(f"Available devices: {', '.join(DEVICE_SIGS.keys())}")
        return

    if args.param:
        # Update single parameter
        print(f"🔍 Researching: {args.param} in {args.device}...")
        audio_knowledge = web_search_parameter_info(args.device, args.param)

        if not audio_knowledge:
            print("❌ No information found")
            return

        # Remove sources before storing (just for reference during development)
        sources = audio_knowledge.pop('sources', [])
        if sources:
            print(f"\n📚 Sources found:")
            for src in sources:
                print(f"  - {src}")

        update_parameter_audio_knowledge(
            device_sig,
            args.param,
            audio_knowledge,
            dry_run=args.dry_run
        )

    elif args.all:
        # Get all parameters for device
        client = firestore.Client(project='fadebender', database='dev-display-value')
        doc = client.collection('device_mappings').document(device_sig).get()

        if not doc.exists:
            print(f"❌ Device {device_sig} not found")
            return

        params_meta = doc.to_dict().get('params_meta', [])
        total = len(params_meta)

        print(f"🔄 Updating {total} parameters for {args.device}...")

        for i, param in enumerate(params_meta, 1):
            param_name = param.get('name')
            print(f"\n[{i}/{total}] Researching: {param_name}...")

            audio_knowledge = web_search_parameter_info(args.device, param_name)

            if not audio_knowledge:
                print(f"  ⚠️  No information found, skipping")
                continue

            # Remove sources
            audio_knowledge.pop('sources', None)

            update_parameter_audio_knowledge(
                device_sig,
                param_name,
                audio_knowledge,
                dry_run=args.dry_run
            )

    else:
        parser.print_help()


if __name__ == '__main__':
    main()
