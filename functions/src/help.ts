import { onRequest } from 'firebase-functions/v2/https';
import { getConfigValue, isRagEnabled } from './config';
import { isVertexSearchEnabled } from './vertex-search';
import { generateRAGHelp } from './help-rag';
import { generateFallbackHelp, HelpResponse } from './help-fallback';
import { generateHelpResponse, ResponseFormat } from './help-rag-conversational';
import * as logger from 'firebase-functions/logger';

/**
 * Help Endpoint with Feature-Flagged RAG and Conversational Support
 *
 * Supports three modes:
 * 1. Conversational RAG Mode (conversational = true): Uses Vertex AI Search + LLM with session management
 * 2. RAG Mode (rag.vertex_ai_search.enabled = true): Uses Vertex AI Search + LLM
 * 3. Fallback Mode (rag.vertex_ai_search.enabled = false): Uses LLM only
 *
 * Configuration in configs/rag_config.json:
 * - rag.enabled: Master switch for RAG system
 * - rag.vertex_ai_search.enabled: Enable/disable Vertex AI Search
 * - rag.vertex_ai_search.fallback_on_error: Auto-fallback if RAG fails
 */

interface HelpRequest {
  query: string;
  userId?: string;
  sessionId?: string;
  projectContext?: any;
  format?: ResponseFormat;
  conversational?: boolean;
}

/**
 * Process help query with feature-flagged RAG
 */
async function processHelpQuery(request: HelpRequest): Promise<HelpResponse> {
  logger.info('Help query received', {
    query: request.query,
    userId: request.userId,
    conversational: request.conversational,
    hasSessionId: !!request.sessionId,
    hasProjectContext: !!request.projectContext,
  });

  // Check if RAG system is enabled at all
  if (!isRagEnabled()) {
    logger.warn('RAG system is disabled in config');
    const fallback = await generateFallbackHelp(request.query);
    return fallback;
  }

  // Check if Vertex AI Search is enabled
  const useRAG = isVertexSearchEnabled();
  const fallbackOnError = getConfigValue('rag.vertex_ai_search.fallback_on_error', true);

  logger.info('Help mode selected', {
    useRAG,
    conversational: request.conversational,
    fallbackOnError,
    query: request.query,
  });

  if (useRAG) {
    try {
      // Use conversational RAG if requested or if sessionId is provided
      if (request.conversational || request.sessionId) {
        logger.info('Using conversational RAG mode');
        const conversationalResponse = await generateHelpResponse({
          query: request.query,
          sessionId: request.sessionId,
          userId: request.userId,
          projectContext: request.projectContext,
          format: request.format,
        });

        // Convert to HelpResponse format
        return {
          response: conversationalResponse.answer,
          model_used: 'vertex-ai-search-conversational',
          sources: conversationalResponse.sources?.map(uri => ({
            title: uri.split('/').pop() || uri,
            snippet: '',
          })),
          mode: 'rag-conversational',
          sessionId: conversationalResponse.sessionId,
          format: conversationalResponse.format,
          conversationContext: conversationalResponse.conversationContext,
        };
      }

      // Try traditional RAG mode
      const ragResponse = await generateRAGHelp(request.query);
      return ragResponse;
    } catch (error: any) {
      logger.error('RAG help generation failed', {
        error: error.message,
        query: request.query,
        willFallback: fallbackOnError,
      });

      if (fallbackOnError) {
        logger.info('Falling back to non-RAG help');
        const fallback = await generateFallbackHelp(request.query);
        return fallback;
      }

      throw error;
    }
  } else {
    // Use fallback mode (no RAG)
    const fallback = await generateFallbackHelp(request.query);
    return fallback;
  }
}

/**
 * HTTP endpoint for help queries
 *
 * Request body:
 * {
 *   query: string;              // Required: The help query
 *   userId?: string;             // Optional: User ID for tracking
 *   sessionId?: string;          // Optional: Session ID for conversation continuity
 *   projectContext?: any;        // Optional: Ableton Live project context
 *   format?: ResponseFormat;     // Optional: 'brief' | 'detailed' | 'bulleted' | 'step-by-step'
 *   conversational?: boolean;    // Optional: Enable conversational mode (default: true if sessionId provided)
 * }
 *
 * Example requests:
 *
 * 1. Simple query (no conversation):
 * {
 *   "query": "What reverb presets are available?"
 * }
 *
 * 2. Start a conversation:
 * {
 *   "query": "My vocals sound weak",
 *   "conversational": true
 * }
 * Response will include sessionId for follow-ups.
 *
 * 3. Follow-up question:
 * {
 *   "query": "What reverb preset do you recommend?",
 *   "sessionId": "session_1234567890_abc123"
 * }
 *
 * 4. With format control:
 * {
 *   "query": "Explain reverb decay [keep it brief]"
 * }
 * Or explicitly:
 * {
 *   "query": "Explain reverb decay",
 *   "format": "brief"
 * }
 *
 * 5. With project context:
 * {
 *   "query": "How can I improve my mix?",
 *   "projectContext": {
 *     "tracks": [...],
 *     "returns": [...]
 *   }
 * }
 */
export const help = onRequest(
  {
    cors: true,
    timeoutSeconds: 60,
    memory: '512MiB',
  },
  async (request, response) => {
    try {
      const {
        query,
        userId,
        sessionId,
        projectContext,
        format,
        conversational,
      } = request.body;

      if (!query || typeof query !== 'string') {
        response.status(400).json({
          error: 'Query is required and must be a string',
        });
        return;
      }

      const helpRequest: HelpRequest = {
        query,
        userId,
        sessionId,
        projectContext,
        format,
        conversational,
      };

      const result = await processHelpQuery(helpRequest);

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
