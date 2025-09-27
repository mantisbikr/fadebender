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

  async chat(text, confirm = true) {
    const response = await fetch(`${API_CONFIG.SERVER_BASE_URL}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text, confirm })
    });

    if (!response.ok) {
      const detail = await response.text().catch(() => '');
      throw new Error(`Chat failed: ${response.status} ${response.statusText} ${detail}`.trim());
    }

    return response.json();
  }

  async getHelp(query) {
    const response = await fetch(`${API_CONFIG.NLP_BASE_URL}/howto`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query })
    });

    if (!response.ok) {
      throw new Error(`Help request failed: ${response.statusText}`);
    }

    return response.json();
  }

  async checkHealth() {
    const response = await fetch(`${API_CONFIG.NLP_BASE_URL}/health`);
    return response.json();
  }
}

export const apiService = new ApiService();
