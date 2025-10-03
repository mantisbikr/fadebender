#!/bin/bash
#
# Deploy preset enricher to Cloud Run
#
# Usage: ./deploy.sh [PROJECT_ID] [REGION]
#

set -e

PROJECT_ID="${1:-fadebender}"
REGION="${2:-us-central1}"
SERVICE_NAME="preset-enricher"

echo "=== Deploying Preset Enricher to Cloud Run ==="
echo "Project: $PROJECT_ID"
echo "Region: $REGION"
echo "Service: $SERVICE_NAME"
echo ""

# Build and deploy
gcloud run deploy $SERVICE_NAME \
  --source . \
  --project=$PROJECT_ID \
  --region=$REGION \
  --platform=managed \
  --allow-unauthenticated \
  --set-env-vars="VERTEX_PROJECT=$PROJECT_ID,VERTEX_LOCATION=$REGION,VERTEX_MODEL=gemini-2.5-flash,KB_BUCKET=fadebender-kb,FIRESTORE_PROJECT_ID=$PROJECT_ID" \
  --memory=512Mi \
  --cpu=1 \
  --timeout=300 \
  --max-instances=10 \
  --min-instances=0

echo ""
echo "=== Deployment Complete ==="
echo ""
echo "Next steps:"
echo "1. Get the service URL:"
echo "   gcloud run services describe $SERVICE_NAME --region=$REGION --project=$PROJECT_ID --format='value(status.url)'"
echo ""
echo "2. Create Pub/Sub push subscription (see setup-pubsub.sh)"
echo ""
