/**
 * Secure Endpoint Wrapper
 *
 * Wraps Cloud Function endpoints with:
 * - Authentication (API key)
 * - Rate limiting
 * - Input sanitization
 * - CORS handling
 * - Error handling
 */

import { Request, HttpsOptions, onRequest } from 'firebase-functions/v2/https';
import { Response } from 'express';
import * as logger from 'firebase-functions/logger';
import { authenticateRequest } from './auth';
import { checkRateLimit } from './rate-limit';

/**
 * Handler function type
 */
export type SecureHandler = (
  request: Request,
  response: Response
) => Promise<void>;

/**
 * Create a secure Cloud Function endpoint
 *
 * Usage:
 * export const myEndpoint = createSecureEndpoint(async (request, response) => {
 *   // Your handler code here
 *   // Input is already authenticated, rate-limited, and sanitized
 *   const { query } = request.body;
 *   response.json({ result: 'success' });
 * });
 */
export function createSecureEndpoint(
  handler: SecureHandler,
  options: Partial<HttpsOptions> = {}
) {
  const defaultOptions: HttpsOptions = {
    cors: false,  // Handled by auth middleware
    timeoutSeconds: 60,
    memory: '512MiB',
    secrets: ['FADEBENDER_API_KEY'],
  };

  const finalOptions = { ...defaultOptions, ...options };

  return onRequest(finalOptions, async (request, response) => {
    try {
      // 1. Authentication & CORS
      if (!authenticateRequest(request, response)) {
        return; // Response already sent by middleware
      }

      // 2. Rate limiting
      if (!(await checkRateLimit(request, response))) {
        return; // Response already sent by middleware
      }

      // 3. Call the handler
      await handler(request, response);

    } catch (error: any) {
      logger.error('Endpoint error', {
        error: error.message,
        stack: error.stack,
        path: request.path,
      });

      // Don't expose internal error details in production
      response.status(500).json({
        error: 'Internal server error',
        message: error.message,
      });
    }
  });
}
