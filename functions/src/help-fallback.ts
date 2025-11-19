/**
 * Fallback Help Response Generator
 *
 * Generates help responses without RAG using basic LLM prompting.
 * Used when RAG is disabled or as a fallback when RAG fails.
 */

import { getConfigValue } from './config';
import { callPythonHelp } from './vertex-direct';
import * as logger from 'firebase-functions/logger';

export interface HelpResponse {
  response: string;
  model_used: string;
  sources?: Array<{ title: string; snippet: string }>;
  mode: 'rag' | 'fallback';
}

/**
 * Generate help response using fallback (non-RAG) method
 */
export async function generateFallbackHelp(query: string): Promise<HelpResponse> {
  logger.info('Using fallback help generator (no RAG)', { query });

  const modelName = getConfigValue('models.help_assistant', 'gemini-1.5-flash');

  // Call Python server /help endpoint without RAG context (fallback mode)
  const responseText = await callPythonHelp({
    query,
    // No context = fallback mode
  });

  logger.info('Fallback help response generated', {
    query,
    responseLength: responseText.length,
    model: modelName,
  });

  return {
    response: responseText,
    model_used: modelName,
    mode: 'fallback',
  };
}

