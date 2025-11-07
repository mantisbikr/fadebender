/**
 * API Service Layer
 * Handles all communication with backend services
 */

const API_CONFIG = {
  NLP_BASE_URL: 'http://127.0.0.1:8000',
  CONTROLLER_BASE_URL: 'http://127.0.0.1:8721',
  SERVER_BASE_URL: 'http://127.0.0.1:8722'
};

class ApiService {
  getEventsURL() {
    return `${API_CONFIG.SERVER_BASE_URL}/events`;
  }
  async queryIntent(intent) {
    const response = await fetch(`${API_CONFIG.SERVER_BASE_URL}/intent/query`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(intent)
    });
    const contentType = response.headers.get('content-type') || '';
    const body = contentType.includes('application/json') ? await response.json() : await response.text();
    if (!response.ok) {
      const detail = (body && body.detail) ? body.detail : (typeof body === 'string' ? body : `${response.status} ${response.statusText}`);
      throw new Error(detail || 'Intent query failed');
    }
    return body;
  }
  async getMasterStatus() {
    const response = await fetch(`${API_CONFIG.SERVER_BASE_URL}/master/status`);
    if (!response.ok) throw new Error(`Master status failed: ${response.statusText}`);
    return response.json();
  }
  async setMasterMixer(field, value) {
    const response = await fetch(`${API_CONFIG.SERVER_BASE_URL}/op/master/mixer`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ field, value })
    });
    if (!response.ok) throw new Error(`Set master mixer failed: ${response.statusText}`);
    return response.json();
  }

  async getReturnRouting(index) {
    const response = await fetch(`${API_CONFIG.SERVER_BASE_URL}/return/routing?index=${index}`);
    if (!response.ok) throw new Error(`Return routing failed: ${response.statusText}`);
    return response.json();
  }
  async getTrackRouting(index) {
    const response = await fetch(`${API_CONFIG.SERVER_BASE_URL}/track/routing?index=${index}`);
    if (!response.ok) throw new Error(`Track routing failed: ${response.statusText}`);
    return response.json();
  }
  async setTrackRouting(track_index, payload) {
    const response = await fetch(`${API_CONFIG.SERVER_BASE_URL}/track/routing`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ track_index, ...payload })
    });
    if (!response.ok) throw new Error(`Set track routing failed: ${response.statusText}`);
    return response.json();
  }
  async setReturnRouting(return_index, payload) {
    const response = await fetch(`${API_CONFIG.SERVER_BASE_URL}/return/routing`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ return_index, ...payload })
    });
    if (!response.ok) throw new Error(`Set return routing failed: ${response.statusText}`);
    return response.json();
  }
  async getAppConfig() {
    const response = await fetch(`${API_CONFIG.SERVER_BASE_URL}/config`, {
      cache: 'no-cache',  // Force fresh config on every load
      headers: {
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        'Pragma': 'no-cache'
      }
    });
    if (!response.ok) throw new Error(`Config fetch failed: ${response.statusText}`);
    return response.json();
  }

  async getSnapshot() {
    const response = await fetch(`${API_CONFIG.SERVER_BASE_URL}/snapshot`);
    if (!response.ok) throw new Error(`Snapshot failed: ${response.statusText}`);
    return response.json();
  }
  async updateAppConfig(payload) {
    const response = await fetch(`${API_CONFIG.SERVER_BASE_URL}/config/update`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload || {})
    });
    if (!response.ok) throw new Error(`Config update failed: ${response.statusText}`);
    return response.json();
  }
  async reloadAppConfig() {
    const response = await fetch(`${API_CONFIG.SERVER_BASE_URL}/config/reload`, {
      method: 'POST'
    });
    if (!response.ok) throw new Error(`Config reload failed: ${response.statusText}`);
    return response.json();
  }
  async parseIntent(text, model = undefined, strict = undefined) {
    const response = await fetch(`${API_CONFIG.SERVER_BASE_URL}/intent/parse`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text, model, strict })
    });

    if (!response.ok) {
      throw new Error(`Intent parse failed: ${response.status} ${response.statusText}`);
    }

    return response.json();
  }

  async executeCanonicalIntent(intent) {
    const response = await fetch(`${API_CONFIG.SERVER_BASE_URL}/intent/execute`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(intent)
    });
    const contentType = response.headers.get('content-type') || '';
    let body = null;
    try { body = contentType.includes('application/json') ? await response.json() : await response.text(); } catch {}
    if (!response.ok) {
      const detail = (body && body.detail) ? body.detail : (typeof body === 'string' ? body : `${response.status} ${response.statusText}`);
      throw new Error(detail || 'Intent execute failed');
    }
    return body;
  }

  async readIntent(body) {
    const response = await fetch(`${API_CONFIG.SERVER_BASE_URL}/intent/read`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    });
    if (!response.ok) throw new Error(`Intent read failed: ${response.status} ${response.statusText}`);
    return response.json();
  }
  async parseCommand(text, context = null, model = 'gemini-flash') {
    const response = await fetch(`${API_CONFIG.NLP_BASE_URL}/parse`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text, model, context })
    });

    if (!response.ok) {
      throw new Error(`NLP parsing failed: ${response.statusText}`);
    }

    return response.json();
  }

  async executeIntent(intent) {
    const response = await fetch(`${API_CONFIG.CONTROLLER_BASE_URL}/execute-intent`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(intent)
    });

    if (!response.ok) {
      throw new Error(`Intent execution failed: ${response.statusText}`);
    }

    return response.json();
  }

  async chat(text, confirm = true, model = undefined) {
    const response = await fetch(`${API_CONFIG.SERVER_BASE_URL}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text, confirm, model })
    });

    if (!response.ok) {
      const detail = await response.text().catch(() => '');
      throw new Error(`Chat failed: ${response.status} ${response.statusText} ${detail}`.trim());
    }

    return response.json();
  }

  async getHelp(query, context = null) {
    // Route help to server which uses local knowledge base
    const response = await fetch(`${API_CONFIG.SERVER_BASE_URL}/help`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query, context })
    });

    if (!response.ok) {
      throw new Error(`Help request failed: ${response.statusText}`);
    }

    return response.json();
  }

  async getProjectOutline() {
    const response = await fetch(`${API_CONFIG.SERVER_BASE_URL}/project/outline`);
    if (!response.ok) throw new Error(`Project outline failed: ${response.statusText}`);
    return response.json();
  }

  // Transport API
  async getTransport() {
    const response = await fetch(`${API_CONFIG.SERVER_BASE_URL}/transport`);
    if (!response.ok) throw new Error(`Transport get failed: ${response.statusText}`);
    return response.json();
  }
  async setTransport(action, value = undefined) {
    const response = await fetch(`${API_CONFIG.SERVER_BASE_URL}/transport`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action, value })
    });
    if (!response.ok) throw new Error(`Transport set failed: ${response.statusText}`);
    return response.json();
  }

  async getTrackStatus(index) {
    const response = await fetch(`${API_CONFIG.SERVER_BASE_URL}/track/status?index=${index}`);
    if (!response.ok) throw new Error(`Track status failed: ${response.statusText}`);
    return response.json();
  }
  async getTrackSends(index) {
    const response = await fetch(`${API_CONFIG.SERVER_BASE_URL}/track/sends?index=${index}`);
    if (!response.ok) throw new Error(`Track sends failed: ${response.statusText}`);
    return response.json();
  }
  async setSend(track_index, send_index, value) {
    const response = await fetch(`${API_CONFIG.SERVER_BASE_URL}/op/send`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ track_index, send_index, value })
    });
    if (!response.ok) throw new Error(`Send op failed: ${response.statusText}`);
    return response.json();
  }

  async selectTrack(index) {
    const response = await fetch(`${API_CONFIG.SERVER_BASE_URL}/op/select_track`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ track_index: index })
    });
    if (!response.ok) throw new Error(`Select track failed: ${response.statusText}`);
    return response.json();
  }

  async setMixer(track_index, field, value) {
    const response = await fetch(`${API_CONFIG.SERVER_BASE_URL}/op/mixer`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ track_index, field, value })
    });
    if (!response.ok) throw new Error(`Mixer op failed: ${response.statusText}`);
    return response.json();
  }

  // Return tracks API
  async getReturnTracks() {
    const response = await fetch(`${API_CONFIG.SERVER_BASE_URL}/returns`);
    if (!response.ok) throw new Error(`Return tracks failed: ${response.statusText}`);
    return response.json();
  }
  async getReturnDevices(index) {
    const response = await fetch(`${API_CONFIG.SERVER_BASE_URL}/return/devices?index=${index}`);
    if (!response.ok) throw new Error(`Return devices failed: ${response.statusText}`);
    return response.json();
  }

  // Track devices (Phase A - minimal)
  async getTrackDevices(index) {
    const response = await fetch(`${API_CONFIG.SERVER_BASE_URL}/track/devices?index=${index}`);
    if (!response.ok) throw new Error(`Track devices failed: ${response.statusText}`);
    return response.json();
  }
  async getTrackDeviceParams(index, device) {
    const response = await fetch(`${API_CONFIG.SERVER_BASE_URL}/track/device/params?index=${index}&device=${device}`);
    if (!response.ok) throw new Error(`Track device params failed: ${response.statusText}`);
    return response.json();
  }
  async setTrackDeviceParam(track_index, device_index, param_index, value) {
    const response = await fetch(`${API_CONFIG.SERVER_BASE_URL}/op/track/device/param`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ track_index, device_index, param_index, value })
    });
    if (!response.ok) throw new Error(`Set track device param failed: ${response.statusText}`);
    return response.json();
  }

  // Master devices (Phase A - minimal)
  async getMasterDevices() {
    const response = await fetch(`${API_CONFIG.SERVER_BASE_URL}/master/devices`);
    if (!response.ok) throw new Error(`Master devices failed: ${response.statusText}`);
    return response.json();
  }
  async getMasterDeviceParams(device) {
    const response = await fetch(`${API_CONFIG.SERVER_BASE_URL}/master/device/params?device=${device}`);
    if (!response.ok) throw new Error(`Master device params failed: ${response.statusText}`);
    return response.json();
  }
  async setMasterDeviceParam(device_index, param_index, value) {
    const response = await fetch(`${API_CONFIG.SERVER_BASE_URL}/op/master/device/param`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ device_index, param_index, value })
    });
    if (!response.ok) throw new Error(`Set master device param failed: ${response.statusText}`);
    return response.json();
  }
  async getReturnSends(index) {
    const response = await fetch(`${API_CONFIG.SERVER_BASE_URL}/return/sends?index=${index}`);
    if (!response.ok) throw new Error(`Return sends failed: ${response.statusText}`);
    return response.json();
  }
  async getReturnDeviceParams(index, device) {
    const response = await fetch(`${API_CONFIG.SERVER_BASE_URL}/return/device/params?index=${index}&device=${device}`);
    if (!response.ok) throw new Error(`Return device params failed: ${response.statusText}`);
    return response.json();
  }
  async getReturnDeviceCapabilities(index, device) {
    const response = await fetch(`${API_CONFIG.SERVER_BASE_URL}/return/device/capabilities?index=${index}&device=${device}`);
    if (!response.ok) throw new Error(`Return device capabilities failed: ${response.statusText}`);
    return response.json();
  }
  async getTrackMixerCapabilities(index) {
    const response = await fetch(`${API_CONFIG.SERVER_BASE_URL}/track/mixer/capabilities?index=${index}`);
    if (!response.ok) throw new Error(`Track mixer capabilities failed: ${response.statusText}`);
    return response.json();
  }
  async getReturnMixerCapabilities(index) {
    const response = await fetch(`${API_CONFIG.SERVER_BASE_URL}/return/mixer/capabilities?index=${index}`);
    if (!response.ok) throw new Error(`Return mixer capabilities failed: ${response.statusText}`);
    return response.json();
  }
  async getMasterMixerCapabilities() {
    const response = await fetch(`${API_CONFIG.SERVER_BASE_URL}/master/mixer/capabilities`);
    if (!response.ok) throw new Error(`Master mixer capabilities failed: ${response.statusText}`);
    return response.json();
  }
  async getReturnDeviceMap(index, device) {
    const response = await fetch(`${API_CONFIG.SERVER_BASE_URL}/return/device/map?index=${index}&device=${device}`);
    if (!response.ok) throw new Error(`Return device map failed: ${response.statusText}`);
    return response.json();
  }
  async getReturnDeviceMapSummary(index, device) {
    const response = await fetch(`${API_CONFIG.SERVER_BASE_URL}/return/device/map_summary?index=${index}&device=${device}`);
    if (!response.ok) throw new Error(`Return device map summary failed: ${response.statusText}`);
    return response.json();
  }
  async bypassReturnDevice(return_index, device_index, on) {
    const response = await fetch(`${API_CONFIG.SERVER_BASE_URL}/return/device/bypass`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ return_index, device_index, on })
    });
    if (!response.ok) throw new Error(`Bypass device failed: ${response.statusText}`);
    return response.json();
  }
  async saveReturnDeviceUserPreset(return_index, device_index, preset_name, user_id = null) {
    const response = await fetch(`${API_CONFIG.SERVER_BASE_URL}/return/device/save_as_user_preset`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ return_index, device_index, preset_name, user_id })
    });
    if (!response.ok) throw new Error(`Save user preset failed: ${response.statusText}`);
    return response.json();
  }
  async setReturnDeviceParam(return_index, device_index, param_index, value) {
    const response = await fetch(`${API_CONFIG.SERVER_BASE_URL}/op/return/device/param`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ return_index, device_index, param_index, value })
    });
    if (!response.ok) throw new Error(`Set return param failed: ${response.statusText}`);
    return response.json();
  }
  async setReturnSend(return_index, send_index, value) {
    const response = await fetch(`${API_CONFIG.SERVER_BASE_URL}/op/return/send`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ return_index, send_index, value })
    });
    if (!response.ok) throw new Error(`Set return send failed: ${response.statusText}`);
    return response.json();
  }
  async setReturnMixer(return_index, field, value) {
    const response = await fetch(`${API_CONFIG.SERVER_BASE_URL}/op/return/mixer`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ return_index, field, value })
    });
    if (!response.ok) throw new Error(`Set return mixer failed: ${response.statusText}`);
    return response.json();
  }

  async learnReturnDevice(return_index, device_index, resolution = 21, sleep_ms = 25) {
    const response = await fetch(`${API_CONFIG.SERVER_BASE_URL}/return/device/learn`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ return_index, device_index, resolution, sleep_ms })
    });
    if (!response.ok) throw new Error(`Return device learn failed: ${response.statusText}`);
    return response.json();
  }
  async learnReturnDeviceStart(return_index, device_index, resolution = 41, sleep_ms = 20) {
    const response = await fetch(`${API_CONFIG.SERVER_BASE_URL}/return/device/learn_start`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ return_index, device_index, resolution, sleep_ms })
    });
    if (!response.ok) throw new Error(`Return device learn start failed: ${response.statusText}`);
    return response.json();
  }
  async learnReturnDeviceStatus(job_id) {
    const response = await fetch(`${API_CONFIG.SERVER_BASE_URL}/return/device/learn_status?id=${encodeURIComponent(job_id)}`);
    if (!response.ok) throw new Error(`Return device learn status failed: ${response.statusText}`);
    return response.json();
  }
  async deleteReturnDeviceMap(index, device) {
    const response = await fetch(`${API_CONFIG.SERVER_BASE_URL}/return/device/map_delete`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ return_index: index, device_index: device })
    });
    if (!response.ok) throw new Error(`Return device map delete failed: ${response.statusText}`);
    return response.json();
  }

  async undoLast() {
    const response = await fetch(`${API_CONFIG.SERVER_BASE_URL}/op/undo_last`, {
      method: 'POST'
    });
    if (!response.ok) throw new Error(`Undo failed: ${response.statusText}`);
    return response.json();
  }

  async redoLast() {
    const response = await fetch(`${API_CONFIG.SERVER_BASE_URL}/op/redo_last`, {
      method: 'POST'
    });
    if (!response.ok) throw new Error(`Redo failed: ${response.statusText}`);
    return response.json();
  }

  async getHistoryState() {
    const response = await fetch(`${API_CONFIG.SERVER_BASE_URL}/op/history_state`);
    if (!response.ok) throw new Error(`History state failed: ${response.statusText}`);
    return response.json();
  }

  async checkHealth() {
    const response = await fetch(`${API_CONFIG.SERVER_BASE_URL}/health`);
    return response.json();
  }

  async checkControllerHealth() {
    const response = await fetch(`${API_CONFIG.SERVER_BASE_URL}/controller/health`);
    return response.json();
  }
}

export const apiService = new ApiService();
