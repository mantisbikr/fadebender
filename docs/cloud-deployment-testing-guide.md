# Cloud Deployment & Testing Guide for Fadebender RAG System

This guide shows how to deploy the Fadebender RAG system to Firebase Cloud Functions and test it from anywhere, including your iPad while traveling.

---

## Prerequisites

1. **Firebase Project Setup**
   - Your Firebase project is already configured
   - Project ID: Check `firebase.json` or run `firebase use`
   - Ensure Vertex AI Search is configured and indexed

2. **Firebase CLI**
   - Already installed (you're using it for emulators)
   - Logged in: `firebase login --reauth` (if needed)

3. **Build Dependencies**
   - Node.js and npm installed
   - TypeScript compiled

---

## Step 1: Deploy Cloud Functions

### Deploy All Functions

```bash
# From project root
cd functions

# Install dependencies (if not already done)
npm install

# Build TypeScript
npm run build

# Deploy all functions
firebase deploy --only functions
```

### Deploy Only Help Function (Faster)

```bash
firebase deploy --only functions:help
```

### Check Deployment Status

```bash
firebase functions:log --only help
```

---

## Step 2: Get Your Cloud Function URL

After deployment, Firebase will display the URL:

```
✔  functions[us-central1-help(us-central1)]: Successful create operation.
Function URL (help(us-central1)): https://us-central1-YOUR-PROJECT-ID.cloudfunctions.net/help
```

**Save this URL** - you'll use it for all API requests.

Example:
```
https://us-central1-fadebender-abcd1234.cloudfunctions.net/help
```

---

## Step 3: Testing from iPad (or Any Device)

You can test using any of these methods:

### Option 1: Using Shortcuts App (iPad/iPhone)

1. Open **Shortcuts** app on iPad
2. Create new shortcut
3. Add action: **Get Contents of URL**
4. Configure:
   - URL: `https://YOUR-FUNCTION-URL/help`
   - Method: `POST`
   - Request Body: `JSON`
   - Body content:
     ```json
     {
       "query": "What reverb presets are available?",
       "conversational": true
     }
     ```
5. Add action: **Show Result**
6. Save and run

**For conversational follow-ups:**
Use the `sessionId` from the first response in subsequent queries:
```json
{
  "query": "Which one is best for vocals?",
  "sessionId": "session_1234567890_abc123"
}
```

### Option 2: Using Pythonista (iPad)

Install **Pythonista** app, then create this script:

```python
import requests
import json

# Your Cloud Function URL
URL = "https://YOUR-FUNCTION-URL/help"

def ask_fadebender(query, session_id=None, format=None):
    payload = {
        "query": query,
        "conversational": True
    }

    if session_id:
        payload["sessionId"] = session_id

    if format:
        payload["format"] = format

    response = requests.post(URL, json=payload)
    return response.json()

# Example usage
print("=== Test 1: Basic Query ===")
result = ask_fadebender("What reverb presets are available?")
print(result["response"])
print(f"\nSession ID: {result.get('sessionId')}")

# Follow-up using session
print("\n=== Test 2: Follow-up ===")
session_id = result.get("sessionId")
result2 = ask_fadebender(
    "Which one is best for vocals?",
    session_id=session_id
)
print(result2["response"])

# Brief answer
print("\n=== Test 3: Brief Format ===")
result3 = ask_fadebender(
    "Explain reverb decay",
    format="brief"
)
print(result3["response"])
```

### Option 3: Using Web Browser (iPad Safari)

Create a simple HTML file and host it on GitHub Pages or CodePen:

```html
<!DOCTYPE html>
<html>
<head>
    <title>Fadebender Help Tester</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }
        textarea {
            width: 100%;
            height: 100px;
            font-size: 16px;
            padding: 10px;
        }
        button {
            padding: 12px 24px;
            font-size: 16px;
            background: #007AFF;
            color: white;
            border: none;
            border-radius: 8px;
            margin: 10px 5px;
        }
        #response {
            margin-top: 20px;
            padding: 15px;
            background: #f5f5f5;
            border-radius: 8px;
            white-space: pre-wrap;
        }
        select {
            padding: 8px;
            font-size: 16px;
            margin: 10px 5px;
        }
    </style>
</head>
<body>
    <h1>Fadebender Help</h1>

    <textarea id="query" placeholder="Enter your question here...">What reverb presets are available?</textarea>

    <div>
        <label>Format:</label>
        <select id="format">
            <option value="">Default</option>
            <option value="brief">Brief</option>
            <option value="detailed">Detailed</option>
            <option value="bulleted">Bulleted</option>
            <option value="step-by-step">Step-by-step</option>
        </select>
    </div>

    <button onclick="askQuestion()">Ask</button>
    <button onclick="clearSession()">New Conversation</button>

    <div id="response"></div>

    <script>
        // Replace with your actual Cloud Function URL
        const FUNCTION_URL = 'https://YOUR-FUNCTION-URL/help';
        let sessionId = null;

        async function askQuestion() {
            const query = document.getElementById('query').value;
            const format = document.getElementById('format').value;

            const payload = {
                query: query,
                conversational: true
            };

            if (sessionId) {
                payload.sessionId = sessionId;
            }

            if (format) {
                payload.format = format;
            }

            try {
                const response = await fetch(FUNCTION_URL, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(payload)
                });

                const result = await response.json();

                // Save session ID for follow-ups
                if (result.sessionId) {
                    sessionId = result.sessionId;
                }

                // Display response
                document.getElementById('response').innerHTML =
                    `<strong>Answer:</strong>\n${result.response}\n\n` +
                    `<strong>Format:</strong> ${result.format}\n` +
                    `<strong>Session ID:</strong> ${sessionId}\n` +
                    (result.sources ? `<strong>Sources:</strong> ${result.sources.length}` : '');

            } catch (error) {
                document.getElementById('response').innerText =
                    'Error: ' + error.message;
            }
        }

        function clearSession() {
            sessionId = null;
            document.getElementById('response').innerText = 'Session cleared. Starting new conversation.';
        }
    </script>
</body>
</html>
```

---

## Step 4: Test Examples

### Test Suite for Comprehensive Testing

Save these as a collection in your HTTP client or Pythonista:

#### 1. Device Parameters
```bash
curl -X POST https://YOUR-FUNCTION-URL/help \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What does reverb decay do?",
    "format": "brief"
  }'
```

#### 2. Preset Recommendations
```bash
curl -X POST https://YOUR-FUNCTION-URL/help \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What reverb presets are available?",
    "format": "bulleted"
  }'
```

#### 3. Audio Engineering Advice
```bash
curl -X POST https://YOUR-FUNCTION-URL/help \
  -H "Content-Type: application/json" \
  -d '{
    "query": "My vocals sound weak",
    "conversational": true
  }'
```

**Save the sessionId from response, then:**

```bash
curl -X POST https://YOUR-FUNCTION-URL/help \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What reverb preset do you recommend?",
    "sessionId": "SESSION_ID_FROM_PREVIOUS_RESPONSE"
  }'
```

#### 4. Step-by-Step Guide
```bash
curl -X POST https://YOUR-FUNCTION-URL/help \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How to set up a reverb send",
    "format": "step-by-step"
  }'
```

#### 5. Detailed Explanation
```bash
curl -X POST https://YOUR-FUNCTION-URL/help \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Explain sidechaining in Ableton",
    "format": "detailed"
  }'
```

#### 6. With Project Context
```bash
curl -X POST https://YOUR-FUNCTION-URL/help \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How can I improve my mix?",
    "projectContext": {
      "tracks": [
        {"name": "Vocals", "number": 1},
        {"name": "Guitar", "number": 2},
        {"name": "Drums", "number": 3}
      ],
      "returns": [
        {"name": "Reverb", "letter": "A"},
        {"name": "Delay", "letter": "B"}
      ]
    }
  }'
```

---

## Step 5: Monitor and Debug

### View Logs from iPad

Use Firebase Console on iPad:
1. Go to https://console.firebase.google.com
2. Select your project
3. Navigate to **Functions** → **Logs**
4. Filter by function name: `help`

### View Logs from Terminal

```bash
# Real-time logs
firebase functions:log --only help

# Recent logs
firebase functions:log --only help --limit 50
```

### Check Vertex AI Search Usage

1. Go to Google Cloud Console
2. Navigate to **Vertex AI Search** → **Data Stores**
3. Check indexing status and search analytics

---

## Response Format Examples

### Brief Format Response
```json
{
  "response": "Reverb decay controls the length of the reverb tail (0.1s to 60s). Short decay = tight sound, long decay = spacious effect.",
  "model_used": "vertex-ai-search-conversational",
  "format": "brief",
  "sessionId": "session_1234567890_abc123",
  "sources": ["device-catalog.html"]
}
```

### Bulleted Format Response
```json
{
  "response": "Available reverb presets:\n- Cathedral: Large ambient spaces\n- Plate Medium: Warm vocal reverb\n- Vocal Hall: Natural vocal space\n- Concert Hall: Orchestra-style reverb\n...",
  "format": "bulleted",
  "sessionId": "session_1234567890_abc123",
  "sources": ["preset-catalog.html"]
}
```

### Conversational Follow-up Response
```json
{
  "response": "For the weak vocals you mentioned earlier, I recommend the Plate Medium preset. It adds warmth without muddiness. Set the wet/dry mix to 15-20% to maintain vocal clarity.",
  "format": "conversational",
  "sessionId": "session_1234567890_abc123",
  "conversationContext": {
    "turnCount": 2,
    "previousQuery": "My vocals sound weak"
  }
}
```

---

## Troubleshooting

### Issue: CORS Errors from Browser

**Solution:** CORS is enabled in the function. If you still see errors:
1. Check that `cors: true` is set in the function config
2. Ensure you're using HTTPS (not HTTP)
3. Try from a different browser or use Pythonista

### Issue: Function Timeout

**Solution:** Current timeout is 60 seconds. If queries timeout:
1. Check Vertex AI Search is responding
2. Simplify the query
3. Increase timeout in `functions/src/help.ts`:
   ```typescript
   export const help = onRequest({
     cors: true,
     timeoutSeconds: 120,  // Increase to 2 minutes
     memory: '512MiB',
   }, ...);
   ```

### Issue: No Results from RAG

**Solution:**
1. Verify Vertex AI Search is indexed:
   ```bash
   gcloud ai search data-stores list --location=global
   ```
2. Check logs for indexing errors
3. Verify catalogs are uploaded to GCS bucket

### Issue: Session Not Persisting

**Solution:**
1. Ensure Firestore is enabled in Firebase Console
2. Check Firestore rules allow writes to `help_conversations`
3. Verify `sessionId` is being sent in follow-up requests

---

## Cost Optimization

### Estimated Costs (per 1000 queries)

- **Cloud Functions:** ~$0.40 (with 60s timeout, 512MB memory)
- **Vertex AI Search:** ~$3.00 (answer generation enabled)
- **Firestore:** ~$0.10 (conversation storage)

**Total:** ~$3.50 per 1000 queries

### Tips to Reduce Costs

1. **Disable conversational mode for simple queries**
   ```json
   {
     "query": "What reverb presets exist?",
     "conversational": false
   }
   ```

2. **Use brief format when possible**
   ```json
   {
     "query": "Explain decay [keep it brief]"
   }
   ```

3. **Clean up old sessions**
   - Run cleanup function weekly
   - Sessions older than 7 days are automatically deleted

4. **Use caching for common queries**
   - Implement Redis or Firestore cache for frequently asked questions

---

## Security Considerations

### Current Setup
- CORS enabled (anyone can call your function)
- No authentication required

### Recommended for Production

1. **Add API Key Authentication**
   ```typescript
   // In help.ts
   const apiKey = request.headers['x-api-key'];
   if (apiKey !== getConfigValue('api_key')) {
     response.status(401).json({ error: 'Unauthorized' });
     return;
   }
   ```

2. **Use Firebase Auth**
   ```typescript
   import { getAuth } from 'firebase-admin/auth';

   const token = request.headers.authorization?.split('Bearer ')[1];
   const decodedToken = await getAuth().verifyIdToken(token);
   const userId = decodedToken.uid;
   ```

3. **Rate Limiting**
   - Use Cloud Armor for rate limiting
   - Or implement in-function rate limiting with Firestore

---

## Next Steps

1. ✅ Deploy functions: `firebase deploy --only functions:help`
2. ✅ Get function URL from deployment output
3. ✅ Test basic query from iPad (use curl or Shortcuts app)
4. ✅ Test conversational flow (save sessionId, send follow-up)
5. ✅ Test different formats (brief, detailed, bulleted, step-by-step)
6. ✅ Monitor logs and costs in Firebase Console

---

## Quick Reference: API Request Format

```typescript
// TypeScript/JavaScript
const response = await fetch('https://YOUR-FUNCTION-URL/help', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    query: 'Your question here',
    conversational: true,         // Optional
    sessionId: 'session_xyz',     // Optional (for follow-ups)
    format: 'brief',              // Optional: brief|detailed|bulleted|step-by-step
    projectContext: {...},        // Optional
    userId: 'user123'             // Optional
  })
});

const result = await response.json();
console.log(result.response);     // AI-generated answer
console.log(result.sessionId);    // Use for follow-ups
console.log(result.format);       // Detected/used format
console.log(result.sources);      // Source documents
```

---

Happy testing from your iPad! 🎵✨
