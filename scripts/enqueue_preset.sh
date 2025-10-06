#!/usr/bin/env bash
# Publish a single preset_enrich_requested message to Pub/Sub

set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <preset_id> [PROJECT_ID] [TOPIC_NAME]" >&2
  exit 1
fi

PRESET_ID="$1"
PROJECT_ID="${2:-${GOOGLE_CLOUD_PROJECT:-fadebender}}"
TOPIC_NAME="${3:-${TOPIC_NAME:-preset-enrich}}"

gcloud pubsub topics publish "$TOPIC_NAME" \
  --project="$PROJECT_ID" \
  --message="{\"event\":\"preset_enrich_requested\",\"preset_id\":\"$PRESET_ID\"}"

echo "✓ Enqueued $PRESET_ID to topic $TOPIC_NAME in $PROJECT_ID"

