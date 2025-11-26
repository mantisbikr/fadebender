import { onRequest } from 'firebase-functions/v2/https';
import * as logger from 'firebase-functions/logger';
import { getFirestore } from 'firebase-admin/firestore';
import { callPythonHelp } from './vertex-direct';

interface PresetRecommendationsRequest {
  device_type: string;
  goal: string;
  userId?: string;
}

interface PresetRecommendation {
  preset_id: string;
  name: string;
  why: string;
  suggested_commands: string[];
}

interface PresetRecommendationsResponse {
  recommendations: PresetRecommendation[];
}

export const presetRecommendations = onRequest(
  {
    cors: true,
    timeoutSeconds: 60,
    memory: '512MiB',
  },
  async (request, response) => {
    try {
      const body = request.body as PresetRecommendationsRequest;
      const { device_type, goal } = body || {};

      if (!device_type || typeof device_type !== 'string') {
        response.status(400).json({ error: 'device_type is required and must be a string' });
        return;
      }
      if (!goal || typeof goal !== 'string') {
        response.status(400).json({ error: 'goal is required and must be a string' });
        return;
      }

      logger.info('Preset recommendations request', { device_type, goal });

      // Step 1: read candidate presets for the device_type.
      const db = getFirestore();
      const snap = await db
        .collection('presets')
        .where('category', '==', device_type)
        .limit(25)
        .get();

      const candidates: any[] = [];
      snap.forEach((doc) => {
        const data = doc.data() as any;
        candidates.push({
          preset_id: doc.id,
          name: data.name || doc.id,
          device_name: data.device_name,
          device_type: data.category || data.device_type,
          subcategory: data.subcategory,
          genre_tags: data.genre_tags || [],
          description: data.description,
          audio_engineering: data.audio_engineering,
        });
      });

      if (candidates.length === 0) {
        response.json({ recommendations: [] });
        return;
      }

      // Step 2: ask Python /help LLM to rank candidates for this goal.
      // We piggyback on the existing Vertex integration by sending a structured prompt.
      const prompt = `
You are helping choose presets for a ${device_type}.

User goal:
${goal}

Candidate presets (JSON):
${JSON.stringify(candidates, null, 2)}

Task:
- Pick the best 3 presets for the goal.
- For each, provide:
  - preset_id
  - name
  - why (one or two sentences, grounded in audio_engineering / description)
- Respond in STRICT JSON only:
{
  "recommendations": [
    { "preset_id": "...", "name": "...", "why": "..." }
  ]
}
`;

      let ranked: PresetRecommendationsResponse = { recommendations: [] };
      try {
        const raw = await callPythonHelp({ query: prompt });
        ranked = JSON.parse(raw) as PresetRecommendationsResponse;
      } catch (e: any) {
        logger.warn('Preset ranking via LLM failed, falling back to simple list', {
          error: e?.message,
        });
        ranked = {
          recommendations: candidates.slice(0, 3).map((c) => ({
            preset_id: c.preset_id,
            name: c.name,
            why: `Matches device_type=${device_type}; goal="${goal}".`,
            suggested_commands: [],
          })),
        };
      }

      // Ensure suggested_commands field is present.
      const recommendations: PresetRecommendation[] = (ranked.recommendations || []).map(
        (rec) => ({
          ...rec,
          suggested_commands: rec.suggested_commands || [],
        }),
      );

      const resp: PresetRecommendationsResponse = { recommendations };
      response.json(resp);
    } catch (error: any) {
      logger.error('Preset recommendations error', { error: error.message });
      response.status(500).json({
        error: 'internal_error',
        message: error.message,
      });
    }
  },
);
