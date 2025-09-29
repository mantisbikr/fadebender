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

  async getHelp(query) {
    // Route help to server which uses local knowledge base
    const response = await fetch(`${API_CONFIG.SERVER_BASE_URL}/help`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query })
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
    const response = await fetch(`${API_CONFIG.NLP_BASE_URL}/health`);
    return response.json();
  }
}

export const apiService = new ApiService();
