/**
 * Fadebender Cloud Functions
 *
 * Firebase Cloud Functions for RAG-powered help and conversation system
 *
 * Phase 1: Basic help endpoint with RAG retrieval
 * Phase 2: Multi-turn conversations
 * Phase 3: Project context injection
 * Phase 4: Device/preset discovery
 */

import { help } from './help';

// Export Cloud Functions
export {
  help,
};

// TODO: Future endpoints
// export { chat } from './chat';           // Phase 2: Conversation system
// export { parseIntent } from './intent'; // Migrate existing intent parser
