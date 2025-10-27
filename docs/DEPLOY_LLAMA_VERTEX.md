# Deploying Llama 3.1 8B in Vertex AI Model Garden

## Step 1: Access Vertex AI Model Garden

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Navigate to **Vertex AI** > **Model Garden**
3. Search for "Llama 3.1 8B" or "meta-llama/Llama-3.1-8B-Instruct"

## Step 2: Deploy the Model

There are two deployment options:

### Option A: Model-as-a-Service (MaaS) - RECOMMENDED
**Fastest, no infrastructure management**

1. Find **Llama 3.1 8B Instruct** in Model Garden
2. Click **Deploy** or **Enable API**
3. Select **Model-as-a-Service (MaaS)** option
4. Click **Deploy**
5. Note the model endpoint: `meta/llama3-8b-instruct-maas`

**Pricing:**
- Pay per token (input + output)
- No infrastructure costs
- Scales automatically

### Option B: Dedicated Endpoint
**More control, potentially faster for high volume**

1. Find **Llama 3.1 8B Instruct** in Model Garden
2. Click **Deploy**
3. Select **Deploy to endpoint**
4. Configure:
   - Machine type: `n1-standard-4` or `n1-standard-8`
   - Accelerator: Optional (GPU for faster inference)
   - Min replicas: 1
   - Max replicas: 1-3 (for auto-scaling)
5. Click **Deploy** (takes 10-15 minutes)
6. Note the endpoint ID

**Pricing:**
- Charged for compute time (even when idle)
- Fixed costs based on machine type
- Better for consistent high volume

## Step 3: Configure Environment Variables

Add to your `.env` file or export:

```bash
# For Model-as-a-Service (MaaS)
export LLAMA_VERTEX_MODEL="meta/llama3-8b-instruct-maas"

# OR for dedicated endpoint
export LLAMA_VERTEX_MODEL="projects/YOUR_PROJECT/locations/us-central1/endpoints/YOUR_ENDPOINT_ID"

# Required: Your GCP project
export LLM_PROJECT_ID="your-project-id"

# Optional: Override default region
export GCP_REGION="us-central1"

# Existing Gemini config (keep this)
export VERTEX_MODEL="gemini-2.0-flash-exp"  # or your Gemini model
```

## Step 4: Run the Comparison Test

```bash
cd /Users/sunils/ai-projects/fadebender
python3 scripts/test_llama_vs_gemini.py
```

## Step 5: Interpret Results

The script will show:
- **Accuracy**: Both models should parse intents correctly
- **Latency**: Llama should be 3-10x faster than Gemini
- **Success Rate**: Target >90% for production use

### Expected Performance

| Metric | Gemini 2.5 Flash | Llama 3.1 8B (Expected) |
|--------|------------------|-------------------------|
| Avg Latency | 2000-4000ms | 200-800ms |
| Success Rate | 95-100% | 85-95% |
| Cost/1M tokens | $0.075 | $0.02-0.05 |

## Troubleshooting

### Error: "Model not found"
- Ensure Llama is deployed in your project
- Check the model name matches your deployment
- Verify region is correct (default: us-central1)

### Error: "Permission denied"
- Enable Vertex AI API in your project
- Grant your service account `Vertex AI User` role
- For MaaS: Enable the specific model API

### High latency
- Check region (use same region as your app)
- Consider dedicated endpoint for consistent performance
- Warm up: First request is always slower (model loading)

## Cost Optimization

**For low-moderate volume (< 1M tokens/day):**
- Use Model-as-a-Service (MaaS)
- Pay only for what you use
- No idle costs

**For high volume (> 1M tokens/day):**
- Use dedicated endpoint
- More predictable costs
- Potentially faster

## Next Steps

After testing:
1. If Llama performs well (>90% accuracy, faster): Update default model in config
2. If Llama has accuracy issues: Stick with Gemini, focus on fixing regex patterns
3. Consider hybrid: Llama for simple intents, Gemini for complex reasoning

## Model Names Reference

| Model | Vertex AI Name | Use Case |
|-------|---------------|----------|
| Gemini 2.0 Flash | `gemini-2.0-flash-exp` | Complex reasoning, high accuracy |
| Gemini 1.5 Flash | `gemini-1.5-flash-002` | Balanced performance |
| Llama 3.1 8B | `meta/llama3-8b-instruct-maas` | Fast intent parsing |
| Llama 3.1 70B | `meta/llama3-70b-instruct-maas` | Higher accuracy (slower) |
| Llama 3.1 405B | `meta/llama3-405b-instruct-maas` | Highest accuracy (expensive) |
