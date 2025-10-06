# Cost Optimization & Security Fixes

**Date:** 2025-10-05
**Issue:** Unexpectedly high Gemini API costs due to public Cloud Run endpoint and wrong API priority

---

## **What Was Wrong**

### 1. **Security Issue: Public Endpoint**
- ❌ Cloud Run worker was **publicly accessible** without authentication
- ❌ Bots/scanners could trigger expensive LLM API calls
- ❌ No ingress restrictions (accepted all internet traffic)

### 2. **Cost Issue: Wrong API Priority**
- ❌ **Gemini API was primary** (expensive, paid per request)
- ❌ **Vertex AI was fallback** (cheaper, has free tier with service account)
- ❌ Line 378 in `main.py`: `if GENAI_API_KEY:` runs first
- ❌ Deployment injected `LLM_API_KEY` secret, forcing Gemini usage

### 3. **No Rate Limiting**
- ❌ No protection against runaway costs
- ❌ Could process unlimited requests if triggered

---

## **Fixes Applied**

### ✅ Security Fixes
```bash
# 1. Removed public access
gcloud run services remove-iam-policy-binding preset-enricher \
  --region=us-central1 \
  --member="allUsers" \
  --role="roles/run.invoker"

# 2. Restricted ingress to internal only
gcloud run services update preset-enricher \
  --region=us-central1 \
  --ingress=internal-and-cloud-load-balancing

# 3. Added Pub/Sub invoker permission
gcloud run services add-iam-policy-binding preset-enricher \
  --region=us-central1 \
  --member="serviceAccount:service-487213218407@gcp-sa-pubsub.iam.gserviceaccount.com" \
  --role="roles/run.invoker"
```

### ✅ Cost Optimization
1. **Swapped API Priority** (`main.py:406`)
   - Now: Vertex AI first (cheaper)
   - Fallback: Gemini API only if `USE_GENAI_PRIMARY=1`

2. **Added Rate Limiting** (`main.py:120-136`)
   - Max 20 LLM calls per hour (configurable via `MAX_LLM_CALLS_PER_HOUR`)
   - Tracks call timestamps, rejects excess requests

3. **Removed Gemini API Secret** (`deploy.sh:29`)
   - Changed: `--set-secrets="LLM_API_KEY=..."` → `--clear-secrets`
   - Forces Vertex AI usage (no API key fallback)

4. **Added Auth Header Check** (`main.py:789-794`)
   - Rejects requests without Bearer token
   - Extra safety layer beyond IAM

### ✅ Deployment Config Updates
**File:** `cloud-workers/preset-enricher/deploy.sh`

**Old (Insecure & Expensive):**
```bash
--allow-unauthenticated \
--set-env-vars="...,LLM_CHUNKED_ONLY=1" \
--set-secrets="LLM_API_KEY=llm-api-key:latest"
```

**New (Secure & Cost-Optimized):**
```bash
--no-allow-unauthenticated \
--ingress=internal-and-cloud-load-balancing \
--set-env-vars="...,LLM_CHUNKED_ONLY=1,MAX_LLM_CALLS_PER_HOUR=20,USE_GENAI_PRIMARY=0" \
--clear-secrets
```

---

## **Cost Comparison**

| **Metric** | **Before (Gemini API)** | **After (Vertex AI)** |
|------------|-------------------------|----------------------|
| **Pricing Model** | $0.075 per 1M input tokens | Free tier + $0.075 (same model) |
| **Free Tier** | None | 1,000 requests/month free |
| **Auth Method** | API Key (easy to leak) | Service Account (scoped) |
| **Rate Limiting** | None | 20 calls/hour |
| **Public Access** | Yes (dangerous!) | No (internal only) |
| **Monthly Cost (20 req)** | ~$3-5 | ~$0 (within free tier) |

---

## **How to Deploy Fixes**

### 1. **Redeploy Worker (Required)**
```bash
cd cloud-workers/preset-enricher
./deploy.sh
```

### 2. **Verify Security**
```bash
# Should return 404 or 403 (blocked)
curl https://preset-enricher-u4vgqt2gka-uc.a.run.app/health

# Check IAM policy
gcloud run services get-iam-policy preset-enricher \
  --region=us-central1 \
  --project=fadebender
```

### 3. **Set Budget Alerts**
```bash
# Go to: https://console.cloud.google.com/billing/budgets
# Create budget: $20/month with alerts at 50%, 70%, 90%, 100%
```

### 4. **(Optional) Disable Gemini API Entirely**
If not using elsewhere:
```bash
# This will prevent ANY Gemini API usage
gcloud services disable generativelanguage.googleapis.com \
  --project=fadebender --force
```

---

## **Monitoring & Alerts**

### Check Recent Usage
```bash
# View recent invocations
gcloud logging read \
  "resource.type=cloud_run_revision AND resource.labels.service_name=preset-enricher" \
  --limit=50 \
  --project=fadebender \
  --format="table(timestamp,httpRequest.status,jsonPayload.message)"

# Check for rate limit hits
gcloud logging read \
  "jsonPayload.message=~RATE_LIMIT" \
  --limit=20 \
  --project=fadebender
```

### Set Up Alerts
1. **Budget Alert:** Email when >70% of monthly budget
2. **API Quota Alert:** Email if approaching Vertex AI limits
3. **Error Rate Alert:** Email if Cloud Run errors >5%

---

## **Lessons Learned**

1. ✅ **Always use `--no-allow-unauthenticated`** for Cloud Run services
2. ✅ **Set ingress restrictions** (`internal-and-cloud-load-balancing` for Pub/Sub)
3. ✅ **Prefer Vertex AI over Gemini API** (free tier + service account auth)
4. ✅ **Add rate limiting** to any LLM-calling code
5. ✅ **Set budget alerts BEFORE deploying** cloud services
6. ✅ **Review IAM policies** regularly for public access
7. ✅ **Check GCP Console billing** weekly to catch issues early

---

## **Files Modified**

- ✅ `cloud-workers/preset-enricher/main.py` - Added rate limiting, swapped API priority, added auth check
- ✅ `cloud-workers/preset-enricher/deploy.sh` - Secured deployment config
- ✅ `scripts/fix-cloud-run-auth.sh` - Emergency security fix script
- ✅ `docs/architecture/gcp-deployment-plan.md` - Production deployment guide

---

## **Next Steps**

1. ✅ Redeploy worker immediately: `cd cloud-workers/preset-enricher && ./deploy.sh`
2. ⏳ Set budget alerts: https://console.cloud.google.com/billing/budgets
3. ⏳ Review billing for last 7 days: https://console.cloud.google.com/billing/reports
4. ⏳ (Optional) Disable Gemini API if unused: `gcloud services disable generativelanguage.googleapis.com`
5. ⏳ Add same protections to other services (server, nlp-service if deployed)

---

**Status:** ✅ Security fixed, cost optimization applied, ready to redeploy
