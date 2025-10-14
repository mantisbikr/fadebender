#!/usr/bin/env python3
"""
Upload preset images to GCS and link them to Firestore presets.

Usage:
  python3 scripts/upload_preset_images.py --images-dir /Users/sunils/Desktop/reverb_presets --device-type reverb

Creates thumbnails (300x200) and uploads both full and thumbnail versions to GCS.
Updates Firestore presets with image_url and thumbnail_url fields.
"""
import argparse
import os
import sys
from pathlib import Path
from typing import Optional

try:
    from google.cloud import firestore, storage
    from PIL import Image
except ImportError as e:
    print(f"Missing dependency: {e}")
    print("Install: pip install google-cloud-firestore google-cloud-storage pillow")
    sys.exit(1)


# GCS Configuration
BUCKET_NAME = "fadebender-presets"
BASE_PATH = "images"  # images/reverb/full/..., images/reverb/thumbnails/...

# Thumbnail settings
THUMBNAIL_WIDTH = 300
THUMBNAIL_HEIGHT = 200


def create_thumbnail(image_path: Path, output_path: Path, width: int = 300, height: int = 200) -> bool:
    """Create a thumbnail from an image, maintaining aspect ratio within bounds.

    Args:
        image_path: Path to original image
        output_path: Path to save thumbnail
        width: Max thumbnail width
        height: Max thumbnail height

    Returns:
        True if successful, False otherwise
    """
    try:
        with Image.open(image_path) as img:
            # Calculate thumbnail size maintaining aspect ratio
            img.thumbnail((width, height), Image.Resampling.LANCZOS)
            # Save thumbnail
            img.save(output_path, optimize=True)
            print(f"  ✓ Created thumbnail: {output_path.name} ({img.width}x{img.height})")
            return True
    except Exception as e:
        print(f"  ✗ Failed to create thumbnail: {e}")
        return False


def upload_to_gcs(bucket, local_path: Path, gcs_path: str) -> Optional[str]:
    """Upload file to GCS and return public URL.

    Args:
        bucket: GCS bucket object
        local_path: Local file path
        gcs_path: Destination path in GCS

    Returns:
        Public URL if successful, None otherwise
    """
    try:
        blob = bucket.blob(gcs_path)
        blob.upload_from_filename(str(local_path))
        # Make publicly accessible
        blob.make_public()
        public_url = blob.public_url
        print(f"  ✓ Uploaded to GCS: {gcs_path}")
        return public_url
    except Exception as e:
        print(f"  ✗ Failed to upload {gcs_path}: {e}")
        return None


def update_preset_in_firestore(db, preset_id: str, image_url: str, thumbnail_url: str, width: int, height: int) -> bool:
    """Update Firestore preset document with image URLs.

    Args:
        db: Firestore client
        preset_id: Preset document ID
        image_url: Full image URL
        thumbnail_url: Thumbnail URL
        width: Original image width
        height: Original image height

    Returns:
        True if successful, False otherwise
    """
    try:
        doc_ref = db.collection("presets").document(preset_id)
        doc = doc_ref.get()

        if not doc.exists:
            print(f"  ✗ Preset {preset_id} not found in Firestore")
            return False

        doc_ref.update({
            "image_url": image_url,
            "thumbnail_url": thumbnail_url,
            "image_width": width,
            "image_height": height,
            "updated_at": firestore.SERVER_TIMESTAMP,
        })
        print(f"  ✓ Updated Firestore preset: {preset_id}")
        return True
    except Exception as e:
        print(f"  ✗ Failed to update Firestore: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Upload preset images to GCS and link to Firestore")
    parser.add_argument("--images-dir", required=True, help="Directory containing preset images")
    parser.add_argument("--device-type", required=True, help="Device type (reverb, delay, etc.)")
    parser.add_argument("--project", default="fadebender", help="GCP project ID")
    parser.add_argument("--database", default="dev-display-value", help="Firestore database ID")
    parser.add_argument("--dry-run", action="store_true", help="Don't actually upload or update")
    args = parser.parse_args()

    images_dir = Path(args.images_dir)
    if not images_dir.exists():
        print(f"Error: Images directory not found: {images_dir}")
        return 1

    # Initialize GCS and Firestore clients
    print(f"Initializing GCS bucket: {BUCKET_NAME}")
    storage_client = storage.Client(project=args.project)
    bucket = storage_client.bucket(BUCKET_NAME)

    # Create bucket if it doesn't exist
    if not args.dry_run:
        if not bucket.exists():
            print(f"Creating bucket: {BUCKET_NAME}")
            bucket = storage_client.create_bucket(BUCKET_NAME, location="us-central1")
        else:
            print(f"Using existing bucket: {BUCKET_NAME}")

    print(f"Initializing Firestore: {args.project}/{args.database}")
    db = firestore.Client(project=args.project, database=args.database)

    # Find all image files
    image_extensions = {".png", ".jpg", ".jpeg"}
    image_files = [f for f in images_dir.iterdir() if f.suffix.lower() in image_extensions]

    if not image_files:
        print(f"No images found in {images_dir}")
        return 1

    print(f"\nFound {len(image_files)} images to process\n")

    # Create temp directory for thumbnails
    temp_dir = images_dir / "_thumbnails"
    if not args.dry_run:
        temp_dir.mkdir(exist_ok=True)

    success_count = 0
    skip_count = 0
    error_count = 0

    for image_path in sorted(image_files):
        preset_id = image_path.stem  # Filename without extension
        print(f"Processing: {image_path.name} → {preset_id}")

        if args.dry_run:
            print(f"  [DRY RUN] Would upload full image and thumbnail")
            print(f"  [DRY RUN] Would update preset: {preset_id}")
            success_count += 1
            continue

        # Get original image dimensions
        try:
            with Image.open(image_path) as img:
                orig_width, orig_height = img.size
        except Exception as e:
            print(f"  ✗ Failed to read image: {e}")
            error_count += 1
            continue

        # Create thumbnail
        thumbnail_path = temp_dir / image_path.name
        if not create_thumbnail(image_path, thumbnail_path, THUMBNAIL_WIDTH, THUMBNAIL_HEIGHT):
            error_count += 1
            continue

        # Upload full image
        full_gcs_path = f"{BASE_PATH}/{args.device_type}/full/{image_path.name}"
        full_url = upload_to_gcs(bucket, image_path, full_gcs_path)
        if not full_url:
            error_count += 1
            continue

        # Upload thumbnail
        thumb_gcs_path = f"{BASE_PATH}/{args.device_type}/thumbnails/{image_path.name}"
        thumb_url = upload_to_gcs(bucket, thumbnail_path, thumb_gcs_path)
        if not thumb_url:
            error_count += 1
            continue

        # Update Firestore
        if update_preset_in_firestore(db, preset_id, full_url, thumb_url, orig_width, orig_height):
            success_count += 1
        else:
            skip_count += 1

        print()  # Blank line between images

    # Cleanup temp directory
    if not args.dry_run and temp_dir.exists():
        import shutil
        shutil.rmtree(temp_dir)

    # Summary
    print("=" * 60)
    print(f"✓ Successfully processed: {success_count}")
    print(f"⊘ Skipped (preset not found): {skip_count}")
    print(f"✗ Errors: {error_count}")
    print(f"Total: {len(image_files)}")
    print("=" * 60)

    return 0 if error_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
