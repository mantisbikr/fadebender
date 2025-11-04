/**
 * SuggestionEngine - Generates suggestions based on FSM state
 *
 * Takes current FSM state and produces ranked suggestions for what the user can type next.
 * Pure logic module with zero external dependencies (except FSM).
 *
 * Examples:
 *   State: { action: "set" }
 *   Input: "tra"
 *   Suggestions: ["track", "return", "master"] (filtered to "track")
 *
 *   State: { action: "set", targetType: "track", targetId: "1" }
 *   Input: "v"
 *   Suggestions: ["volume", "pan", "mute", "solo", "cue", "send"] (filtered to "volume")
 */

/**
 * @typedef {Object} Suggestion
 * @property {string} value - The suggested value
 * @property {string} display - Display text (may include description)
 * @property {string} type - Type of suggestion: 'action', 'target_type', 'target_id', 'param', 'value'
 * @property {number} score - Relevance score (higher = more relevant)
 * @property {string} [description] - Optional description
 */

export class SuggestionEngine {
  /**
   * @param {import('./MixerFSM.js').MixerFSM} fsmEngine - FSM instance
   */
  constructor(fsmEngine) {
    this.fsm = fsmEngine;

    // Descriptions for better UX
    this.descriptions = {
      // Actions
      'set': 'Set parameter to absolute value',
      'increase': 'Increase parameter by amount',
      'decrease': 'Decrease parameter by amount',
      'toggle': 'Toggle parameter on/off',

      // Target types
      'track': 'Audio track (1-999)',
      'return': 'Return track (A-L)',
      'master': 'Master track',

      // Mixer params
      'volume': 'Track volume (-70 to +6 dB)',
      'pan': 'Stereo pan (-100 to +100)',
      'mute': 'Mute on/off',
      'solo': 'Solo on/off',
      'cue': 'Cue/Monitor on/off',
      'send': 'Send level to return track',

      // Values
      'on': 'Enable',
      'off': 'Disable'
    };
  }

  /**
   * Get suggestions for current state and partial input
   * @param {Object} currentState - Current FSM state
   * @param {string} partialToken - Partial token user is typing (e.g., "tra")
   * @param {Object} context - Additional context (e.g., available tracks/returns)
   * @returns {Suggestion[]} - Array of suggestions
   */
  getSuggestions(currentState, partialToken = '', context = {}) {
    // Get valid next tokens from FSM
    const nextTokens = this.fsm.getNextTokens(currentState, context);

    // Convert to suggestion objects
    let suggestions = nextTokens.map(token => ({
      value: token.value,
      display: token.value,
      type: token.type,
      score: 1.0,
      description: this.descriptions[token.value] || ''
    }));

    // Filter by prefix if partial token provided
    if (partialToken && partialToken.length > 0) {
      suggestions = this.filterByPrefix(suggestions, partialToken);
    }

    // Rank by relevance
    suggestions = this.rankSuggestions(suggestions, {
      ...context,
      partialToken,
      currentState
    });

    return suggestions;
  }

  /**
   * Filter suggestions by prefix match
   * @param {Suggestion[]} suggestions - Suggestions to filter
   * @param {string} prefix - Prefix to match
   * @returns {Suggestion[]} - Filtered suggestions
   */
  filterByPrefix(suggestions, prefix) {
    const lowerPrefix = prefix.toLowerCase();

    return suggestions.filter(suggestion => {
      const lowerValue = suggestion.value.toLowerCase();

      // Exact prefix match
      if (lowerValue.startsWith(lowerPrefix)) {
        return true;
      }

      // Fuzzy match (contains prefix)
      if (lowerValue.includes(lowerPrefix)) {
        return true;
      }

      return false;
    });
  }

  /**
   * Rank suggestions by relevance
   * @param {Suggestion[]} suggestions - Suggestions to rank
   * @param {Object} context - Context for ranking
   * @returns {Suggestion[]} - Sorted suggestions (highest score first)
   */
  rankSuggestions(suggestions, context = {}) {
    const { partialToken = '', currentState = {} } = context;

    // Assign scores based on multiple factors
    suggestions.forEach(suggestion => {
      let score = 1.0;

      // Factor 1: Prefix match quality
      if (partialToken.length > 0) {
        const lowerValue = suggestion.value.toLowerCase();
        const lowerPrefix = partialToken.toLowerCase();

        if (lowerValue.startsWith(lowerPrefix)) {
          // Exact prefix match → higher score
          score += 2.0;

          // Boost score based on how much of the word is typed
          const matchRatio = partialToken.length / suggestion.value.length;
          score += matchRatio * 1.0;
        } else if (lowerValue.includes(lowerPrefix)) {
          // Contains prefix but doesn't start with it → lower score
          score += 0.5;
        }
      }

      // Factor 2: Common actions get priority
      if (suggestion.type === 'action') {
        const commonActions = ['set', 'increase', 'decrease', 'toggle'];
        if (commonActions.includes(suggestion.value)) {
          score += 0.5;
        }
      }

      // Factor 3: Most commonly used params get priority
      if (suggestion.type === 'param') {
        const commonParams = ['volume', 'pan', 'mute'];
        if (commonParams.includes(suggestion.value)) {
          score += 0.3;
        }
      }

      // Factor 4: Shorter suggestions (easier to type)
      if (suggestion.value.length <= 4) {
        score += 0.2;
      }

      suggestion.score = score;
    });

    // Sort by score (highest first)
    return suggestions.sort((a, b) => b.score - a.score);
  }

  /**
   * Get top N suggestions
   * @param {Object} currentState - Current FSM state
   * @param {string} partialToken - Partial token
   * @param {number} limit - Max number of suggestions
   * @param {Object} context - Additional context
   * @returns {Suggestion[]} - Top N suggestions
   */
  getTopSuggestions(currentState, partialToken = '', limit = 5, context = {}) {
    const suggestions = this.getSuggestions(currentState, partialToken, context);
    return suggestions.slice(0, limit);
  }

  /**
   * Get ghost text (single best suggestion for inline display)
   * @param {Object} currentState - Current FSM state
   * @param {string} partialToken - Partial token
   * @param {Object} context - Additional context
   * @returns {string} - Ghost text to display (just the completion part)
   */
  getGhostText(currentState, partialToken = '', context = {}) {
    const suggestions = this.getSuggestions(currentState, partialToken, context);

    if (suggestions.length === 0) {
      return '';
    }

    // Return the top suggestion
    const topSuggestion = suggestions[0];

    // Only show ghost text if it's a strong match (score > 2.0)
    if (topSuggestion.score < 2.0) {
      return '';
    }

    // Return only the remaining part of the word (not the prefix)
    if (partialToken.length > 0 && topSuggestion.value.toLowerCase().startsWith(partialToken.toLowerCase())) {
      return topSuggestion.value.slice(partialToken.length);
    }

    return topSuggestion.value;
  }
}

export default SuggestionEngine;
