#!/usr/bin/env python3
"""
Export a compact per-signature digest for offline LLM analysis.

Two modes:
1) By known signature:
   python3 scripts/export_signature_digest.py --signature <SIG> --out digest.json

2) By live return/device (server must be running):
   python3 scripts/export_signature_digest.py --return 0 --device 0 --out digest.json

The digest includes:
- signature
- device_name (best-effort)
- preset_count
- per-parameter summary with:
  - index, name, min, max
  - numeric_display: stats (count, unique, min, p25, median, p75, max)
  - labels: list of distinct non-numeric display strings (if any)

It pulls data from the running server (127.0.0.1:8722) using:
- /presets?structure_signature=...
- /presets/{preset_id}
- /return/device/params and /return/devices (when computing signature from live)

Note: This script does not require Firestore credentials; it queries the server API.
"""
import argparse
import json
import math
import statistics
import sys
from typing import Any, Dict, List, Optional, Tuple

import urllib.request
import urllib.parse

SERVER = "http://127.0.0.1:8722"


def _get(url: str) -> Dict[str, Any]:
    with urllib.request.urlopen(url, timeout=5) as resp:
        data = resp.read()
        return json.loads(data.decode("utf-8"))


def _make_signature_from_live(ret_idx: int, dev_idx: int) -> Tuple[str, Optional[str]]:
    # Fetch device name
    devs = _get(f"{SERVER}/return/devices?index={ret_idx}")
    device_name = None
    for d in ((devs or {}).get("data") or {}).get("devices", []):
        if int(d.get("index", -1)) == int(dev_idx):
            device_name = str(d.get("name", f"Device {dev_idx}"))
            break
    # Fetch params and compute signature on server side via map endpoint
    ms = _get(f"{SERVER}/return/device/map?index={ret_idx}&device={dev_idx}")
    sig = str(ms.get("signature") or "")
    return sig, device_name


def _parse_display_num(s: Any) -> Optional[float]:
    if s is None:
        return None
    try:
        # Common numeric strings already look like 250.0, 58.0, etc.
        # Extract first number
        import re
        m = re.search(r"-?\d+(?:\.\d+)?", str(s))
        if not m:
            return None
        return float(m.group(0))
    except Exception:
        return None


def _summarize(values: List[float]) -> Dict[str, Any]:
    if not values:
        return {"count": 0, "unique": 0}
    vals = sorted(values)
    out = {
        "count": len(vals),
        "unique": len(set(vals)),
        "min": vals[0],
        "p25": vals[int(0.25 * (len(vals)-1))],
        "median": statistics.median(vals),
        "p75": vals[int(0.75 * (len(vals)-1))],
        "max": vals[-1],
    }
    return out


def export_digest(signature: str, out_path: str) -> None:
    # List presets for signature
    qs = urllib.parse.urlencode({"structure_signature": signature})
    pres = _get(f"{SERVER}/presets?{qs}")
    preset_summaries = (pres or {}).get("presets", [])
    # Fetch detail for each preset to build per-parameter aggregates
    per_param: Dict[str, Dict[str, Any]] = {}
    device_name: Optional[str] = None
    for ps in preset_summaries:
        pid = ps.get("id") or ps.get("preset_id")
        if not pid:
            continue
        detail = _get(f"{SERVER}/presets/{pid}")
        if not device_name:
            device_name = detail.get("device_name") or detail.get("name")
        pvals = dict(detail.get("parameter_values") or {})
        pdisp = dict(detail.get("parameter_display_values") or {})
        # On first preset, seed per_param with structural info from server live if available
        for pname, val in pvals.items():
            rec = per_param.setdefault(pname, {
                "name": pname,
                "index": None,
                "min": None,
                "max": None,
                "numeric_display": [],
                "labels": set(),
            })
            # Collect numeric display if possible, else label bucket
            dstr = pdisp.get(pname)
            num = _parse_display_num(dstr)
            if num is not None:
                rec["numeric_display"].append(float(num))
            elif dstr is not None:
                rec["labels"].add(str(dstr))

    # Build digest structure
    out: Dict[str, Any] = {
        "signature": signature,
        "device_name": device_name,
        "preset_count": len(preset_summaries),
        "params": [],
    }
    for pname, rec in per_param.items():
        nums = rec.get("numeric_display") or []
        labs = list(sorted(rec.get("labels") or []))
        out["params"].append({
            "name": pname,
            "index": rec.get("index"),
            "min": rec.get("min"),
            "max": rec.get("max"),
            "numeric_display_stats": _summarize(nums),
            "labels": labs,
        })

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)
    print(f"Wrote digest for signature {signature} with {len(out['params'])} params to {out_path}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--signature", help="Structure signature (SHA1)")
    ap.add_argument("--return", dest="ret", type=int, help="Return index (0-based)")
    ap.add_argument("--device", dest="dev", type=int, help="Device index (0-based)")
    ap.add_argument("--out", required=True, help="Output JSON path")
    args = ap.parse_args()

    sig = args.signature
    if not sig:
        if args.ret is None or args.dev is None:
            print("Either --signature or (--return and --device) is required", file=sys.stderr)
            sys.exit(2)
        sig, _ = _make_signature_from_live(int(args.ret), int(args.dev))
        if not sig:
            print("Failed to compute signature from live", file=sys.stderr)
            sys.exit(3)
    export_digest(sig, args.out)


if __name__ == "__main__":
    main()

