# Quick Start: Get RAG Working in 15 Minutes! 🚀

Follow these steps to get your first RAG query working.

---

## Step 1: Install Firebase CLI (if not already)

```bash
npm install -g firebase-tools
firebase --version
```

---

## Step 2: Login to Firebase

```bash
firebase login
```

This opens your browser. Login with your Google account.

---

## Step 3: Create Firebase Project

**Option A: Via Console (Easiest)**

1. Go to https://console.firebase.google.com/
2. Click **"Add Project"**
3. Project name: `fadebender` (or whatever you prefer)
4. Disable Google Analytics (optional, not needed for RAG)
5. Click **"Create Project"**
6. Wait 1-2 minutes for creation

**Option B: Via CLI**

```bash
firebase projects:create fadebender --display-name "Fadebender Dev"
```

---

## Step 4: Link Local Project

```bash
# From project root
firebase use fadebender

# Verify
firebase projects:list
```

Should show `fadebender` with a checkmark.

---

## Step 5: Enable Firebase Services

In Firebase Console (https://console.firebase.google.com/project/fadebender):

### 5a. Firestore Database
1. Click **"Firestore Database"** in left sidebar
2. Click **"Create database"**
3. Start in **production mode** (we'll add rules later)
4. Location: Choose closest to you (e.g., `us-central1`)
5. Click **"Enable"**

### 5b. Firebase Realtime Database (for command queue)
1. Click **"Realtime Database"** in left sidebar
2. Click **"Create Database"**
3. Location: Same as Firestore
4. Security rules: **locked mode** for now
5. Click **"Enable"**

### 5c. Cloud Functions
Will be enabled automatically when you deploy.

### 5d. Firebase Studio (THE RAG ENGINE!)
1. Click **"Firebase Studio"** in left sidebar (may be under "Build" section)
2. Click **"Get Started"**
3. This creates the RAG data store

---

## Step 6: Authenticate with Google Cloud (ADC)

**Note:** Fadebender uses Vertex AI with Application Default Credentials (no API keys needed!)

```bash
# Authenticate with your Google Cloud account
gcloud auth application-default login

# This opens your browser and creates credentials at:
# ~/.config/gcloud/application_default_credentials.json
```

**Verify authentication:**
```bash
gcloud auth application-default print-access-token
# Should print an access token (if this works, you're authenticated)
```

---

## Step 7: Enable Vertex AI API

```bash
# Enable Vertex AI API for your project
gcloud services enable aiplatform.googleapis.com --project=fadebender
```

---

## Step 7a: Configure Environment Variables (Optional)

If you want to override defaults, create `functions/.env.local`:

```bash
cd functions
cat > .env.local << 'EOF'
# Project ID (optional - auto-detected from Firebase)
LLM_PROJECT_ID=fadebender

# Region (optional - defaults to us-central1)
GCP_REGION=us-central1
EOF
```

**Default behavior** (no `.env.local` needed):
- Project ID: Auto-detected from `GCLOUD_PROJECT` (Firebase Functions default)
- Region: `us-central1`
- Authentication: Application Default Credentials

---

## Step 8: Install Dependencies

```bash
# Still in functions/ directory
npm install
```

This will take 2-3 minutes (lots of dependencies).

---

## Step 9: Build TypeScript

```bash
npm run build
```

Should compile without errors. Output goes to `lib/` directory.

---

## Step 10: Configure Firebase Studio Data Source

**We need to make your `knowledge/` directory accessible to Firebase Studio.**

### Option A: Upload to Cloud Storage (Recommended for Testing)

```bash
# From project root
# 1. Create a bucket
gsutil mb gs://fadebender-knowledge

# 2. Upload knowledge files
gsutil -m cp -r knowledge/** gs://fadebender-knowledge/

# 3. In Firebase Console → Firebase Studio → Data Sources
# Add Cloud Storage source: gs://fadebender-knowledge/
```

### Option B: Use Firebase Hosting (Alternative)

```bash
# From project root
firebase init hosting

# Select:
# - Public directory: knowledge
# - Configure as single-page app: No
# - Set up rewrites: No

# Deploy
firebase deploy --only hosting

# In Firebase Console → Firebase Studio → Data Sources
# Add Hosting source: https://fadebender.web.app
```

### Option C: GitHub (For Production)

Connect your GitHub repo in Firebase Studio → Data Sources.

**For now, use Option A (Cloud Storage) - it's fastest!**

---

## Step 11: Index Knowledge Base in Firebase Studio

1. Firebase Console → **Firebase Studio**
2. Click **"Data Sources"**
3. Click **"Add Data Source"**
4. Choose **"Cloud Storage"** (or whatever you chose in Step 10)
5. Path: `gs://fadebender-knowledge/` (adjust if different)
6. Click **"Create"**
7. **Wait 5-10 minutes** for indexing (494 files = takes time!)

You'll see indexing progress in the console.

---

## Step 12: Start Firebase Emulators

```bash
# From project root
firebase emulators:start
```

This starts:
- Functions Emulator: `http://localhost:5001`
- Firestore Emulator: `http://localhost:8080`
- Emulator UI: `http://localhost:4000`

---

## Step 13: Test Your First RAG Query! 🎉

**In another terminal:**

```bash
curl -X POST http://localhost:5001/fadebender/us-central1/help \
  -H "Content-Type: application/json" \
  -d '{"query": "How do I set track volume in Fadebender?"}'
```

**Expected Response:**

```json
{
  "response": "To set track volume in Fadebender, use the command:\n\n`set track 1 volume to -6 dB`\n\nYou can also use relative adjustments:\n\n`increase track 1 volume by 3 dB`",
  "model_used": "gemini-2.5-flash-lite"
}
```

**If this works, RAG is working!** 🎉

---

## Step 14: Check Logs

In the emulator terminal, you should see:

```
Help query received { query: 'How do I set track volume...', userId: undefined }
Model selection for help_assistant: gemini-2.5-flash-lite
Help response generated {
  query: 'How do I set track volume...',
  responseLength: 150,
  configuredModel: 'gemini-2.5-flash-lite',
  actualModel: 'gemini-2.0-flash-experimental'
}
```

---

## Step 15: Deploy to Production (Optional)

Once emulator works:

```bash
firebase deploy --only functions
```

This deploys to live Firebase. Your function will be at:
```
https://us-central1-fadebender.cloudfunctions.net/help
```

---

## Troubleshooting

### "Firebase project not found"
```bash
firebase use --add
# Select fadebender
```

### "Not authenticated" or "Permission denied" errors

Make sure you've run `gcloud auth application-default login` and enabled Vertex AI API:

```bash
# Re-authenticate
gcloud auth application-default login

# Enable Vertex AI API
gcloud services enable aiplatform.googleapis.com --project=fadebender

# Verify authentication
gcloud auth application-default print-access-token
```

### "Module not found" errors
```bash
cd functions
rm -rf node_modules package-lock.json
npm install
npm run build
```

### Firebase Studio not indexing
- Check Cloud Storage bucket exists: `gsutil ls gs://fadebender-knowledge/`
- Check files uploaded: `gsutil ls -r gs://fadebender-knowledge/`
- Wait longer (494 files takes 10-15 minutes to index)

### Response is generic (not using RAG docs)
- Firebase Studio indexing may not be complete yet
- Check Firebase Console → Firebase Studio → Data Sources → Status
- For Phase 1, RAG retrieval is not yet integrated (that's next!)
  - Currently using fallback prompt with general knowledge
  - Once Studio indexing completes, we'll integrate retrieval

---

## What's Next?

### Immediate Next Steps:

1. **Integrate Firebase Studio Retrieval**
   - Add actual RAG document retrieval to `help.ts`
   - Use Firebase Studio SDK to fetch relevant docs
   - Include retrieved docs in prompt

2. **Test RAG Quality**
   - Query: "What is reverb decay?"
   - Should retrieve relevant docs from `knowledge/audio-fundamentals/`
   - Response should be based on knowledge base, not generic

3. **Add Device Catalog Generation (Phase 2)**
   - Generate `device-catalog.md` from Firestore
   - Add first device (Reverb) to RAG

---

## Quick Test Commands

```bash
# Test volume control question
curl -X POST http://localhost:5001/fadebender/us-central1/help \
  -H "Content-Type: application/json" \
  -d '{"query": "How do I set track volume?"}'

# Test device question
curl -X POST http://localhost:5001/fadebender/us-central1/help \
  -H "Content-Type: application/json" \
  -d '{"query": "What is reverb decay?"}'

# Test Ableton knowledge
curl -X POST http://localhost:5001/fadebender/us-central1/help \
  -H "Content-Type: application/json" \
  -d '{"query": "Explain send routing in Ableton"}'

# Test Fadebender commands
curl -X POST http://localhost:5001/fadebender/us-central1/help \
  -H "Content-Type: application/json" \
  -d '{"query": "How do I open return A reverb controls?"}'
```

---

## Success Checklist

- [ ] Firebase project created
- [ ] Services enabled (Firestore, Realtime DB, Studio)
- [ ] Google AI API key obtained
- [ ] Dependencies installed (`npm install` in functions/)
- [ ] TypeScript built (`npm run build`)
- [ ] Knowledge base uploaded to Cloud Storage
- [ ] Firebase Studio data source configured
- [ ] Indexing started (check console for progress)
- [ ] Emulators running (`firebase emulators:start`)
- [ ] First test query successful
- [ ] Logs show model selection working
- [ ] Response is helpful

---

**Ready to query your 494-file knowledge base!** 🎉

Next up: Integrate actual RAG retrieval to use those docs!
