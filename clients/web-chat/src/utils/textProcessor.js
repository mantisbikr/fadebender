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
      // Common shortened typos
      'trac': 'track', 'trck': 'track',

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

  // Allow augmenting corrections from server config (nlp.typo_corrections)
  setExternalCorrections(map) {
    if (!map || typeof map !== 'object') return;
    const merged = { ...this.corrections };
    Object.entries(map).forEach(([k, v]) => {
      if (typeof k === 'string' && typeof v === 'string') {
        merged[String(k).toLowerCase()] = String(v).toLowerCase();
      }
    });
    this.corrections = merged;
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
    // Only validate basic constraints - let backend handle command validation
    if (!text || text.trim().length < 2) {
      return { valid: false, error: 'Command too short' };
    }

    if (text.length > 300) {
      return { valid: false, error: 'Command too long' };
    }

    // All other validation handled by backend
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
