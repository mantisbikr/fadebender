#!/bin/bash
#
# Set up GCP infrastructure for preset enrichment
#
# Creates:
# - Pub/Sub topic and subscription
# - GCS bucket for knowledge base
# - Service account with permissions
#
# Usage: ./setup-gcp.sh [PROJECT_ID] [REGION]
#

set -e

PROJECT_ID="${1:-fadebender}"
REGION="${2:-us-central1}"
TOPIC_NAME="preset-enrich"
SUBSCRIPTION_NAME="preset-enrich-sub"
KB_BUCKET="fadebender-kb"
SERVICE_ACCOUNT="preset-enricher-sa"

echo "=== Setting up GCP Infrastructure ==="
echo "Project: $PROJECT_ID"
echo "Region: $REGION"
echo ""

# Set project
gcloud config set project $PROJECT_ID

# Enable required APIs
echo "Enabling required APIs..."
gcloud services enable \
  run.googleapis.com \
  pubsub.googleapis.com \
  storage.googleapis.com \
  firestore.googleapis.com \
  aiplatform.googleapis.com \
  --project=$PROJECT_ID

echo ""
echo "=== Creating Pub/Sub Topic ==="
gcloud pubsub topics create $TOPIC_NAME \
  --project=$PROJECT_ID \
  2>/dev/null || echo "Topic $TOPIC_NAME already exists"

echo ""
echo "=== Creating GCS Bucket for Knowledge Base ==="
gsutil mb -p $PROJECT_ID -l $REGION gs://$KB_BUCKET/ \
  2>/dev/null || echo "Bucket $KB_BUCKET already exists"

echo ""
echo "=== Uploading Knowledge Base to GCS ==="
# Upload knowledge base files
if [ -d "../../knowledge" ]; then
  gsutil -m rsync -r ../../knowledge gs://$KB_BUCKET/
  echo "Knowledge base uploaded to gs://$KB_BUCKET/"
else
  echo "WARNING: knowledge/ directory not found. Upload manually:"
  echo "  gsutil -m rsync -r ./knowledge gs://$KB_BUCKET/"
fi

echo ""
echo "=== Creating Service Account ==="
gcloud iam service-accounts create $SERVICE_ACCOUNT \
  --display-name="Preset Enricher Service Account" \
  --project=$PROJECT_ID \
  2>/dev/null || echo "Service account $SERVICE_ACCOUNT already exists"

# Grant permissions
echo "Granting permissions to service account..."
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$SERVICE_ACCOUNT@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/datastore.user" \
  --condition=None

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$SERVICE_ACCOUNT@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/storage.objectViewer" \
  --condition=None

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$SERVICE_ACCOUNT@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/aiplatform.user" \
  --condition=None

echo ""
echo "=== Setup Complete ==="
echo ""
echo "Next steps:"
echo ""
echo "1. Deploy Cloud Run service:"
echo "   cd preset-enricher && ./deploy.sh $PROJECT_ID $REGION"
echo ""
echo "2. Get Cloud Run service URL:"
echo "   SERVICE_URL=\$(gcloud run services describe preset-enricher --region=$REGION --project=$PROJECT_ID --format='value(status.url)')"
echo ""
echo "3. Create Pub/Sub push subscription:"
echo "   gcloud pubsub subscriptions create $SUBSCRIPTION_NAME \\"
echo "     --topic=$TOPIC_NAME \\"
echo "     --push-endpoint=\$SERVICE_URL \\"
echo "     --ack-deadline=300 \\"
echo "     --project=$PROJECT_ID"
echo ""
echo "4. Update server .env:"
echo "   PUBSUB_TOPIC=$TOPIC_NAME"
echo "   VERTEX_PROJECT=$PROJECT_ID"
echo ""
echo "5. Restart server and test by loading a new preset in Ableton"
echo ""
