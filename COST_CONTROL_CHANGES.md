# Cost Control Changes (Oct 7, 2025)

## Problem
$17/day in Gemini API charges from `llm-research-409622` project

## Root Cause
- Active Gemini API keys configured in `.env` files
- `intents/parser.py` using `google.generativeai` (paid API)

## Actions Taken

### 1. Deleted All Gemini API Keys
- **llm-research-409622**: Deleted 2 keys (Beatswara Key, Fadebender Key)
- **fadebender**: Deleted 1 key (redacted - already deleted from GCP)

### 2. Updated Configuration Files
- `.env`: Removed API keys, commented out service account path
- `nlp-service/.env`: Removed API keys, changed PROJECT_ID to fadebender
- `nlp-service/.env.development`: Removed API keys
- `carnatic-ai-project/src/config/llm_config.py`: Removed hardcoded API key

### 3. Migrated to Vertex AI
- `nlp-service/intents/parser.py`: Replaced `google.generativeai` with Vertex AI SDK
- Uses Application Default Credentials (no API key needed)
- Falls back to rule-based parsing if Vertex AI unavailable

### 4. Verified
- All API keys deleted from GCP
- Parser tested and working via web UI
- Using ADC: `gcloud auth application-default login`

## Result
- **Before**: ~$17/day in charges
- **After**: $0 (using Vertex AI with fadebender project quota)

## Service Accounts
- Kept `llm-research@llm-research-409622.iam.gserviceaccount.com` (no cost, not used)
- Kept `fadebender-service@fadebender.iam.gserviceaccount.com` (needed for Cloud Run)
- Removed service account key from local `.env` (using ADC instead)
