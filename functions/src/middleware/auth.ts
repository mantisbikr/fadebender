/**
 * Authentication Middleware for Cloud Functions
 *
 * Security layers:
 * 1. API Key validation (for server-to-server calls)
 * 2. Origin validation (CORS whitelist)
 * 3. Request sanitization
 */

import { Request } from 'firebase-functions/v2/https';
import { Response } from 'express';
import * as logger from 'firebase-functions/logger';

/**
 * Allowed origins for CORS
 * - localhost for development
 * - Add production domains as needed
 */
const ALLOWED_ORIGINS = [
  'http://localhost:3000',     // WebUI dev
  'http://localhost:8722',     // Python server dev
  'http://127.0.0.1:3000',
  'http://127.0.0.1:8722',
  // Add production domains when deploying to prod
  // 'https://fadebender.app',
  // 'https://studio.fadebender.app',
];

/**
 * API Key validation
 * Expects header: X-API-Key: <secret>
 *
 * To set API key in Firebase:
 * firebase functions:secrets:set FADEBENDER_API_KEY
 */
export function validateApiKey(request: Request): boolean {
  // Try multiple ways to access the header (case-insensitive)
  const apiKey = request.headers['x-api-key'] ||
                 request.headers['X-API-Key'] ||
                 request.headers['X-Api-Key'] ||
                 (request as any).get?.('X-API-Key');

  // Get expected API key from environment
  const expectedKey = process.env.FADEBENDER_API_KEY;

  if (!expectedKey) {
    logger.error('FADEBENDER_API_KEY not configured in environment');
    return false;
  }

  // Debug logging
  logger.info('API Key validation', {
    hasKey: !!apiKey,
    hasExpectedKey: !!expectedKey,
    keysMatch: apiKey === expectedKey,
    apiKeyLength: apiKey ? (apiKey as string).length : 0,
    expectedKeyLength: expectedKey ? expectedKey.length : 0,
    allHeaders: JSON.stringify(request.headers),
  });

  if (!apiKey || apiKey !== expectedKey) {
    logger.warn('Invalid or missing API key', {
      ip: request.ip,
      origin: request.headers.origin,
      hasKey: !!apiKey,
    });
    return false;
  }

  return true;
}

/**
 * CORS origin validation
 */
export function validateOrigin(request: Request): boolean {
  const origin = request.headers.origin;

  // If no origin header (non-browser request), require API key
  if (!origin) {
    return true; // Will be caught by API key validation
  }

  // Check if origin is allowed
  const isAllowed = ALLOWED_ORIGINS.includes(origin);

  if (!isAllowed) {
    logger.warn('Rejected request from unauthorized origin', {
      origin,
      ip: request.ip,
    });
  }

  return isAllowed;
}

/**
 * Set CORS headers for allowed origin
 */
export function setCorsHeaders(request: Request, response: Response): void {
  const origin = request.headers.origin;

  if (origin && ALLOWED_ORIGINS.includes(origin)) {
    response.set('Access-Control-Allow-Origin', origin);
    response.set('Access-Control-Allow-Methods', 'POST, OPTIONS');
    response.set('Access-Control-Allow-Headers', 'Content-Type, X-API-Key');
    response.set('Access-Control-Max-Age', '3600');
  }
}

/**
 * Input sanitization - prevent injection attacks
 */
export function sanitizeInput(query: string): string {
  if (typeof query !== 'string') {
    throw new Error('Query must be a string');
  }

  // Trim and limit length
  const sanitized = query.trim();

  if (sanitized.length === 0) {
    throw new Error('Query cannot be empty');
  }

  if (sanitized.length > 5000) {
    throw new Error('Query too long (max 5000 characters)');
  }

  // Block obvious injection attempts
  const suspiciousPatterns = [
    /<script/i,
    /javascript:/i,
    /on\w+\s*=/i,  // onload=, onclick=, etc.
    /\$\{/,        // Template literals
  ];

  for (const pattern of suspiciousPatterns) {
    if (pattern.test(sanitized)) {
      logger.warn('Blocked suspicious query pattern', {
        pattern: pattern.toString(),
      });
      throw new Error('Query contains invalid characters');
    }
  }

  return sanitized;
}

/**
 * Complete auth middleware
 * Use this at the start of each endpoint
 */
export function authenticateRequest(request: Request, response: Response): boolean {
  try {
    // 1. Set CORS headers first
    setCorsHeaders(request, response);

    // 2. Handle preflight
    if (request.method === 'OPTIONS') {
      response.status(204).send('');
      return false; // Don't continue processing
    }

    // 3. Validate origin
    if (!validateOrigin(request)) {
      response.status(403).json({
        error: 'Forbidden',
        message: 'Origin not allowed',
      });
      return false;
    }

    // 4. Validate API key
    if (!validateApiKey(request)) {
      response.status(401).json({
        error: 'Unauthorized',
        message: 'Invalid or missing API key',
      });
      return false;
    }

    // 5. All checks passed
    return true;

  } catch (error: any) {
    logger.error('Auth middleware error', error);
    response.status(500).json({
      error: 'Internal server error',
      message: error.message,
    });
    return false;
  }
}
