/**
 * Enhanced Vertex AI Search Integration with Advanced Features
 *
 * This module demonstrates all available Vertex AI Search configurations
 * that can be used to improve search quality and answer generation.
 */

import * as logger from 'firebase-functions/logger';
import { getConfigValue } from './config';

export interface SearchResult {
  title: string;
  snippet: string;
  uri?: string;
  relevanceScore?: number;
  extractiveAnswers?: ExtractiveAnswer[];
  extractiveSegments?: ExtractiveSegment[];
}

export interface ExtractiveAnswer {
  content: string;
  pageNumber?: number;
  confidence?: number;
}

export interface ExtractiveSegment {
  content: string;
  pageNumber?: number;
  relevanceScore?: number;
}

export interface SearchSummary {
  summaryText: string;
  summarySkippedReasons?: string[];
  safetyAttributes?: {
    categories: string[];
    scores: number[];
  };
}

export interface SearchResponse {
  results: SearchResult[];
  totalResults: number;
  summary?: SearchSummary;
  attributionToken?: string;
}

export interface SearchOptions {
  maxResults?: number;

  // Content Search Spec
  snippetSpec?: {
    maxSnippetCount?: number;        // Max snippets per result (default: 1)
    referenceOnly?: boolean;          // Only return references, no snippets
    returnSnippet?: boolean;          // Whether to return snippets (default: true)
  };

  summarySpec?: {
    summaryResultCount?: number;      // Number of results to use for summary (default: 3-5)
    includeCitations?: boolean;       // Include source citations (default: false)
    ignoreAdversarialQuery?: boolean; // Ignore harmful queries (default: false)
    ignoreNonSummarySeekingQuery?: boolean; // Only summarize for questions (default: false)
    modelPromptSpec?: {
      preamble?: string;              // Custom instructions for the LLM
    };
    languageCode?: string;            // Output language (default: 'en')
  };

  extractiveContentSpec?: {
    maxExtractiveAnswerCount?: number;   // Max extractive answers (default: 1)
    maxExtractiveSegmentCount?: number;  // Max extractive segments (default: 1)
    returnExtractiveSegmentScore?: boolean; // Include relevance scores
    numPreviousSegments?: number;        // Context before answer (default: 0)
    numNextSegments?: number;            // Context after answer (default: 0)
  };

  // Query Expansion
  queryExpansionSpec?: {
    condition?: 'AUTO' | 'DISABLED';  // AUTO enables query expansion
    pinUnexpandedResults?: boolean;   // Keep original results at top
  };

  // Spell Correction
  spellCorrectionSpec?: {
    mode?: 'AUTO' | 'SUGGESTION_ONLY' | 'DISABLED';
  };

  // Boost Spec - Boost certain documents/fields
  boostSpec?: {
    conditionBoostSpecs?: Array<{
      condition: string;              // e.g., "document.metadata.category='reverb'"
      boost: number;                  // Boost multiplier (e.g., 2.0)
    }>;
  };

  // Filter - Filter results by metadata
  filter?: string;                     // e.g., "document.metadata.device='reverb'"

  // Order By - Sort results
  orderBy?: string;                    // e.g., "document.metadata.updated_date desc"

  // Safe Search
  safeSearch?: boolean;                // Enable safe search filtering

  // User Info - For personalization
  userInfo?: {
    userId?: string;
    userAgent?: string;
  };

  // Facet Specs - For faceted search
  facetSpecs?: Array<{
    facetKey: {
      key: string;                     // Metadata field to facet on
    };
    limit?: number;                    // Max facet values to return
  }>;
}

/**
 * Enhanced search with all available options
 */
export async function searchVertexAIEnhanced(
  query: string,
  options: SearchOptions = {}
): Promise<SearchResponse> {
  const projectId = getConfigValue('rag.vertex_ai_search.project_id', '');
  const location = getConfigValue('rag.vertex_ai_search.location', 'global');
  const engineId = getConfigValue('rag.vertex_ai_search.engine_id', '');
  const servingConfig = getConfigValue('rag.vertex_ai_search.serving_config', 'default_search');

  if (!projectId || !engineId) {
    throw new Error('Vertex AI Search not configured');
  }

  const endpoint = `https://discoveryengine.googleapis.com/v1/projects/${projectId}/locations/${location}/collections/default_collection/engines/${engineId}/servingConfigs/${servingConfig}:search`;

  // Build request body with all options
  const requestBody: any = {
    query,
    pageSize: options.maxResults || 5,
  };

  // Add content search spec
  if (options.snippetSpec || options.summarySpec || options.extractiveContentSpec) {
    requestBody.contentSearchSpec = {};

    if (options.snippetSpec) {
      requestBody.contentSearchSpec.snippetSpec = options.snippetSpec;
    }

    if (options.summarySpec) {
      requestBody.contentSearchSpec.summarySpec = options.summarySpec;
    }

    if (options.extractiveContentSpec) {
      requestBody.contentSearchSpec.extractiveContentSpec = options.extractiveContentSpec;
    }
  }

  // Add query expansion
  if (options.queryExpansionSpec) {
    requestBody.queryExpansionSpec = options.queryExpansionSpec;
  } else {
    // Default to AUTO
    requestBody.queryExpansionSpec = { condition: 'AUTO' };
  }

  // Add spell correction
  if (options.spellCorrectionSpec) {
    requestBody.spellCorrectionSpec = options.spellCorrectionSpec;
  } else {
    // Default to AUTO
    requestBody.spellCorrectionSpec = { mode: 'AUTO' };
  }

  // Add boost spec
  if (options.boostSpec) {
    requestBody.boostSpec = options.boostSpec;
  }

  // Add filter
  if (options.filter) {
    requestBody.filter = options.filter;
  }

  // Add order by
  if (options.orderBy) {
    requestBody.orderBy = options.orderBy;
  }

  // Add safe search
  if (options.safeSearch) {
    requestBody.safeSearch = options.safeSearch;
  }

  // Add user info
  if (options.userInfo) {
    requestBody.userInfo = options.userInfo;
  }

  // Add facet specs
  if (options.facetSpecs) {
    requestBody.facetSpecs = options.facetSpecs;
  }

  logger.info('Vertex AI Enhanced Search', { query, options: requestBody });

  try {
    const { GoogleAuth } = await import('google-auth-library');
    const auth = new GoogleAuth({
      scopes: ['https://www.googleapis.com/auth/cloud-platform'],
    });
    const client = await auth.getClient();
    const accessToken = await client.getAccessToken();

    if (!accessToken.token) {
      throw new Error('Failed to get access token');
    }

    const response = await fetch(endpoint, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${accessToken.token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(requestBody),
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Vertex AI Search failed: ${response.status} ${errorText}`);
    }

    const data = await response.json();

    // Parse results with enhanced fields
    const results: SearchResult[] = (data.results || []).map((result: any) => {
      const document = result.document || {};
      const structData = document.structData || {};

      return {
        title: structData.title || document.name || 'Untitled',
        snippet: getSnippet(structData),
        uri: structData.uri || document.name,
        relevanceScore: result.relevanceScore,
        extractiveAnswers: structData.extractive_answers,
        extractiveSegments: structData.extractive_segments,
      };
    });

    // Parse summary if available
    let summary: SearchSummary | undefined;
    if (data.summary) {
      summary = {
        summaryText: data.summary.summaryText || '',
        summarySkippedReasons: data.summary.summarySkippedReasons,
        safetyAttributes: data.summary.safetyAttributes,
      };
    }

    logger.info('Vertex AI Enhanced Search results', {
      query,
      resultCount: results.length,
      hasSummary: !!summary,
    });

    return {
      results,
      totalResults: data.totalSize || results.length,
      summary,
      attributionToken: data.attributionToken,
    };
  } catch (error: any) {
    logger.error('Vertex AI Enhanced Search error', {
      error: error.message,
      query,
    });
    throw error;
  }
}

function getSnippet(structData: any): string {
  if (structData.snippet) return structData.snippet;
  if (structData.content) return truncate(structData.content, 200);
  if (structData.description) return structData.description;
  if (structData.extractive_answers && structData.extractive_answers.length > 0) {
    return structData.extractive_answers[0].content || '';
  }
  return '';
}

function truncate(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text;
  return text.substring(0, maxLength) + '...';
}

/**
 * Example: Search with answer generation (summary)
 */
export async function searchWithAnswerGeneration(query: string): Promise<SearchResponse> {
  return searchVertexAIEnhanced(query, {
    maxResults: 5,
    summarySpec: {
      summaryResultCount: 5,
      includeCitations: true,
      ignoreAdversarialQuery: true,
      ignoreNonSummarySeekingQuery: false,
      modelPromptSpec: {
        preamble: 'You are an expert audio engineer and Ableton Live instructor. Provide clear, actionable advice based on the retrieved documents. Include specific parameter recommendations when relevant.',
      },
      languageCode: 'en',
    },
    extractiveContentSpec: {
      maxExtractiveAnswerCount: 3,
      maxExtractiveSegmentCount: 5,
      returnExtractiveSegmentScore: true,
    },
  });
}

/**
 * Example: Search for specific device/preset with boosting
 */
export async function searchDevicePresets(deviceName: string, query: string): Promise<SearchResponse> {
  return searchVertexAIEnhanced(query, {
    maxResults: 10,
    boostSpec: {
      conditionBoostSpecs: [
        {
          condition: `document.uri:*${deviceName.toLowerCase()}*`,
          boost: 2.0,
        },
      ],
    },
    summarySpec: {
      summaryResultCount: 5,
      includeCitations: true,
      modelPromptSpec: {
        preamble: `You are recommending ${deviceName} presets. List specific preset names and explain when to use each one.`,
      },
    },
  });
}
