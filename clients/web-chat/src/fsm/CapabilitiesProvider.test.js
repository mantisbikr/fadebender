/**
 * CapabilitiesProvider Tests - Comprehensive test suite for capabilities fetching
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import CapabilitiesProvider from './CapabilitiesProvider.js';

// Mock fetch globally
global.fetch = vi.fn();

describe('CapabilitiesProvider', () => {
  let provider;
  let mockSnapshot;

  beforeEach(() => {
    provider = new CapabilitiesProvider('http://localhost:8722');

    // Mock snapshot response
    mockSnapshot = {
      ok: true,
      track_count: 3,
      return_count: 2,
      tracks: [
        { index: 0, name: 'Track 1', type: 'audio', devices: [{ index: 0, name: 'Reverb' }] },
        { index: 1, name: 'Track 2', type: 'audio', devices: [] },
        { index: 2, name: 'Drums', type: 'audio', devices: [{ index: 0, name: 'Compressor' }, { index: 1, name: 'EQ' }] },
      ],
      returns: [
        { index: 0, name: 'A-Reverb', devices: [{ index: 0, name: 'Reverb' }] },
        { index: 1, name: 'B-Delay', devices: [{ index: 0, name: 'Delay' }] },
      ],
      master: {
        name: 'Master',
        devices: [{ index: 0, name: 'Limiter' }],
      },
    };

    // Reset mock
    fetch.mockReset();
  });

  describe('Basic Functionality', () => {
    it('should create provider with default URL', () => {
      const p = new CapabilitiesProvider();
      expect(p).toBeDefined();
      expect(p.apiBaseUrl).toBe('http://localhost:8722');
    });

    it('should create provider with custom URL', () => {
      const p = new CapabilitiesProvider('http://example.com:8080');
      expect(p.apiBaseUrl).toBe('http://example.com:8080');
    });

    it('should have default cache TTL', () => {
      expect(provider.cacheTTL).toBe(5000);
    });
  });

  describe('Context Fetching', () => {
    it('should fetch and transform context', async () => {
      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockSnapshot,
      });

      const context = await provider.getContext();

      expect(context).toMatchObject({
        trackCount: 3,
        returnCount: 2,
      });

      expect(context.tracks).toHaveLength(3);
      expect(context.returns).toHaveLength(2);
      expect(context.master).toBeDefined();
      expect(context.timestamp).toBeGreaterThan(0);
    });

    it('should call correct API endpoint', async () => {
      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockSnapshot,
      });

      await provider.getContext();

      expect(fetch).toHaveBeenCalledWith(
        'http://localhost:8722/snapshot',
        expect.objectContaining({
          method: 'GET',
          headers: { 'Content-Type': 'application/json' },
        })
      );
    });

    it('should include force_refresh query param when requested', async () => {
      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockSnapshot,
      });

      await provider.getContext(true);

      expect(fetch).toHaveBeenCalledWith(
        'http://localhost:8722/snapshot?force_refresh=true',
        expect.any(Object)
      );
    });
  });

  describe('Caching', () => {
    it('should cache context on first fetch', async () => {
      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockSnapshot,
      });

      const context1 = await provider.getContext();
      const context2 = await provider.getContext();

      // Should only call fetch once
      expect(fetch).toHaveBeenCalledTimes(1);

      // Should return same cached object
      expect(context1).toBe(context2);
    });

    it('should refetch when cache expires', async () => {
      provider.setCacheTTL(100); // 100ms TTL

      fetch.mockResolvedValue({
        ok: true,
        json: async () => mockSnapshot,
      });

      await provider.getContext();

      // Wait for cache to expire
      await new Promise(resolve => setTimeout(resolve, 150));

      await provider.getContext();

      // Should have called fetch twice
      expect(fetch).toHaveBeenCalledTimes(2);
    });

    it('should skip cache when forceRefresh is true', async () => {
      fetch.mockResolvedValue({
        ok: true,
        json: async () => mockSnapshot,
      });

      await provider.getContext();
      await provider.getContext(true); // Force refresh

      // Should call fetch twice
      expect(fetch).toHaveBeenCalledTimes(2);
    });

    it('should invalidate cache manually', async () => {
      fetch.mockResolvedValue({
        ok: true,
        json: async () => mockSnapshot,
      });

      await provider.getContext();
      provider.invalidateCache();
      await provider.getContext();

      // Should call fetch twice
      expect(fetch).toHaveBeenCalledTimes(2);
    });

    it('should allow setting cache TTL', () => {
      provider.setCacheTTL(10000);
      expect(provider.cacheTTL).toBe(10000);

      provider.setCacheTTL(-500); // Should clamp to 0
      expect(provider.cacheTTL).toBe(0);
    });
  });

  describe('Error Handling', () => {
    it('should handle network errors gracefully', async () => {
      fetch.mockRejectedValueOnce(new Error('Network error'));

      const context = await provider.getContext();

      // Should return fallback context
      expect(context).toMatchObject({
        trackCount: 0,
        returnCount: 0,
        tracks: [],
        returns: [],
      });
    });

    it('should handle HTTP errors', async () => {
      fetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
        statusText: 'Internal Server Error',
      });

      const context = await provider.getContext();

      // Should return fallback context
      expect(context).toMatchObject({
        trackCount: 0,
        returnCount: 0,
      });
    });

    it('should handle invalid JSON', async () => {
      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => { throw new Error('Invalid JSON'); },
      });

      const context = await provider.getContext();

      // Should return fallback context
      expect(context).toMatchObject({
        trackCount: 0,
        returnCount: 0,
      });
    });

    it('should use cached data on subsequent errors', async () => {
      // First call succeeds
      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockSnapshot,
      });

      const context1 = await provider.getContext();
      expect(context1.trackCount).toBe(3);

      // Second call fails but cache is still valid (within TTL)
      fetch.mockRejectedValueOnce(new Error('Network error'));

      const context2 = await provider.getContext();
      expect(context2.trackCount).toBe(3); // From cache

      // If cache is invalidated and fetch fails, should get fallback
      provider.invalidateCache();
      fetch.mockRejectedValueOnce(new Error('Network error'));

      const context3 = await provider.getContext();
      expect(context3.trackCount).toBe(0); // Fallback, no cache available
    });

    it('should handle snapshot with ok:false', async () => {
      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ ok: false }),
      });

      const context = await provider.getContext();

      // Should return fallback context
      expect(context).toMatchObject({
        trackCount: 0,
        returnCount: 0,
      });
    });
  });

  describe('Track Names', () => {
    it('should get track names', async () => {
      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockSnapshot,
      });

      const names = await provider.getTrackNames();

      expect(names).toEqual(['Track 1', 'Track 2', 'Drums']);
    });

    it('should generate default names for unnamed tracks', async () => {
      const modifiedSnapshot = {
        ...mockSnapshot,
        tracks: [{ index: 0, type: 'audio' }], // No name
      };

      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => modifiedSnapshot,
      });

      const names = await provider.getTrackNames();

      expect(names).toEqual(['Track 1']);
    });
  });

  describe('Return Names', () => {
    it('should get return names', async () => {
      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockSnapshot,
      });

      const names = await provider.getReturnNames();

      expect(names).toEqual(['A-Reverb', 'B-Delay']);
    });

    it('should generate default names for unnamed returns', async () => {
      const modifiedSnapshot = {
        ...mockSnapshot,
        returns: [{ index: 0 }, { index: 1 }], // No names
      };

      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => modifiedSnapshot,
      });

      const names = await provider.getReturnNames();

      expect(names).toEqual(['Return A', 'Return B']);
    });
  });

  describe('Device Names', () => {
    it('should get track device names', async () => {
      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockSnapshot,
      });

      const devices = await provider.getTrackDeviceNames(2); // Drums track

      expect(devices).toEqual(['Compressor', 'EQ']);
    });

    it('should return empty array for track with no devices', async () => {
      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockSnapshot,
      });

      const devices = await provider.getTrackDeviceNames(1); // Track 2 has no devices

      expect(devices).toEqual([]);
    });

    it('should return empty array for nonexistent track', async () => {
      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockSnapshot,
      });

      const devices = await provider.getTrackDeviceNames(99);

      expect(devices).toEqual([]);
    });

    it('should get return device names', async () => {
      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockSnapshot,
      });

      const devices = await provider.getReturnDeviceNames(0); // A-Reverb

      expect(devices).toEqual(['Reverb']);
    });

    it('should return empty array for return with no devices', async () => {
      const modifiedSnapshot = {
        ...mockSnapshot,
        returns: [{ index: 0, name: 'Empty', devices: [] }],
      };

      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => modifiedSnapshot,
      });

      const devices = await provider.getReturnDeviceNames(0);

      expect(devices).toEqual([]);
    });

    it('should return empty array for nonexistent return', async () => {
      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockSnapshot,
      });

      const devices = await provider.getReturnDeviceNames(99);

      expect(devices).toEqual([]);
    });

    it('should generate default device names', async () => {
      const modifiedSnapshot = {
        ...mockSnapshot,
        tracks: [
          { index: 0, name: 'Track 1', devices: [{ index: 0 }] }, // No name
        ],
      };

      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => modifiedSnapshot,
      });

      const devices = await provider.getTrackDeviceNames(0);

      expect(devices).toEqual(['Device 0']);
    });
  });

  describe('Availability Check', () => {
    it('should return true when snapshot is accessible', async () => {
      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockSnapshot,
      });

      const available = await provider.isAvailable();

      expect(available).toBe(true);
    });

    it('should return false when snapshot fails', async () => {
      fetch.mockRejectedValueOnce(new Error('Network error'));

      const available = await provider.isAvailable();

      expect(available).toBe(false);
    });

    it('should return false when HTTP error', async () => {
      fetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
      });

      const available = await provider.isAvailable();

      expect(available).toBe(false);
    });
  });

  describe('Real-World Scenarios', () => {
    it('should handle typical session with multiple tracks and returns', async () => {
      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockSnapshot,
      });

      const context = await provider.getContext();

      expect(context.trackCount).toBe(3);
      expect(context.returnCount).toBe(2);
      expect(context.tracks[2].name).toBe('Drums');
      expect(context.returns[1].name).toBe('B-Delay');
    });

    it('should handle empty session', async () => {
      const emptySnapshot = {
        ok: true,
        track_count: 0,
        return_count: 0,
        tracks: [],
        returns: [],
        master: { name: 'Master', devices: [] },
      };

      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => emptySnapshot,
      });

      const context = await provider.getContext();

      expect(context.trackCount).toBe(0);
      expect(context.returnCount).toBe(0);
    });

    it('should reuse cached data for sequential component queries', async () => {
      fetch.mockResolvedValue({
        ok: true,
        json: async () => mockSnapshot,
      });

      // First query fetches data
      const context1 = await provider.getContext();
      expect(context1.trackCount).toBe(3);

      // Subsequent queries use cache
      const names1 = await provider.getTrackNames();
      const names2 = await provider.getReturnNames();
      const devices1 = await provider.getTrackDeviceNames(0);

      // Should only fetch once (first call)
      expect(fetch).toHaveBeenCalledTimes(1);

      expect(names1).toHaveLength(3);
      expect(names2).toHaveLength(2);
      expect(devices1).toHaveLength(1);
    });
  });
});
