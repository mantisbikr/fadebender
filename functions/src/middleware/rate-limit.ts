/**
 * Rate Limiting Middleware for Cloud Functions
 *
 * Protects against:
 * - Brute force attacks
 * - Excessive API usage
 * - Cost overruns from Vertex AI calls
 *
 * Uses Firestore for distributed rate limiting across function instances
 */

import { getFirestore } from 'firebase-admin/firestore';
import { Request } from 'firebase-functions/v2/https';
import { Response } from 'express';
import * as logger from 'firebase-functions/logger';

/**
 * Rate limit configuration
 */
interface RateLimitConfig {
  maxRequests: number;      // Max requests per window
  windowSeconds: number;    // Time window in seconds
  blockDurationSeconds: number;  // How long to block after exceeding limit
}

/**
 * Default rate limits
 * - Per IP: 60 requests per minute (generous for normal usage)
 * - Per user: 100 requests per minute (if userId provided)
 */
const DEFAULT_LIMITS: Record<string, RateLimitConfig> = {
  ip: {
    maxRequests: 60,
    windowSeconds: 60,
    blockDurationSeconds: 300, // 5 minutes
  },
  user: {
    maxRequests: 100,
    windowSeconds: 60,
    blockDurationSeconds: 300,
  },
};

/**
 * Track rate limit attempts in Firestore
 */
interface RateLimitRecord {
  identifier: string;       // IP or userId
  type: 'ip' | 'user';
  count: number;
  windowStart: number;      // Timestamp
  blocked: boolean;
  blockedUntil?: number;    // Timestamp when block expires
  lastRequest: number;
}

/**
 * Get identifier from request (IP or userId)
 */
function getIdentifier(request: Request, type: 'ip' | 'user'): string | null {
  if (type === 'ip') {
    return request.ip || request.headers['x-forwarded-for'] as string || 'unknown';
  }

  // Extract userId from request body or headers
  const userId = request.body?.userId || request.headers['x-user-id'];
  return userId || null;
}

/**
 * Check rate limit for a request
 */
export async function checkRateLimit(
  request: Request,
  response: Response,
  config: RateLimitConfig = DEFAULT_LIMITS.ip
): Promise<boolean> {
  try {
    const db = getFirestore();
    const now = Date.now();

    // Check both IP and user-based rate limits
    const checks = [
      { type: 'ip' as const, config: DEFAULT_LIMITS.ip },
      { type: 'user' as const, config: DEFAULT_LIMITS.user },
    ];

    for (const check of checks) {
      const identifier = getIdentifier(request, check.type);
      if (!identifier) continue; // Skip if no identifier

      const docId = `${check.type}_${identifier}`;
      const docRef = db.collection('rate_limits').doc(docId);

      // Get current record
      const doc = await docRef.get();
      const record = doc.exists ? doc.data() as RateLimitRecord : null;

      // Check if currently blocked
      if (record?.blocked && record.blockedUntil && record.blockedUntil > now) {
        const remainingSeconds = Math.ceil((record.blockedUntil - now) / 1000);

        logger.warn('Rate limit exceeded', {
          type: check.type,
          identifier,
          remainingSeconds,
        });

        response.status(429).json({
          error: 'Too many requests',
          message: `Rate limit exceeded. Try again in ${remainingSeconds} seconds.`,
          retryAfter: remainingSeconds,
        });

        return false;
      }

      // Calculate window start
      const windowStart = now - (check.config.windowSeconds * 1000);

      // Check if we're in a new window
      if (!record || record.windowStart < windowStart) {
        // Start new window
        await docRef.set({
          identifier,
          type: check.type,
          count: 1,
          windowStart: now,
          blocked: false,
          lastRequest: now,
        });
        continue; // This check passed
      }

      // Increment count in current window
      const newCount = record.count + 1;

      if (newCount > check.config.maxRequests) {
        // Block this identifier
        const blockedUntil = now + (check.config.blockDurationSeconds * 1000);

        await docRef.update({
          count: newCount,
          blocked: true,
          blockedUntil,
          lastRequest: now,
        });

        const remainingSeconds = check.config.blockDurationSeconds;

        logger.warn('Rate limit triggered', {
          type: check.type,
          identifier,
          count: newCount,
          maxRequests: check.config.maxRequests,
          blockedFor: remainingSeconds,
        });

        response.status(429).json({
          error: 'Too many requests',
          message: `Rate limit exceeded. Try again in ${remainingSeconds} seconds.`,
          retryAfter: remainingSeconds,
        });

        return false;
      }

      // Update count
      await docRef.update({
        count: newCount,
        lastRequest: now,
      });
    }

    // All checks passed
    return true;

  } catch (error: any) {
    // Don't block requests if rate limiting fails
    logger.error('Rate limit check failed', {
      error: error.message,
      ip: request.ip,
    });

    // Allow request to proceed (fail open)
    return true;
  }
}

/**
 * Clean up old rate limit records
 * Run this periodically via scheduled function
 */
export async function cleanupRateLimits(): Promise<number> {
  const db = getFirestore();
  const now = Date.now();
  const maxAge = 24 * 60 * 60 * 1000; // 24 hours

  const oldRecords = await db
    .collection('rate_limits')
    .where('lastRequest', '<', now - maxAge)
    .get();

  const batch = db.batch();
  oldRecords.docs.forEach(doc => {
    batch.delete(doc.ref);
  });

  await batch.commit();

  logger.info('Cleaned up old rate limit records', {
    deletedCount: oldRecords.size,
  });

  return oldRecords.size;
}
