# Fadebender Cloud Functions

Firebase Cloud Functions with Genkit for RAG-powered help and conversation system.

## Phase 1 Setup Status

- [x] Project structure created
- [x] Package.json with Genkit dependencies
- [x] TypeScript configuration
- [x] RAG configuration (configs/rag_config.json)
- [x] Basic `/help` endpoint scaffold
- [ ] Firebase project creation (next step)
- [ ] Firebase Studio data source configuration
- [ ] Deploy and test

## Prerequisites

1. **Node.js 18+**
   ```bash
   node --version  # Should be >= 18
   ```

2. **Firebase CLI**
   ```bash
   npm install -g firebase-tools
   firebase --version
   ```

3. **Genkit CLI** (optional, for development)
   ```bash
   npm install -g genkit
   ```

4. **Google Cloud Account** with billing enabled

## Setup Steps

### Step 1: Install Dependencies

```bash
cd functions
npm install
```

### Step 2: Create Firebase Project

**Option A: Via Firebase Console (Recommended for first time)**

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Click "Add Project"
3. Project name: `fadebender-dev` (or your preferred name)
4. Enable Google Analytics (optional)
5. Wait for project creation

**Option B: Via CLI**

```bash
firebase projects:create fadebender-dev --display-name "Fadebender Development"
```

### Step 3: Link Local Project to Firebase

```bash
# From project root
firebase use fadebender-dev

# Verify
firebase projects:list
```

### Step 4: Enable Required Services

**In Firebase Console:**

1. **Firestore Database**
   - Go to Firestore Database
   - Click "Create database"
   - Start in production mode
   - Choose region: `us-central1`

2. **Firebase Realtime Database**
   - Go to Realtime Database
   - Click "Create Database"
   - Start in locked mode (we'll add rules later)

3. **Cloud Functions**
   - Automatically enabled when you deploy

4. **Firebase Studio** (for RAG)
   - Go to Firebase Studio (in left sidebar)
   - Click "Get Started"
   - This creates the RAG data store

### Step 5: Set Environment Variables

Create `functions/.env.local`:

```bash
# Google AI API Key for Gemini
GOOGLE_AI_API_KEY=your_gemini_api_key_here

# Firebase Admin (auto-configured in Cloud Functions)
# FIREBASE_CONFIG is automatically available
```

To get Google AI API Key:
1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create API key
3. Copy and paste above

### Step 6: Configure Firebase Studio Data Sources

**Option A: Via Firebase Console**

1. Go to Firebase Studio in Console
2. Click "Data Sources"
3. Add data source:
   - Name: `fadebender-knowledge`
   - Type: `Cloud Storage` or `GitHub`
   - Path: Point to your `knowledge/` directory

**Option B: Via Firebase CLI** (Coming soon in Firebase SDK)

For now, we'll use the Console method.

### Step 7: Build and Test Locally

```bash
# Build TypeScript
cd functions
npm run build

# Start Firebase Emulators
firebase emulators:start

# In another terminal, test the help endpoint
curl -X POST http://localhost:5001/fadebender-dev/us-central1/help \
  -H "Content-Type: application/json" \
  -d '{"query": "How do I set track volume?"}'
```

### Step 8: Deploy to Firebase

```bash
# Deploy functions only
firebase deploy --only functions

# Or deploy everything (functions, firestore rules, etc.)
firebase deploy
```

## Project Structure

```
functions/
├── src/
│   ├── index.ts           # Main entry point, exports all functions
│   ├── config.ts          # Configuration loader (rag_config.json)
│   ├── genkit-config.ts   # Genkit initialization
│   └── help.ts            # /help endpoint with RAG
├── package.json
├── tsconfig.json
└── README.md (this file)
```

## Available Endpoints

### POST /help

Simple help query endpoint.

**Request:**
```json
{
  "query": "How do I set track volume?",
  "userId": "user123"  // optional
}
```

**Response:**
```json
{
  "response": "To set track volume in Fadebender...",
  "model_used": "gemini-1.5-flash",
  "sources": [...]  // populated once RAG is configured
}
```

## Development Workflow

### Local Development

```bash
# Watch mode for TypeScript
npm run build:watch

# In another terminal
firebase emulators:start

# Test endpoint
curl -X POST http://localhost:5001/fadebender-dev/us-central1/help \
  -H "Content-Type: application/json" \
  -d '{"query": "test"}'
```

### Genkit Development UI

```bash
# Start Genkit dev server
npm run genkit:dev

# Opens UI at http://localhost:4000
# Allows testing flows interactively
```

## Configuration

RAG configuration is in `/configs/rag_config.json`.

Key settings:
- `rag.enabled`: Master toggle for RAG system
- `rag.firebase_studio.data_sources.paths`: Paths to knowledge base files
- `rag.retrieval.top_k`: Number of documents to retrieve
- `rag.cost_optimization.*`: Cost control settings

## Troubleshooting

### "Firebase project not found"

```bash
# Re-link project
firebase use fadebender-dev

# Or select interactively
firebase use
```

### "Permission denied" during deploy

```bash
# Login again
firebase login --reauth

# Check you have Owner/Editor role on project
firebase projects:list
```

### "Module not found" errors

```bash
cd functions
rm -rf node_modules package-lock.json
npm install
```

### Firebase Studio not indexing documents

1. Check data source configuration in Console
2. Verify file paths in `rag_config.json`
3. Files must be accessible (Cloud Storage bucket or GitHub repo)
4. Allow 5-10 minutes for initial indexing

## Next Steps (After Phase 1)

- [ ] Phase 2: Device catalog generation from Firestore
- [ ] Phase 3: Multi-turn conversation system (`/chat` endpoint)
- [ ] Phase 4: Project context injection
- [ ] Phase 5: Full project analysis engine

## Resources

- [Firebase Documentation](https://firebase.google.com/docs)
- [Genkit Documentation](https://firebase.google.com/docs/genkit)
- [Firebase Studio Guide](https://firebase.google.com/docs/studio)
- [Architecture Document](../docs/architecture/rag-firebase-studio-architecture.md)

## Support

For issues or questions, see the main project documentation or open an issue.
