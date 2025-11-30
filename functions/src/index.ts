/**
 * Fadebender Cloud Functions
 *
 * Firebase Cloud Functions for RAG-powered help and conversation system
 *
 * Phase 1: Basic help endpoint with RAG retrieval
 * Phase 2: Multi-turn conversations
 * Phase 3: Project context injection
 * Phase 4: Device/preset discovery + advisory tools
 */

// Initialize Firebase Admin SDK
import { initializeApp } from 'firebase-admin/app';
initializeApp();

import { help } from './help';
import { mixAdvice } from './mix-advice';
import { presetRecommendations } from './preset-recommendations';
import { presetTuningAdvice } from './preset-tuning-advice';
import { deviceExplainer } from './device-explainer';
import { getUserProfile, updateUserProfile } from './user-profile';
import { health } from './health';

// Export Cloud Functions
export {
  help,
  mixAdvice,
  presetRecommendations,
  presetTuningAdvice,
  deviceExplainer,
  getUserProfile,
  updateUserProfile,
  health,
};

// TODO: Future endpoints
// export { chat } from './chat';           // Phase 2: Conversation system
// export { parseIntent } from './intent'; // Migrate existing intent parser
