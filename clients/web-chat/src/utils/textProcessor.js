/**
 * Text Processing Utilities
 * Handles typo correction, normalization, and validation
 */

class TextProcessor {
  constructor() {
    // Common DAW term corrections
    this.corrections = {
      // Track references
      'track1': 'track 1', 'track2': 'track 2', 'track3': 'track 3',
      'trk1': 'track 1', 'trk2': 'track 2', 'trk3': 'track 3',
      'trak': 'track', 'tracj': 'track',

      // Volume terms
      'volum': 'volume', 'vollume': 'volume', 'vol': 'volume',
      'loudr': 'louder', 'quiter': 'quieter', 'quietr': 'quieter',
      'incrase': 'increase', 'increse': 'increase', 'incrasing': 'increasing', 'increace': 'increase',

      // Pan terms
      'pann': 'pan', 'centre': 'center', 'centr': 'center',

      // Numbers (context-aware: 'for' -> 'four' only in number context)
      'won': 'one', 'too': 'two', 'tre': 'three', 'fiv': 'five',
      'siks': 'six', 'sevn': 'seven', 'ate': 'eight',

      // Effects and instruments
      'reverb': 'reverb', 'revreb': 'reverb', 'reverbb': 'reverb', 'revebr': 'reverb', 'reverv': 'reverb', 'teh': 'the',
      // Returns and common misspellings
      'retrun': 'return', 'retun': 'return',
      // Stereo misspellings
      'strereo': 'stereo', 'streo': 'stereo', 'stere': 'stereo',
      'piano': 'piano', 'pian': 'piano', 'paino': 'piano',

      // dB and percentages
      'db': 'dB', 'decibel': 'dB', 'decibels': 'dB',
      'percent': '%', 'pct': '%', 'percnt': '%'
    };
  }

  correctTypos(text) {
    let corrected = text.toLowerCase();

    // Special case: "four" when it means "for" in "four the piano"
    corrected = corrected.replace(/\bfour\s+(the\s+)?piano\b/gi, 'for the piano');

    // Apply corrections
    Object.entries(this.corrections).forEach(([typo, correction]) => {
      const regex = new RegExp(`\\b${typo}\\b`, 'gi');
      corrected = corrected.replace(regex, correction);
    });

    return corrected;
  }

  normalizeCommand(text) {
    return text
      .trim()
      .replace(/\s+/g, ' ') // Multiple spaces to single space
      // Keep digits, letters, space, %, -, and decimal point for dB values
      .replace(/[^\w\s%.-]/g, '')
      .toLowerCase();
  }

  validateCommand(text) {
    if (!text || text.trim().length < 2) {
      return { valid: false, error: 'Command too short' };
    }

    if (text.length > 300) {
      return { valid: false, error: 'Command too long' };
    }

    // Expanded DAW-related keywords - be more inclusive
    const dawKeywords = [
      'track', 'volume', 'pan', 'set', 'make', 'increase', 'decrease', 'reduce', 'raise', 'lower',
      'reverb', 'delay', 'echo', 'eq', 'bass', 'treble', 'gain', 'level',
      'piano', 'guitar', 'drums', 'vocal', 'synth', 'kick', 'snare', 'hi-hat',
      'loud', 'quiet', 'soft', 'hard', 'wet', 'dry', 'left', 'right', 'center',
      'up', 'down', 'add', 'remove', 'turn', 'adjust', 'change', 'modify',
      'more', 'less', 'higher', 'lower', 'boost', 'cut', 'mute', 'solo',
      'db', 'percent', '%', 'amount', 'bit', 'little', 'much', 'lot',
      // Sends/routing/help terms
      'send', 'sends', 'routing', 'route', 'control', 'help', 'how', 'guide',
      // Mixer entities
      'master', 'return', 'cue'
    ];

    const hasKeyword = dawKeywords.some(keyword => text.includes(keyword));

    if (!hasKeyword) {
      // Allow help-style queries to pass through to /help
      if (text.includes('how') || text.includes('help')) {
        return { valid: true };
      }
      return { valid: false, error: 'Not a recognized DAW command' };
    }

    return { valid: true };
  }

  processInput(rawText) {
    const normalized = this.normalizeCommand(rawText);
    const corrected = this.correctTypos(normalized);
    const validation = this.validateCommand(corrected);

    return {
      original: rawText,
      processed: corrected,
      corrections: normalized !== corrected,
      validation
    };
  }
}

export const textProcessor = new TextProcessor();
