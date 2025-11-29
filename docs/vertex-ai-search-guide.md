# Vertex AI Search Configuration Guide for Fadebender

## What's in Your RAG System

### ✅ Device & Preset Mappings ARE in Vertex Search!

Your RAG system now contains comprehensive device and preset information:

#### **Device Catalog** (78 KB HTML)
Contains **5 fully mapped devices** from dev-display-value database:

1. **Reverb** (64ccfc23...)
   - 33 parameters with audio knowledge
   - Examples: Decay, Predelay, Wet/Dry, Filter controls
   - Audio knowledge explains: "Decay controls reverb tail length; shorter = tighter sound, longer = spacious"

2. **Delay** (9bfcc8b6...)
   - 21 parameters with audio knowledge
   - Examples: Feedback, Delay Time, Filter, Sync modes

3. **Align Delay** (82da8cce...)
   - 15 parameters
   - Used for phase alignment and timing correction

4. **Amp** (d554752f...)
   - 10 parameters with audio knowledge
   - Guitar amp simulation controls

5. **Compressor** (9e906e0a...)
   - 22 parameters with audio knowledge
   - Examples: Ratio, Threshold, Attack, Release, Knee

**What Vertex Search can retrieve:**
- Parameter ranges: "Reverb decay ranges from 0.1s to 60s"
- Audio knowledge: "Increasing reverb predelay separates dry signal from reverb onset"
- Use cases: "Use 10-25ms predelay for natural room simulation"
- Technical details: Full parameter descriptions with sonic effects

#### **Preset Catalog** (25 KB HTML)
Contains **114 presets** across all 5 devices:

- **Reverb**: 52 presets (Cathedral, Church, Concert Hall, Plate, etc.)
- **Delay**: 32 presets (4th Bandpass, Ping Pong, Tape Echo, etc.)
- **Align Delay**: 1 preset
- **Amp**: 11 presets
- **Compressor**: 18 presets (Gentle, Punchy, Limiter, etc.)

**What Vertex Search can retrieve:**
- Preset names: "Cathedral preset for reverb"
- Parameter values: "Cathedral uses 4.5s decay, 25ms predelay"
- When to use: RAG can recommend "Use Cathedral preset for large ambient spaces"

---

## Vertex AI Search API Features

All these features are **exposed via API** and can be used in your web UI:

### 1. **Answer Generation (summarySpec)** ⭐ MOST IMPORTANT

This generates AI-powered answers from your documents (like ChatGPT with RAG):

```typescript
summarySpec: {
  summaryResultCount: 5,        // Use top 5 results for answer
  includeCitations: true,        // Include source links
  modelPromptSpec: {
    preamble: 'You are an expert audio engineer...' // Custom instructions
  },
  languageCode: 'en'
}
```

**Example Query**: "What reverb preset should I use for vocals?"

**Without summarySpec**: Returns 5 document snippets
**With summarySpec**: Returns AI-generated answer:
> "For vocals, I recommend the **Plate Medium** or **Vocal Hall** presets. Plate reverbs (2-3s decay) add warmth without muddiness. Set predelay to 15-25ms to preserve vocal clarity. Alternative: **Cathedral** for dramatic effect, but reduce wet mix to 15-20%."
>
> *Sources: device-catalog.html, preset-catalog.html*

### 2. **Extractive Answers (extractiveContentSpec)**

Extracts exact text passages that answer the question:

```typescript
extractiveContentSpec: {
  maxExtractiveAnswerCount: 3,   // Up to 3 direct answers
  maxExtractiveSegmentCount: 5,  // Up to 5 relevant segments
  returnExtractiveSegmentScore: true,
  numPreviousSegments: 1,        // Context before
  numNextSegments: 1             // Context after
}
```

**Example**: Returns exact quotes from your docs with relevance scores.

### 3. **Boosting (boostSpec)**

Boost specific documents or fields to prioritize them:

```typescript
boostSpec: {
  conditionBoostSpecs: [
    {
      condition: 'document.uri:*reverb*',  // Boost reverb docs
      boost: 2.0                            // 2x relevance
    },
    {
      condition: 'document.uri:*preset*',   // Boost preset catalog
      boost: 1.5
    }
  ]
}
```

**Use case**: When user asks about reverb, boost reverb-related docs to surface them first.

### 4. **Filtering (filter)**

Filter results by metadata:

```typescript
filter: 'document.uri:*device-catalog*'  // Only search device catalog
filter: 'document.uri:*preset*'          // Only search presets
```

**Use case**: If you add metadata tags, you can filter by:
- Device type: `metadata.device_type='reverb'`
- Difficulty: `metadata.difficulty='beginner'`

### 5. **Snippet Configuration (snippetSpec)**

Control how snippets are returned:

```typescript
snippetSpec: {
  maxSnippetCount: 3,      // Show 3 snippets per result
  returnSnippet: true,     // Include snippets
  referenceOnly: false     // Show full snippets, not just refs
}
```

### 6. **Query Expansion & Spell Correction**

Already in your current code:

```typescript
queryExpansionSpec: {
  condition: 'AUTO',              // Expand queries with synonyms
  pinUnexpandedResults: false     // Don't force original results to top
},
spellCorrectionSpec: {
  mode: 'AUTO'                    // Auto-correct typos
}
```

---

## Recommended Configuration for Fadebender

### For Help/Advisory Queries

When user asks: *"my vocals sound weak"* or *"what reverb should I use"*

```typescript
const response = await searchVertexAIEnhanced(query, {
  maxResults: 5,

  // Generate AI answer
  summarySpec: {
    summaryResultCount: 5,
    includeCitations: true,
    ignoreNonSummarySeekingQuery: false,
    modelPromptSpec: {
      preamble: `You are an expert audio engineer and Ableton Live instructor.
      Provide clear, actionable advice based on the retrieved documents.
      When recommending devices or presets, include:
      - Specific device/preset names
      - Parameter settings (e.g., "Set reverb decay to 2-3s")
      - Fadebender commands (e.g., "load reverb preset cathedral on return A")
      Always cite sources.`
    }
  },

  // Get extractive answers too
  extractiveContentSpec: {
    maxExtractiveAnswerCount: 3,
    maxExtractiveSegmentCount: 5,
    returnExtractiveSegmentScore: true
  }
});

// Display in UI:
// 1. response.summary.summaryText (AI-generated answer)
// 2. response.results (source documents with snippets)
// 3. Suggested commands extracted from answer
```

### For Device/Preset Lookup

When user asks: *"what are the reverb presets"* or *"explain reverb decay parameter"*

```typescript
const response = await searchVertexAIEnhanced(query, {
  maxResults: 10,

  // Boost device/preset catalogs
  boostSpec: {
    conditionBoostSpecs: [
      { condition: 'document.uri:*device-catalog*', boost: 2.0 },
      { condition: 'document.uri:*preset-catalog*', boost: 2.0 }
    ]
  },

  // Generate structured answer
  summarySpec: {
    summaryResultCount: 5,
    includeCitations: true,
    modelPromptSpec: {
      preamble: `List specific presets and parameters from the device catalog.
      Format as a structured list with:
      - Preset name
      - When to use it
      - Key parameter values
      - Fadebender command to load it`
    }
  }
});
```

### For Context-Aware Project Advice

When user asks: *"how can I improve my mix"* (needs project context + RAG)

```typescript
// 1. Get project context
const projectInfo = await getProjectTopology(); // Your existing function

// 2. Search with context-aware prompt
const response = await searchVertexAIEnhanced(
  `mixing advice for project with ${projectInfo.trackCount} tracks, using ${projectInfo.returns.join(', ')}`,
  {
    summarySpec: {
      summaryResultCount: 5,
      includeCitations: true,
      modelPromptSpec: {
        preamble: `Analyze this Ableton Live project and provide specific advice:

        Project Context:
        - Tracks: ${JSON.stringify(projectInfo.tracks)}
        - Returns: ${JSON.stringify(projectInfo.returns)}
        - Routing: ${JSON.stringify(projectInfo.routing)}

        Based on the retrieved audio engineering knowledge and this project,
        provide actionable mixing advice with specific Fadebender commands.`
      }
    }
  }
);
```

---

## What RAG Can Now Answer

### ✅ Device Parameters
- "What does reverb decay do?"
- "Explain compressor ratio parameter"
- "What's the range for delay feedback?"

### ✅ Preset Recommendations
- "What reverb preset should I use for vocals?"
- "Show me compressor presets for drums"
- "Which delay preset creates a ping pong effect?"

### ✅ Audio Engineering Advice
- "My vocals sound weak" → RAG retrieves: EQ advice, compression techniques, reverb settings
- "My mix sounds muddy" → RAG retrieves: Low-end management, EQ curves, frequency ranges
- "How to make kick punch through" → RAG retrieves: Sidechain compression, EQ carving, layering

### ✅ Ableton Live Knowledge
- "What are sends and returns" → From Ableton manual
- "How does sidechaining work" → From Ableton manual
- "Explain automation lanes" → From Ableton manual

### ✅ Fadebender Commands
- "How do I control reverb on return A" → From user-guide.html
- "How to load a preset" → From user-guide.html
- "What commands are available" → From user-guide.html

---

## Implementation Example

```typescript
// functions/src/help-rag.ts

import { searchVertexAIEnhanced } from './vertex-search-enhanced';

export async function generateHelpResponse(
  query: string,
  projectContext?: any
): Promise<string> {

  // Search with answer generation
  const searchResponse = await searchVertexAIEnhanced(query, {
    maxResults: 5,

    summarySpec: {
      summaryResultCount: 5,
      includeCitations: true,
      modelPromptSpec: {
        preamble: projectContext
          ? `You are an expert audio engineer analyzing this Ableton Live project:
             ${JSON.stringify(projectContext)}

             Provide specific, actionable advice based on the retrieved documents
             and this project's configuration. Include Fadebender commands when relevant.`
          : `You are an expert audio engineer and Ableton Live instructor.
             Provide clear, actionable advice with specific parameter recommendations
             and Fadebender commands when relevant.`
      }
    },

    extractiveContentSpec: {
      maxExtractiveAnswerCount: 3,
      maxExtractiveSegmentCount: 5
    },

    // Boost relevant catalogs
    boostSpec: {
      conditionBoostSpecs: [
        { condition: 'document.uri:*device-catalog*', boost: 1.5 },
        { condition: 'document.uri:*preset-catalog*', boost: 1.5 }
      ]
    }
  });

  // Return AI-generated summary with citations
  return searchResponse.summary?.summaryText ||
         'No relevant information found.';
}
```

---

## Console Configuration

You can also configure these in the Vertex AI Search console:

1. **Search > Configure** → Enable "Customize Answers"
2. **Summary Settings** → Set preamble, citation style
3. **Boost/Bury** → Boost specific documents
4. **Synonyms** → Add domain-specific synonyms (e.g., "reverb" = "reverberation")

These console settings become defaults that your API calls can override.

---

## Summary

**YES**, your device and preset mappings ARE in Vertex Search and CAN provide:
- Specific preset recommendations with names
- Parameter values and ranges
- Audio knowledge explanations
- When to use each preset/parameter
- Fadebender commands to implement advice

The key is using **summarySpec** with a well-crafted preamble to generate structured, actionable answers that reference specific presets and parameters from your catalogs.
