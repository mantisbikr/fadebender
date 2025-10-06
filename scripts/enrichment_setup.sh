#!/usr/bin/env bash
# One-shot setup for secure preset enrichment:
# - Deploy Cloud Run worker with Vertex-only (DISABLE_GENAI=1)
# - Configure IAM for OIDC push
# - Update Pub/Sub push subscription to use OIDC with worker SA
# - Optionally re-publish a test message

set -euo pipefail

PROJECT_ID="${1:-${GOOGLE_CLOUD_PROJECT:-fadebender}}"
REGION="${2:-${VERTEX_LOCATION:-us-central1}}"
TOPIC_NAME="${TOPIC_NAME:-preset-enrich}"
SUBSCRIPTION_NAME="${SUBSCRIPTION_NAME:-preset-enrich-sub}"
SERVICE_NAME="${SERVICE_NAME:-preset-enricher}"
WORKER_SA_NAME="${WORKER_SA_NAME:-preset-enricher-sa}"
WORKER_SA="${WORKER_SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"

echo "=== Enrichment Setup ==="
echo "Project:        $PROJECT_ID"
echo "Region:         $REGION"
echo "Service:        $SERVICE_NAME"
echo "Topic:          $TOPIC_NAME"
echo "Subscription:   $SUBSCRIPTION_NAME"
echo "Worker SA:      $WORKER_SA"

gcloud config set project "$PROJECT_ID" >/dev/null

echo "\n[1/6] Ensure service account exists: $WORKER_SA"
gcloud iam service-accounts create "$WORKER_SA_NAME" \
  --display-name="Preset Enricher Service Account" \
  --project="$PROJECT_ID" 2>/dev/null || true

echo "\n[2/6] Grant minimal roles to worker SA (Firestore, Storage, Vertex)"
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:$WORKER_SA" \
  --role="roles/datastore.user" --condition=None >/dev/null || true
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:$WORKER_SA" \
  --role="roles/storage.objectViewer" --condition=None >/dev/null || true
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:$WORKER_SA" \
  --role="roles/aiplatform.user" --condition=None >/dev/null || true

echo "\n[3/6] Deploy Cloud Run worker (Vertex-only, DISABLE_GENAI=1)"
pushd cloud-workers/preset-enricher >/dev/null
./deploy.sh "$PROJECT_ID" "$REGION"
popd >/dev/null

SERVICE_URL=$(gcloud run services describe "$SERVICE_NAME" --region="$REGION" --project="$PROJECT_ID" --format='value(status.url)')
echo "Service URL: $SERVICE_URL"

echo "\n[4/6] Allow worker SA to be invoked by Pub/Sub (Run Invoker)"
gcloud run services add-iam-policy-binding "$SERVICE_NAME" \
  --region="$REGION" \
  --project="$PROJECT_ID" \
  --member="serviceAccount:$WORKER_SA" \
  --role="roles/run.invoker" >/dev/null || true

echo "\n[5/6] Allow Pub/Sub service agent to mint OIDC tokens for worker SA"
PROJECT_NUMBER=$(gcloud projects describe "$PROJECT_ID" --format='value(projectNumber)')
PUBSUB_SA="service-${PROJECT_NUMBER}@gcp-sa-pubsub.iam.gserviceaccount.com"
gcloud iam service-accounts add-iam-policy-binding "$WORKER_SA" \
  --project="$PROJECT_ID" \
  --member="serviceAccount:${PUBSUB_SA}" \
  --role="roles/iam.serviceAccountTokenCreator" >/dev/null || true

echo "\n[6/6] Create or update push subscription with OIDC"
# Ensure topic exists
gcloud pubsub topics create "$TOPIC_NAME" --project="$PROJECT_ID" 2>/dev/null || true

if gcloud pubsub subscriptions describe "$SUBSCRIPTION_NAME" --project="$PROJECT_ID" >/dev/null 2>&1; then
  gcloud pubsub subscriptions update "$SUBSCRIPTION_NAME" \
    --project="$PROJECT_ID" \
    --push-endpoint="$SERVICE_URL" \
    --push-auth-service-account="$WORKER_SA" \
    --push-auth-token-audience="$SERVICE_URL"
else
  gcloud pubsub subscriptions create "$SUBSCRIPTION_NAME" \
    --project="$PROJECT_ID" \
    --topic="$TOPIC_NAME" \
    --push-endpoint="$SERVICE_URL" \
    --push-auth-service-account="$WORKER_SA" \
    --push-auth-token-audience="$SERVICE_URL" \
    --ack-deadline=300
fi

echo "\n✅ Setup complete"
echo "Subscription: $(gcloud pubsub subscriptions describe "$SUBSCRIPTION_NAME" --project="$PROJECT_ID" --format='value(pushConfig.oidcToken.serviceAccountEmail)')"
echo "\nYou can enqueue a test message:"
echo "gcloud pubsub topics publish $TOPIC_NAME --project=$PROJECT_ID --message='{"event":"preset_enrich_requested","preset_id":"reverb_big_room"}'"
