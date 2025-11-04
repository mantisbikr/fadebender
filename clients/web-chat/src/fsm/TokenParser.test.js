/**
 * TokenParser Tests - Comprehensive test suite for token parsing and shortcut expansion
 */

import { describe, it, expect, beforeEach } from 'vitest';
import TokenParser from './TokenParser.js';

describe('TokenParser', () => {
  let parser;

  beforeEach(() => {
    parser = new TokenParser();
  });

  describe('Basic Parsing', () => {
    it('should parse simple input', () => {
      const tokens = parser.parse('set track 1 volume -20');

      expect(tokens).toHaveLength(5);
      expect(tokens.map(t => t.expanded)).toEqual(['set', 'track', '1', 'volume', '-20']);
    });

    it('should handle empty input', () => {
      expect(parser.parse('')).toEqual([]);
      expect(parser.parse(null)).toEqual([]);
      expect(parser.parse(undefined)).toEqual([]);
    });

    it('should handle extra whitespace', () => {
      const tokens = parser.parse('  set   track    1  ');

      expect(tokens).toHaveLength(3);
      expect(tokens.map(t => t.expanded)).toEqual(['set', 'track', '1']);
    });

    it('should skip stop words', () => {
      const tokens = parser.parse('set track 1 volume to -20');

      expect(tokens.map(t => t.expanded)).not.toContain('to');
      expect(tokens.map(t => t.expanded)).toEqual(['set', 'track', '1', 'volume', '-20']);
    });

    it('should maintain token positions', () => {
      const tokens = parser.parse('set track 1');

      expect(tokens[0].position).toBe(0);
      expect(tokens[1].position).toBe(1);
      expect(tokens[2].position).toBe(2);
    });
  });

  describe('Action Shortcuts', () => {
    it('should expand action shortcuts (no ambiguous single letters)', () => {
      expect(parser.expandShortcut('set')).toBe('set');
      expect(parser.expandShortcut('inc')).toBe('increase');
      expect(parser.expandShortcut('dec')).toBe('decrease');
      expect(parser.expandShortcut('tog')).toBe('toggle');
    });

    it('should handle action shortcuts case-insensitively', () => {
      expect(parser.expandShortcut('SET')).toBe('set');
      expect(parser.expandShortcut('INC')).toBe('increase');
      expect(parser.expandShortcut('Dec')).toBe('decrease');
    });
  });

  describe('Target Shortcuts', () => {
    it('should expand track shortcuts', () => {
      expect(parser.expandShortcut('trk')).toBe('track');
      expect(parser.expandShortcut('track')).toBe('track');
    });

    it('should expand return shortcuts', () => {
      expect(parser.expandShortcut('ret')).toBe('return');
      expect(parser.expandShortcut('return')).toBe('return');
    });

    it('should expand master shortcuts', () => {
      expect(parser.expandShortcut('mst')).toBe('master');
      expect(parser.expandShortcut('master')).toBe('master');
    });
  });

  describe('Parameter Shortcuts', () => {
    it('should expand volume shortcuts', () => {
      expect(parser.expandShortcut('v')).toBe('volume');
      expect(parser.expandShortcut('vol')).toBe('volume');
      expect(parser.expandShortcut('volume')).toBe('volume');
    });

    it('should expand pan shortcuts', () => {
      expect(parser.expandShortcut('p')).toBe('pan');
      expect(parser.expandShortcut('pan')).toBe('pan');
    });

    it('should expand cue shortcut', () => {
      expect(parser.expandShortcut('c')).toBe('cue');
      expect(parser.expandShortcut('mute')).toBe('mute');
      expect(parser.expandShortcut('solo')).toBe('solo');
    });
  });

  describe('Combined Shortcuts', () => {
    it('should expand track shortcuts (t1, t2, etc.)', () => {
      const tokens1 = parser.parse('t1');
      expect(tokens1.map(t => t.expanded)).toEqual(['track', '1']);

      const tokens2 = parser.parse('t99');
      expect(tokens2.map(t => t.expanded)).toEqual(['track', '99']);
    });

    it('should expand return shortcuts (ra, rb, etc.)', () => {
      const tokens1 = parser.parse('ra');
      expect(tokens1.map(t => t.expanded)).toEqual(['return', 'A']);

      const tokens2 = parser.parse('rl');
      expect(tokens2.map(t => t.expanded)).toEqual(['return', 'L']);
    });

    it('should handle return number shortcuts (r0 → return A)', () => {
      const tokens1 = parser.parse('r0');
      expect(tokens1.map(t => t.expanded)).toEqual(['return', 'A']);

      const tokens2 = parser.parse('r11');
      expect(tokens2.map(t => t.expanded)).toEqual(['return', 'L']);
    });

    it('should handle combined shortcuts case-insensitively', () => {
      const tokens1 = parser.parse('T1');
      expect(tokens1.map(t => t.expanded)).toEqual(['track', '1']);

      const tokens2 = parser.parse('RA');
      expect(tokens2.map(t => t.expanded)).toEqual(['return', 'A']);
    });

    it('should not expand ambiguous shortcuts (m1, s1, d1)', () => {
      // m1 could be master 1 or mute 1, so don't expand
      const tokens = parser.parse('m1');
      expect(tokens).toHaveLength(1);
      expect(tokens[0].expanded).toBe('m1');
    });
  });

  describe('Full Command Parsing', () => {
    it('should parse: set track 1 volume -20', () => {
      const tokens = parser.parse('set track 1 volume -20');
      expect(tokens.map(t => t.expanded)).toEqual(['set', 'track', '1', 'volume', '-20']);
    });

    it('should parse: set t1 v -20', () => {
      const tokens = parser.parse('set t1 v -20');
      expect(tokens.map(t => t.expanded)).toEqual(['set', 'track', '1', 'volume', '-20']);
    });

    it('should parse: inc ra pan 10', () => {
      const tokens = parser.parse('inc ra pan 10');
      expect(tokens.map(t => t.expanded)).toEqual(['increase', 'return', 'A', 'pan', '10']);
    });

    it('should parse: tog t2 mute', () => {
      const tokens = parser.parse('tog t2 mute');
      expect(tokens.map(t => t.expanded)).toEqual(['toggle', 'track', '2', 'mute']);
    });

    it('should parse: set master volume -6db', () => {
      const tokens = parser.parse('set master volume -6db');
      expect(tokens.map(t => t.expanded)).toEqual(['set', 'master', 'volume', '-6db']);
    });
  });

  describe('parseToStrings', () => {
    it('should return array of expanded strings', () => {
      const strings = parser.parseToStrings('set t1 v -20');
      expect(strings).toEqual(['set', 'track', '1', 'volume', '-20']);
    });

    it('should handle empty input', () => {
      expect(parser.parseToStrings('')).toEqual([]);
    });
  });

  describe('detectType', () => {
    it('should detect action tokens', () => {
      expect(parser.detectType('set')).toBe('action');
      expect(parser.detectType('increase')).toBe('action');
      expect(parser.detectType('inc')).toBe('action');
      expect(parser.detectType('tog')).toBe('action');
    });

    it('should detect target type tokens', () => {
      expect(parser.detectType('track')).toBe('target_type');
      expect(parser.detectType('return')).toBe('target_type');
      expect(parser.detectType('master')).toBe('target_type');
      expect(parser.detectType('trk')).toBe('target_type');
    });

    it('should detect parameter tokens', () => {
      expect(parser.detectType('volume')).toBe('param');
      expect(parser.detectType('pan')).toBe('param');
      expect(parser.detectType('v')).toBe('param');
      expect(parser.detectType('p')).toBe('param');
    });

    it('should detect track ID with context', () => {
      const context = { previousTokens: ['set', 'track'] };
      expect(parser.detectType('1', context)).toBe('target_id');
      expect(parser.detectType('99', context)).toBe('target_id');
    });

    it('should detect return ID with context', () => {
      const context = { previousTokens: ['set', 'return'] };
      expect(parser.detectType('A', context)).toBe('target_id');
      expect(parser.detectType('l', context)).toBe('target_id');
    });

    it('should detect numeric values', () => {
      expect(parser.detectType('-20')).toBe('value');
      expect(parser.detectType('10.5')).toBe('value');
      expect(parser.detectType('50%')).toBe('value');
      expect(parser.detectType('-6db')).toBe('value');
      expect(parser.detectType('-6dB')).toBe('value');
    });

    it('should detect boolean values', () => {
      expect(parser.detectType('on')).toBe('value');
      expect(parser.detectType('off')).toBe('value');
      expect(parser.detectType('true')).toBe('value');
      expect(parser.detectType('false')).toBe('value');
      expect(parser.detectType('1')).toBe('value');
      expect(parser.detectType('0')).toBe('value');
    });

    it('should return unknown for unrecognized tokens', () => {
      expect(parser.detectType('xyz')).toBe('unknown');
      expect(parser.detectType('foobar')).toBe('unknown');
    });
  });

  describe('Custom Shortcuts', () => {
    it('should add custom action shortcuts', () => {
      parser.addShortcut('action', 'a', 'adjust');
      expect(parser.expandShortcut('a')).toBe('adjust');
    });

    it('should add custom target shortcuts', () => {
      parser.addShortcut('target', 'g', 'group');
      expect(parser.expandShortcut('g')).toBe('group');
    });

    it('should add custom parameter shortcuts', () => {
      parser.addShortcut('param', 'f', 'frequency');
      expect(parser.expandShortcut('f')).toBe('frequency');
    });

    it('should get shortcuts by category', () => {
      const actionShortcuts = parser.getShortcuts('action');
      expect(actionShortcuts).toHaveProperty('set');
      expect(actionShortcuts.set).toBe('set');

      const targetShortcuts = parser.getShortcuts('target');
      expect(targetShortcuts).toHaveProperty('track');

      const paramShortcuts = parser.getShortcuts('param');
      expect(paramShortcuts).toHaveProperty('volume');
    });
  });

  describe('Edge Cases', () => {
    it('should handle tokens with mixed case', () => {
      const tokens = parser.parse('SET Track 1 Volume -20');
      expect(tokens.map(t => t.expanded)).toEqual(['set', 'track', '1', 'volume', '-20']);
    });

    it('should handle tabs and newlines', () => {
      const tokens = parser.parse('set\ttrack\n1\rvolume');
      expect(tokens.map(t => t.expanded)).toEqual(['set', 'track', '1', 'volume']);
    });

    it('should preserve original token in Token object', () => {
      const tokens = parser.parse('inc t1');

      expect(tokens[0].original).toBe('inc');
      expect(tokens[0].expanded).toBe('increase');

      // Combined shortcut: original is the full "t1" for first token
      expect(tokens[1].original).toBe('t1');
      expect(tokens[1].expanded).toBe('track');
    });

    it('should not expand invalid combined shortcuts', () => {
      const tokens = parser.parse('t0'); // Track 0 is invalid
      expect(tokens).toHaveLength(1);
      expect(tokens[0].expanded).toBe('t0');
    });

    it('should not expand ambiguous shortcuts', () => {
      const tokens = parser.parse('m1'); // Could be master 1 or mute 1
      expect(tokens).toHaveLength(1);
      expect(tokens[0].expanded).toBe('m1');
    });
  });

  describe('Real-World Examples', () => {
    it('should parse short command: set t1 v -20', () => {
      const tokens = parser.parseToStrings('set t1 v -20');
      expect(tokens).toEqual(['set', 'track', '1', 'volume', '-20']);
    });

    it('should parse medium command: inc ra pan by 10', () => {
      const tokens = parser.parseToStrings('inc ra pan by 10');
      expect(tokens).toEqual(['increase', 'return', 'A', 'pan', '10']); // 'by' is stop word
    });

    it('should parse verbose command: set track 12 volume to -6 dB', () => {
      const tokens = parser.parseToStrings('set track 12 volume to -6db');
      expect(tokens).toEqual(['set', 'track', '12', 'volume', '-6db']); // 'to' is stop word
    });

    it('should parse toggle command: tog t5 mute', () => {
      const tokens = parser.parseToStrings('tog t5 mute');
      expect(tokens).toEqual(['toggle', 'track', '5', 'mute']);
    });

    it('should parse master command: set master cue -12', () => {
      const tokens = parser.parseToStrings('set master cue -12');
      expect(tokens).toEqual(['set', 'master', 'cue', '-12']);
    });

    it('should parse percentage command: increase t3 volume by 20%', () => {
      const tokens = parser.parseToStrings('increase t3 volume by 20%');
      expect(tokens).toEqual(['increase', 'track', '3', 'volume', '20%']);
    });
  });
});
