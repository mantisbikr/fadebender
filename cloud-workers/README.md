# Cloud Workers - Preset Metadata Enrichment

**Status:** Ready for deployment
**Architecture:** Pub/Sub → Cloud Run → Firestore + GCS

## Overview

This directory contains the Cloud Run worker that handles background preset metadata enrichment using LLM + knowledge base RAG.

### Architecture

```
┌──────────────┐
│   Ableton    │
│  (Load Dev)  │
└──────┬───────┘
       │
       ▼
┌──────────────────┐
│  Local Server    │  1. Captures preset (fast, minimal metadata)
│  /return/device  │  2. Saves to Firestore with values_status="verified"
│                  │  3. Enqueues Pub/Sub message (non-blocking)
└────────┬─────────┘
         │
         │ Pub/Sub: "preset_enrich_requested"
         │
         ▼
┌────────────────────────┐
│  Cloud Run Worker      │  4. Receives Pub/Sub push
│  preset-enricher       │  5. Loads preset from Firestore
│                        │  6. Fetches KB from GCS (*.md files)
│                        │  7. Generates rich metadata (LLM + RAG)
│                        │  8. Updates Firestore:
│                        │     - metadata_status="enriched"
│                        │     - metadata_version=2
│                        │     - enriched_at (timestamp)
└────────────────────────┘
         │
         ▼
┌──────────────────┐
│   Firestore      │  ✅ Preset now has rich metadata
│   presets/       │  ✅ Available to all users
└──────────────────┘
```

### Why Cloud Run?

**Problem:** Local server metadata generation is slow (5-10s) and blocks captures
**Solution:** Offload to Cloud Run workers that run in parallel

**Benefits:**
- ✅ **Non-blocking** - Local captures complete in <500ms
- ✅ **Scalable** - Auto-scales 0→10 instances based on queue depth
- ✅ **Richer metadata** - Uses full knowledge base from GCS
- ✅ **Cost-effective** - Pay per request, scales to zero
- ✅ **Versioned KB** - Update KB in GCS without server restart
- ✅ **Multi-user** - One enrichment serves all users

---

## Setup

### Prerequisites

1. **GCP Project** with billing enabled
2. **gcloud CLI** installed and authenticated
3. **Firestore** database created (Native mode)
4. **Service Account** key for local server (already have: `fadebender-service-key.json`)

### Step 1: Set up GCP Infrastructure

Run the setup script to create all required resources:

```bash
cd /Users/sunils/ai-projects/fadebender/cloud-workers
chmod +x setup-gcp.sh
./setup-gcp.sh fadebender us-central1
```

This creates:
- ✅ Pub/Sub topic: `preset-enrich`
- ✅ GCS bucket: `fadebender-kb` (with knowledge base uploaded)
- ✅ Service account: `preset-enricher-sa@fadebender.iam.gserviceaccount.com`
- ✅ IAM permissions: Firestore, Storage, Vertex AI

### Step 2: Deploy Cloud Run Worker

```bash
cd preset-enricher
chmod +x deploy.sh
./deploy.sh fadebender us-central1
```

This:
- Builds Docker image from source
- Deploys to Cloud Run (512Mi RAM, 1 CPU, auto-scale 0-10)
- Sets environment variables (project, model, bucket)
- Returns service URL (e.g., `https://preset-enricher-xxx.run.app`)

### Step 3: Create Pub/Sub Push Subscription

Get the Cloud Run service URL:

```bash
SERVICE_URL=$(gcloud run services describe preset-enricher \
  --region=us-central1 \
  --project=fadebender \
  --format='value(status.url)')
echo $SERVICE_URL
```

Create push subscription:

```bash
gcloud pubsub subscriptions create preset-enrich-sub \
  --topic=preset-enrich \
  --push-endpoint=$SERVICE_URL \
  --ack-deadline=300 \
  --project=fadebender
```

### Step 4: Update Local Server Config

Add to `/Users/sunils/ai-projects/fadebender/.env`:

```bash
# Enable Pub/Sub enqueueing
PUBSUB_TOPIC=preset-enrich
VERTEX_PROJECT=fadebender
```

Restart server:

```bash
cd /Users/sunils/ai-projects/fadebender
make restart-all
```

### Step 5: Test End-to-End

1. **Load a new preset in Ableton** (e.g., "Reverb Vocal Hall")

2. **Check local server logs** - should see:
   ```
   [AUTO-CAPTURE] Capturing new preset: reverb_vocal_hall
   [AUTO-CAPTURE] Extracted 35 parameter values
   [AUTO-CAPTURE] ✓ Saved preset reverb_vocal_hall to Firestore
   [PUBSUB] Enqueued preset_enrich_requested for reverb_vocal_hall
   ```

3. **Check Cloud Run logs** (1-2 minutes later):
   ```bash
   gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=preset-enricher" \
     --limit=50 \
     --project=fadebender \
     --format=json
   ```

   Should see:
   ```
   [WORKER] Received event: preset_enrich_requested, preset_id: reverb_vocal_hall
   [WORKER] Processing preset: Vocal Hall (reverb)
   [WORKER] Parameter count: 35
   [WORKER] Loaded KB: 45823 chars
   [WORKER] Generated metadata keys: ['description', 'audio_engineering', ...]
   [FIRESTORE] Updated preset reverb_vocal_hall with enriched metadata
   ```

4. **Verify in Firestore**:
   ```bash
   # Check metadata was enriched
   gcloud firestore documents get presets/reverb_vocal_hall \
     --project=fadebender \
     --format=json | jq '.fields.metadata_status.stringValue'
   # Should return: "enriched"
   ```

---

## Monitoring

### Check Cloud Run Metrics

```bash
# View service details
gcloud run services describe preset-enricher \
  --region=us-central1 \
  --project=fadebender

# View recent logs
gcloud logging read "resource.type=cloud_run_revision" \
  --limit=20 \
  --project=fadebender
```

### Check Pub/Sub Queue

```bash
# View topic
gcloud pubsub topics describe preset-enrich --project=fadebender

# View subscription
gcloud pubsub subscriptions describe preset-enrich-sub --project=fadebender

# Check for undelivered messages
gcloud pubsub subscriptions seek preset-enrich-sub \
  --time=$(date -u +%Y-%m-%dT%H:%M:%S) \
  --project=fadebender
```

### Health Check

```bash
SERVICE_URL=$(gcloud run services describe preset-enricher \
  --region=us-central1 \
  --project=fadebender \
  --format='value(status.url)')

curl $SERVICE_URL/health
# Should return:
# {"status":"healthy","service":"preset-enricher","project":"fadebender",...}
```

---

## Updating Knowledge Base

The worker loads markdown files from GCS. To update:

```bash
# Upload updated knowledge base
gsutil -m rsync -r ./knowledge gs://fadebender-kb/

# Worker will use new KB immediately (no redeploy needed)
```

---

## Cost Estimates

**Cloud Run:**
- $0.00002400 per vCPU-second
- $0.00000250 per GiB-second
- 512Mi RAM, 1 CPU, 10s avg execution
- ~$0.0003 per enrichment
- 1000 enrichments/month ≈ **$0.30/month**

**Pub/Sub:**
- First 10GB/month free
- ~1KB per message
- 1000 messages/month ≈ **Free**

**GCS Storage:**
- $0.020 per GB/month
- ~50MB KB ≈ **$0.001/month**

**Vertex AI (Gemini 2.5 Flash):**
- Input: $0.000075 per 1K chars
- Output: $0.00030 per 1K chars
- ~10K input + 2K output per enrichment
- ~$0.0013 per enrichment
- 1000 enrichments/month ≈ **$1.30/month**

**Total: ~$1.60/month for 1000 enrichments**

---

## Troubleshooting

### Worker not receiving messages

Check Pub/Sub subscription:

```bash
gcloud pubsub subscriptions describe preset-enrich-sub --project=fadebender
```

Ensure `pushConfig.pushEndpoint` matches Cloud Run URL.

### Worker failing with 404

Check that Gemini 2.5 Flash is available:

```bash
curl $SERVICE_URL/health
# Verify model name in response
```

### Firestore permission errors

Check service account has `roles/datastore.user`:

```bash
gcloud projects get-iam-policy fadebender \
  --flatten="bindings[].members" \
  --filter="bindings.members:preset-enricher-sa@fadebender.iam.gserviceaccount.com"
```

### Knowledge base not loading

Check GCS bucket:

```bash
gsutil ls -r gs://fadebender-kb/
# Should show all .md files
```

---

## Files

```
cloud-workers/
├── README.md                     # This file
├── setup-gcp.sh                  # Infrastructure setup script
└── preset-enricher/
    ├── main.py                   # Cloud Run worker (Flask app)
    ├── requirements.txt          # Python dependencies
    ├── Dockerfile                # Container definition
    └── deploy.sh                 # Deployment script
```

---

## Next Steps

1. ✅ Set up GCP infrastructure (`./setup-gcp.sh`)
2. ✅ Deploy Cloud Run worker (`./deploy.sh`)
3. ✅ Create Pub/Sub subscription
4. ✅ Update local server `.env`
5. ⏭️ Test with new preset load
6. ⏭️ Monitor Cloud Run logs
7. ⏭️ Add UI event listeners for `preset_enriched` events (auto-refresh)

---

## Architecture Notes

**Why not Cloud Functions?**
- Cloud Run gives more control over container, dependencies, and runtime
- Better for long-running LLM requests (300s timeout)
- Can use latest Python 3.11 with latest SDK versions

**Why Pub/Sub push vs pull?**
- Push simplifies worker (no subscription management)
- Auto-retry with exponential backoff
- Better integration with Cloud Run (auto-scaling)

**Why GCS for KB instead of embedding in container?**
- Faster updates (no redeploy needed)
- Versioned storage
- Easier collaboration (multiple contributors can update KB)
- Supports large KB files (100s of MB)

**Metadata versioning:**
- `metadata_version=1`: Local server (minimal, fast)
- `metadata_version=2`: Cloud enriched (full KB + RAG)
- Allows backfill and incremental enrichment

---

**Questions?** Check Cloud Run logs or open an issue.
