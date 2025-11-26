import { onRequest } from 'firebase-functions/v2/https';
import * as logger from 'firebase-functions/logger';
import { getFirestore } from 'firebase-admin/firestore';

interface UserProfile {
  preferred_units?: 'db' | 'percent';
  default_vocal_track?: number;
  default_bass_track?: number;
  safe_max_gain_db?: number;
  genres?: string[];
  [key: string]: any;
}

interface UserProfileRequest {
  userId: string;
  profile?: UserProfile;
}

export const getUserProfile = onRequest(
  {
    cors: true,
    timeoutSeconds: 30,
    memory: '256MiB',
  },
  async (request, response) => {
    try {
      const body = request.body as UserProfileRequest;
      const { userId } = body || {};

      if (!userId || typeof userId !== 'string') {
        response.status(400).json({ error: 'userId is required and must be a string' });
        return;
      }

      const db = getFirestore();
      const doc = await db.collection('users').doc(userId).get();
      const data = (doc.exists ? (doc.data() as UserProfile) : {}) || {};

      response.json({ userId, profile: data });
    } catch (error: any) {
      logger.error('getUserProfile error', { error: error.message });
      response.status(500).json({ error: 'internal_error', message: error.message });
    }
  },
);

export const updateUserProfile = onRequest(
  {
    cors: true,
    timeoutSeconds: 30,
    memory: '256MiB',
  },
  async (request, response) => {
    try {
      const body = request.body as UserProfileRequest;
      const { userId, profile } = body || {};

      if (!userId || typeof userId !== 'string') {
        response.status(400).json({ error: 'userId is required and must be a string' });
        return;
      }
      if (!profile || typeof profile !== 'object') {
        response.status(400).json({ error: 'profile is required and must be an object' });
        return;
      }

      const db = getFirestore();
      await db.collection('users').doc(userId).set(profile, { merge: true });

      response.json({ ok: true, userId });
    } catch (error: any) {
      logger.error('updateUserProfile error', { error: error.message });
      response.status(500).json({ error: 'internal_error', message: error.message });
    }
  },
);

