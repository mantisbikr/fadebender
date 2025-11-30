/**
 * Fallback Help Response Generator
 *
 * Uses Vertex AI Search (standard edition) with LLM summaries.
 * Returns AI-generated answers based on relevant documents.
 */

import { callVertexSearch } from './vertex-direct';
import * as logger from 'firebase-functions/logger';

export interface HelpResponse {
  response: string;
  model_used: string;
  sources?: Array<{ title: string; snippet: string }>;
  mode: 'rag' | 'rag-conversational' | 'fallback' | 'search-results';
  sessionId?: string;
  format?: string;
  conversationContext?: {
    turnCount: number;
    previousQuery?: string;
  };
}

/**
 * Generate help response using Vertex AI Search with LLM summaries.
 * Returns AI-generated answers based on relevant documents.
 */
export async function generateFallbackHelp(query: string): Promise<HelpResponse> {
  logger.info('Using Vertex AI Search with LLM summaries', { query });

  // Call Vertex AI Search - returns AI-generated summary
  const responseText = await callVertexSearch({
    query,
    // Context can be added here in the future
  });

  logger.info('Vertex Search AI summary received', {
    query,
    responseLength: responseText.length,
    model: 'vertex-ai-search-llm',
  });

  return {
    response: responseText,
    model_used: 'vertex-ai-search-llm',
    mode: 'rag', // AI-generated answer from Vertex AI Search LLM
  };
}

