# Vertex AI Search Metadata Issue - Expert Consultation

## Summary
We successfully deployed Cloud Functions to call Vertex AI Search (Standard Edition) and are getting valid search results with titles and URIs, but **no content snippets**. We need to extract actual content from the documents to provide meaningful answers to users.

---

## Current Architecture

```
WebUI → Python Server (localhost:8722)
         ↓ [HTTPS + API Key]
      Cloud Functions (deployed)
         ↓ [Search-only, no LLM]
      Vertex AI Search → Documents
         ↓
      Returns: titles + URIs only (no snippets)
```

**Working:**
- ✅ Search queries return 5 relevant documents
- ✅ Titles extracted correctly (e.g., "reverb", "26.32_Reverb", "device-catalog")
- ✅ URIs extracted correctly (e.g., `gs://fadebender-knowledge/ableton-live/26_Live_Audio_Effect_Reference/26.32_Reverb/26.32_Reverb.html`)
- ✅ Staying within free tier quota (~10k searches/day)

**Not Working:**
- ❌ No content snippets returned
- ❌ Cannot extract meaningful text from documents
- ❌ Users only see "Found 5 relevant documents" with titles but no actual information

---

## Vertex AI Search Configuration

**Project ID:** `487213218407`
**Location:** `global`
**Data Store ID:** `fadebender-knowledge`
**Serving Config:** `default_search`
**Edition:** Standard Edition (not Enterprise)
**Indexing:** HTML files uploaded to `gs://fadebender-knowledge/`

**Documents Structure:**
All documents are well-structured HTML files with:
- `<title>` tags (extracted successfully)
- `<h1>`, `<h2>`, `<h3>` headings for sections
- Rich content in `<p>`, `<ul>`, `<table>` tags

**Example Document:** `preset-catalog.html`
```html
<h2 id="reverb-presets">Reverb Presets</h2>
<p><strong>Device Signature</strong>: <code>64ccfc236b79371d...</code><br />
<strong>Preset Count</strong>: 52</p>
<hr />
<h3 id="ambience">Ambience</h3>
<p><strong>Device</strong>: Reverb<br />
<strong>Preset ID</strong>: <code>reverb_ambience</code><br />
<strong>Category</strong>: reverb</p>
<p><strong>Parameter Settings</strong>:</p>
<ul>
<li><strong>Chorus Amount</strong>: 0.019999999552965164</li>
<li><strong>Decay Time</strong>: 0.4699999988079071</li>
<!-- ... more parameters ... -->
</ul>
```

---

## Current API Call

**Code:** `functions/src/vertex-direct.ts`

```typescript
const client = new SearchServiceClient();

const request = {
  servingConfig: 'projects/487213218407/locations/global/collections/default_collection/dataStores/fadebender-knowledge/servingConfigs/default_search',
  query: 'reverb presets',
  pageSize: 5,
  // NO contentSearchSpec - avoids LLM quota consumption
};

const [results] = await client.search(request, { autoPaginate: false });
```

---

## Response Structure Discovered

**From Cloud Functions logs:**

```javascript
{
  hasDocument: true,
  hasDerivedStructData: true,
  availableFields: ["title", "link", "can_fetch_raw_content"],

  // Sample field structure:
  sampleField: {
    kind: "stringValue",
    stringValue: "reverb"
  }
}
```

**Fields Available:**
- ✅ `title` (stringValue) - e.g., "reverb", "26.32_Reverb"
- ✅ `link` (stringValue) - e.g., "gs://fadebender-knowledge/ableton-live/..."
- ✅ `can_fetch_raw_content` (booleanValue) - `true` for all documents
- ❌ `snippet` - **NOT PRESENT**
- ❌ `extractive_answers` - **NOT PRESENT**
- ❌ `extractiveSegments` - **NOT PRESENT**

**Current Extraction Code:**
```typescript
const fields = doc.derivedStructData?.fields || {};

const title = fields.title?.stringValue || 'Untitled';
const snippet = fields.snippet?.stringValue || ''; // Always empty
const uri = fields.link?.stringValue || '';

return `### ${index + 1}. ${title}\n${snippet}\n*Source: ${uri}*`;
```

**Actual Output:**
```markdown
Found 5 relevant documents:

### 1. reverb

*Source: gs://fadebender-knowledge/.archive/ableton-live-old/audio-effects/reverb.html*

---

### 2. deep_audio_engineering_reverb

*Source: gs://fadebender-knowledge/audio-fundamentals/deep_audio_engineering_reverb.html*

---
(etc.)
```

---

## What We've Tried

### 1. ✅ Removed Enterprise Features
**Problem:** Initially got "Cannot use enterprise edition features" errors
**Solution:** Removed `contentSearchSpec.summarySpec` and `extractiveContentSpec` from API calls
**Result:** Search works, but no snippets

### 2. ✅ Fixed Response Parsing
**Problem:** Getting `null` responses initially
**Solution:** Changed from `autoPaginate: true` (returns `[results, request, response]`) to `autoPaginate: false` (returns `[results]`)
**Result:** Can now extract titles and URIs

### 3. ✅ Tried Multiple Field Names
**Code Attempted:**
```typescript
const snippet = fields.snippet?.stringValue ||
               fields.snippets?.[0]?.snippet ||
               fields.extractive_answers?.[0]?.content ||
               fields.description?.stringValue ||
               fields.htmlDescription?.stringValue ||
               '';
```
**Result:** All variants return empty - the fields simply don't exist in Standard Edition

### 4. 🔍 Checked Document Structure
**What we found:**
- `can_fetch_raw_content: true` - Documents CAN be fetched
- Documents are indexed from `gs://fadebender-knowledge/`
- HTML is well-structured with semantic headings
- Titles are extracted correctly, proving indexing works

---

## Key Questions for Expert

### 1. How to Get Content Snippets in Standard Edition?

**Question:** Is there a way to get content snippets (not just titles) from Vertex AI Search Standard Edition without using LLM features?

**What we need:** Extract ~200-500 characters of relevant content from each search result to provide context.

**Options we're considering:**
- A) Use different API parameters in the search request?
- B) Use a different serving config setting?
- C) Fetch raw content using `can_fetch_raw_content` flag?
- D) Re-upload documents with metadata that includes manual snippets?

### 2. Document Metadata Configuration

**Question:** When uploading HTML documents to Vertex AI Search, what metadata should we include to ensure snippets are returned?

**Current upload method:** Files uploaded to GCS bucket (`gs://fadebender-knowledge/`), then indexed via Vertex AI Search console.

**Do we need to:**
- Add `<meta>` tags to HTML files?
- Create a separate metadata file (JSONL)?
- Use a specific schema when uploading?
- Configure the data store differently?

### 3. Using `can_fetch_raw_content`

**Question:** How do we use the `can_fetch_raw_content: true` flag to fetch the actual HTML content?

**Specific questions:**
- Is there an API method to fetch raw content using the document ID?
- Do we need special permissions to access `gs://` URLs from Cloud Functions?
- Would this count against different quota limits?
- What's the recommended approach for extracting relevant sections from fetched HTML?

### 4. Alternative Search Configurations

**Question:** Are there Standard Edition serving config options we're missing?

**Current config:** `default_search` (created automatically)

**Should we:**
- Create a custom serving config with specific parameters?
- Enable specific features in the data store settings?
- Use different index settings when uploading documents?

### 5. Structured Data vs Unstructured Data

**Question:** Should we be using "structured data" instead of "unstructured data" for HTML documents?

**Current setup:** HTML files treated as unstructured website data

**Alternative:** Convert HTML to structured JSONL with explicit fields like:
```json
{
  "id": "reverb-presets",
  "title": "Reverb Presets",
  "content": "There are 52 reverb presets available...",
  "category": "audio-effects",
  "uri": "gs://fadebender-knowledge/preset-catalog.html#reverb-presets"
}
```

Would this give us better snippet extraction?

---

## Code References

**Cloud Functions (TypeScript):**
- Main search function: `functions/src/vertex-direct.ts:42-104`
- Response parsing: `functions/src/vertex-direct.ts:96-108`

**Search Request:**
```typescript
// Line 57-63
const request = {
  servingConfig: name,
  query: query,
  pageSize: 5,
  // NO contentSearchSpec - avoids LLM quota consumption
};
```

**Field Extraction:**
```typescript
// Line 100-106
const fields = doc.derivedStructData?.fields || {};

const title = fields.title?.stringValue || doc.name || 'Untitled';
const snippet = fields.snippet?.stringValue || ''; // Always empty
const uri = fields.link?.stringValue || doc.name || '';
```

---

## Expected vs Actual Behavior

### Expected
```markdown
### 1. Reverb Presets
There are 52 reverb presets available in Ableton Live. The Reverb device
includes presets like Ambience, Arena Tail, Ballad Reverb, and more. Each
preset has specific parameter settings for Decay Time, Pre-Delay, Diffusion...

*Source: gs://fadebender-knowledge/fadebender/preset-catalog.html*
```

### Actual
```markdown
### 1. device-catalog

*Source: gs://fadebender-knowledge/fadebender/device-catalog.html*
```

---

## Constraints

1. **Must stay in free tier** - Cannot use Enterprise Edition ($300+/month)
2. **Must avoid LLM quota** - Cannot use `summarySpec` or `extractiveContentSpec` (100-1000 requests/day limit)
3. **Can use search quota** - ~10,000 searches/day available in Standard Edition
4. **Can use external LLM** - Python server has Gemini access for answer generation (outside Vertex AI Search)

---

## Desired Solution

**Ideal flow:**
1. User asks: "how many reverb presets are there?"
2. Cloud Functions searches Vertex AI → returns documents with **content snippets**
3. Python server sends snippets to Gemini → generates natural language answer
4. User sees: "There are 52 reverb presets in Ableton Live, including Ambience, Arena Tail, Cathedral..."

**Current flow:**
1. User asks: "how many reverb presets are there?"
2. Cloud Functions searches Vertex AI → returns only **titles** ("device-catalog", "reverb")
3. Python server has no content to send to Gemini
4. User sees: "Found 5 relevant documents: device-catalog, reverb..." ❌

---

## Questions Summary

1. How to get content snippets in Standard Edition without LLM features?
2. What metadata/schema should HTML documents have for proper snippet extraction?
3. How to use `can_fetch_raw_content: true` to fetch actual HTML content?
4. Are there serving config options we're missing?
5. Should we use structured JSONL instead of HTML for better results?

---

## Environment Details

- **Node.js**: 20 (Cloud Functions Gen 2)
- **SDK**: `@google-cloud/discoveryengine` v2.5.2
- **Region**: us-central1 (Cloud Functions), global (Vertex AI Search)
- **GCS Bucket**: `gs://fadebender-knowledge/`
- **Document Count**: ~50 HTML files
- **Average Document Size**: 20-150KB HTML

---

## Contact

For follow-up questions or clarifications, please reference:
- Cloud Functions logs: `firebase functions:log --only help`
- Full deployment guide: `PRODUCTION_DEPLOYMENT.md`
- Vertex AI Search Console: https://console.cloud.google.com/gen-app-builder/engines?project=487213218407
