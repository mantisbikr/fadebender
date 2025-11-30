import * as logger from 'firebase-functions/logger';
import { getFirestore } from 'firebase-admin/firestore';
import { callPythonHelp } from './vertex-direct';
import { createSecureEndpoint } from './middleware/secure-endpoint';

interface DeviceExplainerRequest {
  device_type: string;
  experience_level?: 'beginner' | 'advanced';
}

interface DeviceControlInfo {
  name: string;
  role: string;
  tips?: string;
}

interface DeviceExplainerResponse {
  summary: string;
  controls: DeviceControlInfo[];
}

export const deviceExplainer = createSecureEndpoint(async (request, response) => {
  const body = request.body as DeviceExplainerRequest;
  const { device_type, experience_level } = body || {};

  if (!device_type || typeof device_type !== 'string') {
    response.status(400).json({ error: 'device_type is required and must be a string' });
    return;
  }

  logger.info('Device explainer request', { device_type, experience_level });

  // Placeholder: fetch one mapping document to seed explanation.
  const db = getFirestore();
  const snap = await db
    .collection('device_mappings')
    .where('device_type', '==', device_type)
    .limit(1)
    .get();

  let mapping: any = null;
  snap.forEach((doc) => {
    mapping = doc.data();
  });

  const prompt = `Explain the core controls of a ${device_type} in Fadebender for a ${
    experience_level || 'beginner'
  }.

Device mapping metadata (may be partial):
${JSON.stringify(mapping || {}, null, 2)}
`;

  const summary = await callPythonHelp({ query: prompt });

  const resp: DeviceExplainerResponse = {
    summary,
    controls: [],
  };

  response.json(resp);
});

