#!/bin/bash
# Emergency fix: Secure Cloud Run worker to prevent unauthorized LLM API usage

set -e

PROJECT_ID="fadebender"
REGION="us-central1"
SERVICE_NAME="preset-enricher"  # Note: NOT preset-enricher-worker!
# Pub/Sub config
TOPIC_NAME="preset-enrich"
SUBSCRIPTION_NAME="preset-enrich-sub"  # ensure this matches your actual subscription
# Service account used for OIDC push auth (recommended)
WORKER_SA="preset-enricher-sa@${PROJECT_ID}.iam.gserviceaccount.com"

echo "🔒 Securing Cloud Run worker from public access..."

# 1. Get project number for Pub/Sub service account
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format='value(projectNumber)')
PUBSUB_SA="service-${PROJECT_NUMBER}@gcp-sa-pubsub.iam.gserviceaccount.com"

# 2. Restrict to authenticated requests only
echo "📌 Step 1: Removing public access (allUsers invoker role)..."
gcloud run services remove-iam-policy-binding $SERVICE_NAME \
  --region=$REGION \
  --project=$PROJECT_ID \
  --member="allUsers" \
  --role="roles/run.invoker" 2>/dev/null || echo "  (already removed or never existed)"

echo "📌 Step 1b: Setting ingress to internal-only..."
gcloud run services update $SERVICE_NAME \
  --region=$REGION \
  --project=$PROJECT_ID \
  --ingress=internal-and-cloud-load-balancing

# 3. Grant Pub/Sub service account permission to invoke
echo "📌 Step 2: Granting Invoker to worker SA (used for OIDC push token)..."
gcloud run services add-iam-policy-binding $SERVICE_NAME \
  --region=$REGION \
  --project=$PROJECT_ID \
  --member="serviceAccount:${WORKER_SA}" \
  --role="roles/run.invoker" || true

echo "📌 Step 2b: Allow Pub/Sub service agent to mint OIDC tokens for worker SA..."
gcloud iam service-accounts add-iam-policy-binding ${WORKER_SA} \
  --project=$PROJECT_ID \
  --member="serviceAccount:${PUBSUB_SA}" \
  --role="roles/iam.serviceAccountTokenCreator" || true

# 4. Verify current settings
echo ""
echo "✅ Security settings updated!"
echo ""
echo "Current configuration:"
gcloud run services describe $SERVICE_NAME \
  --region=$REGION \
  --project=$PROJECT_ID \
  --format="table(
    status.url,
    spec.template.metadata.annotations.'run.googleapis.com/ingress'
  )"

echo ""
echo "IAM bindings:"
gcloud run services get-iam-policy $SERVICE_NAME \
  --region=$REGION \
  --project=$PROJECT_ID \
  --format="table(bindings.role,bindings.members)"

echo ""
echo "🔍 Testing public access (should fail):"
curl -s -w "\nHTTP Status: %{http_code}\n" https://preset-enricher-u4vgqt2gka-uc.a.run.app/health || echo "✅ Correctly blocked!"

echo ""
echo "📊 Recent invocation logs (last 1 hour):"
gcloud logging read \
  "resource.type=cloud_run_revision AND resource.labels.service_name=${SERVICE_NAME} AND timestamp>=\"$(date -u -v-1H '+%Y-%m-%dT%H:%M:%SZ')\"" \
  --limit=20 \
  --project=$PROJECT_ID \
  --format="table(timestamp,httpRequest.requestMethod,httpRequest.status,jsonPayload.message)"

echo ""
echo "📫 Updating Pub/Sub push subscription to use OIDC auth with worker SA..."
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region=$REGION --project=$PROJECT_ID --format='value(status.url)')
gcloud pubsub subscriptions update ${SUBSCRIPTION_NAME} \
  --project=$PROJECT_ID \
  --push-endpoint="$SERVICE_URL" \
  --push-auth-service-account="$WORKER_SA" \
  --push-auth-token-audience="$SERVICE_URL" || echo "(Create the subscription if it doesn't exist.)"

echo ""
echo "🔎 Subscription details:"
gcloud pubsub subscriptions describe ${SUBSCRIPTION_NAME} \
  --project=$PROJECT_ID \
  --format="value(pushConfig.pushEndpoint,pushConfig.oidcToken.serviceAccountEmail)"

echo ""
echo "⚠️  IMPORTANT: Redeploy the worker with updated code:"
echo "   cd cloud-workers/preset-enricher"
echo "   ./deploy.sh"
