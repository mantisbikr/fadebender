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
// Empirical mapping captured from Live in 3 dB steps
// Format: [dB, float]
const VOLUME_MAP = [
  [-70, 0.0],
  [-63, 0.021345632150769234],
  [-60, 0.03462362661957741],
  [-57, 0.05101150646805763],
  [-54, 0.06778648495674133],
  [-51, 0.08523604273796082],
  [-48, 0.10353590548038483],
  [-45, 0.12271705269813538],
  [-42, 0.1428816020488739],
  [-39, 0.16421939432621002],
  [-36, 0.18703696131706238],
  [-33, 0.2116302251815796],
  [-30, 0.23843887448310852],
  [-27, 0.2682555615901947],
  [-24, 0.302414208650589],
  [-21, 0.3436638116836548],
  [-18, 0.39999979734420776],
  [-15, 0.47494229674339294],
  [-12, 0.5499998927116394],
  [-9, 0.624942421913147],
  [-6, 0.699999988079071],
  [-3, 0.7749424576759338],
  [0, 0.8500000238418579],
  [3, 0.9249424338340759],
  [6, 1.0],
];

function interp(y, pts) {
  if (!pts || pts.length === 0) return 0;
  if (y <= pts[0][0]) return pts[0][1];
  if (y >= pts[pts.length - 1][0]) return pts[pts.length - 1][1];
  let lo = 0, hi = pts.length - 1;
  while (lo <= hi) {
    const mid = (lo + hi) >> 1;
    if (pts[mid][0] < y) lo = mid + 1; else hi = mid - 1;
  }
  const i1 = Math.max(0, hi);
  const i2 = Math.min(pts.length - 1, lo);
  const [x1, y1] = pts[i1];
  const [x2, y2] = pts[i2];
  if (x2 === x1) return y1;
  const t = (y - x1) / (x2 - x1);
  return y1 + t * (y2 - y1);
}

export function dbToLiveFloat(dbValue) {
  const dbClamped = Math.max(-60.0, Math.min(6.0, parseFloat(dbValue)));
  // Interpolate from empirical map
  return Math.max(0.0, Math.min(1.0, interp(dbClamped, VOLUME_MAP)));
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
  const floatClamped = Math.max(0.0, Math.min(1.0, parseFloat(floatValue)));
  if (floatClamped <= 0.001) return -60.0;
  // Build inverse points (float, db) once
  if (!liveFloatToDb._inv) {
    liveFloatToDb._inv = VOLUME_MAP.map(([db, f]) => [f, db]).sort((a, b) => a[0] - b[0]);
  }
  const inv = liveFloatToDb._inv;
  return Math.max(-60.0, Math.min(6.0, interp(floatClamped, inv)));
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
