#!/bin/bash
#
# Sync local knowledge base to GCS
#
# Usage: ./sync-kb.sh [PROJECT_ID]
#

set -e

PROJECT_ID="${1:-fadebender}"
KB_BUCKET="fadebender-kb"
KB_LOCAL="../knowledge"

echo "=== Syncing Knowledge Base to GCS ==="
echo "Local:  $KB_LOCAL"
echo "Bucket: gs://$KB_BUCKET/"
echo ""

# Check if local KB exists
if [ ! -d "$KB_LOCAL" ]; then
    echo "ERROR: Knowledge base directory not found: $KB_LOCAL"
    exit 1
fi

# Sync to GCS (only uploads new/changed files)
echo "Syncing..."
gsutil -m rsync -r -d $KB_LOCAL gs://$KB_BUCKET/

echo ""
echo "✅ Knowledge base synced to gs://$KB_BUCKET/"
echo ""
echo "Cloud workers will use updated KB immediately (no redeploy needed)"
echo ""
