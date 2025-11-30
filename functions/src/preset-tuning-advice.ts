import * as logger from 'firebase-functions/logger';
import { getFirestore } from 'firebase-admin/firestore';
import { callVertexSearch } from './vertex-direct';
import { createSecureEndpoint } from './middleware/secure-endpoint';
import { sanitizeInput } from './middleware/auth';

interface DeviceLocation {
  domain: 'track' | 'return';
  track_index?: number;
  return_index?: number;
  device_index: number;
}

interface PresetTuningAdviceRequest {
  device_type: string;
  goal: string;
  location: DeviceLocation;
  preset_id?: string;
}

interface TweakSuggestion {
  param: string;
  from?: number | string;
  to?: number | string;
  unit?: string;
  reason?: string;
}

interface PresetTuningAdviceResponse {
  analysis: string;
  tweaks: TweakSuggestion[];
}

export const presetTuningAdvice = createSecureEndpoint(async (request, response) => {
  const body = request.body as PresetTuningAdviceRequest;
  const { device_type, goal, location, preset_id } = body || {};

  if (!device_type || typeof device_type !== 'string') {
    response.status(400).json({ error: 'device_type is required and must be a string' });
    return;
  }
  if (!goal || typeof goal !== 'string') {
    response.status(400).json({ error: 'goal is required and must be a string' });
    return;
  }
  if (!location || typeof location !== 'object' || typeof location.device_index !== 'number') {
    response.status(400).json({ error: 'location with device_index is required' });
    return;
  }

  // Sanitize input
  const sanitizedGoal = sanitizeInput(goal);

  logger.info('Preset tuning advice request', { device_type, goal: sanitizedGoal, location });

  const pythonServerUrl = process.env.PYTHON_SERVER_URL || 'http://localhost:8722';
  const db = getFirestore();

  // Step 1: fetch capabilities for the specified device instance
  let deviceSummary = '';
  try {
        const { domain, device_index } = location;
        const idx =
          domain === 'track' ? location.track_index ?? 1 : location.return_index ?? 0;

        const path =
          domain === 'track'
            ? `/track/device/capabilities?index=${idx}&device=${device_index}`
            : `/return/device/capabilities?index=${idx}&device=${device_index}`;

        const res = await fetch(`${pythonServerUrl}${path}`, { method: 'GET' });
        if (res.ok) {
          const data: any = await res.json().catch(() => ({}));
          const caps = data.data || {};
          const dname = caps.device_name || 'Unknown';
          const dtype = caps.device_type || device_type;
          const values = caps.values || {};

          const paramSummaries: string[] = [];
          Object.entries(values).forEach(([name, v]) => {
            const vv: any = v;
            const disp = vv.display_value ?? vv.value;
            paramSummaries.push(`${name}: ${disp}`);
          });

          deviceSummary = `Device: ${dname} (type=${dtype})\nParameters:\n- ${paramSummaries.join(
            '\n- ',
          )}`;
        }
      } catch (e: any) {
        logger.warn('presetTuningAdvice capabilities fetch failed', { error: e.message });
      }

      // Step 2: Optionally fetch preset metadata to enrich context
      let presetMetadataSummary = '';
      try {
        if (preset_id && typeof preset_id === 'string') {
          const doc = await db.collection('presets').doc(preset_id).get();
          if (doc.exists) {
            const data = doc.data() as any;
            const meta = {
              name: data.name,
              device_name: data.device_name,
              category: data.category || data.device_type,
              subcategory: data.subcategory,
              description: data.description,
              audio_engineering: data.audio_engineering,
              natural_language_controls: data.natural_language_controls,
            };
            presetMetadataSummary = JSON.stringify(meta, null, 2);
          }
        }
      } catch (e: any) {
        logger.warn('presetTuningAdvice preset metadata fetch failed', { error: e.message });
      }

      // Step 3: Ask LLM (via Python /help) for structured tuning advice, using device + preset context.
      const prompt = `
You are an expert mix engineer.

User goal:
${goal}

Device type: ${device_type}

Current device instance:
${deviceSummary || '(no details available)'}

Preset metadata (may be partial):
${presetMetadataSummary || '(no preset metadata available)'}

Task:
- Suggest concrete parameter tweaks to move toward the goal.
- Focus on a small number of high-impact parameters (2-5 tweaks).
- Respond in STRICT JSON only, no prose.
- JSON shape:
{
  "analysis": "short explanation of what to change and why",
  "tweaks": [
    { "param": "Decay Time", "from": 2.5, "to": 1.6, "unit": "s", "reason": "shorter, more intimate space" }
  ]
}
`;

      let analysis = '';
      let tweaks: TweakSuggestion[] = [];

      try {
        const raw = await callVertexSearch({ query: prompt });
        const parsed = JSON.parse(raw) as PresetTuningAdviceResponse;
        analysis = parsed.analysis || '';
        tweaks = Array.isArray(parsed.tweaks) ? parsed.tweaks : [];
      } catch (e: any) {
        logger.warn('presetTuningAdvice JSON parse failed, falling back to text-only analysis', {
          error: e.message,
        });
        // Fallback: treat raw response as analysis only
        try {
          const raw = await callVertexSearch({ query: prompt });
          analysis = raw;
          tweaks = [];
        } catch (inner: any) {
          analysis = 'Unable to generate tuning advice at this time.';
          tweaks = [];
        }
      }

  const resp: PresetTuningAdviceResponse = {
    analysis,
    tweaks,
  };

  response.json(resp);
});
