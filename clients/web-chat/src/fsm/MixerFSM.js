/**
 * MixerFSM - Finite State Machine for Mixer Commands
 *
 * Handles command construction for mixer operations (set/increase/decrease).
 * Pure logic module with zero dependencies - fully testable.
 *
 * State Flow:
 *   START → ACTION → TARGET_TYPE → TARGET_ID → PARAM → [VALUE] → COMPLETE
 *
 * Examples:
 *   - "set track 1 volume to -20"
 *   - "increase return A pan by 10"
 *   - "toggle track 2 mute"
 */

/**
 * @typedef {Object} FSMState
 * @property {string} phase - Current phase: 'action', 'target_type', 'target_id', 'param', 'value', 'complete'
 * @property {string|null} action - Action: 'set', 'increase', 'decrease', 'toggle'
 * @property {string|null} targetType - Target type: 'track', 'return', 'master'
 * @property {number|string|null} targetId - Track number (1-999) or return letter (A-Z)
 * @property {string|null} param - Parameter name: 'volume', 'pan', 'mute', 'solo', 'send'
 * @property {string|null} sendRef - For sends: 'A', 'B', 'C', etc.
 * @property {number|string|null} value - Value (number, relative %, or 'on'/'off' for toggles)
 * @property {string|null} error - Error message if transition failed
 */

/**
 * @typedef {Object} Token
 * @property {string} value - Token value
 * @property {string} type - Token type: 'action', 'target_type', 'target_id', 'param', 'value', 'keyword'
 * @property {string} display - Display text for suggestion dropdown
 * @property {string|null} description - Tooltip/help text
 */

export class MixerFSM {
  constructor() {
    // Valid actions
    this.actions = ['set', 'increase', 'decrease', 'toggle'];

    // Valid target types
    this.targetTypes = ['track', 'return', 'master'];

    // Valid mixer parameters
    this.mixerParams = ['volume', 'pan', 'mute', 'solo', 'cue', 'send'];

    // Toggle-only parameters (don't require values)
    this.toggleParams = new Set(['mute', 'solo', 'cue']);

    // Send letters (A-L for 12 returns)
    this.sendLetters = 'ABCDEFGHIJKL'.split('');
  }

  /**
   * Create initial empty state
   * @returns {FSMState}
   */
  createInitialState() {
    return {
      phase: 'action',
      action: null,
      targetType: null,
      targetId: null,
      param: null,
      sendRef: null,
      value: null,
      error: null
    };
  }

  /**
   * Process a single token and return new state
   * @param {FSMState} currentState - Current FSM state
   * @param {string} token - Token to process (lowercase)
   * @returns {FSMState} - New state after processing token
   */
  processToken(currentState, token) {
    const newState = { ...currentState, error: null };
    const tokenLower = token.toLowerCase().trim();

    // Skip empty tokens
    if (!tokenLower) return newState;

    switch (currentState.phase) {
      case 'action':
        return this._processAction(newState, tokenLower);

      case 'target_type':
        return this._processTargetType(newState, tokenLower);

      case 'target_id':
        return this._processTargetId(newState, tokenLower);

      case 'param':
        return this._processParam(newState, tokenLower);

      case 'send_ref':
        return this._processSendRef(newState, tokenLower);

      case 'value':
        return this._processValue(newState, tokenLower);

      case 'complete':
        // Already complete, ignore additional tokens
        return newState;

      default:
        newState.error = `Unknown phase: ${currentState.phase}`;
        return newState;
    }
  }

  /**
   * Process action token (set/increase/decrease/toggle)
   */
  _processAction(state, token) {
    if (this.actions.includes(token)) {
      state.action = token;
      state.phase = 'target_type';
    } else {
      state.error = `Invalid action: "${token}". Expected: ${this.actions.join(', ')}`;
    }
    return state;
  }

  /**
   * Process target type token (track/return/master)
   */
  _processTargetType(state, token) {
    if (this.targetTypes.includes(token)) {
      state.targetType = token;
      state.phase = token === 'master' ? 'param' : 'target_id';
    } else {
      state.error = `Invalid target type: "${token}". Expected: ${this.targetTypes.join(', ')}`;
    }
    return state;
  }

  /**
   * Process target ID token (track number or return letter)
   */
  _processTargetId(state, token) {
    if (state.targetType === 'track') {
      // Expect track number (1-999)
      const trackNum = parseInt(token, 10);
      if (!isNaN(trackNum) && trackNum >= 1 && trackNum <= 999) {
        state.targetId = trackNum;
        state.phase = 'param';
      } else {
        state.error = `Invalid track number: "${token}". Expected: 1-999`;
      }
    } else if (state.targetType === 'return') {
      // Expect return letter (A-L) or number (0-11)
      const upperToken = token.toUpperCase();
      if (this.sendLetters.includes(upperToken)) {
        state.targetId = upperToken;
        state.phase = 'param';
      } else {
        const returnNum = parseInt(token, 10);
        if (!isNaN(returnNum) && returnNum >= 0 && returnNum <= 11) {
          state.targetId = this.sendLetters[returnNum];
          state.phase = 'param';
        } else {
          state.error = `Invalid return ID: "${token}". Expected: A-L or 0-11`;
        }
      }
    }
    return state;
  }

  /**
   * Process parameter token (volume/pan/mute/solo/send)
   */
  _processParam(state, token) {
    if (this.mixerParams.includes(token)) {
      state.param = token;

      // If it's a send, next token should be send letter (A, B, C, etc.)
      if (token === 'send') {
        state.phase = 'send_ref';
      }
      // Toggle params (mute/solo/cue) can complete immediately for 'toggle' action
      else if (state.action === 'toggle' && this.toggleParams.has(token)) {
        state.phase = 'complete';
      }
      // Otherwise, expect a value
      else {
        state.phase = 'value';
      }
    } else {
      state.error = `Invalid parameter: "${token}". Expected: ${this.mixerParams.join(', ')}`;
    }
    return state;
  }

  /**
   * Process send reference (A, B, C, etc.)
   */
  _processSendRef(state, token) {
    const upperToken = token.toUpperCase();
    if (this.sendLetters.includes(upperToken)) {
      state.sendRef = upperToken;
      state.phase = 'value';
    } else {
      state.error = `Invalid send reference: "${token}". Expected: A-L`;
    }
    return state;
  }

  /**
   * Process value token (number, percentage, or on/off)
   */
  _processValue(state, token) {
    // Handle toggle values (on/off)
    if (this.toggleParams.has(state.param)) {
      if (['on', 'true', '1'].includes(token)) {
        state.value = true;
        state.phase = 'complete';
      } else if (['off', 'false', '0'].includes(token)) {
        state.value = false;
        state.phase = 'complete';
      } else {
        state.error = `Invalid toggle value: "${token}". Expected: on/off`;
      }
      return state;
    }

    // Handle numeric values
    const numMatch = token.match(/^(-?\d+(?:\.\d+)?)\s*(%|db|dB)?$/);
    if (numMatch) {
      const num = parseFloat(numMatch[1]);
      const unit = numMatch[2] || null;

      state.value = {
        raw: num,
        unit: unit,
        display: token
      };
      state.phase = 'complete';
    } else {
      state.error = `Invalid value: "${token}". Expected: number, percentage, or dB`;
    }
    return state;
  }

  /**
   * Get valid next tokens for current state
   * @param {FSMState} state - Current FSM state
   * @param {Object} context - Optional context (track count, return count, etc.)
   * @returns {Token[]} - Array of valid next tokens with metadata
   */
  getNextTokens(state, context = {}) {
    const tokens = [];

    switch (state.phase) {
      case 'action':
        return this.actions.map(action => ({
          value: action,
          type: 'action',
          display: action.charAt(0).toUpperCase() + action.slice(1),
          description: this._getActionDescription(action)
        }));

      case 'target_type':
        return this.targetTypes.map(type => ({
          value: type,
          type: 'target_type',
          display: type.charAt(0).toUpperCase() + type.slice(1),
          description: this._getTargetTypeDescription(type)
        }));

      case 'target_id':
        if (state.targetType === 'track') {
          // Suggest track numbers (1-999, or from context)
          const trackCount = context.trackCount || 8;
          for (let i = 1; i <= Math.min(trackCount, 12); i++) {
            tokens.push({
              value: i.toString(),
              type: 'target_id',
              display: `Track ${i}`,
              description: context.trackNames?.[i - 1] || `Track ${i}`
            });
          }
        } else if (state.targetType === 'return') {
          // Suggest return letters (A-L)
          const returnCount = context.returnCount || 4;
          for (let i = 0; i < Math.min(returnCount, this.sendLetters.length); i++) {
            const letter = this.sendLetters[i];
            tokens.push({
              value: letter,
              type: 'target_id',
              display: `Return ${letter}`,
              description: context.returnNames?.[i] || `Return ${letter}`
            });
          }
        }
        return tokens;

      case 'param':
        return this.mixerParams.map(param => ({
          value: param,
          type: 'param',
          display: param.charAt(0).toUpperCase() + param.slice(1),
          description: this._getParamDescription(param)
        }));

      case 'send_ref':
        // Suggest send letters for sends
        const sendCount = context.returnCount || 4;
        for (let i = 0; i < Math.min(sendCount, this.sendLetters.length); i++) {
          const letter = this.sendLetters[i];
          tokens.push({
            value: letter,
            type: 'send_ref',
            display: `Send ${letter}`,
            description: `Send to Return ${letter}`
          });
        }
        return tokens;

      case 'value':
        // Suggest common values based on parameter type
        return this._getValueSuggestions(state);

      case 'complete':
        return [];

      default:
        return [];
    }
  }

  /**
   * Get value suggestions based on parameter type
   */
  _getValueSuggestions(state) {
    const param = state.param;

    if (this.toggleParams.has(param)) {
      return [
        { value: 'on', type: 'value', display: 'On', description: 'Enable' },
        { value: 'off', type: 'value', display: 'Off', description: 'Disable' }
      ];
    }

    if (param === 'volume' || param === 'send') {
      return [
        { value: '0', type: 'value', display: '0 dB', description: 'Unity gain' },
        { value: '-6', type: 'value', display: '-6 dB', description: 'Half volume' },
        { value: '-12', type: 'value', display: '-12 dB', description: 'Quarter volume' },
        { value: '-inf', type: 'value', display: '-∞ dB', description: 'Muted' }
      ];
    }

    if (param === 'pan') {
      return [
        { value: '0', type: 'value', display: 'Center', description: 'Center pan' },
        { value: '-50', type: 'value', display: 'Left', description: 'Full left' },
        { value: '50', type: 'value', display: 'Right', description: 'Full right' }
      ];
    }

    return [];
  }

  /**
   * Check if state is complete (ready to execute)
   * @param {FSMState} state - FSM state
   * @returns {boolean}
   */
  isComplete(state) {
    return state.phase === 'complete' && !state.error;
  }

  /**
   * Convert FSM state to intent object (for execution)
   * @param {FSMState} state - Complete FSM state
   * @returns {Object|null} - Intent object or null if incomplete
   */
  toIntent(state) {
    if (!this.isComplete(state)) {
      return null;
    }

    const intent = {
      domain: state.targetType,
      action: state.action,
      field: state.param
    };

    // Add target identification
    if (state.targetType === 'track') {
      intent.track_index = state.targetId - 1; // Convert to 0-indexed
    } else if (state.targetType === 'return') {
      intent.return_ref = state.targetId;
    }

    // Add send reference if applicable
    if (state.param === 'send' && state.sendRef) {
      intent.send_ref = state.sendRef;
    }

    // Add value if present
    if (state.value !== null) {
      if (typeof state.value === 'object' && state.value.raw !== undefined) {
        intent.value = state.value.raw;
        intent.unit = state.value.unit;
      } else {
        intent.value = state.value;
      }
    }

    return intent;
  }

  // Helper: Get action descriptions
  _getActionDescription(action) {
    const descriptions = {
      set: 'Set parameter to absolute value',
      increase: 'Increase parameter by relative amount',
      decrease: 'Decrease parameter by relative amount',
      toggle: 'Toggle parameter on/off'
    };
    return descriptions[action] || '';
  }

  // Helper: Get target type descriptions
  _getTargetTypeDescription(type) {
    const descriptions = {
      track: 'Audio/MIDI track',
      return: 'Return track (effects bus)',
      master: 'Master output channel'
    };
    return descriptions[type] || '';
  }

  // Helper: Get parameter descriptions
  _getParamDescription(param) {
    const descriptions = {
      volume: 'Track/channel volume level',
      pan: 'Stereo pan position (L/R)',
      mute: 'Mute audio output',
      solo: 'Solo this track (mute others)',
      cue: 'Monitor in headphones',
      send: 'Send to return track (effects bus)'
    };
    return descriptions[param] || '';
  }
}

export default MixerFSM;
