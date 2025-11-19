import { onRequest } from 'firebase-functions/v2/https';
import { getConfigValue, isRagEnabled } from './config';
import { isVertexSearchEnabled } from './vertex-search';
import { generateRAGHelp } from './help-rag';
import { generateFallbackHelp, HelpResponse } from './help-fallback';
import * as logger from 'firebase-functions/logger';

/**
 * Help Endpoint with Feature-Flagged RAG
 *
 * Supports two modes:
 * 1. RAG Mode (rag.vertex_ai_search.enabled = true): Uses Vertex AI Search + LLM
 * 2. Fallback Mode (rag.vertex_ai_search.enabled = false): Uses LLM only
 *
 * Configuration in configs/rag_config.json:
 * - rag.enabled: Master switch for RAG system
 * - rag.vertex_ai_search.enabled: Enable/disable Vertex AI Search
 * - rag.vertex_ai_search.fallback_on_error: Auto-fallback if RAG fails
 */

/**
 * Process help query with feature-flagged RAG
 */
async function processHelpQuery(query: string, userId?: string): Promise<HelpResponse> {
  logger.info('Help query received', { query, userId });

  // Check if RAG system is enabled at all
  if (!isRagEnabled()) {
    logger.warn('RAG system is disabled in config');
    const fallback = await generateFallbackHelp(query);
    return fallback;
  }

  // Check if Vertex AI Search is enabled
  const useRAG = isVertexSearchEnabled();
  const fallbackOnError = getConfigValue('rag.vertex_ai_search.fallback_on_error', true);

  logger.info('Help mode selected', {
    useRAG,
    fallbackOnError,
    query,
  });

  if (useRAG) {
    try {
      // Try RAG mode first
      const ragResponse = await generateRAGHelp(query);
      return ragResponse;
    } catch (error: any) {
      logger.error('RAG help generation failed', {
        error: error.message,
        query,
        willFallback: fallbackOnError,
      });

      if (fallbackOnError) {
        logger.info('Falling back to non-RAG help');
        const fallback = await generateFallbackHelp(query);
        return fallback;
      }

      throw error;
    }
  } else {
    // Use fallback mode (no RAG)
    const fallback = await generateFallbackHelp(query);
    return fallback;
  }
}

/**
 * HTTP endpoint for help queries
 */
export const help = onRequest(
  {
    cors: true,
    timeoutSeconds: 60,
    memory: '512MiB',
  },
  async (request, response) => {
    try {
      const { query, userId } = request.body;

      if (!query || typeof query !== 'string') {
        response.status(400).json({
          error: 'Query is required and must be a string',
        });
        return;
      }

      const result = await processHelpQuery(query, userId);

      response.json(result);
    } catch (error: any) {
      logger.error('Help endpoint error', error);
      response.status(500).json({
        error: 'Internal server error',
        message: error.message,
      });
    }
  }
);
