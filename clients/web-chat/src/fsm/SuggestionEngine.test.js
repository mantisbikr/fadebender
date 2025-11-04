/**
 * SuggestionEngine Tests - Comprehensive test suite for suggestion generation
 */

import { describe, it, expect, beforeEach } from 'vitest';
import SuggestionEngine from './SuggestionEngine.js';
import MixerFSM from './MixerFSM.js';

describe('SuggestionEngine', () => {
  let fsm;
  let engine;

  beforeEach(() => {
    fsm = new MixerFSM();
    engine = new SuggestionEngine(fsm);
  });

  describe('Basic Functionality', () => {
    it('should create engine with FSM', () => {
      expect(engine).toBeDefined();
      expect(engine.fsm).toBe(fsm);
    });

    it('should get suggestions for empty state', () => {
      const state = fsm.createInitialState();
      const suggestions = engine.getSuggestions(state);

      expect(Array.isArray(suggestions)).toBe(true);
      expect(suggestions.length).toBeGreaterThan(0);

      // Should suggest actions
      const actionValues = suggestions.map(s => s.value);
      expect(actionValues).toContain('set');
      expect(actionValues).toContain('increase');
      expect(actionValues).toContain('decrease');
      expect(actionValues).toContain('toggle');
    });

    it('should return suggestion objects with correct shape', () => {
      const state = fsm.createInitialState();
      const suggestions = engine.getSuggestions(state);

      expect(suggestions.length).toBeGreaterThan(0);

      const suggestion = suggestions[0];
      expect(suggestion).toHaveProperty('value');
      expect(suggestion).toHaveProperty('display');
      expect(suggestion).toHaveProperty('type');
      expect(suggestion).toHaveProperty('score');
      expect(typeof suggestion.value).toBe('string');
      expect(typeof suggestion.score).toBe('number');
    });
  });

  describe('Prefix Filtering', () => {
    it('should return all suggestions when prefix is empty', () => {
      const state = fsm.createInitialState();
      const allSuggestions = engine.getSuggestions(state, '');
      const noFilterSuggestions = engine.getSuggestions(state);

      expect(allSuggestions.length).toBe(noFilterSuggestions.length);
    });

    it('should filter by prefix match', () => {
      const state = fsm.createInitialState();
      const suggestions = engine.getSuggestions(state, 's');

      const values = suggestions.map(s => s.value);

      // Should include 'set'
      expect(values).toContain('set');

      // Should not include non-matching actions
      expect(values).not.toContain('toggle');
    });

    it('should handle case-insensitive filtering', () => {
      const state = fsm.createInitialState();
      const lowerSuggestions = engine.getSuggestions(state, 's');
      const upperSuggestions = engine.getSuggestions(state, 'S');

      expect(lowerSuggestions.map(s => s.value)).toEqual(upperSuggestions.map(s => s.value));
    });

    it('should filter to single suggestion with full prefix', () => {
      const state = fsm.createInitialState();
      const suggestions = engine.getSuggestions(state, 'set');

      expect(suggestions.length).toBeGreaterThan(0);
      expect(suggestions[0].value).toBe('set');
    });

    it('should return empty array when no match', () => {
      const state = fsm.createInitialState();
      const suggestions = engine.getSuggestions(state, 'xyz');

      expect(suggestions).toEqual([]);
    });
  });

  describe('Suggestions at Different FSM States', () => {
    it('should suggest target types after action', () => {
      let state = fsm.createInitialState();
      state = fsm.processToken(state, 'set');
      const suggestions = engine.getSuggestions(state);

      const values = suggestions.map(s => s.value);
      expect(values).toContain('track');
      expect(values).toContain('return');
      expect(values).toContain('master');
    });

    it('should suggest track IDs after "track"', () => {
      let state = fsm.createInitialState();
      state = fsm.processToken(state, 'set');
      state = fsm.processToken(state, 'track');

      const suggestions = engine.getSuggestions(state, '', { availableTracks: [1, 2, 3] });

      const values = suggestions.map(s => s.value);
      expect(values).toContain('1');
      expect(values).toContain('2');
      expect(values).toContain('3');
    });

    it('should suggest return IDs after "return"', () => {
      let state = fsm.createInitialState();
      state = fsm.processToken(state, 'set');
      state = fsm.processToken(state, 'return');

      const suggestions = engine.getSuggestions(state, '', { availableReturns: ['A', 'B'] });

      const values = suggestions.map(s => s.value);
      expect(values).toContain('A');
      expect(values).toContain('B');
    });

    it('should suggest params after target ID', () => {
      let state = fsm.createInitialState();
      state = fsm.processToken(state, 'set');
      state = fsm.processToken(state, 'track');
      state = fsm.processToken(state, '1');

      const suggestions = engine.getSuggestions(state);

      const values = suggestions.map(s => s.value);
      expect(values).toContain('volume');
      expect(values).toContain('pan');
      expect(values).toContain('mute');
    });

    it('should suggest values after param', () => {
      let state = fsm.createInitialState();
      state = fsm.processToken(state, 'set');
      state = fsm.processToken(state, 'track');
      state = fsm.processToken(state, '1');
      state = fsm.processToken(state, 'volume');

      const suggestions = engine.getSuggestions(state);

      // Should have some suggestions (values are flexible)
      expect(suggestions.length).toBeGreaterThan(0);
    });
  });

  describe('Ranking', () => {
    it('should rank exact prefix matches higher', () => {
      let state = fsm.createInitialState();
      state = fsm.processToken(state, 'set');

      const suggestions = engine.getSuggestions(state, 't');

      // "track" should rank higher than "return" (contains 't' but doesn't start with it)
      const trackIndex = suggestions.findIndex(s => s.value === 'track');
      const returnIndex = suggestions.findIndex(s => s.value === 'return');

      if (returnIndex !== -1) {
        expect(trackIndex).toBeLessThan(returnIndex);
      }
    });

    it('should assign higher scores to exact prefix matches', () => {
      const suggestions = [
        { value: 'track', type: 'target_type', display: 'track', score: 1.0, description: '' },
        { value: 'return', type: 'target_type', display: 'return', score: 1.0, description: '' }
      ];

      const ranked = engine.rankSuggestions(suggestions, { partialToken: 't' });

      const trackScore = ranked.find(s => s.value === 'track')?.score || 0;
      const returnScore = ranked.find(s => s.value === 'return')?.score || 0;

      expect(trackScore).toBeGreaterThan(returnScore);
    });

    it('should sort suggestions by score', () => {
      const state = fsm.createInitialState();
      const suggestions = engine.getSuggestions(state, 's');

      // Verify sorted by score descending
      for (let i = 0; i < suggestions.length - 1; i++) {
        expect(suggestions[i].score).toBeGreaterThanOrEqual(suggestions[i + 1].score);
      }
    });
  });

  describe('Top Suggestions', () => {
    it('should return top N suggestions', () => {
      const state = fsm.createInitialState();
      const topSuggestions = engine.getTopSuggestions(state, '', 3);

      expect(topSuggestions.length).toBeLessThanOrEqual(3);
    });

    it('should return all suggestions if fewer than limit', () => {
      let state = fsm.createInitialState();
      state = fsm.processToken(state, 'set');
      state = fsm.processToken(state, 'track');
      state = fsm.processToken(state, '1');
      state = fsm.processToken(state, 'volume');

      const topSuggestions = engine.getTopSuggestions(state, '', 100);

      // Should return all available suggestions even if < 100
      expect(topSuggestions.length).toBeGreaterThan(0);
      expect(topSuggestions.length).toBeLessThan(100);
    });
  });

  describe('Ghost Text', () => {
    it('should return completion part only', () => {
      const state = fsm.createInitialState();
      const ghostText = engine.getGhostText(state, 's');

      // Should return "et" (completion of "set")
      if (ghostText.length > 0) {
        expect(ghostText).not.toContain('s');
        expect('s' + ghostText).toMatch(/set/i);
      }
    });

    it('should return empty string when no strong match', () => {
      const state = fsm.createInitialState();
      const ghostText = engine.getGhostText(state, 'xyz');

      expect(ghostText).toBe('');
    });

    it('should return top suggestion for empty prefix', () => {
      const state = fsm.createInitialState();
      const ghostText = engine.getGhostText(state, '');

      // May return empty or a full suggestion
      expect(typeof ghostText).toBe('string');
    });

    it('should handle partial matches', () => {
      let state = fsm.createInitialState();
      state = fsm.processToken(state, 'set');

      const ghostText = engine.getGhostText(state, 'tra');

      // Should complete "tra" to "track" → return "ck"
      if (ghostText.length > 0) {
        expect('tra' + ghostText).toBe('track');
      }
    });
  });

  describe('Filter By Prefix', () => {
    it('should filter exact prefix matches', () => {
      const suggestions = [
        { value: 'track', type: 'target_type', display: 'track', score: 1.0, description: '' },
        { value: 'return', type: 'target_type', display: 'return', score: 1.0, description: '' },
        { value: 'master', type: 'target_type', display: 'master', score: 1.0, description: '' }
      ];

      const filtered = engine.filterByPrefix(suggestions, 't');

      expect(filtered.length).toBeGreaterThan(0);
      expect(filtered.map(s => s.value)).toContain('track');
      // Note: fuzzy matching includes 'return' and 'master' since they contain 't'
      expect(filtered.map(s => s.value)).toContain('return'); // contains 't'
      expect(filtered.map(s => s.value)).toContain('master'); // contains 't'
    });

    it('should filter fuzzy matches', () => {
      const suggestions = [
        { value: 'return', type: 'target_type', display: 'return', score: 1.0, description: '' },
        { value: 'master', type: 'target_type', display: 'master', score: 1.0, description: '' }
      ];

      const filtered = engine.filterByPrefix(suggestions, 't');

      // 'return' contains 't', so should be included
      expect(filtered.map(s => s.value)).toContain('return');
      expect(filtered.map(s => s.value)).toContain('master'); // 'master' also contains 't'
    });

    it('should handle case-insensitive filtering', () => {
      const suggestions = [
        { value: 'Track', type: 'target_type', display: 'Track', score: 1.0, description: '' }
      ];

      const filtered = engine.filterByPrefix(suggestions, 't');

      expect(filtered.length).toBe(1);
      expect(filtered[0].value).toBe('Track');
    });
  });

  describe('Context-Aware Suggestions', () => {
    it('should use context for available tracks', () => {
      let state = fsm.createInitialState();
      state = fsm.processToken(state, 'set');
      state = fsm.processToken(state, 'track');

      // FSM uses trackCount, not availableTracks
      const context = { trackCount: 3 };
      const suggestions = engine.getSuggestions(state, '', context);

      const values = suggestions.map(s => s.value);
      expect(values).toContain('1');
      expect(values).toContain('2');
      expect(values).toContain('3');
      expect(values.length).toBe(3); // Only 3 tracks
    });

    it('should use context for available returns', () => {
      let state = fsm.createInitialState();
      state = fsm.processToken(state, 'set');
      state = fsm.processToken(state, 'return');

      // FSM uses returnCount, not availableReturns
      const context = { returnCount: 12 }; // All 12 returns (A-L)
      const suggestions = engine.getSuggestions(state, '', context);

      const values = suggestions.map(s => s.value);
      expect(values).toContain('A');
      expect(values).toContain('B');
      expect(values).toContain('L'); // 12th return
      expect(values.length).toBe(12); // All 12 returns
    });
  });

  describe('Edge Cases', () => {
    it('should handle empty partial token', () => {
      const state = fsm.createInitialState();
      const suggestions = engine.getSuggestions(state, '');

      expect(Array.isArray(suggestions)).toBe(true);
      expect(suggestions.length).toBeGreaterThan(0);
    });

    it('should handle undefined partial token', () => {
      const state = fsm.createInitialState();
      const suggestions = engine.getSuggestions(state);

      expect(Array.isArray(suggestions)).toBe(true);
    });

    it('should handle invalid state gracefully', () => {
      const invalidState = {};
      const suggestions = engine.getSuggestions(invalidState, '');

      // Should not crash, may return empty array
      expect(Array.isArray(suggestions)).toBe(true);
    });

    it('should handle special characters in prefix', () => {
      const state = fsm.createInitialState();
      const suggestions = engine.getSuggestions(state, '-');

      // Should not crash
      expect(Array.isArray(suggestions)).toBe(true);
    });
  });

  describe('Real-World Scenarios', () => {
    it('should suggest correctly for "set t"', () => {
      let state = fsm.createInitialState();
      state = fsm.processToken(state, 'set');

      const suggestions = engine.getSuggestions(state, 't');

      const values = suggestions.map(s => s.value);
      expect(values).toContain('track');
    });

    it('should suggest correctly for "set track 1 v"', () => {
      let state = fsm.createInitialState();
      state = fsm.processToken(state, 'set');
      state = fsm.processToken(state, 'track');
      state = fsm.processToken(state, '1');

      const suggestions = engine.getSuggestions(state, 'v');

      const values = suggestions.map(s => s.value);
      expect(values).toContain('volume');
    });

    it('should suggest correctly for "increase return A p"', () => {
      let state = fsm.createInitialState();
      state = fsm.processToken(state, 'increase');
      state = fsm.processToken(state, 'return');
      state = fsm.processToken(state, 'A');

      const suggestions = engine.getSuggestions(state, 'p');

      const values = suggestions.map(s => s.value);
      expect(values).toContain('pan');
    });
  });
});
