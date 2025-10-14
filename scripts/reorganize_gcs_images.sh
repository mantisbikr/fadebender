#!/bin/bash
# Reorganize GCS images to match knowledge base structure
# From: gs://fadebender-presets/images/reverb/...
# To:   gs://fadebender-presets/images/ableton-live/audio-effects/reverb/...

set -e

BUCKET="fadebender-assets"
DEVICE_TYPE=$1

if [ -z "$DEVICE_TYPE" ]; then
    echo "Usage: $0 <device-type>"
    echo "Example: $0 reverb"
    exit 1
fi

echo "Reorganizing ${DEVICE_TYPE} images to ableton-live/audio-effects/ structure..."

# Move full images
echo "Moving full images..."
gsutil -m mv "gs://${BUCKET}/images/${DEVICE_TYPE}/full/*" \
    "gs://${BUCKET}/images/ableton-live/audio-effects/${DEVICE_TYPE}/full/"

# Move thumbnails
echo "Moving thumbnails..."
gsutil -m mv "gs://${BUCKET}/images/${DEVICE_TYPE}/thumbnails/*" \
    "gs://${BUCKET}/images/ableton-live/audio-effects/${DEVICE_TYPE}/thumbnails/"

# Clean up old directories
echo "Cleaning up old directories..."
gsutil -m rm -r "gs://${BUCKET}/images/${DEVICE_TYPE}/" || true

echo "✓ Done! New structure:"
echo "  gs://${BUCKET}/images/ableton-live/audio-effects/${DEVICE_TYPE}/full/"
echo "  gs://${BUCKET}/images/ableton-live/audio-effects/${DEVICE_TYPE}/thumbnails/"
