/**
 * TokenParser - Input Tokenization and Shortcut Expansion
 *
 * Parses user input into tokens and expands shortcuts for faster typing.
 * Pure logic module with zero dependencies - fully testable.
 *
 * Examples:
 *   "set t1 vol -20"  → ["set", "track", "1", "volume", "-20"]
 *   "inc ra pan 10"   → ["increase", "return", "A", "pan", "10"]
 *   "tog t2 m"        → ["toggle", "track", "2", "mute"]
 */

/**
 * @typedef {Object} Token
 * @property {string} original - Original token text
 * @property {string} expanded - Expanded token text
 * @property {number} position - Token position in input (0-indexed)
 */

export class TokenParser {
  constructor() {
    // Shortcut mappings for actions (no ambiguous single letters)
    this.actionShortcuts = {
      'set': 'set',
      'inc': 'increase',
      'increase': 'increase',
      'dec': 'decrease',
      'decrease': 'decrease',
      'tog': 'toggle',
      'toggle': 'toggle'
    };

    // Shortcut mappings for target types (no ambiguous single letters)
    this.targetShortcuts = {
      'trk': 'track',
      'track': 'track',
      'ret': 'return',
      'return': 'return',
      'mst': 'master',
      'master': 'master'
    };

    // Shortcut mappings for parameters (unambiguous single letters OK)
    this.paramShortcuts = {
      'v': 'volume',
      'vol': 'volume',
      'volume': 'volume',
      'p': 'pan',
      'pan': 'pan',
      'mute': 'mute',
      'solo': 'solo',
      'c': 'cue',
      'cue': 'cue',
      'send': 'send'
    };

    // Combined shortcuts for "t1" → ["track", "1"], "ra" → ["return", "A"]
    this.combinedShortcuts = {
      // Track shortcuts: t1, t2, ..., t99
      pattern: /^([trmsd])(\d+|[a-l])$/i,
      expand: (match) => {
        const prefix = match[1].toLowerCase();
        const suffix = match[2];

        // Determine target type from prefix
        let targetType;
        if (prefix === 't') targetType = 'track';
        else if (prefix === 'r') targetType = 'return';
        else if (prefix === 'm' || prefix === 's' || prefix === 'd') return null; // Ambiguous, don't expand

        // Determine ID from suffix
        if (targetType === 'track') {
          // t1 → ["track", "1"]
          const trackNum = parseInt(suffix, 10);
          if (!isNaN(trackNum) && trackNum >= 1 && trackNum <= 999) {
            return [targetType, suffix];
          }
        } else if (targetType === 'return') {
          // ra → ["return", "A"], r1 → ["return", "1"]
          if (/^[a-l]$/i.test(suffix)) {
            return [targetType, suffix.toUpperCase()];
          } else {
            const returnNum = parseInt(suffix, 10);
            if (!isNaN(returnNum) && returnNum >= 0 && returnNum <= 11) {
              return [targetType, String.fromCharCode(65 + returnNum)];
            }
          }
        }

        return null;
      }
    };

    // Stop words to skip during parsing (optional)
    this.stopWords = new Set(['to', 'by', 'at', 'the', 'a', 'an']);
  }

  /**
   * Parse input into tokens with shortcut expansion
   * @param {string} input - Raw user input
   * @returns {Token[]} - Array of parsed tokens
   */
  parse(input) {
    if (!input || typeof input !== 'string') {
      return [];
    }

    // Split on whitespace
    const rawTokens = input.trim().split(/\s+/).filter(token => token.length > 0);

    const tokens = [];
    let position = 0;

    for (let i = 0; i < rawTokens.length; i++) {
      const rawToken = rawTokens[i];
      const lowerToken = rawToken.toLowerCase();

      // Skip stop words
      if (this.stopWords.has(lowerToken)) {
        continue;
      }

      // Check for combined shortcuts (t1, ra, etc.)
      const combinedMatch = this.combinedShortcuts.pattern.exec(rawToken);
      if (combinedMatch) {
        const expanded = this.combinedShortcuts.expand(combinedMatch);
        if (expanded) {
          // Add multiple tokens from combined shortcut
          expanded.forEach((expandedToken, idx) => {
            tokens.push({
              original: idx === 0 ? rawToken : '',
              expanded: expandedToken,
              position: position + idx
            });
          });
          position += expanded.length;
          continue;
        }
      }

      // Try expanding as single token
      const expandedToken = this.expandShortcut(rawToken);
      tokens.push({
        original: rawToken,
        expanded: expandedToken,
        position: position
      });
      position++;
    }

    return tokens;
  }

  /**
   * Expand a single token using shortcut maps
   * @param {string} token - Token to expand
   * @returns {string} - Expanded token (or original if no match)
   */
  expandShortcut(token) {
    const lowerToken = token.toLowerCase();

    // Try action shortcuts
    if (this.actionShortcuts[lowerToken]) {
      return this.actionShortcuts[lowerToken];
    }

    // Try target shortcuts
    if (this.targetShortcuts[lowerToken]) {
      return this.targetShortcuts[lowerToken];
    }

    // Try parameter shortcuts
    if (this.paramShortcuts[lowerToken]) {
      return this.paramShortcuts[lowerToken];
    }

    // No shortcut found, return original (lowercase for consistency)
    return lowerToken;
  }

  /**
   * Parse input and return only expanded tokens (for FSM processing)
   * @param {string} input - Raw user input
   * @returns {string[]} - Array of expanded token strings
   */
  parseToStrings(input) {
    return this.parse(input).map(token => token.expanded);
  }

  /**
   * Detect token type based on context (for suggestion filtering)
   * @param {string} token - Token to analyze
   * @param {Object} context - Context object with previous tokens
   * @returns {string} - Token type: 'action', 'target_type', 'target_id', 'param', 'value', 'unknown'
   */
  detectType(token, context = {}) {
    const lowerToken = token.toLowerCase();
    const { previousTokens = [] } = context;

    // Check if it's an action
    if (this.actionShortcuts[lowerToken]) {
      return 'action';
    }

    // Check if it's a target type
    if (this.targetShortcuts[lowerToken]) {
      return 'target_type';
    }

    // Check if it's a parameter
    if (this.paramShortcuts[lowerToken]) {
      return 'param';
    }

    // Check if it's a target ID (number for track, letter for return)
    if (previousTokens.length > 0) {
      const lastToken = previousTokens[previousTokens.length - 1];
      if (lastToken === 'track' && /^\d+$/.test(token)) {
        return 'target_id';
      }
      if (lastToken === 'return' && /^[a-l]$/i.test(token)) {
        return 'target_id';
      }
    }

    // Check if it's a numeric value
    if (/^-?\d+(\.\d+)?(%|db|dB)?$/.test(token)) {
      return 'value';
    }

    // Check if it's a boolean value (on/off)
    if (['on', 'off', 'true', 'false', '1', '0'].includes(lowerToken)) {
      return 'value';
    }

    return 'unknown';
  }

  /**
   * Add custom shortcut mapping
   * @param {string} category - Category: 'action', 'target', 'param'
   * @param {string} shortcut - Shortcut key
   * @param {string} expansion - Full form
   */
  addShortcut(category, shortcut, expansion) {
    const lowerShortcut = shortcut.toLowerCase();
    const lowerExpansion = expansion.toLowerCase();

    if (category === 'action') {
      this.actionShortcuts[lowerShortcut] = lowerExpansion;
    } else if (category === 'target') {
      this.targetShortcuts[lowerShortcut] = lowerExpansion;
    } else if (category === 'param') {
      this.paramShortcuts[lowerShortcut] = lowerExpansion;
    }
  }

  /**
   * Get all shortcuts for a category (for suggestion dropdown)
   * @param {string} category - Category: 'action', 'target', 'param'
   * @returns {Object} - Shortcut map
   */
  getShortcuts(category) {
    if (category === 'action') {
      return { ...this.actionShortcuts };
    } else if (category === 'target') {
      return { ...this.targetShortcuts };
    } else if (category === 'param') {
      return { ...this.paramShortcuts };
    }
    return {};
  }
}

export default TokenParser;
