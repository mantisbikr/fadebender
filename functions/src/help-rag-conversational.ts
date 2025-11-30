/**
 * Conversational RAG System for Fadebender Help
 *
 * Features:
 * - Multi-turn conversations with context retention
 * - Response format detection (brief/detailed/bulleted/step-by-step)
 * - Dynamic system prompt adjustment
 * - Session management in Firestore
 */

import * as logger from 'firebase-functions/logger';
import { getFirestore, FieldValue } from 'firebase-admin/firestore';
import { searchVertexAIEnhanced, SearchResponse } from './vertex-search-enhanced';

export interface ConversationTurn {
  query: string;
  response: string;
  timestamp: number;
  format?: ResponseFormat;
}

export interface ConversationSession {
  sessionId: string;
  userId?: string;
  turns: ConversationTurn[];
  projectContext?: any;
  createdAt: number;
  updatedAt: number;
}

export type ResponseFormat =
  | 'brief'
  | 'detailed'
  | 'bulleted'
  | 'step-by-step'
  | 'conversational'
  | 'default';

export interface HelpRequest {
  query: string;
  sessionId?: string;
  userId?: string;
  projectContext?: any;
  format?: ResponseFormat;
}

export interface HelpResponse {
  answer: string;
  sessionId: string;
  sources?: string[];
  format: ResponseFormat;
  conversationContext?: {
    turnCount: number;
    previousQuery?: string;
  };
}

/**
 * Detect response format from user query
 */
export function detectResponseFormat(query: string): ResponseFormat {
  const lowerQuery = query.toLowerCase();

  // Brief/short patterns
  if (lowerQuery.match(/\b(brief|short|quick|one sentence|concise|keep it (brief|short))\b/)) {
    return 'brief';
  }

  // Detailed patterns
  if (lowerQuery.match(/\b(detailed?|in detail|comprehensive|explain everything|tell me everything)\b/)) {
    return 'detailed';
  }

  // Bulleted patterns
  if (lowerQuery.match(/\b(bullet(ed)?( points?| list)?|as (a )?list|list( format)?)\b/)) {
    return 'bulleted';
  }

  // Step-by-step patterns
  if (lowerQuery.match(/\b(step[ -]by[ -]step|numbered list|guide me|walk me through)\b/)) {
    return 'step-by-step';
  }

  // Conversational (follow-up questions)
  if (lowerQuery.match(/^(what about|how about|and|also|what if|should i also)\b/i)) {
    return 'conversational';
  }

  return 'default';
}

/**
 * Generate preamble based on response format and context
 */
export function generatePreamble(
  format: ResponseFormat,
  hasConversationContext: boolean,
  projectContext?: any
): string {
  // Base identity
  let preamble = 'You are an expert audio engineer and Ableton Live instructor for Fadebender, an AI-powered mixing assistant.';

  // Add project context if available
  if (projectContext) {
    preamble += `\n\nCurrent Ableton Live Project Context:\n${JSON.stringify(projectContext, null, 2)}`;
  }

  // Add conversation context note
  if (hasConversationContext) {
    preamble += '\n\nThis is a follow-up question in an ongoing conversation. Reference previous context when relevant.';
  }

  // Add format-specific instructions
  switch (format) {
    case 'brief':
      preamble += '\n\nProvide a CONCISE answer (1-3 sentences maximum). Be direct and to the point. Include only the most essential information.';
      break;

    case 'detailed':
      preamble += '\n\nProvide a COMPREHENSIVE and DETAILED answer. Include:\n- In-depth explanations of concepts\n- Multiple examples and use cases\n- Technical details and parameter ranges\n- Best practices and professional tips\n- Specific Fadebender commands when relevant\n\nUse clear sections and formatting to organize the information.';
      break;

    case 'bulleted':
      preamble += '\n\nProvide your answer as a BULLETED LIST. Each point should be:\n- Clear and concise\n- Actionable when applicable\n- Include specific values/presets/commands\n\nExample format:\n- Point 1: Specific recommendation\n- Point 2: Parameter setting\n- Point 3: Fadebender command';
      break;

    case 'step-by-step':
      preamble += '\n\nProvide a STEP-BY-STEP guide using a NUMBERED LIST. Each step should:\n1. Be clear and sequential\n2. Include specific actions to take\n3. Include parameter values or preset names\n4. Include Fadebender commands when relevant\n\nFormat each step clearly with the number followed by the action.';
      break;

    case 'conversational':
      preamble += '\n\nThis is a follow-up question. Provide a natural, conversational response that:\n- Builds on the previous answer\n- References earlier recommendations when relevant\n- Maintains consistency with previous advice\n- Feels like a continuation of the same conversation';
      break;

    default:
      preamble += '\n\nProvide clear, actionable advice based on the retrieved documents. When relevant, include:\n- Specific device/preset names from the catalogs\n- Parameter settings (e.g., "Set reverb decay to 2-3s")\n- Fadebender commands (e.g., "load reverb preset cathedral on return A")\n- Audio engineering explanations';
      break;
  }

  // Always include formatting and citation instructions
  preamble += '\n\nFormatting requirements:';
  preamble += '\n- Use markdown formatting for better readability';
  preamble += '\n- Use **bold** for parameter names and important terms';
  preamble += '\n- Use bullet points for lists';
  preamble += '\n- Include specific numeric ranges WITH units (e.g., "0.5 to 250 ms" not "0 to 100 ms")';
  preamble += '\n- ALWAYS cite your sources at the end';

  return preamble;
}

/**
 * Get or create conversation session
 */
export async function getConversationSession(
  sessionId?: string,
  userId?: string
): Promise<ConversationSession> {
  const db = getFirestore();

  if (sessionId) {
    // Try to retrieve existing session
    const sessionDoc = await db.collection('help_conversations').doc(sessionId).get();

    if (sessionDoc.exists) {
      return sessionDoc.data() as ConversationSession;
    }
  }

  // Create new session
  const newSession: ConversationSession = {
    sessionId: sessionId || generateSessionId(),
    userId,
    turns: [],
    createdAt: Date.now(),
    updatedAt: Date.now(),
  };

  await db.collection('help_conversations').doc(newSession.sessionId).set(newSession);

  return newSession;
}

/**
 * Save conversation turn to Firestore
 */
export async function saveConversationTurn(
  sessionId: string,
  turn: ConversationTurn,
  projectContext?: any
): Promise<void> {
  const db = getFirestore();
  const sessionRef = db.collection('help_conversations').doc(sessionId);

  await sessionRef.update({
    turns: FieldValue.arrayUnion(turn),
    updatedAt: Date.now(),
    ...(projectContext && { projectContext }),
  });
}

/**
 * Build context from previous conversation turns
 */
export function buildConversationContext(turns: ConversationTurn[], limit = 3): string {
  if (turns.length === 0) return '';

  // Get last N turns
  const recentTurns = turns.slice(-limit);

  return recentTurns
    .map((turn, index) => `[Turn ${index + 1}]\nUser: ${turn.query}\nAssistant: ${turn.response}`)
    .join('\n\n');
}

/**
 * Generate unique session ID
 */
function generateSessionId(): string {
  return `session_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`;
}

/**
 * Main conversational RAG function
 */
export async function generateHelpResponse(request: HelpRequest): Promise<HelpResponse> {
  logger.info('Generating help response', {
    query: request.query,
    sessionId: request.sessionId,
    hasProjectContext: !!request.projectContext,
  });

  try {
    // Get or create conversation session
    const session = await getConversationSession(request.sessionId, request.userId);

    // Detect response format (use explicit format or detect from query)
    const format = request.format || detectResponseFormat(request.query);

    // Build conversation context from previous turns
    const conversationContext = buildConversationContext(session.turns, 3);
    const hasConversationContext = session.turns.length > 0;

    // Generate preamble based on format and context
    const preamble = generatePreamble(
      format,
      hasConversationContext,
      request.projectContext || session.projectContext
    );

    // Build enhanced query with conversation context
    let enhancedQuery = request.query;
    if (conversationContext && format === 'conversational') {
      enhancedQuery = `${conversationContext}\n\n[New Question]\n${request.query}`;
    }

    // Search with answer generation
    const searchResponse: SearchResponse = await searchVertexAIEnhanced(enhancedQuery, {
      maxResults: 5,

      summarySpec: {
        summaryResultCount: 5,
        includeCitations: true,
        ignoreAdversarialQuery: true,
        ignoreNonSummarySeekingQuery: false,
        modelPromptSpec: {
          preamble,
        },
        languageCode: 'en',
      },

      extractiveContentSpec: {
        maxExtractiveAnswerCount: 3,
        maxExtractiveSegmentCount: 5,
        returnExtractiveSegmentScore: true,
      },

      // Boost device/preset catalogs for specific recommendations
      boostSpec: {
        conditionBoostSpecs: [
          { condition: 'document.uri:*device-catalog*', boost: 1.5 },
          { condition: 'document.uri:*preset-catalog*', boost: 1.5 },
        ],
      },
    });

    // Extract answer
    const answer = searchResponse.summary?.summaryText ||
                   'I could not find relevant information to answer your question. Please try rephrasing or asking something else.';

    // Extract sources
    const sources = searchResponse.results
      .filter(r => r.uri)
      .map(r => r.uri!)
      .filter((uri, index, self) => self.indexOf(uri) === index) // Unique
      .slice(0, 5);

    // Save conversation turn
    const turn: ConversationTurn = {
      query: request.query,
      response: answer,
      timestamp: Date.now(),
      format,
    };

    await saveConversationTurn(
      session.sessionId,
      turn,
      request.projectContext || session.projectContext
    );

    logger.info('Help response generated', {
      sessionId: session.sessionId,
      format,
      turnCount: session.turns.length + 1,
      sourceCount: sources.length,
    });

    return {
      answer,
      sessionId: session.sessionId,
      sources,
      format,
      conversationContext: {
        turnCount: session.turns.length + 1,
        previousQuery: session.turns.length > 0
          ? session.turns[session.turns.length - 1].query
          : undefined,
      },
    };

  } catch (error: any) {
    logger.error('Error generating help response', {
      error: error.message,
      query: request.query,
    });
    throw error;
  }
}

/**
 * Clear old conversation sessions (cleanup function)
 */
export async function cleanupOldSessions(maxAgeMs = 7 * 24 * 60 * 60 * 1000): Promise<number> {
  const db = getFirestore();
  const cutoffTime = Date.now() - maxAgeMs;

  const oldSessions = await db
    .collection('help_conversations')
    .where('updatedAt', '<', cutoffTime)
    .get();

  const batch = db.batch();
  oldSessions.docs.forEach(doc => {
    batch.delete(doc.ref);
  });

  await batch.commit();

  logger.info('Cleaned up old conversation sessions', {
    deletedCount: oldSessions.size,
  });

  return oldSessions.size;
}
