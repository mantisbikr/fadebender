/**
 * GhostTextGenerator - Converts suggestions into ghost text for inline display
 *
 * Produces Fish shell-style ghost text that appears after the cursor.
 * Pure logic module with zero dependencies.
 *
 * Examples:
 *   Input: "set", Suggestion: "set"
 *   Ghost Text: "" (already complete)
 *
 *   Input: "s", Suggestion: "set"
 *   Ghost Text: "et" (completion part only)
 *
 *   Input: "set t", Suggestion: "track"
 *   Ghost Text: "rack" (completion for current word)
 */

export class GhostTextGenerator {
  constructor() {
    // Minimum score threshold for showing ghost text
    this.minScoreThreshold = 2.0;
  }

  /**
   * Get ghost text for current input
   * @param {string} currentInput - Full input string
   * @param {Array} suggestions - Array of suggestion objects with {value, score}
   * @returns {string} - Ghost text to display (completion part only)
   */
  getGhostText(currentInput, suggestions) {
    if (!suggestions || suggestions.length === 0) {
      return '';
    }

    // Get the top suggestion
    const topSuggestion = suggestions[0];

    // Only show ghost text if it's a strong match and has a score
    if (!topSuggestion || !topSuggestion.score || topSuggestion.score < this.minScoreThreshold) {
      return '';
    }

    // Handle null/empty input
    if (!currentInput) {
      return topSuggestion.value;
    }

    // Extract the partial token (last word being typed)
    const partialToken = this._getPartialToken(currentInput);

    // Return completion part only
    return this._getCompletion(partialToken, topSuggestion.value);
  }

  /**
   * Get completion text (what Tab would insert)
   * @param {string} currentInput - Full input string
   * @param {string} ghostText - Current ghost text
   * @returns {string} - Text to insert when Tab is pressed
   */
  getCompletion(currentInput, ghostText) {
    if (!ghostText) {
      return '';
    }

    // Ghost text is the completion, so return it
    return ghostText;
  }

  /**
   * Get full completed input (current input + ghost text)
   * @param {string} currentInput - Current input
   * @param {string} ghostText - Ghost text
   * @returns {string} - Full completed input
   */
  getFullInput(currentInput, ghostText) {
    return currentInput + ghostText;
  }

  /**
   * Check if ghost text should be shown for current input
   * @param {string} currentInput - Current input
   * @param {Array} suggestions - Suggestions array
   * @returns {boolean} - True if ghost text should be shown
   */
  shouldShowGhostText(currentInput, suggestions) {
    if (!suggestions || suggestions.length === 0) {
      return false;
    }

    const topSuggestion = suggestions[0];
    if (!topSuggestion || topSuggestion.score < this.minScoreThreshold) {
      return false;
    }

    const partialToken = this._getPartialToken(currentInput);
    const completion = this._getCompletion(partialToken, topSuggestion.value);

    return completion.length > 0;
  }

  /**
   * Set minimum score threshold for ghost text
   * @param {number} threshold - New threshold value
   */
  setScoreThreshold(threshold) {
    this.minScoreThreshold = threshold;
  }

  /**
   * Extract partial token (last word being typed) from input
   * @param {string} input - Full input string
   * @returns {string} - Partial token
   * @private
   */
  _getPartialToken(input) {
    if (!input) return '';

    // Trim trailing whitespace only (keep leading for context)
    const trimmed = input.trimEnd();

    // If original input ends with whitespace, there's no partial token
    if (input.length !== trimmed.length) {
      return '';
    }

    // Split and filter empty tokens
    const tokens = trimmed.split(/\s+/).filter(t => t.length > 0);

    // Return last token
    return tokens[tokens.length - 1] || '';
  }

  /**
   * Get completion part of suggestion (what to append)
   * @param {string} partialToken - Partial token being typed
   * @param {string} suggestion - Full suggestion value
   * @returns {string} - Completion text
   * @private
   */
  _getCompletion(partialToken, suggestion) {
    if (!suggestion) return '';
    if (!partialToken) return suggestion;

    // Check if suggestion starts with partial token (case-insensitive)
    const lowerPartial = partialToken.toLowerCase();
    const lowerSuggestion = suggestion.toLowerCase();

    if (lowerSuggestion.startsWith(lowerPartial)) {
      // Return the remaining part
      return suggestion.slice(partialToken.length);
    }

    // No match
    return '';
  }

  /**
   * Get ghost text with full word completion
   * (Alternative implementation that completes to next space)
   * @param {string} currentInput - Full input string
   * @param {Array} suggestions - Suggestions array
   * @returns {string} - Ghost text including space if needed
   */
  getGhostTextWithSpace(currentInput, suggestions) {
    const ghostText = this.getGhostText(currentInput, suggestions);

    if (!ghostText) return '';

    // If completing a word, add a space at the end
    const partialToken = this._getPartialToken(currentInput);
    if (partialToken.length > 0) {
      return ghostText + ' ';
    }

    return ghostText;
  }

  /**
   * Get multi-word ghost text (suggests full command)
   * @param {string} currentInput - Current input
   * @param {Array} suggestions - Suggestions for next tokens
   * @param {number} maxTokens - Maximum tokens to suggest (default: 3)
   * @returns {string} - Multi-word ghost text
   */
  getMultiWordGhostText(currentInput, suggestions, maxTokens = 3) {
    if (!suggestions || suggestions.length === 0) {
      return '';
    }

    // Get top suggestion for current token
    const currentGhost = this.getGhostText(currentInput, suggestions);

    if (!currentGhost) {
      return '';
    }

    // For now, just return single token
    // TODO: Implement multi-token prediction when we have sequence prediction
    return currentGhost;
  }
}

export default GhostTextGenerator;
