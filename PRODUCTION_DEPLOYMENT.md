# Production Deployment Guide

## Current Architecture (After This Fix)

```
WebUI (Production Domain)
    ↓
Python Server (Cloud Run or VM)
    ↓ [HTTPS + API Key]
Cloud Functions (Deployed)
    ↓ [Search Only - No LLM]
Vertex AI Search → Documents
    ↓
Python Server (Gemini) → AI Answer
    ↓
WebUI (Fast Response)
```

**Key Design Decision:**
- Cloud Functions: Lightweight search (high quota ~10k/day free)
- Python Server: AI answer generation (using existing Gemini code)
- This avoids expensive LLM quota on Vertex AI Search

## What You Need for Production

### 1. **CORS Whitelist Update** (REQUIRED)

**File**: `functions/src/middleware/auth.ts` (line 16-23)

**Current** (Development only):
```typescript
const ALLOWED_ORIGINS = [
  'http://localhost:3000',     // WebUI dev
  'http://localhost:8722',     // Python server dev
  'http://127.0.0.1:3000',
  'http://127.0.0.1:8722',
];
```

**Production** (Add your domains):
```typescript
const ALLOWED_ORIGINS = [
  // Development
  'http://localhost:3000',
  'http://localhost:8722',
  'http://127.0.0.1:3000',
  'http://127.0.0.1:8722',

  // Production - ADD YOUR DOMAINS HERE
  'https://fadebender.app',              // Your production WebUI
  'https://www.fadebender.app',          // www subdomain
  'https://studio.fadebender.app',       // Studio subdomain if separate
  'https://api-XXXXXX.run.app',          // Your Python server Cloud Run URL
  // Add any other production domains
];
```

After updating, redeploy:
```bash
cd functions
npm run build
firebase deploy --only functions
```

### 2. **Environment Variables** (REQUIRED)

**Python Server** needs:
```bash
# .env (or Cloud Run environment variables)
FADEBENDER_API_KEY=Kz6L8wdyKApwv7oCHN0OBZsMKy+e2pLa5wwfE5z1/tA=
VERTEX_PROJECT=fadebender
VERTEX_LOCATION=us-central1
```

**If deploying Python to Cloud Run:**
```bash
gcloud run deploy fadebender-server \
  --region us-central1 \
  --set-env-vars FADEBENDER_API_KEY=Kz6L8wdyKApwv7oCHN0OBZsMKy+e2pLa5wwfE5z1/tA= \
  --set-env-vars VERTEX_PROJECT=fadebender \
  --set-env-vars VERTEX_LOCATION=us-central1
```

### 3. **API Key Rotation** (Security Best Practice)

**When to rotate:**
- Every 90 days minimum
- Immediately if exposed/leaked
- Before public launch

**How to rotate:**
```bash
# 1. Generate new key
openssl rand -base64 32

# 2. Store in Secret Manager
printf "NEW_KEY_HERE" | firebase functions:secrets:set FADEBENDER_API_KEY

# 3. Update Python server .env
# Edit .env file with new key

# 4. Redeploy functions (picks up new secret automatically)
firebase deploy --only functions

# 5. Restart Python server
# (Cloud Run: new deployment, VM: restart service)
```

### 4. **Rate Limiting Adjustments** (Optional)

**Current limits** (development-friendly):
- 60 requests/minute per IP
- 100 requests/minute per user

**For production**, adjust in `functions/src/middleware/rate-limit.ts`:
```typescript
const DEFAULT_LIMITS: Record<string, RateLimitConfig> = {
  ip: {
    maxRequests: 100,          // Increase for production traffic
    windowSeconds: 60,
    blockDurationSeconds: 300,
  },
  user: {
    maxRequests: 200,          // Increase for power users
    windowSeconds: 60,
    blockDurationSeconds: 300,
  },
};
```

### 5. **Monitoring & Alerts** (Recommended)

**Set up Google Cloud Monitoring:**

```bash
# 1. Enable Cloud Monitoring API
gcloud services enable monitoring.googleapis.com

# 2. Create alert policy for quota usage
# Go to: https://console.cloud.google.com/monitoring/alerting
# Create alert for:
#   - discoveryengine.googleapis.com/llm_requests (LLM quota)
#   - cloudfunctions.googleapis.com/function/execution_count (Usage)
#   - Firestore rate_limits collection (Blocked IPs)
```

**Key metrics to monitor:**
- Cloud Functions invocations
- Error rates (500 errors)
- Rate limit blocks
- Vertex AI Search quota usage

### 6. **Firestore Security Rules** (REQUIRED)

**File**: `firestore.rules`

Add rules for rate limiting collection:
```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // Rate limits (managed by Cloud Functions only)
    match /rate_limits/{document} {
      allow read, write: if false;  // Only Cloud Functions can access
    }

    // Help conversations (user access)
    match /help_conversations/{sessionId} {
      allow read: if request.auth != null &&
                     request.auth.uid == resource.data.userId;
      allow write: if false;  // Only Cloud Functions can write
    }

    // Your existing rules...
  }
}
```

Deploy:
```bash
firebase deploy --only firestore:rules
```

### 7. **DNS & SSL** (Production Domains)

If hosting WebUI on custom domain:

```bash
# 1. Add custom domain to Firebase Hosting
firebase hosting:channel:deploy production

# 2. Configure DNS (in your domain registrar):
# A record: fadebender.app → Firebase Hosting IP
# CNAME: www.fadebender.app → fadebender.app

# 3. SSL certificates (automatic with Firebase Hosting)
```

### 8. **Cost Estimation** (Monthly)

**Free Tier (Current Setup):**
- Cloud Functions: 2M invocations/month FREE
- Vertex AI Search: ~10,000 searches/month FREE
- Firestore: 50k reads, 20k writes FREE
- **Estimated cost: $0/month** (within free tier)

**If You Exceed Free Tier:**
- Cloud Functions: ~$0.40 per 1M invocations
- Vertex AI Search: ~$0.0001 per search (after free tier)
- Firestore: ~$0.06 per 100k reads
- **Estimated cost: $10-50/month** for moderate usage

### 9. **Backup Strategy** (Critical Data)

**Firestore automatic backup:**
```bash
# Enable scheduled backups
gcloud firestore backups schedules create \
  --database='(default)' \
  --recurrence=daily \
  --retention=7d
```

**API Key backup** (secure location):
- Store in password manager (1Password, LastPass, etc.)
- Keep encrypted backup offline

### 10. **Deployment Checklist**

Before launching to production:

- [ ] Update CORS whitelist with production domains
- [ ] Set environment variables on production Python server
- [ ] Configure Firestore security rules
- [ ] Set up monitoring alerts
- [ ] Test end-to-end flow from production WebUI
- [ ] Verify API key works from production server
- [ ] Check rate limiting is working
- [ ] Set up automated backups
- [ ] Document API key location (password manager)
- [ ] Create runbook for common issues

---

## Quick Start: Test Production Setup Locally

Before deploying, test the production config locally:

1. **Update CORS temporarily** (add your local IP)
2. **Test with production API key**:
   ```bash
   curl -X POST 'https://us-central1-fadebender.cloudfunctions.net/help' \
     -H 'Content-Type: application/json' \
     -H 'X-API-Key: Kz6L8wdyKApwv7oCHN0OBZsMKy+e2pLa5wwfE5z1/tA=' \
     -d '{"query":"test","conversational":true,"userId":"test"}'
   ```
3. **Verify Python server can call Cloud Functions**
4. **Test from WebUI**

---

## Troubleshooting Production Issues

### Issue: CORS errors from production domain

**Fix**: Add domain to ALLOWED_ORIGINS in `auth.ts`

### Issue: 401 Unauthorized

**Fix**: Check API key in Python server environment variables

### Issue: 429 Too Many Requests

**Fix**: IP is rate limited, will auto-unblock after 5 minutes

### Issue: 500 Internal Server Error

**Check**:
- Cloud Functions logs: `firebase functions:log`
- Firestore connection
- Vertex AI Search quota

---

## Cost Optimization Tips

1. **Cache help responses** (in Python server) for common queries
2. **Debounce search requests** (in WebUI) to avoid duplicate searches
3. **Monitor quota usage** weekly
4. **Use Gemini Flash** (cheaper) instead of Pro for answer generation
5. **Consider CDN** for static WebUI assets

---

## Security Hardening (Optional)

**Additional security layers for production:**

1. **Rate limiting by user account** (in addition to IP)
2. **Request signing** (HMAC) for Python → Cloud Functions
3. **Firewall rules** (only allow specific IP ranges)
4. **DDoS protection** (Cloudflare or Cloud Armor)
5. **Audit logging** (log all help requests with user IDs)

---

## Support & Maintenance

**Regular tasks:**
- Weekly: Check quota usage
- Monthly: Review Cloud Functions logs for errors
- Quarterly: Rotate API key
- Annually: Review and optimize costs

**Emergency contacts:**
- Firebase Support: https://firebase.google.com/support
- Google Cloud Support: (if you have a support plan)
- Vertex AI Search: https://cloud.google.com/generative-ai-app-builder/docs/support

---

## Current Deployment Status

- ✅ Cloud Functions deployed with security
- ✅ API key stored in Secret Manager
- ✅ Rate limiting active
- ✅ Standard edition Vertex AI Search (free quota)
- ⚠️ CORS configured for localhost only (UPDATE FOR PRODUCTION)
- ⚠️ Monitoring not yet configured
- ⚠️ Firestore rules need production hardening

---

**Next Steps:**
1. Wait for Vertex AI quota to reset (tomorrow)
2. Test the new architecture (search-only, no LLM summaries)
3. Update CORS for your production domains
4. Deploy and test end-to-end
