import * as logger from 'firebase-functions/logger';
import { getConfigValue } from './config';
import { callPythonHelp } from './vertex-direct';
import { createSecureEndpoint } from './middleware/secure-endpoint';
import { sanitizeInput } from './middleware/auth';

interface MixAdviceRequest {
  query: string;
  userId?: string;
}

interface MixRecommendation {
  description: string;
  intent_suggestion?: string;
}

interface MixAdviceResponse {
  analysis: string;
  recommendations: MixRecommendation[];
}

export const mixAdvice = createSecureEndpoint(async (request, response) => {
  const body = request.body as MixAdviceRequest;
  const { query, userId } = body || {};

  if (!query || typeof query !== 'string') {
    response.status(400).json({ error: 'query is required and must be a string' });
    return;
  }

  // Sanitize input
  const sanitizedQuery = sanitizeInput(query);

  logger.info('Mix advice request', { query: sanitizedQuery, userId });
  const pythonServerUrl = process.env.PYTHON_SERVER_URL || 'http://localhost:8722';

  // Step 1: fetch a lightweight snapshot overview for context.
  let snapshotSummary: string | null = null;
  try {
    const snapRes = await fetch(`${pythonServerUrl}/snapshot`, { method: 'GET' });
    if (snapRes.ok) {
      const snap: any = await snapRes.json().catch(() => ({}));
      const data = snap.data || {};
      const tracks = (data.tracks || []) as Array<{ index: number; name: string; type?: string }>;
      const returns = (data.returns || []) as Array<{ index: number; name: string }>;
      const trackSummary = tracks
        .map((t) => `Track ${t.index}: ${t.name} (${t.type || 'track'})`)
        .join('; ');
      const returnSummary = returns
        .map((r) => `Return ${r.index}: ${r.name}`)
        .join('; ');
      snapshotSummary = `Tracks: ${trackSummary}\nReturns: ${returnSummary}`;
    }
  } catch (e: any) {
    logger.warn('Mix advice snapshot fetch failed', { error: e.message });
  }

  // Step 2: delegate to Python /help via vertex-direct with a hint + snapshot context.
  const mode = getConfigValue('rag.mix_advice.mode', 'basic') as string;
  const helpQueryParts = [`[mix_advice mode=${mode}] ${sanitizedQuery}`];
  if (snapshotSummary) {
    helpQueryParts.push('\n\nCurrent Live set summary:\n', snapshotSummary);
  }
  const helpQuery = helpQueryParts.join('');

  const analysisText = await callPythonHelp({ query: helpQuery });

  const resp: MixAdviceResponse = {
    analysis: analysisText,
    recommendations: [],
  };

  response.json(resp);
});
