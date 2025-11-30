/**
 * RAG-Powered Help Response Generator
 *
 * Uses Vertex AI Search to retrieve relevant documents,
 * then generates contextual responses using LLM.
 */

import { callVertexSearch } from './vertex-direct';
import * as logger from 'firebase-functions/logger';
import { HelpResponse } from './help-fallback';

/**
 * Generate help response using RAG (Vertex AI Search)
 *
 * Uses search-only mode with content extraction to avoid LLM quota consumption.
 * Returns JSON with document content for Python/Gemini to process.
 */
export async function generateRAGHelp(query: string): Promise<HelpResponse> {
  logger.info('Using RAG help generator (search-only + content extraction)', { query });

  // Call Vertex Search with content extraction
  // This will return JSON: {"query": "...", "documents": [{"title": "...", "content": "...", "source": "..."}]}
  const responseText = await callVertexSearch({
    query,
  });

  logger.info('Search-only RAG complete', {
    query,
    responseLength: responseText.length,
  });

  // Response is JSON string with document content
  // Python server will parse this and use Gemini to generate answer
  return {
    response: responseText,
    model_used: 'vertex-ai-search-content-extraction',
    mode: 'rag',
  };
}

