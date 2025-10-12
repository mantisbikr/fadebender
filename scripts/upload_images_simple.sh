#!/bin/bash
# Simple image upload script using macOS sips and gcloud
# Usage: ./upload_images_simple.sh /path/to/images reverb

set -e

IMAGES_DIR=$1
DEVICE_TYPE=$2
MANUFACTURER=${3:-ableton-live}
CATEGORY=${4:-audio-effects}
BUCKET="fadebender-assets"

if [ -z "$IMAGES_DIR" ] || [ -z "$DEVICE_TYPE" ]; then
    echo "Usage: $0 <images-dir> <device-type> [manufacturer] [category]"
    echo "Example: $0 /Users/sunils/Desktop/reverb_presets reverb ableton-live audio-effects"
    echo "Defaults: manufacturer=ableton-live, category=audio-effects"
    exit 1
fi

if [ ! -d "$IMAGES_DIR" ]; then
    echo "Error: Directory not found: $IMAGES_DIR"
    exit 1
fi

echo "Creating GCS bucket if needed..."
gsutil mb -p fadebender -l us-central1 gs://${BUCKET}/ 2>/dev/null || echo "Bucket already exists"

echo "Processing images from: $IMAGES_DIR"
cd "$IMAGES_DIR"

# Create temp dir for thumbnails
mkdir -p _thumbnails

# Process all image files
shopt -s nullglob
for img in *.png *.jpg *.jpeg; do
    [ -f "$img" ] || continue

    echo ""
    echo "Processing: $img"

    # Create thumbnail using macOS sips (built-in)
    echo "  Creating thumbnail (300x200)..."
    sips -Z 300 "$img" --out "_thumbnails/$img" > /dev/null

    # Upload full image (following knowledge base structure)
    echo "  Uploading full image..."
    gsutil -m cp "$img" "gs://${BUCKET}/images/${MANUFACTURER}/${CATEGORY}/${DEVICE_TYPE}/full/$img"
    gsutil acl ch -u AllUsers:R "gs://${BUCKET}/images/${MANUFACTURER}/${CATEGORY}/${DEVICE_TYPE}/full/$img"

    # Upload thumbnail
    echo "  Uploading thumbnail..."
    gsutil -m cp "_thumbnails/$img" "gs://${BUCKET}/images/${MANUFACTURER}/${CATEGORY}/${DEVICE_TYPE}/thumbnails/$img"
    gsutil acl ch -u AllUsers:R "gs://${BUCKET}/images/${MANUFACTURER}/${CATEGORY}/${DEVICE_TYPE}/thumbnails/$img"

    echo "  ✓ Done: $img"
done

echo ""
echo "All images uploaded!"
echo "Run: python3 scripts/link_images_to_presets.py --device-type ${DEVICE_TYPE}"
