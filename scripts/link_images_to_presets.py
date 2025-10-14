#!/usr/bin/env python3
"""Link uploaded images to Firestore presets."""
import argparse
import sys
from pathlib import Path

try:
    from google.cloud import firestore
except ImportError:
    print("Install: pip install google-cloud-firestore")
    sys.exit(1)

BUCKET_NAME = "fadebender-assets"
BASE_URL = f"https://storage.googleapis.com/{BUCKET_NAME}"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--device-type", required=True, help="Device type (reverb, delay, etc.)")
    parser.add_argument("--images-dir", required=True, help="Local images directory")
    parser.add_argument("--manufacturer", default="ableton-live", help="Manufacturer/DAW (default: ableton-live)")
    parser.add_argument("--category", default="audio-effects", help="Category (default: audio-effects)")
    parser.add_argument("--project", default="fadebender")
    parser.add_argument("--database", default="dev-display-value")
    args = parser.parse_args()

    images_dir = Path(args.images_dir)
    if not images_dir.exists():
        print(f"Error: {images_dir} not found")
        return 1

    # Initialize Firestore
    db = firestore.Client(project=args.project, database=args.database)

    # Find all images
    images = list(images_dir.glob("*.png")) + list(images_dir.glob("*.jpg")) + list(images_dir.glob("*.jpeg"))

    print(f"Found {len(images)} images")
    success = 0
    skip = 0

    for img_path in sorted(images):
        # Construct preset_id: device_type + _ + filename
        # e.g., reverb_ambience.png → reverb_ambience
        preset_id = f"{args.device_type}_{img_path.stem}"
        img_name = img_path.name

        # Construct URLs following knowledge base structure
        # gs://fadebender-presets/images/ableton-live/audio-effects/reverb/full/...
        base_path = f"images/{args.manufacturer}/{args.category}/{args.device_type}"
        full_url = f"{BASE_URL}/{base_path}/full/{img_name}"
        thumb_url = f"{BASE_URL}/{base_path}/thumbnails/{img_name}"

        print(f"Linking: {preset_id}")

        # Check if preset exists
        doc_ref = db.collection("presets").document(preset_id)
        doc = doc_ref.get()

        if not doc.exists:
            print(f"  ⊘ Preset not found: {preset_id}")
            skip += 1
            continue

        # Update preset
        try:
            doc_ref.update({
                "image_url": full_url,
                "thumbnail_url": thumb_url,
            })
            print(f"  ✓ Updated")
            success += 1
        except Exception as e:
            print(f"  ✗ Error: {e}")

    print(f"\n✓ Success: {success}")
    print(f"⊘ Skipped: {skip}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
