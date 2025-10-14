#!/usr/bin/env python3
"""
Fit continuous parameter models from captured presets via server API and import results.

Usage:
  python3 scripts/fit_params_from_presets.py --signature <SIG> [--import]
  python3 scripts/fit_params_from_presets.py --return 0 --device 0 [--import]

Models tried per param:
  - linear: y = a*x + b
  - log:    y = a*ln(x+eps) + b
  - exp:    y = exp(a*x + b)  (use ln(y) for regression; only y>0)

Select model by highest R^2, require monotonic sample trend; else skip.
Writes params_meta with {name,index?,control_type,unit_hint?,fit{type, coeffs, r2},confidence}.
If --import is set, POSTs to /device_mapping/import with analysis_status="partial_fits".
"""
import argparse
import json
import math
import statistics
from typing import Any, Dict, List, Optional, Tuple
import urllib.parse
import urllib.request
import time

SERVER = "http://127.0.0.1:8722"


def _get(url: str) -> Dict[str, Any]:
    with urllib.request.urlopen(url, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _post(url: str, payload: dict) -> dict:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _signature_from_live(ret_idx: int, dev_idx: int) -> str:
    ms = _get(f"{SERVER}/return/device/map?index={ret_idx}&device={dev_idx}")
    return str(ms.get("signature") or "")


def _parse_num(s: Any) -> Optional[float]:
    if s is None:
        return None
    try:
        import re
        m = re.search(r"-?\d+(?:\.\d+)?", str(s))
        if not m:
            return None
        return float(m.group(0))
    except Exception:
        return None


def _r2(y_true: List[float], y_pred: List[float]) -> float:
    if not y_true or len(y_true) != len(y_pred):
        return 0.0
    ybar = sum(y_true) / len(y_true)
    ss_tot = sum((y - ybar) ** 2 for y in y_true)
    ss_res = sum((y - yp) ** 2 for y, yp in zip(y_true, y_pred))
    return 1.0 - (ss_res / ss_tot) if ss_tot > 0 else 0.0


def _fit_linear(xs: List[float], ys: List[float]) -> Optional[Tuple[Dict[str, float], List[float], float]]:
    n = len(xs)
    if n < 3:
        return None
    sx = sum(xs); sy = sum(ys)
    sxx = sum(x*x for x in xs)
    sxy = sum(x*y for x, y in zip(xs, ys))
    denom = n * sxx - sx * sx
    if denom == 0:
        return None
    a = (n * sxy - sx * sy) / denom
    b = (sy - a * sx) / n
    y_pred = [a*x + b for x in xs]
    return ({"a": a, "b": b}, y_pred, _r2(ys, y_pred))


def _fit_log(xs: List[float], ys: List[float]) -> Optional[Tuple[Dict[str, float], List[float], float]]:
    n = len(xs)
    if n < 4:
        return None
    eps = 1e-6
    lx = [math.log(max(x, eps)) for x in xs]
    return _fit_linear(lx, ys)


def _fit_exp(xs: List[float], ys: List[float]) -> Optional[Tuple[Dict[str, float], List[float], float]]:
    # ln(y) = a*x + b => y = exp(a*x + b)
    n = len(xs)
    if n < 4:
        return None
    eps = 1e-6
    if any(y <= 0 for y in ys):
        return None
    ly = [math.log(max(y, eps)) for y in ys]
    res = _fit_linear(xs, ly)
    if not res:
        return None
    (coeffs, y_pred_ln, r2_ln) = res
    a = coeffs.get("a", 0.0); b = coeffs.get("b", 0.0)
    y_pred = [math.exp(a*x + b) for x in xs]
    return ({"a": a, "b": b}, y_pred, _r2(ys, y_pred))


def _is_monotonic(xs: List[float], ys: List[float]) -> bool:
    # Check that sample ys are non-decreasing with increasing x (tolerate tiny noise)
    last = None
    for x, y in sorted(zip(xs, ys), key=lambda t: t[0]):
        if last is None:
            last = y
            continue
        if y < last - 1e-6:
            return False
        last = max(last, y)
    return True


def fit_from_presets(signature: str, import_back: bool) -> Dict[str, Any]:
    qs = urllib.parse.urlencode({"structure_signature": signature})
    pres = _get(f"{SERVER}/presets?{qs}")
    preset_summaries = (pres or {}).get("presets", [])
    params_points: Dict[str, List[Tuple[float, float]]] = {}

    for ps in preset_summaries:
        pid = ps.get("id") or ps.get("preset_id")
        if not pid:
            continue
        detail = _get(f"{SERVER}/presets/{pid}")
        pvals = dict(detail.get("parameter_values") or {})
        pdisp = dict(detail.get("parameter_display_values") or {})
        for pname, x in pvals.items():
            y = _parse_num(pdisp.get(pname))
            if y is None:
                continue
            if not isinstance(x, (int, float)):
                continue
            arr = params_points.setdefault(pname, [])
            arr.append((float(x), float(y)))

    params_meta = []
    for pname, pts in params_points.items():
        if len(pts) < 6:
            continue
        xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
        # Require sample monotonicity; if not, skip and rely on JIT probes later
        if not _is_monotonic(xs, ys):
            continue
        candidates = []
        for fitter, ftype in ((_fit_linear, "linear"), (_fit_log, "log"), (_fit_exp, "exp")):
            res = fitter(xs, ys)
            if not res:
                continue
            coeffs, yhat, r2 = res
            candidates.append((ftype, coeffs, r2))
        if not candidates:
            continue
        # Pick best by R^2
        candidates.sort(key=lambda t: t[2], reverse=True)
        ftype, coeffs, r2 = candidates[0]
        confidence = max(0.0, min(1.0, (r2 - 0.85) / 0.15))  # crude
        params_meta.append({
            "name": pname,
            "control_type": "continuous",
            "fit": {"type": ftype, "coeffs": coeffs, "r2": r2},
            "confidence": confidence,
        })

    result = {
        "signature": signature,
        "preset_count": len(preset_summaries),
        "params_meta": params_meta,
        "run_id": int(time.time()),
    }

    if import_back and params_meta:
        payload = {
            "signature": signature,
            "params_meta": params_meta,
            "sources": {"preset_count": len(preset_summaries), "fit_run_id": result["run_id"]},
            "analysis_status": "partial_fits",
        }
        _post(f"{SERVER}/device_mapping/import", payload)

    print(json.dumps(result, indent=2))
    return result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--signature")
    ap.add_argument("--return", dest="ret", type=int)
    ap.add_argument("--device", dest="dev", type=int)
    ap.add_argument("--import", dest="do_import", action="store_true", help="Import fits into mapping")
    args = ap.parse_args()

    sig = args.signature
    if not sig:
        if args.ret is None or args.dev is None:
            raise SystemExit("Provide --signature or --return and --device")
        sig = _signature_from_live(int(args.ret), int(args.dev))
    fit_from_presets(sig, args.do_import)


if __name__ == "__main__":
    main()

