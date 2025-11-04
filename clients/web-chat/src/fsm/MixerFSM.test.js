/**
 * MixerFSM Tests - Comprehensive test suite for mixer state machine
 *
 * Tests all valid command flows and error cases.
 */

import { describe, it, expect, beforeEach } from 'vitest';
import MixerFSM from './MixerFSM.js';

describe('MixerFSM', () => {
  let fsm;

  beforeEach(() => {
    fsm = new MixerFSM();
  });

  describe('Initial State', () => {
    it('should create initial state with correct structure', () => {
      const state = fsm.createInitialState();

      expect(state.phase).toBe('action');
      expect(state.action).toBeNull();
      expect(state.targetType).toBeNull();
      expect(state.targetId).toBeNull();
      expect(state.param).toBeNull();
      expect(state.sendRef).toBeNull();
      expect(state.value).toBeNull();
      expect(state.error).toBeNull();
    });
  });

  describe('Action Processing', () => {
    it('should process valid actions', () => {
      const actions = ['set', 'increase', 'decrease', 'toggle'];

      actions.forEach(action => {
        const state = fsm.createInitialState();
        const newState = fsm.processToken(state, action);

        expect(newState.action).toBe(action);
        expect(newState.phase).toBe('target_type');
        expect(newState.error).toBeNull();
      });
    });

    it('should reject invalid actions', () => {
      const state = fsm.createInitialState();
      const newState = fsm.processToken(state, 'invalid_action');

      expect(newState.action).toBeNull();
      expect(newState.error).toContain('Invalid action');
    });
  });

  describe('Target Type Processing', () => {
    it('should process track target type', () => {
      let state = fsm.createInitialState();
      state = fsm.processToken(state, 'set');
      state = fsm.processToken(state, 'track');

      expect(state.targetType).toBe('track');
      expect(state.phase).toBe('target_id');
      expect(state.error).toBeNull();
    });

    it('should process return target type', () => {
      let state = fsm.createInitialState();
      state = fsm.processToken(state, 'set');
      state = fsm.processToken(state, 'return');

      expect(state.targetType).toBe('return');
      expect(state.phase).toBe('target_id');
      expect(state.error).toBeNull();
    });

    it('should process master target type and skip to param', () => {
      let state = fsm.createInitialState();
      state = fsm.processToken(state, 'set');
      state = fsm.processToken(state, 'master');

      expect(state.targetType).toBe('master');
      expect(state.phase).toBe('param');
      expect(state.error).toBeNull();
    });

    it('should reject invalid target types', () => {
      let state = fsm.createInitialState();
      state = fsm.processToken(state, 'set');
      state = fsm.processToken(state, 'invalid');

      expect(state.targetType).toBeNull();
      expect(state.error).toContain('Invalid target type');
    });
  });

  describe('Target ID Processing', () => {
    it('should process valid track numbers', () => {
      let state = fsm.createInitialState();
      state = fsm.processToken(state, 'set');
      state = fsm.processToken(state, 'track');
      state = fsm.processToken(state, '1');

      expect(state.targetId).toBe(1);
      expect(state.phase).toBe('param');
      expect(state.error).toBeNull();
    });

    it('should process large track numbers', () => {
      let state = fsm.createInitialState();
      state = fsm.processToken(state, 'set');
      state = fsm.processToken(state, 'track');
      state = fsm.processToken(state, '999');

      expect(state.targetId).toBe(999);
      expect(state.error).toBeNull();
    });

    it('should reject invalid track numbers', () => {
      let state = fsm.createInitialState();
      state = fsm.processToken(state, 'set');
      state = fsm.processToken(state, 'track');
      state = fsm.processToken(state, '0');

      expect(state.targetId).toBeNull();
      expect(state.error).toContain('Invalid track number');
    });

    it('should process return letters (A-L)', () => {
      const letters = 'ABCDEFGHIJKL'.split('');

      letters.forEach(letter => {
        let state = fsm.createInitialState();
        state = fsm.processToken(state, 'set');
        state = fsm.processToken(state, 'return');
        state = fsm.processToken(state, letter);

        expect(state.targetId).toBe(letter);
        expect(state.phase).toBe('param');
        expect(state.error).toBeNull();
      });
    });

    it('should process return letters (lowercase)', () => {
      let state = fsm.createInitialState();
      state = fsm.processToken(state, 'set');
      state = fsm.processToken(state, 'return');
      state = fsm.processToken(state, 'a');

      expect(state.targetId).toBe('A');
      expect(state.error).toBeNull();
    });

    it('should process return numbers (0-11)', () => {
      let state = fsm.createInitialState();
      state = fsm.processToken(state, 'set');
      state = fsm.processToken(state, 'return');
      state = fsm.processToken(state, '0');

      expect(state.targetId).toBe('A'); // 0 maps to A
      expect(state.error).toBeNull();
    });

    it('should reject invalid return IDs', () => {
      let state = fsm.createInitialState();
      state = fsm.processToken(state, 'set');
      state = fsm.processToken(state, 'return');
      state = fsm.processToken(state, 'Z');

      expect(state.targetId).toBeNull();
      expect(state.error).toContain('Invalid return ID');
    });
  });

  describe('Parameter Processing', () => {
    it('should process volume parameter', () => {
      let state = fsm.createInitialState();
      state = fsm.processToken(state, 'set');
      state = fsm.processToken(state, 'track');
      state = fsm.processToken(state, '1');
      state = fsm.processToken(state, 'volume');

      expect(state.param).toBe('volume');
      expect(state.phase).toBe('value');
      expect(state.error).toBeNull();
    });

    it('should process pan parameter', () => {
      let state = fsm.createInitialState();
      state = fsm.processToken(state, 'set');
      state = fsm.processToken(state, 'track');
      state = fsm.processToken(state, '1');
      state = fsm.processToken(state, 'pan');

      expect(state.param).toBe('pan');
      expect(state.phase).toBe('value');
      expect(state.error).toBeNull();
    });

    it('should process toggle parameter and complete immediately', () => {
      let state = fsm.createInitialState();
      state = fsm.processToken(state, 'toggle');
      state = fsm.processToken(state, 'track');
      state = fsm.processToken(state, '1');
      state = fsm.processToken(state, 'mute');

      expect(state.param).toBe('mute');
      expect(state.phase).toBe('complete');
      expect(state.error).toBeNull();
    });

    it('should process send parameter and require send ref', () => {
      let state = fsm.createInitialState();
      state = fsm.processToken(state, 'set');
      state = fsm.processToken(state, 'track');
      state = fsm.processToken(state, '1');
      state = fsm.processToken(state, 'send');

      expect(state.param).toBe('send');
      expect(state.phase).toBe('send_ref');
      expect(state.error).toBeNull();
    });

    it('should reject invalid parameters', () => {
      let state = fsm.createInitialState();
      state = fsm.processToken(state, 'set');
      state = fsm.processToken(state, 'track');
      state = fsm.processToken(state, '1');
      state = fsm.processToken(state, 'invalid_param');

      expect(state.param).toBeNull();
      expect(state.error).toContain('Invalid parameter');
    });
  });

  describe('Value Processing', () => {
    it('should process numeric values', () => {
      let state = fsm.createInitialState();
      state = fsm.processToken(state, 'set');
      state = fsm.processToken(state, 'track');
      state = fsm.processToken(state, '1');
      state = fsm.processToken(state, 'volume');
      state = fsm.processToken(state, '-20');

      expect(state.value).toMatchObject({
        raw: -20,
        unit: null
      });
      expect(state.phase).toBe('complete');
      expect(state.error).toBeNull();
    });

    it('should process dB values', () => {
      let state = fsm.createInitialState();
      state = fsm.processToken(state, 'set');
      state = fsm.processToken(state, 'track');
      state = fsm.processToken(state, '1');
      state = fsm.processToken(state, 'volume');
      state = fsm.processToken(state, '-6db');

      expect(state.value).toMatchObject({
        raw: -6,
        unit: 'db'
      });
      expect(state.phase).toBe('complete');
      expect(state.error).toBeNull();
    });

    it('should process percentage values', () => {
      let state = fsm.createInitialState();
      state = fsm.processToken(state, 'increase');
      state = fsm.processToken(state, 'track');
      state = fsm.processToken(state, '1');
      state = fsm.processToken(state, 'volume');
      state = fsm.processToken(state, '20%');

      expect(state.value).toMatchObject({
        raw: 20,
        unit: '%'
      });
      expect(state.phase).toBe('complete');
      expect(state.error).toBeNull();
    });

    it('should process toggle on/off values', () => {
      let state = fsm.createInitialState();
      state = fsm.processToken(state, 'set');
      state = fsm.processToken(state, 'track');
      state = fsm.processToken(state, '1');
      state = fsm.processToken(state, 'mute');
      state = fsm.processToken(state, 'on');

      expect(state.value).toBe(true);
      expect(state.phase).toBe('complete');
      expect(state.error).toBeNull();
    });

    it('should process toggle off values', () => {
      let state = fsm.createInitialState();
      state = fsm.processToken(state, 'set');
      state = fsm.processToken(state, 'track');
      state = fsm.processToken(state, '1');
      state = fsm.processToken(state, 'mute');
      state = fsm.processToken(state, 'off');

      expect(state.value).toBe(false);
      expect(state.phase).toBe('complete');
      expect(state.error).toBeNull();
    });

    it('should reject invalid values', () => {
      let state = fsm.createInitialState();
      state = fsm.processToken(state, 'set');
      state = fsm.processToken(state, 'track');
      state = fsm.processToken(state, '1');
      state = fsm.processToken(state, 'volume');
      state = fsm.processToken(state, 'invalid');

      expect(state.value).toBeNull();
      expect(state.error).toContain('Invalid value');
    });
  });

  describe('Send Processing', () => {
    it('should process send reference after send parameter', () => {
      let state = fsm.createInitialState();
      state = fsm.processToken(state, 'set');
      state = fsm.processToken(state, 'track');
      state = fsm.processToken(state, '1');
      state = fsm.processToken(state, 'send');
      state = fsm.processToken(state, 'A');

      expect(state.param).toBe('send');
      expect(state.sendRef).toBe('A');
      expect(state.phase).toBe('value');
      expect(state.error).toBeNull();
    });

    it('should process complete send command', () => {
      let state = fsm.createInitialState();
      state = fsm.processToken(state, 'set');
      state = fsm.processToken(state, 'track');
      state = fsm.processToken(state, '1');
      state = fsm.processToken(state, 'send');
      state = fsm.processToken(state, 'A');
      state = fsm.processToken(state, '-12');

      expect(fsm.isComplete(state)).toBe(true);
      expect(state.param).toBe('send');
      expect(state.sendRef).toBe('A');
      expect(state.value.raw).toBe(-12);
    });

    it('should reject invalid send reference', () => {
      let state = fsm.createInitialState();
      state = fsm.processToken(state, 'set');
      state = fsm.processToken(state, 'track');
      state = fsm.processToken(state, '1');
      state = fsm.processToken(state, 'send');
      state = fsm.processToken(state, 'Z');

      expect(state.sendRef).toBeNull();
      expect(state.error).toContain('Invalid send reference');
    });
  });

  describe('Complete Command Flows', () => {
    it('should process: set track 1 volume to -20', () => {
      let state = fsm.createInitialState();
      state = fsm.processToken(state, 'set');
      state = fsm.processToken(state, 'track');
      state = fsm.processToken(state, '1');
      state = fsm.processToken(state, 'volume');
      state = fsm.processToken(state, '-20');

      expect(fsm.isComplete(state)).toBe(true);
      expect(state.action).toBe('set');
      expect(state.targetType).toBe('track');
      expect(state.targetId).toBe(1);
      expect(state.param).toBe('volume');
      expect(state.value.raw).toBe(-20);
    });

    it('should process: increase return A pan by 10', () => {
      let state = fsm.createInitialState();
      state = fsm.processToken(state, 'increase');
      state = fsm.processToken(state, 'return');
      state = fsm.processToken(state, 'A');
      state = fsm.processToken(state, 'pan');
      state = fsm.processToken(state, '10');

      expect(fsm.isComplete(state)).toBe(true);
      expect(state.action).toBe('increase');
      expect(state.targetType).toBe('return');
      expect(state.targetId).toBe('A');
      expect(state.param).toBe('pan');
    });

    it('should process: toggle track 2 mute', () => {
      let state = fsm.createInitialState();
      state = fsm.processToken(state, 'toggle');
      state = fsm.processToken(state, 'track');
      state = fsm.processToken(state, '2');
      state = fsm.processToken(state, 'mute');

      expect(fsm.isComplete(state)).toBe(true);
      expect(state.action).toBe('toggle');
      expect(state.param).toBe('mute');
    });

    it('should process: set master volume to -6', () => {
      let state = fsm.createInitialState();
      state = fsm.processToken(state, 'set');
      state = fsm.processToken(state, 'master');
      state = fsm.processToken(state, 'volume');
      state = fsm.processToken(state, '-6');

      expect(fsm.isComplete(state)).toBe(true);
      expect(state.targetType).toBe('master');
      expect(state.param).toBe('volume');
    });
  });

  describe('Intent Conversion', () => {
    it('should convert track command to intent', () => {
      let state = fsm.createInitialState();
      state = fsm.processToken(state, 'set');
      state = fsm.processToken(state, 'track');
      state = fsm.processToken(state, '1');
      state = fsm.processToken(state, 'volume');
      state = fsm.processToken(state, '-20');

      const intent = fsm.toIntent(state);

      expect(intent).toMatchObject({
        domain: 'track',
        action: 'set',
        field: 'volume',
        track_index: 0, // 0-indexed
        value: -20
      });
    });

    it('should convert return command to intent', () => {
      let state = fsm.createInitialState();
      state = fsm.processToken(state, 'increase');
      state = fsm.processToken(state, 'return');
      state = fsm.processToken(state, 'A');
      state = fsm.processToken(state, 'pan');
      state = fsm.processToken(state, '10');

      const intent = fsm.toIntent(state);

      expect(intent).toMatchObject({
        domain: 'return',
        action: 'increase',
        field: 'pan',
        return_ref: 'A',
        value: 10
      });
    });

    it('should convert master command to intent', () => {
      let state = fsm.createInitialState();
      state = fsm.processToken(state, 'set');
      state = fsm.processToken(state, 'master');
      state = fsm.processToken(state, 'volume');
      state = fsm.processToken(state, '-6');

      const intent = fsm.toIntent(state);

      expect(intent).toMatchObject({
        domain: 'master',
        action: 'set',
        field: 'volume',
        value: -6
      });
    });

    it('should return null for incomplete state', () => {
      let state = fsm.createInitialState();
      state = fsm.processToken(state, 'set');
      state = fsm.processToken(state, 'track');

      const intent = fsm.toIntent(state);
      expect(intent).toBeNull();
    });

    it('should return null for state with errors', () => {
      let state = fsm.createInitialState();
      state = fsm.processToken(state, 'invalid_action');

      const intent = fsm.toIntent(state);
      expect(intent).toBeNull();
    });
  });

  describe('getNextTokens', () => {
    it('should return actions at start', () => {
      const state = fsm.createInitialState();
      const tokens = fsm.getNextTokens(state);

      expect(tokens.length).toBe(4);
      expect(tokens.map(t => t.value)).toEqual(['set', 'increase', 'decrease', 'toggle']);
      expect(tokens[0].type).toBe('action');
      expect(tokens[0].description).toBeTruthy();
    });

    it('should return target types after action', () => {
      let state = fsm.createInitialState();
      state = fsm.processToken(state, 'set');

      const tokens = fsm.getNextTokens(state);

      expect(tokens.length).toBe(3);
      expect(tokens.map(t => t.value)).toEqual(['track', 'return', 'master']);
      expect(tokens[0].type).toBe('target_type');
    });

    it('should return track numbers with context', () => {
      let state = fsm.createInitialState();
      state = fsm.processToken(state, 'set');
      state = fsm.processToken(state, 'track');

      const context = { trackCount: 4, trackNames: ['Drums', 'Bass', 'Keys', 'Vocals'] };
      const tokens = fsm.getNextTokens(state, context);

      expect(tokens.length).toBe(4);
      expect(tokens[0].value).toBe('1');
      expect(tokens[0].display).toBe('Track 1');
      expect(tokens[0].description).toBe('Drums');
    });

    it('should return return letters with context', () => {
      let state = fsm.createInitialState();
      state = fsm.processToken(state, 'set');
      state = fsm.processToken(state, 'return');

      const context = { returnCount: 3, returnNames: ['Reverb', 'Delay', 'Chorus'] };
      const tokens = fsm.getNextTokens(state, context);

      expect(tokens.length).toBe(3);
      expect(tokens[0].value).toBe('A');
      expect(tokens[0].display).toBe('Return A');
      expect(tokens[0].description).toBe('Reverb');
    });

    it('should return parameters after target', () => {
      let state = fsm.createInitialState();
      state = fsm.processToken(state, 'set');
      state = fsm.processToken(state, 'track');
      state = fsm.processToken(state, '1');

      const tokens = fsm.getNextTokens(state);

      expect(tokens.length).toBe(6);
      expect(tokens.map(t => t.value)).toContain('volume');
      expect(tokens.map(t => t.value)).toContain('pan');
      expect(tokens.map(t => t.value)).toContain('mute');
    });

    it('should return value suggestions for volume', () => {
      let state = fsm.createInitialState();
      state = fsm.processToken(state, 'set');
      state = fsm.processToken(state, 'track');
      state = fsm.processToken(state, '1');
      state = fsm.processToken(state, 'volume');

      const tokens = fsm.getNextTokens(state);

      expect(tokens.length).toBeGreaterThan(0);
      expect(tokens[0].type).toBe('value');
      expect(tokens.map(t => t.value)).toContain('0');
      expect(tokens.map(t => t.value)).toContain('-6');
    });

    it('should return empty array for complete state', () => {
      let state = fsm.createInitialState();
      state = fsm.processToken(state, 'set');
      state = fsm.processToken(state, 'track');
      state = fsm.processToken(state, '1');
      state = fsm.processToken(state, 'volume');
      state = fsm.processToken(state, '-20');

      const tokens = fsm.getNextTokens(state);
      expect(tokens.length).toBe(0);
    });
  });

  describe('Edge Cases', () => {
    it('should handle empty tokens gracefully', () => {
      const state = fsm.createInitialState();
      const newState = fsm.processToken(state, '');

      expect(newState.phase).toBe('action');
      expect(newState.error).toBeNull();
    });

    it('should handle whitespace tokens', () => {
      const state = fsm.createInitialState();
      const newState = fsm.processToken(state, '   ');

      expect(newState.phase).toBe('action');
      expect(newState.error).toBeNull();
    });

    it('should handle case-insensitive tokens', () => {
      let state = fsm.createInitialState();
      state = fsm.processToken(state, 'SET');
      state = fsm.processToken(state, 'TRACK');
      state = fsm.processToken(state, '1');
      state = fsm.processToken(state, 'VOLUME');

      expect(state.action).toBe('set');
      expect(state.targetType).toBe('track');
      expect(state.param).toBe('volume');
      expect(state.error).toBeNull();
    });

    it('should ignore tokens after completion', () => {
      let state = fsm.createInitialState();
      state = fsm.processToken(state, 'toggle');
      state = fsm.processToken(state, 'track');
      state = fsm.processToken(state, '1');
      state = fsm.processToken(state, 'mute');

      expect(state.phase).toBe('complete');

      // Try to add more tokens
      state = fsm.processToken(state, 'extra_token');

      expect(state.phase).toBe('complete');
      expect(state.error).toBeNull();
    });
  });
});
