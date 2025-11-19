/**
 * Python Server Help Client
 *
 * Calls the existing working Python server /help endpoint
 * This uses the proven Python vertexai SDK for LLM generation
 */

import * as logger from 'firebase-functions/logger';

export interface PythonHelpOptions {
  query: string;
  context?: Record<string, any>;
}

/**
 * Generate help response by calling the existing Python server
 * Uses the working Python /help endpoint with vertexai SDK
 */
export async function callPythonHelp(options: PythonHelpOptions): Promise<string> {
  const { query, context } = options;

  // Call the existing Python server's /help endpoint
  // This endpoint uses the working Python vertexai SDK
  const pythonServerUrl = process.env.PYTHON_SERVER_URL || 'http://localhost:8722';
  const endpoint = `${pythonServerUrl}/help`;

  logger.info('Calling Python server /help endpoint', { query, hasContext: !!context, endpoint });

  try {
    const response = await fetch(endpoint, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        query,
        context,
      }),
    });

    if (!response.ok) {
      const errorText = await response.text();
      logger.error('Python server /help error', {
        status: response.status,
        statusText: response.statusText,
        error: errorText
      });
      throw new Error(`Python server error: ${response.status} ${response.statusText}\n${errorText}`);
    }

    const data = await response.json();
    const text = data.response || data.answer || String(data);

    logger.info('Python server /help response received', {
      responseLength: text.length,
    });

    return text;
  } catch (error: any) {
    logger.error('Python server /help call failed', { error: error.message, query, endpoint });
    throw error;
  }
}
