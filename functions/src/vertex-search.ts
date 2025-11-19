/**
 * Vertex AI Search Integration
 *
 * Retrieves relevant documents from Vertex AI Search data store
 */

import * as logger from 'firebase-functions/logger';
import { getConfigValue } from './config';

export interface SearchResult {
  title: string;
  snippet: string;
  uri?: string;
  relevanceScore?: number;
}

export interface SearchResponse {
  results: SearchResult[];
  totalResults: number;
}

/**
 * Check if Vertex AI Search is enabled
 */
export function isVertexSearchEnabled(): boolean {
  return getConfigValue('rag.vertex_ai_search.enabled', false);
}

/**
 * Search Vertex AI Search data store
 *
 * @param query - User's search query
 * @param maxResults - Maximum number of results to return
 * @returns Search results from Vertex AI Search
 */
export async function searchVertexAI(
  query: string,
  maxResults?: number
): Promise<SearchResponse> {
  if (!isVertexSearchEnabled()) {
    logger.warn('Vertex AI Search is disabled in config');
    return { results: [], totalResults: 0 };
  }

  const projectId = getConfigValue('rag.vertex_ai_search.project_id', '');
  const location = getConfigValue('rag.vertex_ai_search.location', 'global');
  const engineId = getConfigValue('rag.vertex_ai_search.engine_id', '');
  const servingConfig = getConfigValue('rag.vertex_ai_search.serving_config', 'default_search');
  const pageSize = maxResults || getConfigValue('rag.vertex_ai_search.max_results', 5);

  if (!projectId || !engineId) {
    throw new Error('Vertex AI Search not configured: missing project_id or engine_id');
  }

  const endpoint = `https://discoveryengine.googleapis.com/v1/projects/${projectId}/locations/${location}/collections/default_collection/engines/${engineId}/servingConfigs/${servingConfig}:search`;

  logger.info('Searching Vertex AI', { query, pageSize, endpoint });

  try {
    // Use service account credentials (automatic in Cloud Functions)
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
      body: JSON.stringify({
        query,
        pageSize,
        queryExpansionSpec: {
          condition: 'AUTO',
        },
        spellCorrectionSpec: {
          mode: 'AUTO',
        },
      }),
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Vertex AI Search failed: ${response.status} ${errorText}`);
    }

    const data = await response.json();

    // Parse results
    const results: SearchResult[] = (data.results || []).map((result: any) => {
      const document = result.document || {};
      const structData = document.structData || {};

      return {
        title: structData.title || document.name || 'Untitled',
        snippet: getSnippet(structData),
        uri: structData.uri || document.name,
        relevanceScore: result.relevanceScore,
      };
    });

    logger.info('Vertex AI Search results', {
      query,
      resultCount: results.length,
      totalResults: data.totalSize || results.length,
    });

    return {
      results,
      totalResults: data.totalSize || results.length,
    };
  } catch (error: any) {
    logger.error('Vertex AI Search error', {
      error: error.message,
      query,
    });

    // Check if fallback is enabled
    const fallbackOnError = getConfigValue('rag.vertex_ai_search.fallback_on_error', true);
    if (fallbackOnError) {
      logger.warn('Falling back to non-RAG response due to error');
      return { results: [], totalResults: 0 };
    }

    throw error;
  }
}

/**
 * Extract snippet from document struct data
 */
function getSnippet(structData: any): string {
  // Try different fields that might contain content
  if (structData.snippet) return structData.snippet;
  if (structData.content) return truncate(structData.content, 200);
  if (structData.description) return structData.description;
  if (structData.extractive_answers && structData.extractive_answers.length > 0) {
    return structData.extractive_answers[0].content || '';
  }
  return '';
}

/**
 * Truncate text to max length
 */
function truncate(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text;
  return text.substring(0, maxLength) + '...';
}
