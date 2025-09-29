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