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
  --no-allow-unauthenticated \
  --ingress=internal-and-cloud-load-balancing \
  --set-env-vars="VERTEX_PROJECT=$PROJECT_ID,VERTEX_LOCATION=$REGION,VERTEX_MODEL=gemini-2.5-flash,KB_BUCKET=fadebender-kb,FIRESTORE_PROJECT_ID=$PROJECT_ID,LLM_CHUNKED_ONLY=1,MAX_LLM_CALLS_PER_HOUR=20,USE_GENAI_PRIMARY=0,DISABLE_GENAI=1" \
  --clear-secrets \
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
echo "Optional: If you haven't created the secret yet, run:" 
echo "   echo -n 'YOUR_API_KEY' | gcloud secrets create llm-api-key --data-file=- --project=$PROJECT_ID || \\
          echo -n 'YOUR_API_KEY' | gcloud secrets versions add llm-api-key --data-file=- --project=$PROJECT_ID"
echo "And ensure the service account has Secret Manager access: roles/secretmanager.secretAccessor"
