/**
 * GhostTextGenerator Tests - Comprehensive test suite for ghost text generation
 */

import { describe, it, expect, beforeEach } from 'vitest';
import GhostTextGenerator from './GhostTextGenerator.js';

describe('GhostTextGenerator', () => {
  let generator;

  beforeEach(() => {
    generator = new GhostTextGenerator();
  });

  describe('Basic Functionality', () => {
    it('should create generator', () => {
      expect(generator).toBeDefined();
      expect(generator.minScoreThreshold).toBe(2.0);
    });

    it('should suggest full word for empty input', () => {
      const suggestions = [{ value: 'set', score: 3.0 }];
      const ghostText = generator.getGhostText('', suggestions);

      // Empty input should suggest the full word
      expect(ghostText).toBe('set');
    });

    it('should return empty ghost text for no suggestions', () => {
      const ghostText = generator.getGhostText('set', []);

      expect(ghostText).toBe('');
    });

    it('should return empty ghost text for low score', () => {
      const suggestions = [{ value: 'set', score: 1.0 }]; // Below threshold
      const ghostText = generator.getGhostText('s', suggestions);

      expect(ghostText).toBe('');
    });
  });

  describe('Ghost Text Generation', () => {
    it('should generate ghost text for partial match', () => {
      const suggestions = [{ value: 'set', score: 3.0 }];
      const ghostText = generator.getGhostText('s', suggestions);

      expect(ghostText).toBe('et');
    });

    it('should generate ghost text for longer partial', () => {
      const suggestions = [{ value: 'track', score: 3.0 }];
      const ghostText = generator.getGhostText('tra', suggestions);

      expect(ghostText).toBe('ck');
    });

    it('should return empty for complete match', () => {
      const suggestions = [{ value: 'set', score: 3.0 }];
      const ghostText = generator.getGhostText('set', suggestions);

      expect(ghostText).toBe('');
    });

    it('should handle case-insensitive matching', () => {
      const suggestions = [{ value: 'track', score: 3.0 }];
      const ghostText = generator.getGhostText('TRA', suggestions);

      expect(ghostText).toBe('ck');
    });

    it('should return empty for no prefix match', () => {
      const suggestions = [{ value: 'track', score: 3.0 }];
      const ghostText = generator.getGhostText('xyz', suggestions);

      expect(ghostText).toBe('');
    });
  });

  describe('Multi-Word Input', () => {
    it('should suggest for last word only', () => {
      const suggestions = [{ value: 'track', score: 3.0 }];
      const ghostText = generator.getGhostText('set t', suggestions);

      expect(ghostText).toBe('rack');
    });

    it('should handle multiple spaces', () => {
      const suggestions = [{ value: 'volume', score: 3.0 }];
      const ghostText = generator.getGhostText('set track 1 v', suggestions);

      expect(ghostText).toBe('olume');
    });

    it('should return empty when input ends with space', () => {
      const suggestions = [{ value: 'track', score: 3.0 }];
      const ghostText = generator.getGhostText('set ', suggestions);

      // When input ends with space, there's no partial token
      // So we should suggest the full word
      expect(ghostText).toBe('track');
    });

    it('should handle tabs as whitespace', () => {
      const suggestions = [{ value: 'track', score: 3.0 }];
      const ghostText = generator.getGhostText('set\t', suggestions);

      expect(ghostText).toBe('track');
    });
  });

  describe('Completion Methods', () => {
    it('should get completion text', () => {
      const ghostText = 'et';
      const completion = generator.getCompletion('s', ghostText);

      expect(completion).toBe('et');
    });

    it('should return empty for no ghost text', () => {
      const completion = generator.getCompletion('set', '');

      expect(completion).toBe('');
    });

    it('should get full input', () => {
      const fullInput = generator.getFullInput('s', 'et');

      expect(fullInput).toBe('set');
    });

    it('should handle full input with no ghost text', () => {
      const fullInput = generator.getFullInput('set', '');

      expect(fullInput).toBe('set');
    });
  });

  describe('Should Show Ghost Text', () => {
    it('should return true when ghost text available', () => {
      const suggestions = [{ value: 'set', score: 3.0 }];
      const should = generator.shouldShowGhostText('s', suggestions);

      expect(should).toBe(true);
    });

    it('should return false for no suggestions', () => {
      const should = generator.shouldShowGhostText('s', []);

      expect(should).toBe(false);
    });

    it('should return false for low score', () => {
      const suggestions = [{ value: 'set', score: 1.0 }];
      const should = generator.shouldShowGhostText('s', suggestions);

      expect(should).toBe(false);
    });

    it('should return false for complete match', () => {
      const suggestions = [{ value: 'set', score: 3.0 }];
      const should = generator.shouldShowGhostText('set', suggestions);

      expect(should).toBe(false);
    });
  });

  describe('Score Threshold', () => {
    it('should allow changing threshold', () => {
      generator.setScoreThreshold(1.0);
      expect(generator.minScoreThreshold).toBe(1.0);
    });

    it('should show ghost text with lower threshold', () => {
      generator.setScoreThreshold(0.5);
      const suggestions = [{ value: 'set', score: 1.0 }];
      const ghostText = generator.getGhostText('s', suggestions);

      expect(ghostText).toBe('et');
    });

    it('should hide ghost text with higher threshold', () => {
      generator.setScoreThreshold(5.0);
      const suggestions = [{ value: 'set', score: 3.0 }];
      const ghostText = generator.getGhostText('s', suggestions);

      expect(ghostText).toBe('');
    });
  });

  describe('Ghost Text With Space', () => {
    it('should add space for word completion', () => {
      const suggestions = [{ value: 'set', score: 3.0 }];
      const ghostText = generator.getGhostTextWithSpace('s', suggestions);

      expect(ghostText).toBe('et ');
    });

    it('should not add space when no partial token', () => {
      const suggestions = [{ value: 'set', score: 3.0 }];
      const ghostText = generator.getGhostTextWithSpace('', suggestions);

      expect(ghostText).toBe('set');
    });

    it('should return empty when no ghost text', () => {
      const suggestions = [{ value: 'set', score: 1.0 }];
      const ghostText = generator.getGhostTextWithSpace('s', suggestions);

      expect(ghostText).toBe('');
    });
  });

  describe('Multi-Word Ghost Text', () => {
    it('should return single word for now', () => {
      const suggestions = [{ value: 'set', score: 3.0 }];
      const ghostText = generator.getMultiWordGhostText('s', suggestions);

      expect(ghostText).toBe('et');
    });

    it('should return empty for no suggestions', () => {
      const ghostText = generator.getMultiWordGhostText('s', []);

      expect(ghostText).toBe('');
    });

    it('should respect max tokens parameter', () => {
      const suggestions = [{ value: 'set', score: 3.0 }];
      const ghostText = generator.getMultiWordGhostText('s', suggestions, 1);

      expect(ghostText).toBe('et');
    });
  });

  describe('Edge Cases', () => {
    it('should handle null input', () => {
      const suggestions = [{ value: 'set', score: 3.0 }];
      const ghostText = generator.getGhostText(null, suggestions);

      // Null input should suggest the full word
      expect(ghostText).toBe('set');
    });

    it('should handle undefined suggestions', () => {
      const ghostText = generator.getGhostText('s', undefined);

      expect(ghostText).toBe('');
    });

    it('should handle null suggestion', () => {
      const suggestions = [null];
      const ghostText = generator.getGhostText('s', suggestions);

      expect(ghostText).toBe('');
    });

    it('should handle suggestion without score', () => {
      const suggestions = [{ value: 'set' }]; // No score
      const ghostText = generator.getGhostText('s', suggestions);

      expect(ghostText).toBe('');
    });

    it('should handle empty suggestion value', () => {
      const suggestions = [{ value: '', score: 3.0 }];
      const ghostText = generator.getGhostText('s', suggestions);

      expect(ghostText).toBe('');
    });

    it('should handle whitespace in input', () => {
      const suggestions = [{ value: 'set', score: 3.0 }];
      const ghostText = generator.getGhostText('  s  ', suggestions);

      // Input ends with whitespace, so no partial token → suggest full word
      expect(ghostText).toBe('set');
    });
  });

  describe('Real-World Scenarios', () => {
    it('should suggest "set" for "s"', () => {
      const suggestions = [{ value: 'set', score: 3.0 }];
      const ghostText = generator.getGhostText('s', suggestions);

      expect(ghostText).toBe('et');
    });

    it('should suggest "track" for "set t"', () => {
      const suggestions = [{ value: 'track', score: 3.0 }];
      const ghostText = generator.getGhostText('set t', suggestions);

      expect(ghostText).toBe('rack');
    });

    it('should suggest "volume" for "set track 1 v"', () => {
      const suggestions = [{ value: 'volume', score: 3.0 }];
      const ghostText = generator.getGhostText('set track 1 v', suggestions);

      expect(ghostText).toBe('olume');
    });

    it('should not suggest when fully typed', () => {
      const suggestions = [{ value: 'set', score: 3.0 }];
      const ghostText = generator.getGhostText('set', suggestions);

      expect(ghostText).toBe('');
    });

    it('should suggest next word when space typed', () => {
      const suggestions = [{ value: 'track', score: 3.0 }];
      const ghostText = generator.getGhostText('set ', suggestions);

      expect(ghostText).toBe('track');
    });
  });

  describe('Private Methods via Public API', () => {
    it('should extract partial token correctly', () => {
      const suggestions = [{ value: 'test', score: 3.0 }];

      // Test by checking ghost text which uses _getPartialToken
      const ghostText1 = generator.getGhostText('one two thr', suggestions);
      expect(ghostText1).toBe(''); // 'thr' doesn't match 'test'

      const ghostText2 = generator.getGhostText('one two te', suggestions);
      expect(ghostText2).toBe('st'); // 'te' matches 'test'
    });

    it('should get completion correctly', () => {
      const suggestions = [{ value: 'increase', score: 3.0 }];
      const ghostText = generator.getGhostText('inc', suggestions);

      expect(ghostText).toBe('rease');
    });
  });
});
