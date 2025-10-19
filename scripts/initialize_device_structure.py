#!/usr/bin/env python3
"""
Initialize complete device structure (Reverb-style) from learn_device output.

This script takes basic device structure from learn_device (signature + params subcollection)
and transforms it into the complete Reverb format with:
- sections (high-level organization with descriptions)
- grouping (masters, dependents, dependent_master_values, apply_order, requires_for_effect)
- params_meta array in main document (complete metadata)

It also handles uploading preset images to GCS and linking them to Firestore presets.

Usage:
    # Initialize device structure from learn_device output
    python scripts/initialize_device_structure.py \\
        --signature 64ccfc236b79371d0b45e913f81bf0f3a55c6db9 \\
        --device-doc knowledge/ableton-live/audio-effects/delay.md \\
        --device-type delay

    # Include preset image upload
    python scripts/initialize_device_structure.py \\
        --signature 64ccfc236b79371d0b45e913f81bf0f3a55c6db9 \\
        --device-doc knowledge/ableton-live/audio-effects/delay.md \\
        --device-type delay \\
        --preset-images ~/Desktop/preset-images/delay_presets_images

    # Dry run to preview structure without applying
    python scripts/initialize_device_structure.py \\
        --signature 64ccfc236b79371d0b45e913f81bf0f3a55c6db9 \\
        --device-doc knowledge/ableton-live/audio-effects/delay.md \\
        --device-type delay \\
        --dry-run
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from google.cloud import firestore, storage
    from PIL import Image
except ImportError as e:
    print(f"❌ Missing dependency: {e}")
    print("Install: pip install google-cloud-firestore google-cloud-storage pillow")
    sys.exit(1)


# GCS Configuration for preset images
GCS_BUCKET_NAME = "fadebender-presets"
GCS_BASE_PATH = "images"
THUMBNAIL_WIDTH = 300
THUMBNAIL_HEIGHT = 200


def load_device_doc(filepath: str) -> Dict[str, Any]:
    """Parse device documentation markdown to extract parameter groups and context.

    Args:
        filepath: Path to device documentation markdown file

    Returns:
        Dict with 'groups' and 'description' fields
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Extract device overview/description (first paragraph after "## Overview")
    description = ""
    if "## Overview" in content:
        overview_section = content.split("## Overview")[1].split("##")[0].strip()
        # First paragraph only
        description = overview_section.split("\n\n")[0].strip()

    # Parse parameter groups from "## Parameter Groups" section
    groups = {}
    if "## Parameter Groups" in content:
        groups_section = content.split("## Parameter Groups")[1].split("##")[0]
        current_group = None
        current_params = []

        for line in groups_section.split("\n"):
            line = line.strip()
            # Group header like "- **Time & Sync**"
            if line.startswith("- **") and "**" in line[4:]:
                if current_group:
                    groups[current_group] = current_params
                current_group = line.split("**")[1]
                current_params = []
            # Parameter item like "  - **Delay Time knobs** — description"
            elif line.startswith("- **") or line.startswith("  - **"):
                param_line = line.lstrip("- ").split("**")[1].split("—")[0].strip()
                # Extract parameter name (before description)
                current_params.append(param_line)

        # Add last group
        if current_group:
            groups[current_group] = current_params

    return {
        "description": description,
        "groups": groups
    }


def get_learn_device_output(db: firestore.Client, signature: str) -> Optional[Dict[str, Any]]:
    """Fetch learn_device output from Firestore.

    Args:
        db: Firestore client
        signature: Device signature hash

    Returns:
        Device data with params_meta array or None
    """
    try:
        doc_ref = db.collection('device_mappings').document(signature)
        doc = doc_ref.get()

        if not doc.exists:
            print(f"❌ Device {signature} not found in Firestore")
            return None

        data = doc.to_dict()

        # Try params_meta first (new structure), then fallback to params subcollection (old structure)
        if 'params_meta' in data and data['params_meta']:
            # New structure: params stored in params_meta array
            params = data['params_meta']
            print(f"  Using params_meta array ({len(params)} params)")
        else:
            # Old structure: params in subcollection
            print(f"  Fetching params from subcollection...")
            params = []
            for param_doc in doc_ref.collection('params').stream():
                params.append(param_doc.to_dict())
            params.sort(key=lambda p: p.get('index', 0))
            print(f"  Found {len(params)} params in subcollection")

        data['params'] = params
        return data

    except Exception as e:
        print(f"❌ Error fetching device from Firestore: {e}")
        return None


def analyze_parameters(params: List[Dict[str, Any]], device_doc: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze parameters and propose structure.

    Args:
        params: List of parameters from learn_device
        device_doc: Parsed device documentation

    Returns:
        Proposed structure with sections, grouping, params_meta
    """
    # Build params_meta array
    params_meta = []
    for p in params:
        meta = {
            "name": p.get("name"),
            "index": p.get("index"),
            "control_type": p.get("control_type", "continuous"),
        }

        # Add type-specific fields
        if meta["control_type"] == "binary":
            meta["labels"] = p.get("labels", ["Off", "On"])
        elif meta["control_type"] == "quantized":
            meta["labels"] = p.get("labels", [])
            meta["label_map"] = p.get("label_map", {})
        elif meta["control_type"] == "continuous":
            meta["fit"] = p.get("fit")
            meta["min_display"] = p.get("min", 0.0)
            meta["max_display"] = p.get("max", 1.0)
            # Unit will need user confirmation
            meta["unit"] = p.get("unit", "")

        params_meta.append(meta)

    # Detect master/dependent parameters
    masters = []
    dependents = {}
    dependent_master_values = {}

    for p in params_meta:
        name = p["name"]
        # Common patterns for master switches
        if name.endswith(" On") or name.endswith(" Enable"):
            masters.append(name)
            # Find potential dependents (same prefix)
            prefix = name.rsplit(" ", 1)[0]
            for dep in params_meta:
                dep_name = dep["name"]
                if dep_name != name and dep_name.startswith(prefix):
                    dependents[dep_name] = name
                    dependent_master_values[dep_name] = 1.0  # Assume On = 1.0

    # Build sections from doc groups
    sections = {}
    doc_groups = device_doc.get("groups", {})

    for group_name, group_params in doc_groups.items():
        # Map group params to actual param names (fuzzy matching)
        matched_params = []
        for doc_param in group_params:
            for p in params_meta:
                # Fuzzy match: check if doc param is contained in actual param name
                if doc_param.lower() in p["name"].lower() or p["name"].lower() in doc_param.lower():
                    if p["name"] not in matched_params:
                        matched_params.append(p["name"])

        if matched_params:
            sections[group_name] = {
                "technical_name": group_name,
                "description": f"Controls for {group_name.lower()}",
                "sonic_focus": "User will provide sonic focus",
                "parameters": matched_params,
                "technical_notes": []
            }

    # Add Device On to Device section if exists
    device_on_param = next((p["name"] for p in params_meta if p["name"] == "Device On"), None)
    if device_on_param and "Device" not in sections:
        sections["Device"] = {
            "technical_name": "Device",
            "description": "Device on/off control",
            "sonic_focus": "Enable or disable the entire effect",
            "parameters": [device_on_param],
            "technical_notes": []
        }

    # Build grouping structure
    grouping = {
        "masters": masters,
        "dependents": dependents,
        "dependent_master_values": dependent_master_values,
        "apply_order": ["masters", "quantized", "dependents", "continuous"],
        "requires_for_effect": {}
    }

    return {
        "params_meta": params_meta,
        "sections": sections,
        "grouping": grouping
    }


def display_proposed_structure(proposed: Dict[str, Any], device_name: str) -> None:
    """Display proposed structure for user review.

    Args:
        proposed: Proposed structure dict
        device_name: Device name
    """
    print(f"\n{'='*80}")
    print(f"PROPOSED STRUCTURE FOR {device_name.upper()}")
    print(f"{'='*80}\n")

    # Display params_meta
    print(f"📋 PARAMETERS ({len(proposed['params_meta'])} total)")
    print(f"{'-'*80}")
    for p in proposed['params_meta']:
        control_type = p['control_type']
        print(f"  [{p['index']:2d}] {p['name']:<30} {control_type:>12}", end="")

        if control_type == "binary":
            print(f"  labels={p.get('labels', [])}")
        elif control_type == "quantized":
            print(f"  {len(p.get('labels', []))} labels")
        elif control_type == "continuous":
            unit = p.get('unit', '?')
            min_v = p.get('min_display', 0)
            max_v = p.get('max_display', 1)
            print(f"  {min_v}–{max_v} {unit}")
        else:
            print()

    print()

    # Display sections
    print(f"📦 SECTIONS ({len(proposed['sections'])} total)")
    print(f"{'-'*80}")
    for section_name, section in proposed['sections'].items():
        print(f"\n  {section_name}")
        print(f"    Description: {section['description']}")
        print(f"    Parameters ({len(section['parameters'])}):")
        for pname in section['parameters']:
            print(f"      - {pname}")

    print()

    # Display grouping
    grouping = proposed['grouping']
    print(f"🔗 GROUPING")
    print(f"{'-'*80}")
    print(f"  Masters ({len(grouping['masters'])}): {', '.join(grouping['masters']) or 'None'}")
    print(f"  Dependents ({len(grouping['dependents'])}): ")
    for dep, master in grouping['dependents'].items():
        print(f"    {dep} → {master}")

    print()


def get_user_confirmation() -> bool:
    """Ask user to confirm proposed structure.

    Returns:
        True if user confirms, False otherwise
    """
    print(f"\n{'='*80}")
    print("REVIEW AND CONFIRM")
    print(f"{'='*80}\n")
    print("Please review the proposed structure above.")
    print("You will have a chance to edit the JSON before applying.")
    print()

    response = input("Continue? [Y/n]: ").strip().lower()
    return response in ('', 'y', 'yes')


def save_proposed_structure(proposed: Dict[str, Any], output_path: str) -> None:
    """Save proposed structure to JSON file for user editing.

    Args:
        proposed: Proposed structure
        output_path: Path to save JSON file
    """
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(proposed, f, indent=2)
    print(f"✓ Saved proposed structure to: {output_path}")


def load_confirmed_structure(json_path: str) -> Optional[Dict[str, Any]]:
    """Load user-confirmed structure from JSON file.

    Args:
        json_path: Path to JSON file

    Returns:
        Confirmed structure or None
    """
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Error loading confirmed structure: {e}")
        return None


def apply_structure_to_firestore(
    db: firestore.Client,
    signature: str,
    device_name: str,
    device_type: str,
    structure: Dict[str, Any],
    dry_run: bool = False
) -> bool:
    """Apply complete structure to Firestore.

    Args:
        db: Firestore client
        signature: Device signature
        device_name: Device name
        device_type: Device type
        structure: Complete structure with params_meta, sections, grouping
        dry_run: If True, show what would be applied without updating

    Returns:
        True if successful
    """
    if dry_run:
        print(f"\n[DRY RUN] Would apply structure to device_mappings/{signature}")
        print(f"  - params_meta: {len(structure['params_meta'])} parameters")
        print(f"  - sections: {len(structure['sections'])} sections")
        print(f"  - grouping: {len(structure['grouping']['masters'])} masters, {len(structure['grouping']['dependents'])} dependents")
        return True

    try:
        doc_ref = db.collection('device_mappings').document(signature)

        # Update main document with complete structure
        doc_ref.update({
            'device_name': device_name,
            'device_type': device_type,
            'param_count': len(structure['params_meta']),
            'params_meta': structure['params_meta'],
            'sections': structure['sections'],
            'grouping': structure['grouping'],
            'metadata_status': 'structure_initialized',
        })

        print(f"✓ Applied complete structure to Firestore")
        return True

    except Exception as e:
        print(f"❌ Error applying structure to Firestore: {e}")
        import traceback
        traceback.print_exc()
        return False


def upload_preset_images(
    device_type: str,
    images_dir: str,
    db: firestore.Client,
    project: str = "fadebender",
    dry_run: bool = False
) -> Dict[str, int]:
    """Upload preset images to GCS and link to Firestore presets.

    Args:
        device_type: Device type (delay, reverb, etc.)
        images_dir: Directory containing preset images
        db: Firestore client
        project: GCP project ID
        dry_run: If True, show what would be done without uploading

    Returns:
        Dict with counts: {'success': N, 'skipped': M, 'errors': K}
    """
    images_path = Path(images_dir)
    if not images_path.exists():
        print(f"❌ Images directory not found: {images_dir}")
        return {'success': 0, 'skipped': 0, 'errors': 0}

    # Find all image files
    image_extensions = {".png", ".jpg", ".jpeg"}
    image_files = [f for f in images_path.iterdir() if f.suffix.lower() in image_extensions]

    if not image_files:
        print(f"⚠️  No images found in {images_dir}")
        return {'success': 0, 'skipped': 0, 'errors': 0}

    print(f"\n📸 Found {len(image_files)} preset images to upload")

    if dry_run:
        print(f"[DRY RUN] Would upload {len(image_files)} images to GCS")
        return {'success': len(image_files), 'skipped': 0, 'errors': 0}

    # Initialize GCS client
    storage_client = storage.Client(project=project)
    bucket = storage_client.bucket(GCS_BUCKET_NAME)

    # Create bucket if it doesn't exist
    if not bucket.exists():
        print(f"Creating GCS bucket: {GCS_BUCKET_NAME}")
        bucket = storage_client.create_bucket(GCS_BUCKET_NAME, location="us-central1")

    # Create temp directory for thumbnails
    temp_dir = images_path / "_thumbnails"
    temp_dir.mkdir(exist_ok=True)

    success_count = 0
    skip_count = 0
    error_count = 0

    for image_path in sorted(image_files):
        # Preset ID format: devicetype_filename (without extension)
        preset_id = f"{device_type}_{image_path.stem}"
        print(f"\nProcessing: {image_path.name} → {preset_id}")

        # Check if preset exists in Firestore
        doc_ref = db.collection("presets").document(preset_id)
        doc = doc_ref.get()

        if not doc.exists:
            print(f"  ⊘ Preset not found in Firestore: {preset_id}")
            skip_count += 1
            continue

        try:
            # Get original image dimensions
            with Image.open(image_path) as img:
                orig_width, orig_height = img.size

            # Create thumbnail
            thumbnail_path = temp_dir / image_path.name
            with Image.open(image_path) as img:
                img.thumbnail((THUMBNAIL_WIDTH, THUMBNAIL_HEIGHT), Image.Resampling.LANCZOS)
                img.save(thumbnail_path, optimize=True)
                print(f"  ✓ Created thumbnail: {img.width}x{img.height}")

            # Upload full image
            full_gcs_path = f"{GCS_BASE_PATH}/{device_type}/full/{image_path.name}"
            blob = bucket.blob(full_gcs_path)
            blob.upload_from_filename(str(image_path))
            blob.make_public()
            full_url = blob.public_url
            print(f"  ✓ Uploaded full image: {full_gcs_path}")

            # Upload thumbnail
            thumb_gcs_path = f"{GCS_BASE_PATH}/{device_type}/thumbnails/{image_path.name}"
            blob = bucket.blob(thumb_gcs_path)
            blob.upload_from_filename(str(thumbnail_path))
            blob.make_public()
            thumb_url = blob.public_url
            print(f"  ✓ Uploaded thumbnail: {thumb_gcs_path}")

            # Update Firestore preset
            doc_ref.update({
                "image_url": full_url,
                "thumbnail_url": thumb_url,
                "image_width": orig_width,
                "image_height": orig_height,
                "updated_at": firestore.SERVER_TIMESTAMP,
            })
            print(f"  ✓ Updated preset in Firestore")

            success_count += 1

        except Exception as e:
            print(f"  ✗ Error processing {image_path.name}: {e}")
            error_count += 1

    # Cleanup temp directory
    if temp_dir.exists():
        import shutil
        shutil.rmtree(temp_dir)

    return {'success': success_count, 'skipped': skip_count, 'errors': error_count}


def main():
    parser = argparse.ArgumentParser(
        description='Initialize complete device structure from learn_device output',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Initialize Delay device structure
  python scripts/initialize_device_structure.py \\
      --signature abc123... \\
      --device-doc knowledge/ableton-live/audio-effects/delay.md \\
      --device-type delay

  # Include preset image upload
  python scripts/initialize_device_structure.py \\
      --signature abc123... \\
      --device-doc knowledge/ableton-live/audio-effects/delay.md \\
      --device-type delay \\
      --preset-images ~/Desktop/preset-images/delay_presets_images

  # Dry run to preview structure
  python scripts/initialize_device_structure.py \\
      --signature abc123... \\
      --device-doc knowledge/ableton-live/audio-effects/delay.md \\
      --device-type delay \\
      --dry-run
        """
    )

    parser.add_argument('--signature', required=True, help='Device signature hash')
    parser.add_argument('--device-doc', required=True, help='Path to device documentation markdown')
    parser.add_argument('--device-type', required=True, help='Device type (delay, reverb, etc.)')
    parser.add_argument('--preset-images', help='Directory containing preset images to upload')
    parser.add_argument('--project', default='fadebender', help='GCP project ID')
    parser.add_argument('--database', default='dev-display-value', help='Firestore database ID')
    parser.add_argument('--output', help='Output JSON file path (default: temp file)')
    parser.add_argument('--dry-run', action='store_true', help='Preview changes without applying')

    args = parser.parse_args()

    # Validate device doc exists
    if not Path(args.device_doc).exists():
        print(f"❌ Device doc not found: {args.device_doc}")
        return 1

    # Initialize Firestore
    print(f"Initializing Firestore: {args.project}/{args.database}")
    db = firestore.Client(project=args.project, database=args.database)

    # Step 1: Fetch learn_device output
    print(f"\n{'='*80}")
    print("STEP 1: Fetch learn_device output from Firestore")
    print(f"{'='*80}\n")

    device_data = get_learn_device_output(db, args.signature)
    if not device_data:
        return 1

    device_name = device_data.get('device_name', 'Unknown')
    param_count = len(device_data.get('params', []))
    print(f"✓ Loaded device: {device_name} ({param_count} parameters)")

    # Step 2: Parse device documentation
    print(f"\n{'='*80}")
    print("STEP 2: Parse device documentation")
    print(f"{'='*80}\n")

    device_doc = load_device_doc(args.device_doc)
    print(f"✓ Parsed device doc: {len(device_doc['groups'])} parameter groups found")

    # Step 3: Analyze and propose structure
    print(f"\n{'='*80}")
    print("STEP 3: Analyze parameters and propose structure")
    print(f"{'='*80}\n")

    proposed = analyze_parameters(device_data['params'], device_doc)
    display_proposed_structure(proposed, device_name)

    # Step 4: Get user confirmation
    if not args.dry_run and not get_user_confirmation():
        print("❌ Aborted by user")
        return 1

    # Step 5: Save proposed structure for editing
    output_path = args.output or f"/tmp/{args.device_type}_structure_proposed.json"
    save_proposed_structure(proposed, output_path)

    if not args.dry_run:
        print(f"\n{'='*80}")
        print("STEP 4: Edit and confirm structure")
        print(f"{'='*80}\n")
        print(f"Please review and edit the proposed structure in:")
        print(f"  {output_path}")
        print()
        print("Update the following:")
        print("  1. Confirm/correct units for continuous parameters")
        print("  2. Add sonic_focus descriptions to sections")
        print("  3. Verify master/dependent relationships")
        print("  4. Add any requires_for_effect constraints")
        print()
        input("Press Enter when you're done editing and ready to apply...")

        # Load confirmed structure
        confirmed = load_confirmed_structure(output_path)
        if not confirmed:
            return 1
    else:
        confirmed = proposed

    # Step 6: Apply structure to Firestore
    print(f"\n{'='*80}")
    print("STEP 5: Apply structure to Firestore")
    print(f"{'='*80}\n")

    if not apply_structure_to_firestore(
        db, args.signature, device_name, args.device_type, confirmed, args.dry_run
    ):
        return 1

    # Step 7: Upload preset images (if provided)
    if args.preset_images:
        print(f"\n{'='*80}")
        print("STEP 6: Upload preset images to GCS")
        print(f"{'='*80}\n")

        results = upload_preset_images(
            args.device_type, args.preset_images, db, args.project, args.dry_run
        )

        print(f"\n{'='*80}")
        print("PRESET IMAGE UPLOAD SUMMARY")
        print(f"{'='*80}")
        print(f"✓ Successfully uploaded: {results['success']}")
        print(f"⊘ Skipped (preset not found): {results['skipped']}")
        print(f"✗ Errors: {results['errors']}")
        print(f"{'='*80}\n")

    # Final summary
    print(f"\n{'='*80}")
    print("✅ DEVICE STRUCTURE INITIALIZATION COMPLETE")
    print(f"{'='*80}\n")
    print(f"Device: {device_name} ({args.device_type})")
    print(f"Signature: {args.signature}")
    print(f"Parameters: {len(confirmed['params_meta'])}")
    print(f"Sections: {len(confirmed['sections'])}")
    print(f"Masters: {len(confirmed['grouping']['masters'])}")
    print(f"Dependents: {len(confirmed['grouping']['dependents'])}")
    print()
    print("Next steps:")
    print("  1. Phase 3: Classification & Boundary Detection")
    print("  2. Phase 4: Fit Continuous Parameters")
    print("  3. Phase 7: Audio Knowledge Curation")
    print(f"{'='*80}\n")

    return 0


if __name__ == '__main__':
    sys.exit(main())
