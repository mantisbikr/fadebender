/**
 * RAG-Powered Help Response Generator
 *
 * Uses Vertex AI Search to retrieve relevant documents,
 * then generates contextual responses using LLM.
 */

import { getConfigValue } from './config';
import { searchVertexAI } from './vertex-search';
import { callPythonHelp } from './vertex-direct';
import * as logger from 'firebase-functions/logger';
import { HelpResponse } from './help-fallback';

/**
 * Expand query with Fadebender terminology synonyms
 */
function expandQuery(query: string): string {
  const queryExpansionConfig = getConfigValue('rag.query_expansion', {}) as any;

  if (!queryExpansionConfig.enabled) {
    return query;
  }

  const terminology = queryExpansionConfig.fadebender_terminology || {};
  const lowerQuery = query.toLowerCase();
  const synonyms: string[] = [];

  // Check each term in the query and add synonyms
  for (const [term, synonymString] of Object.entries(terminology)) {
    if (lowerQuery.includes(term.toLowerCase())) {
      // Add all synonyms for this term
      synonyms.push(synonymString as string);
    }
  }

  // If we found synonyms, append them to the original query
  if (synonyms.length > 0) {
    const expandedQuery = `${query} ${synonyms.join(' ')}`;
    logger.info('Query expanded', {
      original: query,
      expanded: expandedQuery
    });
    return expandedQuery;
  }

  return query;
}

/**
 * Generate help response using RAG (Vertex AI Search)
 */
export async function generateRAGHelp(query: string): Promise<HelpResponse> {
  logger.info('Using RAG help generator (Vertex AI Search)', { query });

  // Step 1: Expand query with Fadebender terminology
  const expandedQuery = expandQuery(query);

  // Step 2: Retrieve relevant documents from Vertex AI Search
  const searchResults = await searchVertexAI(expandedQuery);

  if (searchResults.results.length === 0) {
    logger.warn('No search results found, this may impact response quality', { query });
  }

  // Step 3: Generate response using Python server's /help endpoint with RAG context
  const modelName = getConfigValue('models.help_assistant', 'gemini-1.5-flash');

  // Pass the RAG documents as context to the Python /help endpoint
  const ragContext = {
    documents: searchResults.results.map(r => ({
      title: r.title,
      content: r.snippet,
      relevanceScore: r.relevanceScore,
    })),
    totalResults: searchResults.totalResults,
  };

  const responseText = await callPythonHelp({
    query,
    context: ragContext,
  });

  logger.info('RAG help response generated', {
    query,
    responseLength: responseText.length,
    model: modelName,
    sourceCount: searchResults.results.length,
  });

  // Format sources for response
  const sources = searchResults.results.slice(0, 3).map(result => ({
    title: result.title,
    snippet: result.snippet.substring(0, 150),
  }));

  return {
    response: responseText,
    model_used: modelName,
    sources,
    mode: 'rag',
  };
}

