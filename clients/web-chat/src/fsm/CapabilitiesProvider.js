/**
 * CapabilitiesProvider - Fetches and transforms Ableton Live session capabilities
 *
 * Provides session context for the FSM (track count, return count, etc.)
 * Pure data layer with no UI dependencies.
 *
 * Examples:
 *   const provider = new CapabilitiesProvider('/api');
 *   const context = await provider.getContext();
 *   // => { trackCount: 8, returnCount: 4, tracks: [...], returns: [...] }
 */

export class CapabilitiesProvider {
  /**
   * @param {string} apiBaseUrl - Base URL for API requests (e.g., 'http://localhost:8722')
   */
  constructor(apiBaseUrl = 'http://localhost:8722') {
    this.apiBaseUrl = apiBaseUrl;
    this._cache = null;
    this._cacheTimestamp = 0;
    this.cacheTTL = 5000; // 5 seconds default TTL
  }

  /**
   * Get FSM context from snapshot data
   * @param {boolean} forceRefresh - Skip cache and force fresh fetch
   * @returns {Promise<Object>} - FSM context with trackCount, returnCount, etc.
   */
  async getContext(forceRefresh = false) {
    const now = Date.now();
    const cacheAge = now - this._cacheTimestamp;

    // Return cached data if fresh enough
    if (!forceRefresh && this._cache && cacheAge < this.cacheTTL) {
      return this._cache;
    }

    // Fetch fresh snapshot
    try {
      const snapshot = await this._fetchSnapshot(forceRefresh);

      // Transform to FSM context format
      const context = {
        trackCount: snapshot.track_count || 0,
        returnCount: snapshot.return_count || 0,
        tracks: snapshot.tracks || [],
        returns: snapshot.returns || [],
        master: snapshot.master || { name: 'Master', devices: [] },
        timestamp: now,
      };

      // Cache the result
      this._cache = context;
      this._cacheTimestamp = now;

      return context;
    } catch (error) {
      console.error('CapabilitiesProvider: Failed to fetch context', error);

      // Return cached data if available, otherwise minimal fallback
      if (this._cache) {
        return this._cache;
      }

      return {
        trackCount: 0,
        returnCount: 0,
        tracks: [],
        returns: [],
        master: { name: 'Master', devices: [] },
        timestamp: now,
      };
    }
  }

  /**
   * Get track names (for autocomplete)
   * @returns {Promise<string[]>} - Array of track names
   */
  async getTrackNames() {
    const context = await this.getContext();
    return context.tracks.map(track => track.name || `Track ${track.index + 1}`);
  }

  /**
   * Get return names (for autocomplete)
   * @returns {Promise<string[]>} - Array of return names
   */
  async getReturnNames() {
    const context = await this.getContext();
    return context.returns.map(ret => ret.name || `Return ${String.fromCharCode(65 + ret.index)}`);
  }

  /**
   * Get device names for a track
   * @param {number} trackIndex - Track index (0-based)
   * @returns {Promise<string[]>} - Array of device names
   */
  async getTrackDeviceNames(trackIndex) {
    const context = await this.getContext();
    const track = context.tracks.find(t => t.index === trackIndex);

    if (!track || !track.devices) {
      return [];
    }

    return track.devices.map(dev => dev.name || `Device ${dev.index}`);
  }

  /**
   * Get device names for a return
   * @param {number} returnIndex - Return index (0-based)
   * @returns {Promise<string[]>} - Array of device names
   */
  async getReturnDeviceNames(returnIndex) {
    const context = await this.getContext();
    const ret = context.returns.find(r => r.index === returnIndex);

    if (!ret || !ret.devices) {
      return [];
    }

    return ret.devices.map(dev => dev.name || `Device ${dev.index}`);
  }

  /**
   * Invalidate cache to force refresh on next request
   */
  invalidateCache() {
    this._cache = null;
    this._cacheTimestamp = 0;
  }

  /**
   * Set cache TTL in milliseconds
   * @param {number} ttl - Time to live in milliseconds
   */
  setCacheTTL(ttl) {
    this.cacheTTL = Math.max(0, ttl);
  }

  /**
   * Fetch snapshot from backend
   * @param {boolean} forceRefresh - Force backend to refresh its cache
   * @returns {Promise<Object>} - Snapshot data
   * @private
   */
  async _fetchSnapshot(forceRefresh = false) {
    const url = `${this.apiBaseUrl}/snapshot${forceRefresh ? '?force_refresh=true' : ''}`;

    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`Snapshot fetch failed: ${response.status} ${response.statusText}`);
    }

    const data = await response.json();

    if (!data.ok) {
      throw new Error('Snapshot returned error status');
    }

    return data;
  }

  /**
   * Check if capabilities are available
   * @returns {Promise<boolean>} - True if snapshot endpoint is accessible
   */
  async isAvailable() {
    try {
      await this._fetchSnapshot(false);
      return true;
    } catch (error) {
      return false;
    }
  }
}

export default CapabilitiesProvider;
