import { onRequest } from 'firebase-functions/v2/https';
import * as logger from 'firebase-functions/logger';
import { getConfigValue } from './config';
import { callPythonHelp } from './vertex-direct';

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

export const mixAdvice = onRequest(
  {
    cors: true,
    timeoutSeconds: 60,
    memory: '512MiB',
  },
  async (request, response) => {
    try {
      const body = request.body as MixAdviceRequest;
      const { query, userId } = body || {};

      if (!query || typeof query !== 'string') {
        response.status(400).json({ error: 'query is required and must be a string' });
        return;
      }

      logger.info('Mix advice request', { query, userId });
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
      const helpQueryParts = [`[mix_advice mode=${mode}] ${query}`];
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
    } catch (error: any) {
      logger.error('Mix advice error', { error: error.message });
      response.status(500).json({
        error: 'internal_error',
        message: error.message,
      });
    }
  },
);
