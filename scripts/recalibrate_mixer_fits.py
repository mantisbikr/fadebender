#!/usr/bin/env python3
"""
Recalibrate mixer fits (track/return volume and sends) to match the piecewise mapping.

This script:
 1) Loads the measured piecewise mapping via fadebender_lom.volume (Firestore DB: 'dev-display-value')
 2) Fits a simple power-law model in dB space to match the piecewise curve
 3) Writes the fitted coefficients back into the SAME 'dev-display-value' Firestore database:
      mixer_mappings/track_channel.params_meta[name='volume'|'send'].fit
      mixer_mappings/return_channel.params_meta[name='volume'|'send'].fit

Prereqs:
  - pip install google-cloud-firestore
  - Ensure credentials for Firestore 'dev-display-value' database are available

Notes:
  - Volume and send ranges are auto-detected from the piecewise data
  - Gamma is fitted by least-squares in log domain keeping min/max fixed
  - Both reads and writes use the 'dev-display-value' database (single source of truth)
"""
from __future__ import annotations

import math
import sys
from dataclasses import dataclass
from typing import List, Tuple, Optional, Dict, Any


# --- Load piecewise mapping using shared module (loads from dev-display-value) ---
def load_piecewise_points(kind: str) -> List[Tuple[float, float]]:
    """Return list of (db, float) pairs for 'volume' or 'send'."""
    try:
        from fadebender_lom import volume as vol
    except Exception as e:
        print("ERROR: failed to import fadebender_lom.volume.\n"
              "Install dependencies and ensure Firestore access for dev-display-value.", file=sys.stderr)
        raise

    # Trigger load
    try:
        getattr(vol, "_try_load_mapping")()
    except Exception as e:
        print(f"ERROR: failed to load piecewise mapping: {e}", file=sys.stderr)
        raise

    pts: List[Tuple[float, float]] = []
    if kind == "volume":
        # Prefer the native piecewise if loaded; if not, synthesize from function
        arr = getattr(vol, "_MAP_DB2F", [])
        if arr:
            pts = [(float(d), float(f)) for d, f in arr]
        else:
            # Synthesize by sampling
            for d in range(-60, 7):
                try:
                    f = float(vol.db_to_live_float(float(d)))
                    pts.append((float(d), f))
                except Exception:
                    continue
    elif kind == "send":
        arr = getattr(vol, "_SEND_MAP_DB2F", [])
        if arr:
            pts = [(float(d), float(f)) for d, f in arr]
        else:
            # Synthesize from send converter
            for d in range(-60, 1):
                try:
                    f = float(vol.db_to_live_float_send(float(d)))
                    pts.append((float(d), f))
                except Exception:
                    continue
    else:
        raise ValueError("kind must be 'volume' or 'send'")

    if not pts:
        raise RuntimeError(f"No piecewise points available for {kind}")
    return pts


@dataclass
class PowerFit:
    min_db: float
    max_db: float
    gamma: float

    def to_dict(self) -> Dict[str, Any]:
        rng = float(self.max_db - self.min_db)
        return {
            "type": "power",
            "coeffs": {
                "min_db": float(self.min_db),
                "max_db": float(self.max_db),
                "range_db": rng,
                "gamma": float(self.gamma),
            }
        }


def fit_power_from_points(points: List[Tuple[float, float]], min_db: float, max_db: float) -> PowerFit:
    """Fit gamma for power law: norm = ((db - min_db)/range_db) ** gamma.

    Uses least squares in log space while discarding endpoints.
    """
    rng = float(max_db - min_db)
    xs: List[float] = []
    ys: List[float] = []
    for db, n in points:
        try:
            y = (float(db) - min_db) / rng
            if y <= 1e-6 or y >= 1.0 - 1e-6:
                continue
            if n <= 0.0 or n >= 1.0:
                continue
            xs.append(math.log(y))
            ys.append(math.log(n))
        except Exception:
            continue
    if not xs or not ys or len(xs) != len(ys):
        raise RuntimeError("Insufficient points to fit gamma")
    # Least squares: ys ≈ gamma * xs
    num = sum(x*y for x, y in zip(xs, ys))
    den = sum(x*x for x in xs)
    gamma = num / den if den != 0.0 else 1.0
    return PowerFit(min_db=min_db, max_db=max_db, gamma=float(gamma))


def write_fit_to_mapping(entity: str, param_name: str, fit: PowerFit) -> bool:
    """Update mixer_mappings/{entity}_channel.params_meta entry for param_name with fit."""
    try:
        from google.cloud import firestore  # type: ignore
    except Exception as e:
        print("ERROR: google-cloud-firestore not installed or not configured.", file=sys.stderr)
        return False

    # Write to dev-display-value database (same as where piecewise mappings are stored)
    try:
        client = firestore.Client(database='dev-display-value')
    except Exception as e:
        print(f"ERROR: cannot connect to Firestore dev-display-value database: {e}", file=sys.stderr)
        return False

    doc_id = f"{entity}_channel"
    ref = client.collection("mixer_mappings").document(doc_id)
    snap = ref.get()
    data: Dict[str, Any] = snap.to_dict() if snap.exists else {}
    params_meta = data.get("params_meta") or []
    # locate param meta
    found = False
    for pm in params_meta:
        if str(pm.get("name", "")).lower() == param_name.lower():
            pm["fit"] = fit.to_dict()
            # enforce canonical unit
            pm.setdefault("unit", "dB")
            found = True
            break
    if not found:
        params_meta.append({"name": param_name, "unit": "dB", "fit": fit.to_dict()})
    data["params_meta"] = params_meta
    try:
        ref.set(data, merge=True)
        return True
    except Exception as e:
        print(f"ERROR: failed to write fit for {entity}/{param_name}: {e}", file=sys.stderr)
        return False


def main() -> int:
    # Fit track volume - auto-detect range from piecewise data
    vol_pts = load_piecewise_points("volume")
    # Find the dB values where normalized hits 0 and 1
    vol_min_db = min(db for db, norm in vol_pts if norm <= 0.001)
    vol_max_db = max(db for db, norm in vol_pts if norm >= 0.999)
    print(f"Volume range detected: {vol_min_db:.1f} to {vol_max_db:.1f} dB")
    vol_fit = fit_power_from_points(vol_pts, min_db=vol_min_db, max_db=vol_max_db)
    print(f"Fitted track volume gamma={vol_fit.gamma:.6f}")
    ok1 = write_fit_to_mapping("track", "volume", vol_fit)

    # Fit track send - auto-detect range from piecewise data
    snd_pts = load_piecewise_points("send")
    # Find the dB values where normalized hits min and max
    snd_min_db = min(db for db, norm in snd_pts if norm <= 0.001)
    snd_max_db = max(db for db, norm in snd_pts)  # Use actual max, not where norm=1
    print(f"Send range detected: {snd_min_db:.1f} to {snd_max_db:.1f} dB")
    snd_fit = fit_power_from_points(snd_pts, min_db=snd_min_db, max_db=snd_max_db)
    print(f"Fitted track send gamma={snd_fit.gamma:.6f}")
    ok2 = write_fit_to_mapping("track", "send", snd_fit)

    # Mirror to return channel as well (same models typically apply)
    ok3 = write_fit_to_mapping("return", "volume", vol_fit)
    ok4 = write_fit_to_mapping("return", "send", snd_fit)

    # Note: Master channel (volume/cue) can be added similarly if desired.

    all_ok = ok1 and ok2 and ok3 and ok4
    print("\nSummary:")
    print(f"  track.volume updated: {ok1}")
    print(f"  track.send   updated: {ok2}")
    print(f"  return.volume updated: {ok3}")
    print(f"  return.send   updated: {ok4}")
    return 0 if all_ok else 2


if __name__ == "__main__":
    raise SystemExit(main())

