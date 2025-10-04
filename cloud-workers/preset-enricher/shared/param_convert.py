from __future__ import annotations

import math
from typing import Any, Dict, Optional, Tuple


def _forward_fit_y(fit: Dict[str, Any], x: float) -> Optional[float]:
    ftype = (fit or {}).get("type")
    if ftype == "linear":
        a = float(fit.get("a", 1.0)); b = float(fit.get("b", 0.0))
        return a * x + b
    if ftype == "log":
        a = float(fit.get("a", 1.0)); b = float(fit.get("b", 0.0))
        if x <= 0:
            return None
        return a * math.log(x) + b
    if ftype == "exp":
        a = float(fit.get("a", 1.0)); b = float(fit.get("b", 0.0))
        return math.exp(a * x + b)
    if ftype == "piecewise":
        pts = fit.get("points") or []
        pts = sorted([(float(p.get("x")), float(p.get("y"))) for p in pts if p.get("x") is not None and p.get("y") is not None])
        if not pts:
            return None
        lo = None; hi = None
        for xx, yy in pts:
            if xx <= x:
                lo = (xx, yy)
            if xx >= x and hi is None:
                hi = (xx, yy)
        if lo and hi and hi[0] != lo[0]:
            x1, y1 = lo; x2, y2 = hi
            t = (x - x1) / (x2 - x1)
            return y1 + t * (y2 - y1)
        return lo[1] if lo else hi[1]
    return None


def _invert_fit_to_value(fit: Dict[str, Any], target_y: float, vmin: float, vmax: float) -> float:
    ftype = fit.get("type")
    if ftype == "linear":
        a = float(fit.get("a", 1.0)); b = float(fit.get("b", 0.0))
        x = (target_y - b) / a if a != 0 else vmin
    elif ftype == "log":
        a = float(fit.get("a", 1.0)); b = float(fit.get("b", 0.0))
        x = math.exp((target_y - b) / a) if a != 0 else vmin
    elif ftype == "exp":
        a = float(fit.get("a", 1.0)); b = float(fit.get("b", 0.0))
        x = (math.log(target_y) - b) / a if (a != 0 and target_y > 0) else vmin
    else:
        pts = fit.get("points") or []
        pts = sorted([(float(p.get("y")), float(p.get("x"))) for p in pts if p.get("x") is not None and p.get("y") is not None])
        if not pts:
            return vmin
        lo = None; hi = None
        for y, xx in pts:
            if y <= target_y:
                lo = (y, xx)
            if y >= target_y and hi is None:
                hi = (y, xx)
        if lo and hi and hi[0] != lo[0]:
            y1, x1 = lo; y2, x2 = hi
            tfrac = (target_y - y1) / (y2 - y1)
            x = x1 + tfrac * (x2 - x1)
        else:
            x = lo[1] if lo else hi[1]
    return max(vmin, min(vmax, float(x)))


def to_display(value: float, learned_param: Dict[str, Any]) -> Tuple[str, Optional[float]]:
    vmin = float(learned_param.get("min", 0.0))
    vmax = float(learned_param.get("max", 1.0))
    unit = learned_param.get("unit")
    ctype = str(learned_param.get("control_type") or "").lower()

    label_map = learned_param.get("label_map") or {}
    samples = learned_param.get("samples") or []
    if ctype in ("binary", "quantized") or label_map or (len({str(s.get("display","")) for s in samples if s.get("display") is not None}) <= 2):
        best = None; bestd = 1e9
        for s in samples:
            sv = float(s.get("value", vmin))
            d = abs(sv - value)
            if d < bestd:
                bestd = d; best = s
        if best and best.get("display") is not None:
            disp = str(best.get("display"))
            dnum = best.get("display_num")
            try:
                dnum = float(dnum) if dnum is not None else None
            except Exception:
                dnum = None
            return disp, dnum
        return f"{value:.3f}", None

    fit = learned_param.get("fit")
    if fit:
        y = _forward_fit_y(fit, float(value))
        if y is not None and math.isfinite(y):
            disp = f"{y:.2f}{(' ' + unit) if unit else ''}" if unit else f"{y:.2f}"
            return disp, float(y)

    if samples:
        pts = sorted([(float(s.get("value", vmin)), s) for s in samples if s.get("display") is not None])
        lo = None; hi = None
        for xv, s in pts:
            if xv <= value:
                lo = (xv, s)
            if xv >= value and hi is None:
                hi = (xv, s)
        if lo and hi:
            lsd = lo[1].get("display"); hsd = hi[1].get("display")
            ln = lo[1].get("display_num"); hn = hi[1].get("display_num")
            if ln is not None and hn is not None:
                try:
                    ln = float(ln); hn = float(hn)
                    t = 0.0 if hi[0]==lo[0] else (value - lo[0])/(hi[0]-lo[0])
                    y = ln + t*(hn - ln)
                    disp = f"{y:.2f}{(' ' + unit) if unit else ''}" if unit else f"{y:.2f}"
                    return disp, float(y)
                except Exception:
                    pass
            if lsd is not None and hsd is not None:
                return (str(lsd), None) if abs(value - lo[0]) <= abs(value - hi[0]) else (str(hsd), None)
        elif lo:
            return str(lo[1].get("display")), None
        elif hi:
            return str(hi[1].get("display")), None

    return f"{value:.3f}", None


def to_normalized(target_display_num: float, learned_param: Dict[str, Any]) -> float:
    vmin = float(learned_param.get("min", 0.0))
    vmax = float(learned_param.get("max", 1.0))
    fit = learned_param.get("fit")
    if fit:
        return _invert_fit_to_value(fit, float(target_display_num), vmin, vmax)
    samples = learned_param.get("samples") or []
    best = None; bestd = 1e9
    for s in samples:
        dy = s.get("display_num")
        if dy is None:
            continue
        try:
            d = abs(float(dy) - float(target_display_num))
        except Exception:
            continue
        if d < bestd:
            bestd = d; best = s
    if best:
        return float(best.get("value", vmin))
    return vmin

