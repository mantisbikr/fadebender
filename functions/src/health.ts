import { onRequest } from 'firebase-functions/v2/https';
import * as logger from 'firebase-functions/logger';

interface HealthResponse {
  server_ok: boolean;
  snapshot_ok: boolean;
  live_connected: boolean | null;
  mode: 'full' | 'explain_only';
}

export const health = onRequest(
  {
    cors: true,
    timeoutSeconds: 15,
    memory: '256MiB',
  },
  async (_request, response) => {
    try {
      const pythonServerUrl = process.env.PYTHON_SERVER_URL || 'http://localhost:8722';

      let server_ok = false;
      let snapshot_ok = false;
      let live_connected: boolean | null = null;

      // Basic server check
      try {
        const res = await fetch(`${pythonServerUrl}/snapshot`, { method: 'GET' });
        server_ok = res.ok;
        if (res.ok) {
          snapshot_ok = true;
          const data: any = await res.json().catch(() => ({}));
          live_connected = !!(data && data.ok);
        }
      } catch (e: any) {
        logger.error('Health check error', { error: e.message });
      }

      const mode: HealthResponse['mode'] = server_ok && snapshot_ok ? 'full' : 'explain_only';

      const resp: HealthResponse = {
        server_ok,
        snapshot_ok,
        live_connected,
        mode,
      };

      response.json(resp);
    } catch (error: any) {
      logger.error('health error', { error: error.message });
      response.status(500).json({ error: 'internal_error', message: error.message });
    }
  },
);

