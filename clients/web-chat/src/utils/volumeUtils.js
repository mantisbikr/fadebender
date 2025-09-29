/**
 * Volume conversion utilities for Ableton Live API.
 *
 * Ableton Live uses a custom logarithmic curve where:
 * - 0 dB corresponds to float value ~0.85 (not 1.0)
 * - The relationship is approximately linear: X ≈ 0.85 - (0.025 × |dB_target|)
 */

/**
 * Convert dB value to Ableton Live API float value (0.0 to 1.0).
 *
 * Formula: X ≈ 0.85 - (0.025 × |dB_target|)
 *
 * @param {number} dbValue - dB value (typically -60 to +6)
 * @returns {number} Float value for Live API (0.0 to 1.0)
 */
export function dbToLiveFloat(dbValue) {
  // Clamp dB to valid range
  const dbClamped = Math.max(-60.0, Math.min(6.0, parseFloat(dbValue)));

  // Apply the formula: X ≈ 0.85 - (0.025 × |dB_target|)
  const floatValue = 0.85 - (0.025 * Math.abs(dbClamped));

  // Clamp to valid Live range
  return Math.max(0.0, Math.min(1.0, floatValue));
}

/**
 * Convert Ableton Live API float value (0.0 to 1.0) to dB.
 *
 * Inverse formula: dB ≈ -(0.85 - X) / 0.025
 *
 * @param {number} floatValue - Live API float value (0.0 to 1.0)
 * @returns {number} dB value (typically -60 to +6)
 */
export function liveFloatToDb(floatValue) {
  // Clamp float to valid range
  const floatClamped = Math.max(0.0, Math.min(1.0, parseFloat(floatValue)));

  // Handle special case for very low values (essentially -infinity dB)
  if (floatClamped <= 0.001) {
    return -60.0;
  }

  // Apply inverse formula: dB = -(0.85 - X) / 0.025
  // This gives us negative dB values as expected
  const dbValue = -(0.85 - floatClamped) / 0.025;

  // Clamp to reasonable dB range
  return Math.max(-60.0, Math.min(6.0, dbValue));
}

/**
 * Safely compute dB from a track status object.
 * Prefers normalized mixer volume when available; falls back to status.volume_db.
 * Returns number | null
 */
export function dbFromStatus(status) {
  try {
    if (!status) return null;
    const v = status?.mixer && typeof status.mixer.volume === 'number' ? Number(status.mixer.volume) : null;
    if (v != null) return liveFloatToDb(v);
    const vdb = status?.volume_db;
    if (typeof vdb === 'number' && Number.isFinite(vdb)) return Number(vdb);
    return null;
  } catch {
    return null;
  }
}

/**
 * Build a human pan label (e.g., '25L', '10R', or '' when unknown) from status.
 */
export function panLabelFromStatus(status) {
  try {
    if (!status) return '';
    const p = status?.mixer?.pan;
    if (p == null) return '';
    const amt = Math.round(Math.abs(Number(p)) * 50);
    return `${amt}${p < 0 ? 'L' : (p > 0 ? 'R' : '')}`;
  } catch {
    return '';
  }
}
